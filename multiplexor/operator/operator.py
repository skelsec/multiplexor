import asyncio
import uuid

from multiplexor.operator.local.common.connector import MultiplexorOperatorConnector
from multiplexor.operator.local.common.listener import MultiplexorOperatorListener
from multiplexor.operator.local.socks5 import MultiplexorSocks5Operator, Socks5PluginServerStartupSettings
from multiplexor.operator.local.sspi import MultiplexorSSPIOperator

from multiplexor.plugins.plugintypes import PluginType
from multiplexor.operator.protocol import OperatorGetAgentInfoCmd, OperatorListAgentsCmd, OperatorStartPlugin, OperatorGetPluginInfoCmd, OperatorListPluginsCmd, OperatorCmdType
from multiplexor.logger.logger import mpexception, Logger
from multiplexor.operator.exceptions import MultiplexorRemoteException

class MultiplexorOperator:
	"""
	This object represents an operator, who controls the multiplexor server.
	It can manage all aspects of the server, list agents, plugins etc and create plugins on the agent

	Use this for managing the server, either via command line or programaticcally using the APIs this object exposes.
	"""
	def __init__(self, connection_string, logger = None, reconnect_tries = None, logging_sink = None, show_remote_logs = False):
		self.connection_string = connection_string
		self.connector = None
		self.logger = logger
		self.show_remote_logs = show_remote_logs
		self.logging_sink = logging_sink
		self.cmd_id_ctr = 0
		self.reply_buffer = {} # cmd_id -> reply
		self.reply_buffer_evt = {} #cmd_id -> event
		self.plugin_created_evt = {} #agent_id -> {plugin_id -> started_event}

		self.connector_task = None
		self.incoming_task = None
		self.disconnected_evt = None
		self.reconnect_tries = reconnect_tries
		self.logger_task = None

	async def start_logger(self):
		if self.logger is None:
			self.logger = Logger('MP Operator', sink = self.logging_sink)
			self.logger_task = asyncio.create_task(self.logger.run())


	@mpexception
	async def handle_incoming(self):
		while True:
			try:
				reply = await self.connector.cmd_in_q.get()
				# enable line below for command debug
				#print('handle_incoming %s' % reply.to_dict())
				if reply.cmdtype in [OperatorCmdType.START_PLUGIN, OperatorCmdType.PLUGIN_STARTED_EVT, 
										OperatorCmdType.PLUGIN_STOPPED_EVT, OperatorCmdType.LOG_EVT, 
										OperatorCmdType.PLUGIN_DATA_EVT, OperatorCmdType.AGENT_CONNECTED_EVT,
										OperatorCmdType.AGENT_DISCONNECTED_EVT]:
					if reply.cmdtype == OperatorCmdType.LOG_EVT:
						if self.show_remote_logs is True:
							await self.logger.log(reply.level, reply.msg)
						try:
							asyncio.create_task(self.on_log(reply))
						except Exception as e:
							await self.logger.exception()
					elif reply.cmdtype == OperatorCmdType.PLUGIN_STARTED_EVT:
						self.plugin_created_evt[reply.agent_id][reply.plugin_id].set()
						try:
							asyncio.create_task(self.on_plugin_start(reply.agent_id, reply.plugin_id))
						except Exception as e:
							await self.logger.exception()
					elif reply.cmdtype == OperatorCmdType.PLUGIN_STOPPED_EVT:
						try:
							asyncio.create_task(self.on_plugin_stop(reply.agent_id, reply.plugin_id))
						except Exception as e:
							await self.logger.exception()
					elif reply.cmdtype == OperatorCmdType.AGENT_CONNECTED_EVT:
						try:
							asyncio.create_task(self.on_agent_connect(reply.agent_id, reply.agentinfo))
						except Exception as e:
							await self.logger.exception()
					elif reply.cmdtype == OperatorCmdType.AGENT_DISCONNECTED_EVT:
						try:
							asyncio.create_task(self.on_agent_disconnect(reply.agent_id))
						except Exception as e:
							await self.logger.exception()
					continue
				else:
					if hasattr(reply, 'cmd_id'):
						if reply.cmd_id is not None:
							self.reply_buffer[reply.cmd_id] = reply
							self.reply_buffer_evt[reply.cmd_id].set()
						else:
							await self.logger.error('Got reply from server with empty command id!')
					else:
							await self.logger.error('Got reply from server without command id!')
			except Exception as e:
				#at this point something bad happened, so we are cleaning up
				#sending out the exception to all cmd ids and notifying them
				#print(str(e))
				if not isinstance(e, asyncio.CancelledError):
					await self.logger.exception()
				for reply_id in self.reply_buffer:
					self.reply_buffer[reply_id] = e
				for reply_id in self.reply_buffer_evt:
					self.reply_buffer_evt[reply_id].set()
				break
		self.disconnected_evt.set()

	@mpexception		
	async def recv_reply(self, cmd_id):
		#
		# Checking if cmd id is already in the buffer, if not we wait for the incoming event
		# then we take out the reply from the buffer, and delete the buffer entry and also the notification entry
		#
		#print('recv_reply called with cmd_id of %s' % cmd_id)
		if cmd_id not in self.reply_buffer:
			await self.reply_buffer_evt[cmd_id].wait()
		reply = self.reply_buffer[cmd_id]
		del self.reply_buffer[cmd_id]
		del self.reply_buffer_evt[cmd_id]
		return reply

	@mpexception
	async def send_cmd(self, cmd):
		## assigns a command id to the command then sends the command
		## returns the command id to the caller, which then can wait for the reply
		##
		cmd.cmd_id = self.cmd_id_ctr
		self.reply_buffer_evt[cmd.cmd_id] = asyncio.Event()
		self.cmd_id_ctr += 1
		# enable line below for outgoing command debug
		#print('send_cmd: %s' % cmd)
		await self.connector.cmd_out_q.put(cmd)
		#print('send_cmd called and returned %s' % cmd.cmd_id)
		return cmd.cmd_id

	@mpexception
	async def connect(self):
		self.disconnected_evt = asyncio.Event()
		await self.start_logger()

		self.connector = MultiplexorOperatorConnector(self.connection_string, self.logger.logQ, ssl_ctx = None, reconnect_interval = 5, reconnect_tries=self.reconnect_tries)
		self.connector_task = asyncio.create_task(self.connector.run())
		try:
			await asyncio.wait_for(self.connector.server_connected.wait(), timeout = 1) #waiting until connector managed to connect to the multiplexor server
		except asyncio.TimeoutError:
			asyncio.create_task(self.on_server_error('Server failed to connect!'))
			await self.terminate()
			raise Exception('Server failed to connect!')
		
		asyncio.create_task(self.on_server_connected(self.connection_string))
		self.incoming_task = asyncio.create_task(self.handle_incoming())

	@mpexception
	async def listen(self):
		await self.start_logger()

		if self.connection_string.find(':') != -1:
			listen_ip, listen_port = self.connection_string.split(':')
		else:
			listen_ip = '127.0.0.1'
			listen_port = int(self.connection_string)
		self.connector = MultiplexorOperatorListener(listen_ip, listen_port, self.logger.logQ, ssl_ctx = None, reconnect_interval = 5)
		self.connector_task = asyncio.create_task(self.connector.run())
		self.incoming_task = asyncio.create_task(self.handle_incoming())

	async def terminate(self):
		await self.logger.debug('terminate called!')
		if self.incoming_task:
			self.incoming_task.cancel()
		if self.connector:
			await self.connector.terminate()
		if self.connector_task:
			self.connector_task.cancel()

		if self.logger_task:
			self.logger_task.cancel()
		self.connector_task = None

		self.connector = None
		self.cmd_id_ctr = 0
		self.reply_buffer = {} # cmd_id -> reply
		self.reply_buffer_evt = {} #cmd_id -> event
		return

	@mpexception
	async def list_agents(self):
		cmd = OperatorListAgentsCmd()
		cmd_id = await self.send_cmd(cmd)
		reply = await self.recv_reply(cmd_id)

		return reply.agents

	@mpexception
	async def start_socks5(self, agent_id, listen_ip = '127.0.0.1', listen_port = 0, remote = False):
		if remote == False:
			if agent_id not in self.plugin_created_evt:
				self.plugin_created_evt[agent_id] = {}
			cmd = OperatorStartPlugin()
			cmd.agent_id = agent_id
			cmd.plugin_type = PluginType.SOCKS5.value
			cmd.operator_token = str(uuid.uuid4())
			cmd.server = Socks5PluginServerStartupSettings(listen_ip = listen_ip, listen_port = listen_port, auth_type = None, remote = False)
			cmd_id = await self.send_cmd(cmd)
			reply = await self.recv_reply(cmd_id)

			if reply.cmdtype == OperatorCmdType.EXCEPTION:
				raise MultiplexorRemoteException(reply.exc_data)
			self.plugin_created_evt[reply.agent_id][reply.plugin_id] = asyncio.Event()
			await self.plugin_created_evt[reply.agent_id][reply.plugin_id].wait() #waiting for the plugin creation event
			del self.plugin_created_evt[reply.agent_id][reply.plugin_id]

			reply = await self.info_plugin(agent_id, reply.plugin_id)
			return reply
			
		else:
			#this passes all controls over to the local sock5server object
			#exits the function when socks5 server is terminated
			so = MultiplexorSocks5Operator(self.logger.logQ, self.connector, agent_id)
			await so.run()
			return

	@mpexception
	async def start_sspi(self, agent_id, listen_ip = '127.0.0.1', listen_port = 0, remote = False):
		if remote == False:
			if agent_id not in self.plugin_created_evt:
				self.plugin_created_evt[agent_id] = {}
			cmd = OperatorStartPlugin()
			cmd.agent_id = agent_id
			cmd.plugin_type = PluginType.SSPI.value
			cmd.server = Socks5PluginServerStartupSettings(listen_ip = listen_ip, listen_port = listen_port, auth_type = None, remote = False)
			cmd_id = await self.send_cmd(cmd)
			reply = await self.recv_reply(cmd_id)
			if reply.cmdtype == OperatorCmdType.EXCEPTION:
				raise MultiplexorRemoteException(reply.exc_data)

			self.plugin_created_evt[reply.agent_id][reply.plugin_id] = asyncio.Event()
			await self.plugin_created_evt[reply.agent_id][reply.plugin_id].wait() #waiting for the plugin creation event
			del self.plugin_created_evt[reply.agent_id][reply.plugin_id]
			
			reply = await self.info_plugin(agent_id, reply.plugin_id)
			return reply
			
		else:
			#this passes all controls over to the local sock5server object
			#exits the function when socks5 server is terminated
			so = MultiplexorSSPIOperator(self.logger.logQ, self.connector, agent_id)
			await so.run()
			return

	async def info_agent(self, agent_id):
		cmd = OperatorGetAgentInfoCmd(agent_id = agent_id)
		cmd_id = await self.send_cmd(cmd)
		reply = await self.recv_reply(cmd_id)
		if reply.cmdtype == OperatorCmdType.EXCEPTION:
			raise MultiplexorRemoteException(reply.exc_data)
		return reply.agentinfo

	
	async def list_agent_plugins(self, agent_id):
		cmd = OperatorListPluginsCmd(agent_id = agent_id)
		cmd_id = await self.send_cmd(cmd)
		reply = await self.recv_reply(cmd_id)
		if reply.cmdtype == OperatorCmdType.EXCEPTION:
			raise MultiplexorRemoteException(reply.exc_data)
		return reply.plugins

	async def info_plugin(self, agent_id, plugin_id):
		cmd = OperatorGetPluginInfoCmd(agent_id = agent_id, plugin_id = plugin_id)
		cmd_id = await self.send_cmd(cmd)
		reply = await self.recv_reply(cmd_id)
		if reply.cmdtype == OperatorCmdType.EXCEPTION:
			raise MultiplexorRemoteException(reply.exc_data)
		return reply.plugininfo

	async def run(self):
		await self.connect()
		try:
			asyncio.create_task(self.on_run())
		except Exception as e:
			await self.logger.exception()
		await self.disconnected_evt.wait()


	async def on_agent_connect(self, agent_id, agentinfo):
		pass

	async def on_agent_disconnect(self, agent_id):
		pass

	async def on_plugin_start(self, agent_id, plugin_id):
		pass

	async def on_plugin_stop(self, agent_id, plugin_id):
		pass
	
	async def on_log(self, log):
		pass

	async def on_server_connected(self, connection_string):
		pass

	async def on_server_error(self, reason):
		pass
	
	async def on_run(self):
		pass

