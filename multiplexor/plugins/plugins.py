import asyncio

from multiplexor.logger.logger import *

class Plugin:
	def __init__(self):
		self.plugin_id = None
		self.plugin_in = None
		self.plugin_out = None
		
class MultiplexorPluginBase:
	def __init__(self, plugin_name, logQ):
		self.plugin_name = plugin_name
		self.logger = Logger(plugin_name, logQ)
		self.plugin_in = asyncio.Queue()
		self.plugin_out = asyncio.Queue()
		self.stop_plugin_evt = asyncio.Event()
	
	@mpexception
	async def handle_in_raw(self):
		while not self.stop_plugin_evt.is_set():
			data = await self.plugin_in.get()
			await self.data_in(data)
			
	@mpexception	
	async def data_out(self, data):
		await self.plugin_out.put(data)
			
	@mpexception
	async def start(self):
		await self.setup()
		await self.run()
		self.stop_plugin_evt.set()

	
	##### OVERRIDE THE FUNCTIONS BELOW
	@mpexception
	async def setup(self):
		pass
	
	@mpexception
	async def run(self):
		pass
	
	@mpexception
	async def data_in(self):
		pass
		
		