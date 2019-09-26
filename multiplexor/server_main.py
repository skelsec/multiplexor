import asyncio
import argparse

from multiplexor.server.transports.websockets import WebsocketsTransportServer
from multiplexor.server.operator.operatorhandler import OperatorHandler
from multiplexor.server.server import MultiplexorServer
from multiplexor.logger.logger import Logger


def main():
	parser = argparse.ArgumentParser(description='multiplexor server startup script')
	parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity, can be stacked')
	parser.add_argument('--agent-listen-ip', default = '0.0.0.0', help='Accept remote agent connections on a spcific IP address. Default: 0.0.0.0')
	parser.add_argument('--agent-listen-port', type = int, default = 8765, help='Accept remote agent connections on a spcific port. Default: 8765')
	
	parser.add_argument('--operator-listen-ip', default = '127.0.0.1', help='Accept remote agent connections on a spcific IP address. Default: 127.0.0.1')
	parser.add_argument('--operator-listen-port', type = int, default = 9999, help='Accept remote agent connections on a spcific port. Default: 9999')

	args = parser.parse_args()
	
	listen_ip = args.agent_listen_ip
	listen_port = args.agent_listen_port
	operator_listen_ip = args.operator_listen_ip
	operator_listen_port = args.operator_listen_port
	
	logger = Logger('Logger')

	op = OperatorHandler(operator_listen_ip, operator_listen_port, logger.logQ)
	transport = WebsocketsTransportServer(listen_ip, listen_port, logger.logQ)
	
	s = MultiplexorServer(logger)
	s.add_transport(transport)
	s.add_ophandler(op)
	
	loop = asyncio.get_event_loop()
	loop.run_until_complete(s.run())

if __name__ == '__main__':
	main()

	