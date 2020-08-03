
import asyncio
import json

from multiplexor.plugins.plugins import *
from multiplexor.plugins.sspi.pluginprotocol import *
from multiplexor.plugins.sspi.plugininfo import *
from multiplexor.logger.logger import *

from multiplexor.plugins.filesystem.pluginprotocol import *


class MultiplexorFilesystem(MultiplexorPluginBase):
	def __init__(self, plugin_id, logQ, plugin_type, plugin_params):
		MultiplexorPluginBase.__init__(self, plugin_id, 'MultiplexorFS', logQ, plugin_type, plugin_params)
		
		self.dispatch_table = {} #session_id to filesystemsession
		self.current_session_id = 0
	
	@mpexception		
	async def terminate(self):
		await self.logger.debug('MultiplexorFS terminate called!')
		for session_id in self.dispatch_table:
			await self.dispatch_table[session_id].terminate()
		
		if self.server is not None:
			self.server.close()
		return
	
	@mpexception		
	async def handle_plugin_data_in(self):
		"""
		Handles the incoming commands from the remote agent's plugin
		"""
		while True:
			data = await self.plugin_in.get()
			if data is None:
				await self.terminate()
				return
			#print('Got plugin data!')
			cmd = FSPluginCMD.from_bytes(data)
			#print('SSPI Plugin data in from remote agent SSPI: %s' % str(cmd))
			
			await self.dispatch_table[cmd.session_id].agent_in.put(cmd)
		
		await self.logger.debug('handle_plugin_data_in exiting!')
		
			
	async def setup(self):
		pass

	@mpexception
	async def run(self):
		"""
		The main function of the plugin.
		"""
		
