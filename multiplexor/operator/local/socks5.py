import asyncio
import weboskcets

from multiplexor.operator.protocol import *
from multiplexor.logger.logger import *

class MultiplexorSocks5SocketProxy:
	def __init__(self):
		"""
		Handles the socket after the socks5 setup is completed.
		
		"""
		self.logger = None
		self.socket_id = None
		self.socket_terminated_evt = None
		self.stop_plugin_evt = None
		
		self.reader = None
		self.writer = None
		self.socket_queue_in = None
		self.socket_queue_out = None
		
		self.server = None
		
	def run(self):
		asyncio.ensure_future(self.proxy_send())
		asyncio.ensure_future(self.proxy_recv())
		
	async def proxy_send(self):
		"""
		Reads the clinet socket, then encapsulates the read data in a socktDataCmd command and dispatches it to a queue.
		In case the client socket is closed it emits a Socks5PluginSocketTerminatedEvent to notify the remote end
		"""
		while not self.socket_terminated_evt.is_set() or not self.stop_plugin_evt.is_set():
			#todo: check timeout
			try:
				data = await self.reader.read(4096)
			except Exception as e:
				await self.logger.info('reader exception! %s' % e)
				#notifying reader/writer that socket is terminated
				self.socket_terminated_evt.set()
				#notifying remote end that socket is terminated
				cmd = Socks5PluginSocketTerminatedEvent()
				cmd.socket_id = self.socket_id
				await self.socket_queue_out.put(cmd.to_bytes())
				return
				
			else:
				if not data:
					#socket terminated...
					await self.logger.info('Client terminated the connection!')
					#notifying reader/writer that socket is terminated
					self.socket_terminated_evt.set()
					#notifying remote end that socket is terminated
					cmd = Socks5PluginSocketTerminatedEvent()
					cmd.socket_id = self.socket_id
					await self.socket_queue_out.put(cmd.to_bytes())
					return
					
				#sending recieved data to the remote agent
				cmd = Socks5PluginSocketDataCmd()
				cmd.socket_id = self.socket_id
				cmd.data = data
				await self.socket_queue_out.put(cmd.to_bytes())
	
	
	async def proxy_recv(self):
		"""
		Dequeues the incoming command if it's data then writes the data byers to the socket.
		In case SOCKET_TERMINATED_EVT the socket will be closed and the event to shut down the socket proxy is set
		"""
		while not self.socket_terminated_evt.is_set() or not self.stop_plugin_evt.is_set():
			cmd = await self.socket_queue_in.get()
			if cmd.cmdtype == Socks5ServerCmdType.SOCKET_DATA:
				self.writer.write(cmd.data)
			
			elif cmd.cmdtype == Socks5ServerCmdType.SOCKET_TERMINATED_EVT:
				#remote agent's socket broken, closing down ours as well
				self.writer.close()
				self.socket_terminated_evt.set()
				
			else:
				await self.logger.info('Got unexpected command type: %s' % cmd.cmdtype)	



