import os
import uuid
import asyncio
from multiplexor.operator.protocol import *
from multiplexor.logger.logger import *
from multiplexor.server.agent import *
from multiplexor.server.protocol import *
from multiplexor.plugins.plugins import *
from multiplexor.plugins import *

#
#
#
# Issue: plugin creation and notification is currently tied to a random token that is generated by the operator, this could be bad if collisions present :(
#
#
#

class MultiplexorServer:
	def __init__(self, logger):
		self.transports = []
		self.ophandlers = {}
		self.agents = {}
		self.agent_tasks = {} #agent -> handle_agent_task
		self.operators = {}
		self.logger = logger
		self.shutdown_evt = asyncio.Event()
		self.agent_dispatch_queue = asyncio.Queue()
		self.operator_dispatch_queue = asyncio.Queue()
		self.operator_incoming_task = {}
		
		self.multiplexor_event_q = asyncio.Queue() #this queue is used to dispatch event messages to all operators connected
		                                          #such event are: logs, plugin created, agent connected, plugin terminated, agent disconnected
		
		self.agent_register_tokens = {} #id - token
		
	##################################################################################################
	##################################################################################################
	
	def add_transport(self, transport):
		#print('adding transport')
		transport.agent_dispatch_queue = self.agent_dispatch_queue
		self.transports.append(transport)
		asyncio.ensure_future(transport.run())
		
	##################################################################################################
	##################################################################################################
	@mpexception
	async def handle_operator_in(self, operator):
		while operator.websocket.open:
			op_cmd = await operator.multiplexor_cmd_in.get()
			if not op_cmd:
				await self.logger.debug('queue broken!')
				return
			await self.logger.debug('Operator sent this: %s' % op_cmd)
			if op_cmd.cmdtype == OperatorCmdType.LIST_AGENTS:
				rply = OperatorListAgentsRply()
				rply.cmd_id = op_cmd.cmd_id
				for k in self.agents:
					rply.agents.append(k)
				
				await operator.multiplexor_cmd_out.put(rply)
				
			elif op_cmd.cmdtype == OperatorCmdType.GET_AGENT_INFO:
				
				try:
					agent = self.agents[op_cmd.agent_id]
				except Exception as e:
					await self.logger.debug('Operator tried to slect and unknown agent %s' % op_cmd.agent_id)
					rply = OperatorExceptionEvt(op_cmd.cmd_id , 'Unknown agent!')
					await operator.multiplexor_cmd_out.put(rply)

				else:
					rply = OperatorGetAgentInfoRply()
					rply.cmd_id = op_cmd.cmd_id
					rply.agent_id = op_cmd.agent_id
					rply.agentinfo = self.agents[op_cmd.agent_id].info
					await operator.multiplexor_cmd_out.put(rply)
			
			elif op_cmd.cmdtype == OperatorCmdType.GET_PLUGINS:
				try:
					agent = self.agents[op_cmd.agent_id]
				except Exception as e:
					await self.logger.debug('Operator tried to slect and unknown agent %s' % op_cmd.agent_id)
					rply = OperatorExceptionEvt(op_cmd.cmd_id , 'Unknown agent!')
					await operator.multiplexor_cmd_out.put(rply)
				else:
					rply = OperatorListPluginsRply()
					rply.cmd_id = op_cmd.cmd_id
					rply.agent_id = op_cmd.agent_id
					for k in agent.plugins:
						rply.plugins.append(k)
					await operator.multiplexor_cmd_out.put(rply)
				
			elif op_cmd.cmdtype == OperatorCmdType.GET_PLUGIN_INFO:
				try:
					agent = self.agents[op_cmd.agent_id]
				except Exception as e:
					await self.logger.debug('Operator tried to select and unknown agent %s ' % (op_cmd.agent_id))
					rply = OperatorExceptionEvt(op_cmd.cmd_id , 'Unknown agent!')
					await operator.multiplexor_cmd_out.put(rply)
				
				try:
					plugin = agent.plugins[op_cmd.plugin_id]
				except Exception as e:
					await self.logger.debug('Operator tried to select an unknown pugin id %s' % (op_cmd.plugin_id))
					rply = OperatorExceptionEvt(op_cmd.cmd_id , 'Unknown plugin!')
					await operator.multiplexor_cmd_out.put(rply)
				
				else:
					rply = OperatorGetPluginInfoRply()
					rply.cmd_id = op_cmd.cmd_id
					rply.agent_id = op_cmd.agent_id
					rply.plugin_id = op_cmd.plugin_id
					rply.plugininfo = plugin.plugin_info.to_dict() #all plugin info objects must have a to_dist fucntion!
					await operator.multiplexor_cmd_out.put(rply)
				
			elif op_cmd.cmdtype == OperatorCmdType.START_PLUGIN:
				try:
					agent = self.agents[op_cmd.agent_id]					
				except Exception as e:
					await self.logger.debug('Operator tried to slect and unknown agent %s' % op_cmd.agent_id)
					rply = OperatorExceptionEvt(op_cmd.cmd_id , 'Unknown agent!')
					await operator.multiplexor_cmd_out.put(rply)

				else:
					try:
						plugin_id = await self.start_plugin(operator, agent, op_cmd)
					except Exception as e:
						await self.logger.debug('Failed to start plugin! Reason: %s' % e)
						rply = OperatorExceptionEvt(op_cmd.cmd_id , 'Failed to start plugin! Reason: %s' % e)
						await operator.multiplexor_cmd_out.put(rply)
						return
					else:
						rply = OperatorStartPluginRply()
						rply.cmd_id = op_cmd.cmd_id
						rply.agent_id = op_cmd.agent_id
						rply.plugin_id = plugin_id
						await operator.multiplexor_cmd_out.put(rply)
						
			elif op_cmd.cmdtype == OperatorCmdType.PLUGIN_DATA_EVT:
				try:
					agent = self.agents[op_cmd.agent_id]
					plugin = agent.plugins[op_cmd.plugin_id]
				except Exception as e:
					await self.logger.debug('Operator tried to select and unknown agent %s and/or unknown pugin id %s' % (op_cmd.agent_id, op_cmd.plugin_id))
				else:
					await plugin.plugin_out.put(bytes.fromhex(op_cmd.data))
				
			else:
				await self.logger.debug('Not implemented operator command!')
	
	async def handle_operator_event(self, ophandler):
		while not self.shutdown_evt.is_set() or not ophandler.transport_terminated_evt.is_set():
			operator, status = await ophandler.operator_dispatch_queue.get()
			if status == 'CONNECTED':
				self.operators[operator.operator_id] = operator
				self.logger.add_consumer(operator)
				await self.logger.debug('New operator in!')
				self.operator_incoming_task[operator.operator_id] = asyncio.create_task(self.handle_operator_in(operator))
			else:
				self.operator_incoming_task[operator.operator_id].cancel()
				await self.operators[operator.operator_id].terminate()
				self.logger.del_consumer(operator)
				del self.operators[operator.operator_id]
				await self.logger.debug('Operator removed! %s' % operator.operator_id)
				
			
	def remove_ophandler(self, ophandler):
		if ophandler in self.ophandlers:
			del self.ophandlers[ophandler]
		return
	
	def add_ophandler(self, ophandler):
		ophandler.operator_dispatch_queue = self.operator_dispatch_queue
		self.ophandlers[ophandler] = 0
		asyncio.ensure_future(self.handle_operator_event(ophandler))
		asyncio.ensure_future(ophandler.run())
		

		
		
	##################################################################################################
	##################################################################################################
	@mpexception
	async def register_agent(self, agent):
		"""
		At the current stage all this function does for registration is:
		1. assign a uuid to the agent
		2. generate a random secret
		3. send the uuid and the secret to the agent
		4. wait for agent to send the uuid and the secret back
		
		in case an agent sends and agent ID and a secret on the first connection we treat it that it's an already existing agent that lost the connection to the server and tries to re-register
		in that scenario we check if we have that agentid with that secret in our table
		"""
		while not self.shutdown_evt.is_set() or not agent.transport_terminated_evt.is_set():
			cmd = await agent.packetizer.multiplexor_in.get()
			if cmd is None:
				return
			if agent.status == AgentStatus.CONNECTED:
				if cmd.cmdtype != ServerCMDType.REGISTER:
					await self.logger.debug('Agent just connected and doesnt want to register!')
					continue
				
				if cmd.agent_id:
					await self.logger.debug('Seems to be a reconnected agent with ID %s' % cmd.agent_id)
					if not cmd.agent_id in self.agent_register_tokens:
						await self.logger.debug('Not existing agent id! %s' % cmd.agent_id)
						return
					if not self.agent_register_tokens[cmd.agent_id] == cmd.secret:
						await self.logger.debug('Incorrect secret! %s %s' % (cmd.agent_id, cmd.secret))
						return
					
					await self.logger.debug('Agent re-registered sucsessfully')
					agent.status = AgentStatus.REGISTERED
					return
					
				await self.logger.debug('Agent wants to register!')
				cmd = MultiplexorRegister()
				cmd.secret = os.urandom(4)
				cmd.agent_id = str(uuid.uuid4())
				agent.status = AgentStatus.REGISTERING
				self.agent_register_tokens[cmd.agent_id] = cmd.secret
				await agent.packetizer.multiplexor_out.put(cmd)
				continue
				
			if agent.status == AgentStatus.REGISTERING:
				await self.logger.debug('Agent registering!')
				if not cmd.agent_id in self.agent_register_tokens:
					await self.logger.debug('Not existing agent id! %s' % cmd.agent_id)
					return
				if not self.agent_register_tokens[cmd.agent_id] == cmd.secret:
					await self.logger.debug('Incorrect secret! %s %s' % (cmd.agent_id, cmd.secret))
					return
					
				await self.logger.debug('Agent registered sucsessfully')
				agent.status = AgentStatus.REGISTERED
				agent.agent_id = cmd.agent_id
				self.agents[agent.agent_id] = agent
				return
		
	@mpexception
	async def start_plugin(self, operator, agent, cmd): #plugin_type, plugin_params
		await self.logger.debug('start_plugin called')
		#print(str(cmd))
		pp = None #plugin parameters object or none
		if cmd.server['remote'] == True:
			#inserting the operator and the agent_id parameter into the startup params
			#these are needed for the remoting only
			
			cmd.server['operator'] = operator
			cmd.server['agent_id'] = agent.agent_id
			
			await self.logger.debug('REMOTE')
			plugin_obj = MultiplexorRemoting
			
		if int(cmd.plugin_type) == PluginType.SOCKS5.value:
			await self.logger.debug('SOCKS5')

			if cmd.agent:
				pp = Socks5PluginAgentStartupSettings.from_dict(cmd.agent)
			
			if cmd.server['remote'] == False:
				plugin_obj = MultiplexorSocks5
		
		elif int(cmd.plugin_type) == PluginType.SSPI.value:
			await self.logger.debug('SSPI')
			
			if cmd.agent:
				pp = SSPIPluginAgentStartupSettings.from_dict(cmd.agent)
				
			if cmd.server['remote'] == False:
				plugin_obj = MultiplexorSSPI

		elif int(cmd.plugin_type) == PluginType.FILESYSTEM.value:
			await self.logger.debug('Filesystem')
			
			if cmd.agent:
				pp = FilesystemPluginAgentStartupSettings.from_dict(cmd.agent)
				
			if cmd.server['remote'] == False:
				plugin_obj = MultiplexorFilesystem
		
		else:
			raise Exception('Not implemented')
		
		plugin_id = agent.add_plugin(plugin_obj, cmd, operator)
		await self.logger.debug('starting')
		asyncio.ensure_future(agent.plugins[plugin_id].start())
		await self.logger.debug('started')
		
		mcmd = MultiplexorPluginStart()
		mcmd.plugin_id = str(plugin_id)
		mcmd.plugin_type = str(cmd.plugin_type)
		mcmd.plugin_params = pp.to_list() if pp else pp  #only passing the plugin params that the remote agent needs, usually none
		await agent.packetizer.multiplexor_out.put(mcmd)
		await self.logger.debug('plugin start command sent to the client')
		return plugin_id
	
	@mpexception
	async def handle_agent_main(self, agent):
		print('New agent connected!')
		await self.logger.info('New agent connected!')
		#this msut be invoked after succsessful registration!

		#notifying operators about new agent
		rply = OperatorAgentConnectedEvt()
		rply.agent_id = agent.agent_id
		rply.agentinfo = agent.info
		rply.cmd_id = '66666'
		for k in self.operators:
			await self.operators[k].multiplexor_cmd_out.put(rply)

		while not self.shutdown_evt.is_set() or not agent.transport_terminated_evt.is_set():
			cmd = await agent.packetizer.multiplexor_in.get()
			if cmd is None:
				await self.terminate_agent(agent)
				return
			if cmd.cmdtype == ServerCMDType.GET_INFO:
				await self.logger.debug(cmd.agent_info)
				try:
					print(cmd.agent_info)
					agent.info = json.loads(cmd.agent_info)
					rply = OperatorAgentConnectedEvt()
					rply.agent_id = agent.agent_id
					rply.agentinfo = agent.info
					rply.cmd_id = '66666'
					for k in self.operators:
						await self.operators[k].multiplexor_cmd_out.put(rply)
				except Exception as e:
					await self.logger.exception()
				
				
			elif cmd.cmdtype == ServerCMDType.PLUGIN_DATA:
				if not cmd.plugin_id in agent.plugins:
					#print('Got plugin data from %s for and unknown plugin id %s' % (agent.agent_id, cmd.plugin_id))
					continue
				#print('Dispatching plugin data!')
				await agent.plugins[cmd.plugin_id].plugin_in.put(cmd.plugin_data)
				
			#elif cmd.cmdtype == ServerCMDType.PLUGIN_START:
			#	#TODO
			#	await self.logQ.put(None)
				
			#elif cmd.cmdtype == ServerCMDType.PLUGIN_STOP:
			#	#TODO
			#	await self.logQ.put(None)
			
			elif cmd.cmdtype == ServerCMDType.PLUGIN_STOPPED_EVT:
				if not cmd.plugin_id in agent.plugins:
					#print('Got plugin data from %s for and unknown plugin id %s' % (agent.agent_id, cmd.plugin_id))
					continue
				await agent.plugins[cmd.plugin_id].plugin_in.put(cmd)
				await self.logger.info('Plugin stopped')

				op = agent.plugin_operator[cmd.plugin_id]
				rply = OperatorPluginStoppedEvt()
				rply.agent_id = agent.agent_id
				rply.plugin_id = cmd.plugin_id
				await op.multiplexor_cmd_out.put(rply)
				
			elif cmd.cmdtype == ServerCMDType.PLUGIN_STARTED_EVT:
				await self.logger.info('Got plugin started event!')
				#### Sanity check
				if not cmd.plugin_id in agent.plugins:
					await self.logger.debug('Got plugin data from %s for and unknown plugin id %s' % (agent.agent_id, cmd.plugin_id))
					continue
				#### dispatching th event to the appropriate queue
				#### await agent.plugins[cmd.plugin_id].plugin_in.put(cmd)
				
				#### notifying all operators of the event
				rply = OperatorPluginStartedEvt()
				rply.agent_id = agent.agent_id
				rply.plugin_id = cmd.plugin_id
				
				op = agent.plugin_operator[cmd.plugin_id]
				await self.logger.info('Dispatching event to operator %s' % op)
				await op.multiplexor_cmd_out.put(rply)
					
				await self.logger.info('Plugin started')

			elif cmd.cmdtype == ServerCMDType.AGENT_LOG:
				src_name = "AGENT PLUGIN %s" % cmd.plugin_id if cmd.plugin_id else "CORE"
				log = LogEntry(cmd.severity, src_name, cmd.msg, agent_id = agent.agent_id)
				await self.logger.logQ.put(log)


	@mpexception
	async def terminate_agent(self, agent):
		#notifying operators about disconnected agent
		rply = OperatorAgentDisconnectedEvt()
		rply.agent_id = agent.agent_id
		for k in self.operators:
			await self.operators[k].multiplexor_cmd_out.put(rply)

		await agent.terminate()
		if agent in self.agent_tasks:
			self.agent_tasks[agent].cancel()
			del self.agent_tasks[agent]
		try:
			del self.agents[agent.agent_id]
		except Exception as e:
			await self.logger.debug('Failed to remove agent from agents list! Reason: %s' % e)
	@mpexception
	async def handle_agent(self, agent):
		#agent needs to register before we talk to her...
		await self.register_agent(agent)
		if agent.status == AgentStatus.REGISTERED:
			logging.info('New agent: %s' % agent.agent_id)
			
			#by default we poll some basic info on the client...
			if not agent.info:
				cmd = MultiplexorGetInfo()
				await agent.packetizer.multiplexor_out.put(cmd)
			
			#now starting the main handler loop
			await self.logger.info('Invoking agent main...')
			await self.handle_agent_main(agent)
			await self.logger.debug('Agent dropped :(')
		else:
			await self.logger.debug('Agent failed to register, let it go let it go...')
			return
	
	@mpexception
	async def run(self):
		asyncio.ensure_future(self.logger.run())
		while not self.shutdown_evt.is_set():
			agent, status = await self.agent_dispatch_queue.get()
			if status == 'CONNECTED':
				self.agent_tasks[agent] = asyncio.create_task(self.handle_agent(agent))
			else:
				await self.terminate_agent(agent)