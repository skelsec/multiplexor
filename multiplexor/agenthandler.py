import asyncio
import enum

from multiplexor.logger.logger import *
from multiplexor.protocol.server import *
		
class AgentStatus(enum.Enum):
	CONNECTED = 0,
	REGISTERING = 1,
	REGISTERED = 2,
	TERMINATING = 3,
	TERMINATED = 4
	
class MultiplexorAgentHandler:
	def __init__(self, logQ):
		self.logger = Logger('MultiplexorAgentHandler', logQ)
		self.agent_id = None
		self.transport = None
		self.trasnport_terminated_evt = asyncio.Event()
		self.packetizer = None
		
		self.plugin_ctr = 0
		self.plugins = {}
		
		self.status = AgentStatus.CONNECTED
		
		self.info = None
		
	@mpexception
	async def handle_plugin_out(self, plugin):
		while not plugin.stop_plugin_evt.is_set():
			data = await plugin.plugin_out.get() #bytes!
			
			cmd = MultiplexorPluginData()
			cmd.plugin_id = plugin.plugin_id
			cmd.plugin_data = data
			await self.packetizer.multiplexor_out.put(cmd)
			await asyncio.sleep(0)
		
	def add_plugin(self, plugin_obj, plugin_type, plugin_params):
		plugin_id = self.plugin_ctr
		self.plugin_ctr += 1
		self.plugins[plugin_id] = plugin_obj(plugin_id, self.logger.logQ, plugin_type, plugin_params)
		asyncio.ensure_future(self.handle_plugin_out(self.plugins[plugin_id]))
		return plugin_id