import asyncio
import uuid

import websockets

from multiplexor.operator.protocol import *
from multiplexor.logger.logger import *
from multiplexor.plugins.socks5.pluginsettings import *
from multiplexor.plugins.socks5.plugininfo import *
from multiplexor.plugins.socks5.plugin import *
from multiplexor.plugins.plugintypes import *

class MultiplexorSocks5Operator:
	def __init__(self, logQ, connector, agent_id):
		self.logger = Logger('SOCKS5', logQ = logQ)
		self.connector = connector
		
		self.agent_id = agent_id #id of the agent connected to the multiplexor server that will be used to relay connections to/from
		self.plugin_id = None

		self.socks5_listen_ip = '127.0.0.1'
		self.socks5_listen_port = 0

		self.current_socket_id = 0
		self.operator_token = str(uuid.uuid4())

		self.plugin_started_evt = asyncio.Event()
		self.dispatch_table = {} #socket_id to SOCKS5LocalClient
		
		self.plugin_info = Socks5PluginInfo()
		self.stop_plugin_evt = asyncio.Event()

		self.server_reply_task = None
		self.server = None
		
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
	async def handle_socks_client(self, reader, writer):
		"""
		This task gets invoked each time a new client connects to the listener socket
		"""
		client_ip, client_port = writer.get_extra_info('peername')
		await self.logger.info('Client connected from %s:%s' % (client_ip, client_port))
		self.plugin_info.active_connections['%s:%s' % (client_ip, client_port)] = None
		self.current_socket_id += 1
		socket_id = str(self.current_socket_id)
		outQ = asyncio.Queue()
		asyncio.ensure_future(self.handle_plugin_out(outQ))
		client = Socks5Client(socket_id, self.logger.logQ, reader, writer, self.stop_plugin_evt, None, outQ, self.plugin_info)
		self.dispatch_table[socket_id] = client
		await client.handle_socks5()
		await self.logger.info('Client disconnected (%s:%s)' % (client_ip, client_port))
		del self.dispatch_table[socket_id]
		del self.plugin_info.active_connections['%s:%s' % (client_ip, client_port)]
		try:

			writer.close()
		except:
			pass

	@mpexception
	async def start_socks5_plugin(self):
		cmd = OperatorStartPlugin()
		cmd.agent_id = self.agent_id
		cmd.plugin_type = PluginType.SOCKS5.value
		cmd.server = Socks5PluginServerStartupSettings(listen_ip = None, listen_port = None, auth_type = None, remote = True)
		cmd.agent = Socks5PluginAgentStartupSettings(self.operator_token)
		await self.connector.cmd_out_q.put(cmd)
		
		await self.plugin_started_evt.wait()
		await self.logger.info('SOCKS5 Plugin succsessfully started on the agent!')

	@mpexception
	async def handle_server_rply(self):
		while self.connector.server_connected.is_set():
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

	@mpexception
	async def terminate(self):
		await self.server.close()
		self.server_reply_task.cancel()
			
	@mpexception
	async def run(self):
		await self.logger.info('Watiting for server connection...')
		await self.connector.server_connected.wait()
		await self.logger.info('Server connected! Setting up SOCKS5 proxy!')
		self.server_reply_task = asyncio.create_task(self.handle_server_rply())
		await self.logger.info('Starting SOCKS5 on the agent...')
		await self.start_socks5_plugin()

		self.server = await asyncio.start_server(self.handle_socks_client, self.socks5_listen_ip, self.socks5_listen_port)
		listen_ip, listen_port = self.server.sockets[0].getsockname()
		await self.logger.info('Local SOCKS5 server listening on %s:%s' % (listen_ip, listen_port))
		await self.server.serve_forever()
