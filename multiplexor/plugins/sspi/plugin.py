import asyncio
import websockets
import json

from multiplexor.plugins.plugins import *
from multiplexor.plugins.sspi.pluginprotocol import *
from multiplexor.plugins.sspi.plugininfo import *
from multiplexor.logger.logger import *
	
class SSPIOperator:
	"""
	This class handles one incoming csocket connection.
	"""
	def __init__(self, session_id, logQ, operator_websocket, plugin_params, agent_out, plugin_info):
		self.logger = Logger('SSPIOperator', logQ=logQ)
		self.session_id = session_id
		self.operator_websocket = operator_websocket # data coing in from this ws, it the data send by the operator
		self.plugin_params = plugin_params
		self.agent_out = agent_out  # data being pushed in this queue will get delivered to the agent's sspi plugin
		self.plugin_info = plugin_info
		
		self.agent_in = asyncio.Queue() #data coing in is the data from the agent's SSPI plugin
		self.handler_task = None

	@mpexception
	async def terminate(self):
		##terminating client SSPI
		await self.logger.info('Terminating SSPI plugin for session %s' % self.session_id)
		cmd = SSPITerminateCmd()
		cmd.session_id = self.session_id
		try:
			await self.agent_out.put(cmd.to_bytes())
		except:
			#maybe the client is dead as well, don't carte at this point
			pass

		##terminating operator SSPI
		cmd = SSPITerminateCmd()
		cmd.session_id = self.session_id
		try:
			await self.operator_websocket.send(json.dumps(cmd.to_dict()))
		except Exception as e:
			pass

		if self.handler_task is not None:
			self.handler_task.cancel()
		
	@mpexception
	async def handle_sspi_client(self):
		#notifying the agent to create a new "socket"
		cmd = SSPIConnectCmd()
		cmd.session_id = str(self.session_id)
		await self.agent_out.put(cmd.to_bytes())
		
		agent_reply = await self.agent_in.get()
		if agent_reply.cmdtype != SSPICmdType.CONNECT:
			await self.logger.error('Session died :( %s' % self.session_id)
			return
		
		while True:
			#now we wait for the websocket client's commands that we will dispatch to the remote end 
			#and then wait for the response and dispatch it to the socket
			try:
				data = await self.operator_websocket.recv()
			
			except Exception as e:
				#this point the operator's sspi plugin crashed/terminated ungracefully
				# we need to notify the remote client to close the plugin
				await self.logger.info('Operator SSPI channel error! Session %s Reason: %s' % (self.session_id, str(e)))
				await self.terminate()
				return

			#print(data)
			cmd = SSPIPluginCMD.from_dict(json.loads(data))
			cmd.session_id = self.session_id
			#print(cmd.cmdtype)
			#sending command to remote plugin session
			await self.agent_out.put(cmd.to_bytes())
			
			reply = await self.agent_in.get()
			
			#await self.logger.debug('Got reply!')		
			#print(reply.to_dict())
			
			try:
				await self.operator_websocket.send(json.dumps(reply.to_dict()))
			except Exception as e:
				#this point the client's sspi plugin crashed/terminated ungracefully
				#we need to notify the operator to close the plugin
				await self.logger.info('Operator SSPI channel error! Session %s Reason: %s' % (self.session_id, str(e)))
				await self.terminate()
				return
	
	@mpexception
	async def run(self):
		self.handler_task = asyncio.create_task(self.handle_sspi_client())
		await self.handler_task

class MultiplexorSSPI(MultiplexorPluginBase):
	def __init__(self, plugin_id, logQ, plugin_type, plugin_params):
		MultiplexorPluginBase.__init__(self, plugin_id, 'MultiplexorSocks5', logQ, plugin_type, plugin_params)
		
		self.dispatch_table = {} #session_id to Socks5Client
		self.current_session_id = 0
	
	@mpexception		
	async def terminate(self):
		await self.logger.debug('MultiplexorSSPI terminate called!')
		for session_id in self.dispatch_table:
			await self.dispatch_table[session_id].terminate()
		
		if self.server is not None:
			self.server.close()
		return
	
	@mpexception		
	async def handle_plugin_data_in(self):
		"""
		Handles the incoming commands from the remote agent's plugin
		"""
		while True:
			data = await self.plugin_in.get()
			if data is None:
				await self.terminate()
				return
			#print('Got plugin data!')
			cmd = SSPIPluginCMD.from_bytes(data)
			#print('SSPI Plugin data in from remote agent SSPI: %s' % str(cmd))
			
			await self.dispatch_table[cmd.session_id].agent_in.put(cmd)
		
		await self.logger.debug('handle_plugin_data_in exiting!')
		
	@mpexception
	async def handle_client(self, operator_websocket, path):
		"""
		This task gets invoked each time a new operator connects to the listener socket
		"""
		client_ip, client_port = operator_websocket.remote_address
		await self.logger.info('operator connected from %s:%s' % (client_ip, client_port))
		self.plugin_info.active_connections['%s:%s' % (client_ip, client_port)] = None
		self.current_session_id += 1
		session_id = str(self.current_session_id)
		operator = SSPIOperator(session_id, self.logger.logQ, operator_websocket, self.plugin_params, self.plugin_out, self.plugin_info)
		self.dispatch_table[session_id] = operator
		await operator.run()
		await self.logger.info('operator disconnected (%s:%s)' % (client_ip, client_port))
		del self.dispatch_table[session_id]
		del self.plugin_info.active_connections['%s:%s' % (client_ip, client_port)]
		try:
			await operator_websocket.close()
		except:
			pass
			
	async def setup(self):
		self.plugin_info = WinAPIPluginInfo()
		#if self.plugin_params:
		#	#print(self.plugin_params)
		#	#if self.plugin_params['listen_ip'] and self.plugin_params['listen_ip'].upper() != 'NONE':
		#	#	listen_ip = self.plugin_params['listen_ip']
		#	#if self.plugin_params['listen_port'] and self.plugin_params['listen_port'].upper() != 'NONE':
		#	#	listen_port = int(self.plugin_params['listen_port'])
				
		self.server = await websockets.serve(self.handle_client, '127.0.0.1', 0, ssl=None)
		
		self.plugin_info.listen_ip, self.plugin_info.listen_port = self.server.sockets[0].getsockname()
		await self.logger.info('SSPI Server is now listening on %s:%s' % (self.plugin_info.listen_ip, self.plugin_info.listen_port))
	
	@mpexception
	async def run(self):
		"""
		The main function of the plugin.
		Sets up a listener server and the Task to dispatch incoming commands to the appropriate sockets
		"""
		asyncio.ensure_future(self.handle_plugin_data_in())
		await self.server.wait_closed()
			