import asyncio
import argparse
import json
import ssl
import logging.config

from multiplexor.server.transports.websockets import WebsocketsTransportServer
from multiplexor.server.operator.operatorhandler import OperatorHandler
from multiplexor.server.server import MultiplexorServer
from multiplexor.logger.logger import Logger
from multiplexor._version import __banner__

multiplexor_logconfig = {
	'version': 1,
	'disable_existing_loggers': False,
	'loggers': {
		'': {
			'level': 'DEBUG',
		},
		'websockets': {
			'level': 'INFO',
		},
		'multiplexor_server': {
			'level': 'DEBUG',
		}
	}
}

async def startup(operator_listen_ip, operator_listen_port, listen_ip, listen_port, agent_sslctx = None, operator_sslctx = None):
	logger = Logger('multiplexor_server')

	ophandler = OperatorHandler(operator_listen_ip, operator_listen_port, logger.logQ, ssl_ctx=operator_sslctx)
	transport = WebsocketsTransportServer(listen_ip, listen_port, logger.logQ, ssl_ctx=agent_sslctx)
	
	mpserver = MultiplexorServer(logger)
	mpserver.add_transport(transport)
	mpserver.add_ophandler(ophandler)

	print(__banner__)
	print('[+] Running config:')
	print('[+] Agent service listening on    : %s:%s' % (listen_ip, listen_port))
	print('[+] Operator service listening on : %s:%s' % (operator_listen_ip, operator_listen_port))
	print('[+] Starting server...')
	await mpserver.run()

def main():
	parser = argparse.ArgumentParser(description='multiplexor server startup script')
	parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity, can be stacked')
	parser.add_argument('--agent-listen-ip', default = '0.0.0.0', help='Accept remote agent connections on a spcific IP address. Default: 0.0.0.0')
	parser.add_argument('--agent-listen-port', type = int, default = 8765, help='Accept remote agent connections on a spcific port. Default: 8765')
	parser.add_argument('--agent-ssl-cert', help='Cert file for the agent server')
	parser.add_argument('--agent-ssl-key', help='Key file for the agent server')
	
	parser.add_argument('--operator-listen-ip', default = '127.0.0.1', help='Accept remote agent connections on a spcific IP address. Default: 127.0.0.1')
	parser.add_argument('--operator-listen-port', type = int, default = 9999, help='Accept remote agent connections on a spcific port. Default: 9999')
	parser.add_argument('--operator-ssl-cert', help='Cert file for the operator server')
	parser.add_argument('--operator-ssl-key', help='Key file for the operator server')
	
	parser.add_argument('-l', '--log-config-file', help='File for log configuration. Dictconfig encoded with json. Overrides verbosity!')
	
	args = parser.parse_args()
	
	listen_ip = args.agent_listen_ip
	listen_port = args.agent_listen_port
	operator_listen_ip = args.operator_listen_ip
	operator_listen_port = args.operator_listen_port

	agent_sslctx = None
	operator_sslctx = None

	if args.agent_ssl_cert is not None:
		agent_sslctx = ssl.SSLContext(ssl.PROTOCOL_TLS)
		agent_sslctx.load_cert_chain(args.agent_ssl_cert, args.agent_ssl_key)

	if args.operator_ssl_cert is not None:
		operator_sslctx = ssl.SSLContext(ssl.PROTOCOL_TLS)
		operator_sslctx.load_cert_chain(args.operator_ssl_cert, args.operator_ssl_key)

	if args.log_config_file:
		with open(args.log_config_file,'r') as f:
			logconf = json.load(f)
	else:
		logconf = multiplexor_logconfig
		if args.verbose == 1:
			logconf['loggers'][''] = 'DEBUG'
			logconf['loggers']['multiplexor_server'] = 'DEBUG'
			logconf['loggers']['websockets'] = 'DEBUG'
		elif args.verbose == 2:
			logconf['loggers'][''] = 1
			logconf['loggers']['multiplexor_server'] = 'DEBUG'
			logconf['loggers']['websockets'] = 1

	logging.config.dictConfig(logconf)
	
	asyncio.run(startup(operator_listen_ip, operator_listen_port, listen_ip, listen_port, agent_sslctx, operator_sslctx))
	

if __name__ == '__main__':
	main()

	