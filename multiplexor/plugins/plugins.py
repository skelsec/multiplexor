import asyncio

from multiplexor.logger.logger import *

class PluginType(enum.Enum):
	SOCKS5 = 0
	PYPYKATZ = 1
	SSPI = 2
	
class Plugin:
	def __init__(self):
		self.plugin_id = None
		self.plugin_in = None
		self.plugin_out = None
		self.stop_plugin_evt = None
		
class MultiplexorPluginBase:
	def __init__(self, plugin_id, plugin_name, logQ):
		self.plugin_id = plugin_id
		self.plugin_name = plugin_name
		self.logger = Logger(plugin_name, logQ)
		self.plugin_in = asyncio.Queue()
		self.plugin_out = asyncio.Queue()
		self.stop_plugin_evt = asyncio.Event()
		
	def get_plugin(self):
		p = Plugin
		p.plugin_id = self.plugin_id
		p.plugin_in = self.plugin_in
		p.plugin_out = self.plugin_out
		p.stop_plugin_evt = self.stop_plugin_evt
		return p
	
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
		
		