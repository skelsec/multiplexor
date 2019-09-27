import asyncio
import enum

from multiplexor.logger.logger import mpexception, Logger
from multiplexor.server.protocol import MultiplexorPluginData
		
class AgentStatus(enum.Enum):
	CONNECTED = 0
	REGISTERING = 1
	REGISTERED = 2
	TERMINATING = 3
	TERMINATED = 4
	
class MultiplexorAgent:
	def __init__(self, logQ):
		self.logger = Logger('MultiplexorAgent', logQ)
		self.agent_id = None
		self.transport = None
		self.transport_terminated_evt = asyncio.Event()
		self.packetizer = None
		
		self.plugin_ctr = 0
		self.plugins = {}
		self.plugin_taks = {}
		self.plugin_operator = {} #plugin_id -> operator
		
		self.status = AgentStatus.CONNECTED
		
		self.info = None

	@mpexception
	async def terminate(self):
		for plugin_id in self.plugin_taks:
			self.plugin_taks[plugin_id].cancel()
		
		
	@mpexception
	async def handle_plugin_out(self, plugin):
		"""
		This function created one per new plugin started
		All it does is to wrap the plugin's outgoing bytes to a server command 
		then dispatches it to the agent's packetizer
		"""
		while not self.transport_terminated_evt.is_set() or not plugin.stop_plugin_evt.is_set():
			data = await plugin.plugin_out.get() #bytes!
			
			cmd = MultiplexorPluginData()
			cmd.plugin_id = plugin.plugin_id
			cmd.plugin_data = data
			await self.packetizer.multiplexor_out.put(cmd)
			await asyncio.sleep(0)
		#at this pont the plugin stopped / agent disconnected
		del self.plugins[plugin.plugin_id]		
		
	def add_plugin(self, plugin_obj, cmd, operator):
		plugin_id = str(self.plugin_ctr)
		self.plugin_ctr += 1
		self.plugin_operator[plugin_id] = operator
		self.plugins[plugin_id] = plugin_obj(plugin_id, self.logger.logQ, cmd.plugin_type, cmd.server)
		self.plugin_taks[plugin_id] = asyncio.create_task(self.handle_plugin_out(self.plugins[plugin_id]))
		return plugin_id