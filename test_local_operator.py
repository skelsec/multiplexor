import asyncio

from multiplexor.operator.local.common.connector import *
from multiplexor.operator.local.common.listener import *
from multiplexor.operator.local.socks5 import *
from multiplexor.operator.local.sspi import *

"""
This script is mainly used for testing or to start plugins and let them run.
It will take ONE command only and just print out whatever is coming out of the server queue
"""

async def listen_reply(connector):
	while True:
		rply = await connector.cmd_in_q.get()
		print(rply.to_dict())
		

async def main(args):
	#TODO: implement verbosity
	
	
	##setting up logging
	logger = Logger('Operator')
	asyncio.ensure_future(logger.run())
	
	## setting up operator
	if args.connection_type == 'connect':
		connector = MultiplexorOperatorConnector(args.connection_string, logger.logQ, ssl_ctx = None, reconnect_interval = 5)
		
	elif args.connection_type == 'listen':
		if args.connection_string.find(':') != -1:
			listen_ip, listen_port = args.connection_string.split(':')
		else:
			listen_ip = '127.0.0.1'
			listen_port = int(args.connection_string)
		connector = MultiplexorOperatorListener(listen_ip, listen_port, logger.logQ, ssl_ctx = None, reconnect_interval = 5)
	
	## starting connector
	asyncio.ensure_future(connector.run())
	
	## sending commands
	if args.command == 'server':
		if args.cmd == 'list':
			cmd = OperatorListAgentsCmd()
			await connector.cmd_out_q.put(cmd)
	
	elif args.command == 'agent':
		if args.cmd == 'info':
			cmd = OperatorGetAgentInfoCmd(args.agentid)
			await connector.cmd_out_q.put(cmd)
			
		elif args.cmd == 'list':
			cmd = OperatorListPluginsCmd(args.agentid)
			await connector.cmd_out_q.put(cmd)
			
	elif args.command == 'plugin':
		if args.cmd == 'info':
			cmd = OperatorGetPluginInfoCmd(args.agentid, args.pluginid)
			await connector.cmd_out_q.put(cmd)
			
			
	elif args.command == 'create':
		if args.type == 'socks5':
			if args.remote == False:
				cmd = OperatorStartPlugin()
				cmd.agent_id = args.agentid
				cmd.plugin_type = PluginType.SOCKS5.value
				cmd.server = Socks5PluginServerStartupSettings(listen_ip = args.listen_ip, listen_port = args.listen_port, auth_type = None, remote = False)
				await connector.cmd_out_q.put(cmd)
			
			else:
				#this passes all controls over to the local sock5server object
				#exits the function when socks5 server is terminated
				so = MultiplexorSocks5Operator(logger.logQ, connector, args.agentid)
				await so.run()
				return
			
			
		elif args.type == 'sspi':
			if args.remote == False:
				#cmd = OperatorStartPlugin()
				cmd.agent_id = args.agentid
				cmd.plugin_type = PluginType.SSPI.value
				cmd.server = Socks5PluginServerStartupSettings(listen_ip = args.listen_ip, listen_port = args.listen_port, auth_type = None, remote = False)
				await connector.cmd_out_q.put(cmd)
			
			else:
				#this passes all controls over to the local sock5server object
				#exits the function when socks5 server is terminated
				so = MultiplexorSSPIOperator(logger.logQ, connector, args.agentid)
				await so.run()
				return


	## waiting for replies
	await listen_reply(connector)
	


if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description='Local operator for multiplexor')
	parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity, can be stacked')
	parser.add_argument('-t', '--connection-type', choices=['listen', 'connect'], help='Defines the connection type to the multiplexor server')
	parser.add_argument('-c', '--connection-string', help = 'Either <ip>:<port> or a websockets URL "ws://<ip>:<port>", depending on the connection type')
	

	subparsers = parser.add_subparsers(help = 'commands')
	subparsers.required = True
	subparsers.dest = 'command'
	
	server_group = subparsers.add_parser('server', help='Server related commands')
	server_group.add_argument('cmd', choices=['list'], help='command')
	
	agent_group = subparsers.add_parser('agent', help='Server related commands')
	agent_group.add_argument('agentid', help='agent ID')
	agent_group.add_argument('cmd', choices=['list','info'], help='command')
	
	
	plugin_group = subparsers.add_parser('plugin', help='Server related commands')
	plugin_group.add_argument('agentid', help='agent ID')
	plugin_group.add_argument('pluginid', help='plugin ID')
	plugin_group.add_argument('cmd', choices=['info'], help='command')
	
	create_plugin_group = subparsers.add_parser('create', help='Starts a plugin on the agent')
	create_plugin_group.add_argument('agentid', help='agent ID')
	create_plugin_group.add_argument('type', choices=['socks5','sspi'], help='command')
	create_plugin_group.add_argument('-r', '--remote', action='store_true', help='plugin server will be listening on the mutiplexor server')
	create_plugin_group.add_argument('-l', '--listen-ip', help='IP to listen on')
	create_plugin_group.add_argument('-p', '--listen-port', help='Port to listen on')
	create_plugin_group.add_argument('-d', '--startup-data', help='Additional data in JSON form to be passed to the plugin startup routine')
	
	args = parser.parse_args()
	
	loop = asyncio.get_event_loop()
	loop.run_until_complete(main(args))
	
			
	