import asyncio

from multiplexor.plugins.plugins import *
from multiplexor.logger.logger import *
from multiplexor.operator.protocol import *

class MultiplexorRemoting(MultiplexorPluginBase):
	def __init__(self, plugin_id, logQ, plugin_type, plugin_params):
		MultiplexorPluginBase.__init__(self, plugin_id, 'MultiplexorSocks5', logQ, plugin_type, plugin_params)		
		self.operator = None
		self.agent_id = None
			
	async def setup(self):
		self.operator = self.plugin_params['operator']
		self.agent_id = self.plugin_params['agent_id']
	
	@mpexception
	async def run(self):
		"""
		The main function of the plugin.
		Sets up a listener server and the Task to dispatch incoming commands to the appropriate sockets
		"""
		while not self.operator.transport_closed.is_set():
			data = await self.plugin_in.get()
			rply = OperatorPluginData(self.agent_id, self.plugin_id, data.hex())
			await self.operator.multiplexor_cmd_out.put(rply)