async def main_loop(args):
	##setting up logging
	logger = Logger('Operator')
	asyncio.ensure_future(logger.run())

	mgr = MultiplexorOperator(args.connection_string, logger)
	await mgr.connect()
		
	## sending commands
	if args.command == 'server':
		if args.cmd == 'list':
			reply = await mgr.list_agents()

	elif args.command == 'agent':
		if args.cmd == 'info':
			reply = await mgr.info_agent(args.agentid)
			
		elif args.cmd == 'list':
			reply = await mgr.list_agent_plugins(args.agentid)
			
	elif args.command == 'plugin':
		if args.cmd == 'info':
			reply = await mgr.info_plugin(args.agentid, args.pluginid)
			
			
	elif args.command == 'create':
		if args.type == 'socks5':
			reply = await mgr.start_socks5(args.agentid, args.listen_ip, args.listen_port, args.remote)
			
			
		elif args.type == 'sspi':
			reply = await mgr.start_socks5(args.agentid, args.listen_ip, args.listen_port, args.remote)
	
	await mgr.terminate()

def main():
	import argparse
	parser = argparse.ArgumentParser(description='Local operator for multiplexor')
	parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity, can be stacked')
	parser.add_argument('-t', '--connection-type', choices=['listen', 'connect'], help='Defines the connection type to the multiplexor server')
	parser.add_argument('-c', '--connection-string', help = 'Either <ip>:<port> or a websockets URL "ws://<ip>:<port>", depending on the connection type')
	

	subparsers = parser.add_subparsers(help = 'commands')
	subparsers.required = True
	subparsers.dest = 'command'
	
	server_group = subparsers.add_parser('server', help='Server related commands')
	server_group.add_argument('cmd', choices=['list'], help='command')
	
	agent_group = subparsers.add_parser('agent', help='Server related commands')
	agent_group.add_argument('cmd', choices=['list','info'], help='command')
	agent_group.add_argument('agentid', help='agent ID')
	
	
	plugin_group = subparsers.add_parser('plugin', help='Server related commands')
	plugin_group.add_argument('cmd', choices=['info'], help='command')
	plugin_group.add_argument('agentid', help='agent ID')
	plugin_group.add_argument('pluginid', help='plugin ID')
	
	create_plugin_group = subparsers.add_parser('create', help='Starts a plugin on the agent')
	create_plugin_group.add_argument('type', choices=['socks5','sspi'], help='command')
	create_plugin_group.add_argument('agentid', help='agent ID')
	create_plugin_group.add_argument('-r', '--remote', action='store_true', help='plugin server will be listening on the mutiplexor server')
	create_plugin_group.add_argument('-l', '--listen-ip', help='IP to listen on')
	create_plugin_group.add_argument('-p', '--listen-port', help='Port to listen on')
	create_plugin_group.add_argument('-d', '--startup-data', help='Additional data in JSON form to be passed to the plugin startup routine')
	
	args = parser.parse_args()

	asyncio.run(main_loop(args))

if __name__ == '__main__':
	main()
	
			
	