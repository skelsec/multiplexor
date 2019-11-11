import asyncio
import websockets
import json
import uuid

from multiplexor.plugins.plugintypes import *
from multiplexor.operator.protocol import *
from multiplexor.plugins.plugins import *
from multiplexor.plugins.sspi.pluginsettings import *
from multiplexor.plugins.sspi.pluginprotocol import *
from multiplexor.plugins.sspi.plugininfo import *
from multiplexor.plugins.sspi.plugin import SSPIOperator
from multiplexor.logger.logger import *


	
class MultiplexorSSPIOperator:
	def __init__(self, logQ, connector, agent_id):
		self.logger = Logger('SSPI', logQ = logQ)
		self.connector = connector
		
		self.agent_id = agent_id #id of the agent connected to the multiplexor server that will be used to relay connections to/from
		self.plugin_id = None

		self.sspi_listen_ip = '127.0.0.1'
		self.sspi_listen_port = 0

		self.current_session_id = 0
		self.operator_token = str(uuid.uuid4())

		self.plugin_started_evt = asyncio.Event()
		self.dispatch_table = {} #socket_id to SOCKS5LocalClient
		
		self.plugin_info = WinAPIPluginInfo()
		self.stop_plugin_evt = asyncio.Event()
		
		
	@mpexception		
	async def handle_plugin_data_in(self):
		"""
		Handles the incoming commands from the remote agent's plugin
		"""
		while self.connector.server_connected.is_set():
			rply = await self.connector.cmd_in_q.get()
			if rply.cmdtype == OperatorCmdType.PLUGIN_STARTED and rply.operator_token == self.operator_token:
				self.plugin_started_evt.set()
				self.plugin_id = rply.plugin_id
				
			elif rply.cmdtype == OperatorCmdType.PLUGIN_DATA_EVT:
				cmd = SSPIPluginCMD.from_bytes(bytes.fromhex(rply.data))
				#print(str(cmd))
				
				if cmd.cmdtype == SSPICmdType.TERMINATED:
					#plugin crashed on the remote end :(
					self.stop_plugin_evt.set()
				
				else:
					await self.dispatch_table[cmd.session_id].remote_in.put(cmd)
		await self.logger.info('handle_plugin_data_in exiting!')
		
	@mpexception
	async def handle_plugin_out(self, plugin_out_q):
		while self.connector.server_connected.is_set():
			data = await plugin_out_q.get()
			cmd = OperatorPluginData()
			cmd.agent_id = self.agent_id
			cmd.plugin_id = self.plugin_id
			cmd.data = data.hex()
			await self.connector.cmd_out_q.put(cmd)
		
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
		outQ = asyncio.Queue()
		asyncio.ensure_future(self.handle_plugin_out(outQ))
		client = SSPIOperator(session_id, self.logger.logQ, websocket, None, outQ, self.plugin_info)
		self.dispatch_table[session_id] = client
		await client.handle_sspi_client()
		await self.logger.info('Client disconnected (%s:%s)' % (client_ip, client_port))
		del self.dispatch_table[session_id]
		del self.plugin_info.active_connections['%s:%s' % (client_ip, client_port)]
		try:
			websocket.close()
		except:
			pass
			
	@mpexception
	async def start_sspi_plugin(self):
		cmd = OperatorStartPlugin()
		cmd.agent_id = self.agent_id
		cmd.plugin_type = PluginType.SSPI.value
		cmd.server = SSPIPluginServerStartupSettings(listen_ip = None, listen_port = None, remote = True)
		cmd.agent = SSPIPluginAgentStartupSettings(self.operator_token)
		await self.connector.cmd_out_q.put(cmd)
		
		await self.plugin_started_evt.wait()
		await self.logger.info('SSPI Plugin succsessfully started on the agent!')
		
	@mpexception
	async def run(self):
		await self.logger.info('Watiting for server connection...')
		await self.connector.server_connected.wait()
		await self.logger.info('Server connected! Setting up SSPI listener!')
		asyncio.ensure_future(self.handle_plugin_data_in())
		await self.logger.info('Starting SSPI on the agent...')
		await self.start_sspi_plugin()

		self.server = await websockets.serve(self.handle_client, self.sspi_listen_ip, self.sspi_listen_port, ssl=None)
		#self.server = await asyncio.start_server(self.handle_socks_client, self.socks5_listen_ip, self.socks5_listen_port)
		listen_ip, listen_port = self.server.sockets[0].getsockname()
		await self.logger.info('Local SSPI server listening on %s:%s' % (listen_ip, listen_port))
		await self.server.wait_closed()

			