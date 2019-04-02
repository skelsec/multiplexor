import asyncio

from multiplexor.plugins.plugins import *

class MultiplexorSocks5SocketProxy:
	def __init__(self, logQ):
		"""
		Handels the socket after the socks5 setup is completed
		"""
		self.logger = Logger(plugin_name, logQ)
		self.socket_id = None
		self.socket_terminated_evt = None
		
		self.reader = None
		self.writer = None
		self.socket_queue_in = None
		self.socket_queue_out = None
		
	async def proxy_send(self, reader, ):
		while not self.socket_broken_evt.is_set() or not self.plugin_broken_evt.is_set() or not self.stop_plugin_evt.is_set() or not socket_terminated_evt.is_set():
			#todo: check timeout
			try:
				data = await reader.read(4096)
			except Exception as e:
				await self.logger.info('reader exception! %s' % e)
				#notifying reader/writer that socket is terminated
				socket_terminated_evt.set()
				#notifying remote end that socket is terminated
				cmd = Socks5PluginSocketTerminatedEvent()
				await self.socket_queue_out(cmd.to_bytes())
				
			else:
				#sending recieved data to the remote agent
				cmd = Socks5PluginSocketDataCmd()
				cmd.data = data
				await self.plugin_out(cmd.to_bytes())
	
	
	async def proxy_recv(self, writer, socket_terminated_evt):
		while not self.socket_broken_evt.is_set() or not self.plugin_broken_evt.is_set() or not self.stop_plugin_evt.is_set() or not socket_terminated_evt.is_set():
			data = await self.plugin_in.get()
			cmd = Socks5PluginCMD.from_bytes(data)
			if cmd.cmdtype == SOCKET_DATA:
				writer.write(cmd.data)
			
			elif cmd.cmdtype == SOCKET_TERMINATED_EVT or cmd.cmdtype == PLUGIN_ERROR:
				#remote agent's socket broken, closing down ours as well
				writer.close()
				socket_terminated_evt.set()
				
			else:
				await self.logger.info('Got unexpected command type: %s' % cmd.cmdtype)	
	
		

class MultiplexorSocks5(MultiplexorPluginBase):
	def __init__(self, logQ):
		MultiplexorPluginBase.__init__(self,'MultiplexorSocks5', logQ)
		
		self.mutual_auth_type = None
		self.supported_auth_types = [SOCKS5Method.NOAUTH]
		self.current_state = SOCKS5ServerState.NEGOTIATION
		self.parser = SOCKS5CommandParser
		
		self.plugin_broken_evt = asyncio.Event()
		

	async def handle_socket_data_in(self):
		pass
			
	
				
	async def handle_socks_client(reader, writer):
		while not self.stop_plugin_evt.is_set():
			msg = await self.parser.from_streamreader(reader)
			
			if self.current_state == SOCKS5ServerState.NEGOTIATION:
				mutual, mutual_idx = get_mutual_preference(self.supported_auth_types, msg.METHODS)
				if mutual is None:
					await self.logger.debug('No common authentication types! Client supports %s' % (','.join([str(x) for x in msg.METHODS])))
					t = await asyncio.wait_for(self.socket_send(SOCKS5NegoReply.construct_auth(SOCKS5Method.NOTACCEPTABLE).to_bytes()), timeout = 1)
					break
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

				t = await asyncio.wait_for(self.socket_send(SOCKS5NegoReply.construct(self.mutual_auth_type).to_bytes()), timeout = 1)
		
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
					#in this case the server acts as a normal socks5 server
					
					#now we need to notify the agent's plugin on the remote end that a new connection is inbound
					#TODO
					
					#######proxy_reader, proxy_writer = await asyncio.wait_for(asyncio.open_connection(host=str(msg.DST_ADDR),port = msg.DST_PORT), timeout=1)
					await self.logger.debug('Connected!')
					
					
					self.session.current_state = SOCKS5ServerState.RELAYING
					#we need to notify the socket client that the connection sucseeded
					t = await asyncio.wait_for(self.send_data(SOCKS5Reply.construct(SOCKS5ReplyType.SUCCEEDED, self.session.allinterface, 0).to_bytes()), timeout = 1)
					#######self.loop.create_task(self.proxy_forwarder(proxy_reader, self.cwriter, (str(msg.DST_ADDR),int(msg.DST_PORT)), self.caddr))
					#######self.loop.create_task(self.proxy_forwarder(self.creader, proxy_writer, self.caddr, (str(msg.DST_ADDR),int(msg.DST_PORT))))

					await asyncio.wait_for(self.session.proxy_closed.wait(), timeout = None)
					break
						

				else:
					t = await asyncio.wait_for(SOCKS5Reply.construct(SOCKS5ReplyType.COMMAND_NOT_SUPPORTED, self.session.allinterface, 0).to_bytes(), timeout = 1)
		
			
		self.stop_plugin_evt.set()
			
			
			
			
	
	await run(self):
		while not self.stop_plugin_evt.is_set():
			server = await asyncio.start_server(handle_socks_client, '127.0.0.1', 0)
			await server.serve_forever()
			
			
			