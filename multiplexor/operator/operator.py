
import asyncio
import websockets

from .protocol import *

agent_id = ''
plugin_id = ''

class Operator:
	def __init__(self):
		self.server_url = None
		self.ws = None
		
		self.server_cmd_q = asyncio.Queue()
		
		self.agents = {}
		
	async def handle_server_in(self):
		global agent_id
		global plugin_id
		
		while True:
			data = await self.ws.recv()
			print('RPLY in!')
			rply = OperatorCmdParser.from_json(data)
			print(rply.to_dict())
			if rply.cmdtype == OperatorCmdType.LIST_AGENTS_RPLY:
				for agent in rply.agents:
					self.agents[agent] = 1
					
					cmd = OperatorGetAgentInfoCmd()
					cmd.agent_id = agent
					await self.server_cmd_q.put(cmd)
			
			elif rply.cmdtype == OperatorCmdType.GET_AGENT_INFO_RPLY:
				if rply.agent_id not in self.agents:
					self.agents[rply.agent_id] = 1
				self.agents[rply.agent_id] = rply.agentinfo
				
				cmd = OperatorStartPlugin()
				cmd.cmdtype = OperatorCmdType.START_PLUGIN
				cmd.agent_id = rply.agent_id
				cmd.plugin_type = 0
				cmd.plugin_data = None
				await self.server_cmd_q.put(cmd)
				
			elif rply.cmdtype == OperatorCmdType.PLUGIN_STARTED:
				#just 3 testing making this global
				agent_id = rply.agent_id
				plugin_id = rply.plugin_id
				
				cmd = OperatorGetPluginInfoCmd()
				cmd.agent_id = rply.agent_id
				cmd.plugin_id = rply.plugin_id
				await self.server_cmd_q.put(cmd)
			
			elif rply.cmdtype == OperatorCmdType.GET_PLUGIN_INFO_RPLY:	
				print(rply.plugininfo)
				
	async def handle_server_in_sspi(self):
		global agent_id
		global plugin_id
		
		while True:
			data = await self.ws.recv()
			print('RPLY in!')
			rply = OperatorCmdParser.from_json(data)
			print(rply.to_dict())
			if rply.cmdtype == OperatorCmdType.LIST_AGENTS_RPLY:
				for agent in rply.agents:
					self.agents[agent] = 1
					
					cmd = OperatorGetAgentInfoCmd()
					cmd.agent_id = agent
					await self.server_cmd_q.put(cmd)
			
			elif rply.cmdtype == OperatorCmdType.GET_AGENT_INFO_RPLY:
				if rply.agent_id not in self.agents:
					self.agents[rply.agent_id] = 1
				self.agents[rply.agent_id] = rply.agentinfo
				
				cmd = OperatorStartPlugin()
				cmd.cmdtype = OperatorCmdType.START_PLUGIN
				cmd.agent_id = rply.agent_id
				cmd.plugin_type = 1
				cmd.plugin_data = None
				await self.server_cmd_q.put(cmd)
				
			elif rply.cmdtype == OperatorCmdType.PLUGIN_STARTED:
				#just 3 testing making this global
				agent_id = rply.agent_id
				plugin_id = rply.plugin_id
				
				cmd = OperatorGetPluginInfoCmd()
				cmd.agent_id = rply.agent_id
				cmd.plugin_id = rply.plugin_id
				await self.server_cmd_q.put(cmd)
			
			elif rply.cmdtype == OperatorCmdType.GET_PLUGIN_INFO_RPLY:	
				print(rply.plugininfo)
		
	async def handle_server_out(self):
		while True:
			cmd = await self.server_cmd_q.get()
			
			await self.ws.send(json.dumps(cmd.to_dict()))
			print('CMD sent!')
		
	async def connect(self):
		print('Connecting!')
		while True:
			self.ws = await websockets.connect(self.server_url)
			asyncio.ensure_future(self.handle_server_in_sspi())
			asyncio.ensure_future(self.handle_server_out())
			
			await self.ws.wait_closed()
			asyncio.sleep(10)
			print('Reconnecting!')
		

	async def send_test_sspi(self):
		self.server_url = 'ws://127.0.0.1:9999'
		asyncio.ensure_future(self.connect())
		#await asyncio.sleep(3)
		print('Sending command')
		cmd = OperatorListAgentsCmd()
		await self.server_cmd_q.put(cmd)
		while True:
			await asyncio.sleep(10)
			if agent_id != '':
				cmd = OperatorGetPluginInfoCmd()
				cmd.agent_id = agent_id
				cmd.plugin_id = plugin_id
				await self.server_cmd_q.put(cmd)
			else:
				print('no plugins started yet :(')
			
	
	async def send_test_data(self):
		self.server_url = 'ws://127.0.0.1:9999'
		asyncio.ensure_future(self.connect())
		#await asyncio.sleep(3)
		print('Sending command')
		cmd = OperatorListAgentsCmd()
		await self.server_cmd_q.put(cmd)
		while True:
			await asyncio.sleep(10)
			if agent_id != '':
				cmd = OperatorGetPluginInfoCmd()
				cmd.agent_id = agent_id
				cmd.plugin_id = plugin_id
				await self.server_cmd_q.put(cmd)
			else:
				print('no plugins started yet :(')