import asyncio

from multiplexor.operator.local.common.connector import MultiplexorOperatorConnector
from multiplexor.operator.local.common.listener import MultiplexorOperatorListener
from multiplexor.operator.local.socks5 import MultiplexorSocks5Operator, Socks5PluginServerStartupSettings
from multiplexor.operator.local.sspi import MultiplexorSSPIOperator

from multiplexor.plugins.plugintypes import PluginType
from multiplexor.operator.protocol import OperatorGetAgentInfoCmd, OperatorListAgentsCmd, OperatorStartPlugin, OperatorGetPluginInfoCmd, OperatorListPluginsCmd, OperatorCmdType
from multiplexor.logger.logger import mpexception, Logger
from multiplexor.operator.exceptions import MultiplexorRemoteException
from multiplexor.operator.operator import MultiplexorOperator


class MultiplexorAutoStart(MultiplexorOperator):
	def __init__(self, connection_string, logger = None):
		MultiplexorOperator.__init__(self, connection_string, logger = None)

		self.agent_tracker = {}
		self.plugin_tracker = {}

	async def on_agent_connect(self, agent_id, agentinfo):
		try:
			print('Agent connected! %s' % agent_id)
			try:
				plugin_id = await self.start_socks5(agent_id, listen_ip = '127.0.0.1', listen_port = 0, remote = False)
				print(plugin_id)
			except:
				await self.logger.exception()
				return
			
			try:
				plugin_id = await self.start_sspi(agent_id, listen_ip = '127.0.0.1', listen_port = 0, remote = False)
				print(plugin_id)
			
			except:
				await self.logger.exception()
				return
			
			self.agent_tracker[agent_id] = agentinfo


		except:
			await self.logger.exception()

	async def on_agent_disconnect(self, agent_id):
		print('Agent disconnected! %s' % agent_id)

	async def on_plugin_start(self, agent_id, plugin_id):
		print('Plugin started! %s %s' % (agent_id, plugin_id))

	async def on_plugin_stop(self, agent_id, plugin_id):
		print('Plugin stopped! %s %s' % (agent_id, plugin_id))
	
	async def on_log(self, log):
		pass

def main():
	cs = 'ws://127.0.0.1:9999'
	mas = MultiplexorAutoStart(cs)
	asyncio.run(mas.run())
	

if __name__ == '__main__':
	main()