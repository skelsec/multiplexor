
import logging
import asyncio
from multiplexor.operator import MultiplexorOperator

async def amain():
	import argparse
	parser = argparse.ArgumentParser(description='auto collector for MP')
	#parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity, can be stacked')
	parser.add_argument('--listen-ip', default = '127.0.0.1', help='Socks service listen IP. Default: 127.0.0.1')
	parser.add_argument('--listen-port', type = int, default = 0, help='Socks5 service port. Default: random')
	parser.add_argument('multiplexor', help='multiplexor connection string in URL format')
	parser.add_argument('agentid', help='Agent ID on the socks server to be opened')
	args = parser.parse_args()

	logging.basicConfig(level=logging.DEBUG)
	logging.getLogger('websockets.server').setLevel(logging.ERROR)
	logging.getLogger('websockets.client').setLevel(logging.ERROR)
	logging.getLogger('websockets.protocol').setLevel(logging.ERROR)
	
	#creating operator and connecting to multiplexor server
	operator = MultiplexorOperator(args.multiplexor) #logging_sink = logger
	await operator.connect()
	#creating socks5 proxy
	server_info = await operator.start_socks5(args.agentid, listen_ip=args.listen_ip, listen_port=args.listen_port)
	print('Created SOCKS5 proxy tunneling to %s' % args.agentid)
	print('Server IP  : %s' % server_info['listen_ip'])
	print('Server port: %s' % server_info['listen_port'])
	print('Server auth: %s' % server_info['auth_type'])
	print('Close this to stop the service')
	await operator.disconnected_evt.wait()


def main():
	asyncio.run(amain())

if __name__ == '__main__':
	main()