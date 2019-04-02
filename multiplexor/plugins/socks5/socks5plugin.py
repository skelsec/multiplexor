import asyncio

from multiplexor.plugins.plugins import *

class MultiplexorSocks5SocketProxy:
	def __init__(self):
		"""
		Handels the socket after the socks5 setup is completed
		"""
		self.logger = None
		self.socket_id = None
		self.socket_terminated_evt = None
		self.plugin_broken_evt = None
		
		self.reader = None
		self.writer = None
		self.socket_queue_in = None
		self.socket_queue_out = None
		
	async def proxy_send(self):
		while not self.socket_terminated_evt.is_set() or not self.plugin_broken_evt.is_set():
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
				await self.plugin_out(cmd.to_bytes())
				return
				
			else:
				if not data:
					#socket terminated...
					await self.logger.info('reader exception! %s' % e)
					#notifying reader/writer that socket is terminated
					self.socket_terminated_evt.set()
					#notifying remote end that socket is terminated
					cmd = Socks5PluginSocketTerminatedEvent()
					cmd.socket_id = self.socket_id
					await self.plugin_out(cmd.to_bytes())
					return
					
				#sending recieved data to the remote agent
				cmd = Socks5PluginSocketDataCmd()
				cmd.socket_id = self.socket_id
				cmd.data = self.data
				await self.plugin_out(cmd.to_bytes())
	
	
	async def proxy_recv(self):
		while not self.socket_terminated_evt.is_set() or not self.plugin_broken_evt.is_set():
			cmd = await self.socket_queue_in.get()
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
		
		self.dispatch_table = {} #socket_id to destination queue
		
		self.current_socket_id = 0
		
			
	async def handle_plugin_data_in(self):
		while not self.plugin_broken_evt.is_set() or not self.stop_plugin_evt.is_set():
			data = await self.plugin_in.get()
			
			cmd = Socks5PluginCMD.from_bytes(data)
			if cmd.cmdtype == Socks5ServerCmdType.PLUGIN_CONNECT:
				await self.dispatch_table[cmd.socket_id].put(cmd)
				
			elif cmd.cmdtype == Socks5ServerCmdType.PLUGIN_LISTEN:
				await self.dispatch_table[cmd.socket_id].put(cmd)

			elif cmd.cmdtype == Socks5ServerCmdType.PLUGIN_UDP:
				await self.dispatch_table[cmd.socket_id].put(cmd)

			elif cmd.cmdtype == Socks5ServerCmdType.PLUGIN_ERROR:
				self.plugin_broken_evt.set()

			elif cmd.cmdtype == Socks5ServerCmdType.SOCKET_TERMINATED_EVT:
				await self.dispatch_table[cmd.socket_id].put(cmd)

			elif cmd.cmdtype == Socks5ServerCmdType.SOCKET_DATA:
				await self.dispatch_table[cmd.socket_id].put(cmd)
			else:
				await self.logger.info('Unknown data in')
		
	async def socket_send(self, writer, data):
		"""
		this is just a dumb helper function
		"""
		writer.write(data)
		await writer.drain()
				
	async def handle_socks_client(reader, writer):
		while not self.stop_plugin_evt.is_set():
			msg = await self.parser.from_streamreader(reader)
			
			if self.current_state == SOCKS5ServerState.NEGOTIATION:
				mutual, mutual_idx = get_mutual_preference(self.supported_auth_types, msg.METHODS)
				if mutual is None:
					await self.logger.debug('No common authentication types! Client supports %s' % (','.join([str(x) for x in msg.METHODS])))
					t = await asyncio.wait_for(self.socket_send(writer, SOCKS5NegoReply.construct_auth(SOCKS5Method.NOTACCEPTABLE).to_bytes()), timeout = 1)
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

				t = await asyncio.wait_for(self.socket_send(writer, SOCKS5NegoReply.construct(self.mutual_auth_type).to_bytes()), timeout = 1)
		
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
					iq = asyncio.Queue()
					socket_id = str(self.current_socket_id)
					self.current_socket_id += 1
					self.dispatch_table[socket_id] = iq
					
					
					cmd = Socks5PluginConnectCmd()
					cmd.socket_id = socket_id
					cmd.dst_addr = str(msg.DST_ADDR)
					cmd.dst_port = str(msg.DST_PORT)
					
					await self.plugin_out.put(cmd.to_bytes())
					
					agent_reply = await self.dispatch_table[self.current_socket_id].get()
					
					if agent_reply.cmdtype == ServerCMDType.PLUGIN_CONNECT:
						#agent sucsessfully connected to the remote end! cool!
						#now we need to set up a socket proxy class, and give it the iq queue (that is still in the dispatch table)
						await self.logger.debug('Connected!')
						proxy = MultiplexorSocks5SocketProxy()
						proxy.logger = Logger(plugin_name, logQ)
						proxy.socket_id = socket_id
						proxy.socket_terminated_evt = asyncio.Event()
						
						proxy.reader = reader
						proxy.writer = writer
						proxy.socket_queue_in = iq
						proxy.socket_queue_out = self.plugin_out
						proxy.plugin_broken_evt = self.plugin_broken_evt
						proxy.run()
						
						#also we need to set up an outbound function
						asyncio.ensure_future(self.handle_socket_data_out(proxy))
						
						#now we wait for the connection to finish
						await proxy.socket_terminated_evt.wait()
						return
					
					else:
						#agent failed to set up the connection :(
						writer.close()
						del self.dispatch_table[socket_id]
						return

				else:
					t = await asyncio.wait_for(SOCKS5Reply.construct(SOCKS5ReplyType.COMMAND_NOT_SUPPORTED, self.session.allinterface, 0).to_bytes(), timeout = 1)		
			
	
	await run(self):
		while not self.stop_plugin_evt.is_set():
			server = await asyncio.start_server(handle_socks_client, '127.0.0.1', 0)
			await server.serve_forever()
			
			
			