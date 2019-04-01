import asyncio

from multiplexor.transports.websockets import WebsocketsTransportServer
from multiplexor.operatorhandler import OperatorHandler
from multiplexor.server import MultiplexorServer

if __name__ == '__main__':
	listen_ip = '127.0.0.1'
	listen_port = 8765
	operator_listen_ip = '127.0.0.1'
	operator_listen_port = 9999	
	
	logging_queue = asyncio.Queue()
	op = OperatorHandler(operator_listen_ip, operator_listen_port)
	transport = WebsocketsTransportServer(listen_ip, listen_port, logging_queue)
	
	s = MultiplexorServer()
	s.add_transport(transport)
	s.add_ophandler(op)
	
	loop = asyncio.get_event_loop()
	loop.run_until_complete(s.run())