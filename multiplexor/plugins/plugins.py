import asyncio
from multiplexor.logger.logger import *
		
class MultiplexorPluginBase:
	"""
	All plugins MUST be inherited from this base class.
	"""

	def __init__(self, plugin_id, plugin_name, logQ, plugin_type, plugin_params):
		self.plugin_id = plugin_id
		self.plugin_name = plugin_name
		self.logger = Logger(plugin_name, logQ=logQ)
		self.plugin_in = asyncio.Queue()
		self.plugin_out = asyncio.Queue()
		self.stop_plugin_evt = asyncio.Event()
		self.plugin_info = None #should b overridden by the inheritor
		self.plugin_type = plugin_type
		self.plugin_params = plugin_params
		self.server = None
	
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
		
		