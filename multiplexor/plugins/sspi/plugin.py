import asyncio
import websockets
import json

from multiplexor.plugins.plugins import *
from multiplexor.plugins.sspi.pluginprotocol import *
from multiplexor.plugins.sspi.plugininfo import *
from multiplexor.logger.logger import *
	
class SSPIClient:
	"""
	This class handles one incoming csocket connection.
	"""
	def __init__(self, session_id, logQ, websocket, stop_plugin_evt, plugin_params, plugin_out, plugin_info):
		self.logger = Logger('SSPIClient', logQ=logQ)
		self.stop_plugin_evt = stop_plugin_evt
		self.session_id = session_id
		self.websocket = websocket
		self.plugin_params = plugin_params
		self.plugin_out = plugin_out
		self.plugin_info = plugin_info
		
		self.remote_in = asyncio.Queue()
	
	@mpexception
	async def handle_sspi_client(self):
		#notifying the agent to create a new "socket"
		cmd = SSPIConnectCmd()
		cmd.session_id = str(self.session_id)
		await self.plugin_out.put(cmd.to_bytes())
		
		agent_reply = await self.remote_in.get()
		if agent_reply.cmdtype != SSPICmdType.CONNECT:
			await self.logger.error('Session died :( %s' % self.session_id)
			return
		
		while True:
			#now we wait for the websocket client's commands that we will dispatch to the remote end 
			#and then wait for the response and dispatch it to the socket
			data = await self.websocket.recv()
			print(data)
			cmd = SSPIPluginCMD.from_dict(json.loads(data))
			cmd.session_id = self.session_id
			print(cmd.cmdtype)
			#sending command to remote plugin session
			await self.plugin_out.put(cmd.to_bytes())
			
			reply = await self.remote_in.get()
			await self.logger.debug('Got reply!')		
			print(reply.to_dict())
			
			await self.websocket.send(json.dumps(reply.to_dict()))
		

class MultiplexorSSPI(MultiplexorPluginBase):
	def __init__(self, plugin_id, logQ, plugin_type, plugin_params):
		MultiplexorPluginBase.__init__(self, plugin_id, 'MultiplexorSocks5', logQ, plugin_type, plugin_params)
		
		self.dispatch_table = {} #session_id to Socks5Client
		self.current_session_id = 0
	
	@mpexception		
	async def terminate(self):
		#TODO!
		return
	
	@mpexception		
	async def handle_plugin_data_in(self):
		"""
		Handles the incoming commands from the remote agent's plugin
		"""
		while not self.stop_plugin_evt.is_set():
			data = await self.plugin_in.get()
			#print('Got plugin data!')
			cmd = SSPIPluginCMD.from_bytes(data)
			print(str(cmd))
			
			"""
			if cmd.session_id not in self.dispatch_table and cmd.cmdtype != WinAPICmdType.PLUGIN_ERROR:
				#This happens this the client connection was terminated on the server (our) side, but the agent still haven't recieved the
				#appropriate socket terminated event and sends more data to the socket that has been already closed
			
				#print('Socket ID is not in the dispatch table %s' % cmd.session_id)
				continue
			"""
			if cmd.cmdtype == SSPICmdType.TERMINATED:
				#plugin crashed on the remote end :(
				self.stop_plugin_evt.set()
			
			else:
				await self.dispatch_table[cmd.session_id].remote_in.put(cmd)
		
		print('handle_plugin_data_in exiting!')
		
	@mpexception
	async def handle_client(self, websocket, path):
		"""
		This task gets invoked each time a new client connects to the listener socket
		"""
		client_ip, client_port = websocket.remote_address
		await self.logger.info('Client connected from %s:%s' % (client_ip, client_port))
		self.plugin_info.active_connections['%s:%s' % (client_ip, client_port)] = None
		self.current_session_id += 1
		session_id = str(self.current_session_id)
		client = SSPIClient(session_id, self.logger.logQ, websocket, self.stop_plugin_evt, self.plugin_params, self.plugin_out, self.plugin_info)
		self.dispatch_table[session_id] = client
		await client.handle_sspi_client()
		await self.logger.info('Client disconnected (%s:%s)' % (client_ip, client_port))
		del self.dispatch_table[session_id]
		del self.plugin_info.active_connections['%s:%s' % (client_ip, client_port)]
		try:

			websocket.close()
		except:
			pass
			
	async def setup(self):
		self.plugin_info = WinAPIPluginInfo()
		listen_ip = '127.0.0.1'
		listen_port = 0
		if self.plugin_params:
			print(self.plugin_params)
			if self.plugin_params['listen_ip'] and self.plugin_params['listen_ip'].upper() != 'NONE':
				listen_ip = self.plugin_params['listen_ip']
			if self.plugin_params['listen_port'] and self.plugin_params['listen_port'].upper() != 'NONE':
				listen_port = int(self.plugin_params['listen_port'])
				
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
			