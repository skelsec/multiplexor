import asyncio
from multiplexor.operator.protocol import *

class MultiplexorServer:
	def __init__(self):
		self.transports = []
		self.ophandlers = []
		self.agents = {}
		self.logQ = asyncio.Queue()
		self.shutdown_evt = asyncio.Event()
		self.agent_dispatch_queue = asyncio.Queue()
		
		self.multiplexor_event_q = asyncio.Queue() #this queue is used to dispatch event messages to all operators connected
		                                          #such event are: logs, plugin created, agent connected, plugin terminated, agent disconnected
		
		self.agent_register_tokens = {} #id - token
		
	##################################################################################################
	##################################################################################################
	
	def add_transport(self, transport):
		transport.agent_dispatch_queue = self.agent_dispatch_queue
		self.transports.append(transport)
		asyncio.ensure_future(transport.run())
		
	##################################################################################################
	##################################################################################################
		
	async def handle_operator_in(self, ophandler):
		while not self.shutdown_evt.is_set() or not ophandler.transport_closed.is_set():
			op_cmd = await ophandler.multiplexor_cmd_in.get()
			
			if op_cmd.cmdtype == OperatorCmdType.LIST_AGENTS:
				rply = OperatorListAgentsRply()
				for k in self.agents:
					rply.agents.append(k)
				
				await ophandler.multiplexor_cmd_out.put(rply)
				
			elif op_cmd.cmdtype == OperatorCmdType.GET_AGENT_INFO:
				
				try:
					agent = self.agents[op_cmd.agent_id]
				except Exception as e:
					print('Operator tried to slect and unknown agent %s' % op_cmd.agent_id)
				else:
					rply = OperatorGetAgentInfoRply()
					rply.agent_id = op_cmd.agent_id
					rply.agentinfo = 'TODO: Implement'
					await ophandler.multiplexor_cmd_out.put(rply)
			
			elif op_cmd.cmdtype == OperatorCmdType.GET_PLUGINS:
				try:
					agent = self.agents[op_cmd.agent_id]
				except Exception as e:
					print('Operator tried to slect and unknown agent %s' % op_cmd.agent_id)
				else:
					rply = OperatorListPluginsRply()
					rply.agent_id = op_cmd.agent_id
					for k in agent.plugins:
						rply.plugins.append(k)
					await ophandler.multiplexor_cmd_out.put(rply)
				
			elif op_cmd.cmdtype == OperatorCmdType.GET_PLUGIN_INFO:
				try:
					agent = self.agents[op_cmd.agent_id]
					plugin = agent.plugins[op_cmd.plugin_id]
					
				except Exception as e:
					print('Operator tried to slect and unknown agent %s and/or unknown pugin id %s' % (op_cmd.agent_id, op_cmd.plugin_id))
				else:
					rply = OperatorGetPluginInfoRply()
					rply.agent_id = op_cmd.agent_id
					rply.plugin_id = op_cmd.plugin_id
					for k in agent.plugins:
						rply.plugins.append(k)
					await ophandler.multiplexor_cmd_out.put(rply)
				
			elif op_cmd.cmdtype == OperatorCmdType.START_PLUGIN:
				try:
					agent = self.agents[op_cmd.agent_id]					
				except Exception as e:
					print('Operator tried to slect and unknown agent %s' % op_cmd.agent_id)
				else:
					rply = OperatorGetPluginInfoRply()
					rply.agent_id = op_cmd.agent_id
					rply.plugin_id = op_cmd.plugin_id
					for k in agent.plugins:
						rply.plugins.append(k)
					await ophandler.multiplexor_cmd_out.put(rply)
				
				
			else:
				print('Not implemented operator command!')
	
	
	def add_ophandler(self, ophandler):
		ophandler.multiplexor_event_q = self.multiplexor_event_q
		self.ophandlers.append(ophandler)
		asyncio.ensure_future(self.handle_operator_in(ophandler))
		asyncio.ensure_future(ophandler.run())

		
		
	##################################################################################################
	##################################################################################################
	async def register_agent(self, agent):
		while not self.shutdown_evt.is_set() or not agent.trasnport_terminated_evt.is_set():
			cmd = await agent.multiplexor_in.get()
			if agent.status == AgentStatus.CONNECTED:
				if cmd.cmdtype != ServerCMDType.REGISTER:
					print('Agent just connected and doesnt want to register!')
					continue
				
				if cmd.agent_id:
					print('Seems to be a reconnected agent with ID %s' % cmd.agent_id)
					if not cmd.agent_id in self.agent_register_tokens:
						print('Not existing agent id! %s' % cmd.agent_id)
						return
					if not self.agent_register_tokens[cmd.agent_id] == cmd.secret:
						print('Incorrect secret! %s' % (cmd.agent_id, cmd.secret))
						return
					
					print('Agent re-registered sucsessfully')
					agent.status = AgentStatus.REGISTERED
					return
					
				cmd = MultiplexorRegister()
				cmd.secret = os.urandom(4)
				cmd.agent_id = uuid.uuid4()
				self.agent_register_tokens[cmd.agent_id] = cmd.secret
				await agent.multiplexor_out.put()
				agent.status == AgentStatus.REGISTERING
				continue
				
			if agent.status == AgentStatus.REGISTERING:
				if not cmd.agent_id in self.agent_register_tokens:
					print('Not existing agent id! %s' % cmd.agent_id)
					return
				if not self.agent_register_tokens[cmd.agent_id] == cmd.secret:
					print('Incorrect secret! %s' % (cmd.agent_id, cmd.secret))
					return
					
				print('Agent re-registered sucsessfully')
				agent.status = AgentStatus.REGISTERED
				agent.agent_id = cmd.agent_id
				return
		
		
	async def start_plugin(self, agent, plugin_type, plugin_params):
		while not self.shutdown_evt.is_set() or not agent.transport.trasnport_terminated_evt.is_set():
			cmd = MultiplexorPluginStart()
			cmd.plugin_type = plugin_type
			cmd.plugin_params = plugin_params
			await agent.multiplexor_out.put(cmd)
		
	async def handle_agent_cmd_in(self, agent):
		while not self.shutdown_evt.is_set() or not agent.transport.trasnport_terminated_evt.is_set():
			
			#cmd is actually reply
			
			print('Agent %s said this: %s' % (agent.agent_id, cmd))
			
	
	async def handle_agent_plugin_out(self, agent):
		while not self.shutdown_evt.is_set() or not agent.transport.trasnport_terminated_evt.is_set():
			
			await agent.multiplexor_out.put(cmd)
	
	async def handle_agent_main(self, agent):
		#this msut be invoked after succsessful registration!
		while not self.shutdown_evt.is_set() or not agent.trasnport_terminated_evt.is_set():
			cmd = await agent.multiplexor_in.get()
			if cmd.cmdtype == ServerCMDType.GET_INFO:
				agent.info = cmd.agent_info
				
			elif cmd.cmdtype == ServerCMDType.PLUGIN_DATA:
				if not cmd.plugin_id in agent.plugins:
					print('Got plugin data from %s for and unknown plugin id %s' % (agent.agent_id, cmd.plugin_id))
					continue
				await agent.plugins[cmd.plugin_id].plugin_in_q.put(cmd.plugin_data)
				
			elif cmd.cmdtype == ServerCMDType.AGENT_LOG:
				#TODO
				await self.logQ.put(None)
				
			elif cmd.cmdtype == ServerCMDType.PLUGIN_START:
				#TODO
				await self.logQ.put(None)
				
			elif cmd.cmdtype == ServerCMDType.PLUGIN_STOP:
				#TODO
				await self.logQ.put(None)
			
			elif cmd.cmdtype == ServerCMDType.PLUGIN_STOPPED_EVT:
				#TODO
				await self.logQ.put(None)
				
			elif cmd.cmdtype == ServerCMDType.PLUGIN_STARTED_EVT:
				#TODO
				await self.logQ.put(None)
			
	async def handle_agent(self, agent):
		while not self.shutdown_evt.is_set() or not agent.trasnport_terminated_evt.is_set():
			#agent needs to register before we talk to her...
			await self.register_agent(agent)
			if agent.status == AgentStatus.REGISTERED:		
				await handle_agent_main()
				print('Agent dropped :(')
			else:
				print('Agent failed to register, let it go let it go...')
				break
		
	async def run(self):
		for ophandler in self.ophandlers:
			self.add_ophandler(ophandler)
		for transport in self.transport:
			self.add_transport(transport)
			
		while not self.shutdown_evt.is_set():
			agent = await self.agent_dispatch_queue.get()
			asyncio.ensure_future(handle_agent(agent))