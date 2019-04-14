import asyncio

from multiplexor.transports.websockets import WebsocketsTransportServer
from multiplexor.operatorhandler import OperatorHandler
from multiplexor.server import MultiplexorServer
from multiplexor.logger.logger import Logger

if __name__ == '__main__':
	listen_ip = '127.0.0.1'
	listen_port = 8765
	operator_listen_ip = '127.0.0.1'
	operator_listen_port = 9999	
	
	logger = Logger('Logger')

	op = OperatorHandler(operator_listen_ip, operator_listen_port, logger.logQ)
	transport = WebsocketsTransportServer(listen_ip, listen_port, logger.logQ)
	
	s = MultiplexorServer(logger)
	s.add_transport(transport)
	s.add_ophandler(op)
	
	loop = asyncio.get_event_loop()
	loop.run_until_complete(s.run())