class MultiplexorSocks5Operator:
	def __init__(self, logger, connector, agent_id):
		self.logger = logger
		self.connector = connector
		
		self.agent_id = agent_id #id of the agent connected to the multiplexor server that will be used to relay connections to/from
		self.plugin_id = None

		self.socks5_listen_ip = '127.0.0.1'
		self.socks5_listen_port = 0

		self.current_socket_id = 0
		self.operator_token = str(uuid.uuid4())

		self.plugin_started_evt = asyncio.Event()
		self.dispatch_table = {} #socket_id to Socks5Client

	@mpexception
	async def handle_socks5(self):
		while not self.stop_plugin_evt.is_set():
			#for starting the socks5 part we give a maxiumum 2 seconds timeout for the socket client
			try:
				result = await asyncio.gather(*[asyncio.wait_for(self.parser.from_streamreader(self.reader, self.current_state, self.mutual_auth_type), timeout=None)], return_exceptions=True)
			except asyncio.CancelledError as e:
				return
			if isinstance(result[0], R3ConnectionClosed):
				return
			elif isinstance(result[0], Exception):
				#most likely parser error :(
				raise result[0]
				return
			else:
				msg = result[0]
			
			if self.current_state == SOCKS5ServerState.NEGOTIATION:
				mutual, mutual_idx = get_mutual_preference(self.supported_auth_types, msg.METHODS)
				if mutual is None:
					await self.logger.debug('No common authentication types! Client supports %s' % (','.join([str(x) for x in msg.METHODS])))
					t = await asyncio.wait_for(self.socket_send(SOCKS5NegoReply.construct_auth(SOCKS5Method.NOTACCEPTABLE).to_bytes()), timeout = 1)
					writer.close()
					return
				await self.logger.debug('Mutual authentication type: %s' % mutual)
				self.mutual_auth_type = mutual
				self.current_state = SOCKS5ServerState.REQUEST # if no authentication is requred then we skip the auth part
				"""
				self.session.mutual_auth_type = mutual
				self.session.authHandler = SOCKS5AuthHandler(self.session.mutual_auth_type, self.session.creds) 

				if self.session.mutual_auth_type == SOCKS5Method.NOAUTH:
					self.session.current_state = SOCKS5ServerState.REQUEST # if no authentication is requred then we skip the auth part
				else:
					self.session.current_state = SOCKS5ServerState.NOT_AUTHENTICATED
				"""

				t = await asyncio.wait_for(self.socket_send( SOCKS5NegoReply.construct(self.mutual_auth_type).to_bytes()), timeout = 1)
		
				"""
				elif self.session.current_state == SOCKS5ServerState.NOT_AUTHENTICATED:
					if self.session.mutual_auth_type == SOCKS5Method.PLAIN:
						status, creds = self.session.authHandler.do_AUTH(msg)
						await self.logger.credential(creds.to_credential())
						if status:
							self.session.current_state = SOCKS5ServerState.REQUEST
							t = await asyncio.wait_for(self.socket_send(SOCKS5NegoReply.construct_auth(SOCKS5Method.NOAUTH).to_bytes()), timeout = 1)
						else:
							t = await asyncio.wait_for(self.socket_send(SOCKS5NegoReply.construct_auth(SOCKS5Method.NOTACCEPTABLE).to_bytes()), timeout = 1)
							break
					else:
						#put GSSAPI implementation here
						raise Exception('Not implemented!')
				"""
			
			elif self.current_state == SOCKS5ServerState.REQUEST:
				await self.logger.debug('Remote client wants to connect to %s:%d' % (str(msg.DST_ADDR), msg.DST_PORT))
				if msg.CMD == SOCKS5Command.CONNECT:					
					#setting up socket_id and a dispatch table entry for our new socket
					#then sending the connection request info to the agent
					#then waiting for the agent's reply
					cmd = Socks5PluginConnectCmd()
					cmd.socket_id = str(self.socket_id)
					cmd.dst_addr = str(msg.DST_ADDR)
					cmd.dst_port = str(msg.DST_PORT)
					
					await self.plugin_out.put(cmd.to_bytes())
					
					#print('waiting 4 reply...')
					agent_reply = await self.remote_in.get()
					
					if agent_reply.cmdtype == Socks5ServerCmdType.PLUGIN_CONNECT:
						#agent sucsessfully connected to the remote end! cool!
						#now we need to set up a socket proxy class, and give it the iq queue (that is still in the dispatch table)
						await self.logger.debug('Connected!')
						proxy = MultiplexorSocks5SocketProxy()
						proxy.logger = Logger('Socks5Proxy', self.logger.logQ)
						proxy.socket_id = str(self.socket_id)
						proxy.socket_terminated_evt = asyncio.Event()
						
						proxy.reader = self.reader
						proxy.writer = self.writer
						proxy.socket_queue_in = self.remote_in
						proxy.socket_queue_out = self.plugin_out
						proxy.stop_plugin_evt = self.stop_plugin_evt
						
						#in case of succsess we send back the currently listening ip and port
						la, lp = self.writer.get_extra_info('sockname')
						rp = SOCKS5Reply.construct(SOCKS5ReplyType.SUCCEEDED, ipaddress.IPv4Address(la), lp)
						self.writer.write(rp.to_bytes())
						
						client_ip, client_port = self.writer.get_extra_info('peername')
						self.plugin_info.active_connections['%s:%s' % (client_ip,client_port)] = '%s:%s' % (msg.DST_ADDR, msg.DST_PORT)
						
						proxy.run()
						
						#now we wait for the connection to finish
						await proxy.socket_terminated_evt.wait()
						return
					
					else:
						#agent failed to set up the connection :(
						#notifying the socket client
						rp = SOCKS5Reply.construct(SOCKS5ReplyType.FAILURE, ipaddress.IPv4Address('0.0.0.0'), 0)
						self.writer.write(rp.to_bytes())
						
						self.writer.close()
						return

			else:
				t = await asyncio.wait_for(SOCKS5Reply.construct(SOCKS5ReplyType.COMMAND_NOT_SUPPORTED, self.session.allinterface, 0).to_bytes(), timeout = 1)	

	async def handle_socks_client(self, reader, writer):
		"""
		This task gets invoked each time a new client connects to the listener socket
		"""
		client_ip, client_port = writer.get_extra_info('peername')
		await self.logger.info('Client connected from %s:%s' % (client_ip, client_port))
		self.plugin_info.active_connections['%s:%s' % (client_ip, client_port)] = None
		self.current_socket_id += 1
		socket_id = str(self.current_socket_id)
		client = Socks5Client(socket_id, self.logger.logQ, reader, writer, self.stop_plugin_evt, self.plugin_params, self.plugin_out, self.plugin_info)
		self.dispatch_table[socket_id] = client
		await client.handle_socks5()
		await self.logger.info('Client disconnected (%s:%s)' % (client_ip, client_port))
		del self.dispatch_table[socket_id]
		del self.plugin_info.active_connections['%s:%s' % (client_ip, client_port)]
		try:

			writer.close()
		except:
			pass

	async def start_socks5_plugin(self):
		cmd = OperatorStartPlugin()
		cmd.cmdtype = OperatorCmdType.START_PLUGIN
		cmd.agent_id = rply.agent_id
		cmd.plugin_type = 0
		cmd.plugin_data = None
		cmd.operator_token = self.operator_token
		await self.connector.cmd_out_q.put(cmd)

		await self.plugin_started_evt.wait()
		await self.logger.info('SOCKS5 Plugin succsessfully started on the agent!')

	async def handle_server_rply(self):
		while not self.connector.server_diconnected.is_set():
			rply = await self.connector.cmd_in_q.get()
			if rply.cmdtype == OperatorCmdType.PLUGIN_STARTED and rply.operator_token == self.operator_token:
				self.plugin_started_evt.set()
				self.plugin_id = rply.plugin_id

			elif rply.cmdtype == OperatorCmdType.PLUGIN_DATA_EVT:
				cmd = Socks5PluginCMD.from_bytes(bytes.fromhex(rply.data))
				#print('socks5 plugin got cmd from agent!')
				#print(str(cmd))
				
				if cmd.socket_id not in self.dispatch_table and cmd.cmdtype != Socks5ServerCmdType.PLUGIN_ERROR:
					#This happens this the client connection was terminated on the server (our) side, but the agent still haven't recieved the
					#appropriate socket terminated event and sends more data to the socket that has been already closed
				
					#print('Socket ID is not in the dispatch table %s' % cmd.socket_id)
					continue
					
				if cmd.cmdtype == Socks5ServerCmdType.PLUGIN_CONNECT:
					#the remote agent acknowledges the socket creation request
					await self.dispatch_table[cmd.socket_id].remote_in.put(cmd)
					
				elif cmd.cmdtype == Socks5ServerCmdType.PLUGIN_LISTEN:
					#the remote agent acknowledges the remote listener request
					await self.dispatch_table[cmd.socket_id].remote_in.put(cmd)

				elif cmd.cmdtype == Socks5ServerCmdType.PLUGIN_UDP:
					#the remote agent acknowledges the udp bind request
					await self.dispatch_table[cmd.socket_id].remote_in.put(cmd)

				elif cmd.cmdtype == Socks5ServerCmdType.PLUGIN_ERROR:
					#plugin crashed on the remote end :(
					self.stop_plugin_evt.set()

				elif cmd.cmdtype == Socks5ServerCmdType.SOCKET_TERMINATED_EVT:
					#socket terminated on the remote agent's end
					await self.dispatch_table[cmd.socket_id].remote_in.put(cmd)

				elif cmd.cmdtype == Socks5ServerCmdType.SOCKET_DATA:
					#socket communication happening
					await self.dispatch_table[cmd.socket_id].remote_in.put(cmd)
				else:
					await self.logger.info('Unknown data in')
			
				#print('handle_plugin_data_in exiting!')

			

	async def run(self):
		self.logger.info('Watiting for server connection...')
		await self.connector.server_diconnected.wait()
		self.logger.info('Server connected! Setting up SOCKS5 proxy!')
		asyncio.ensure_future(self.handle_server_rply())
		self.logger.info('Starting SOCKS5 on the agent...')
		await self.start_socks5_plugin()

		self.server = await asyncio.start_server(self.handle_socks_client, self.socks5_listen_ip, self.socks5_listen_port)
		listen_ip, listen_port = self.server.sockets[0].getsockname()
		self.logger.info('Local SOCKS5 server listening on %s:%s' % (listen_ip, listen_port))
		await self.server.serve_forever()


if __name__ == '__main__':
	import argparse
