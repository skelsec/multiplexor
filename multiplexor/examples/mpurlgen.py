

def main():
	import argparse
	parser = argparse.ArgumentParser(description='URL generator helper for MP')
	parser.add_argument('-p', '--protocol', default = 'ldap', help='Protocol')
	parser.add_argument('--auth-type', default = 'ntlm', help='Authentication type (ntlm or kerberos)')
	parser.add_argument('--ip', default = '127.0.0.1', help='MP operator listen IP. Default: 127.0.0.1')
	parser.add_argument('--port', type = int, default = 9999, help='MP operator service port. Default: 9999')
	parser.add_argument('agentid', help='Agent ID for authentication')
	parser.add_argument('agentid', help='Agent ID for authentication')
	args = parser.parse_args()

	fdict = {
		'protocol' : args.protocol,
		'authtype' : args.auth_type,
		'host' : args.ip,
		'port' : args.port,
		'authagentid' : args.agentid,
		'proxyagentid' : args.proxyagentid,
	}

	url = '{protocol}+multiplexor-{authtype}://IP:PORT/?proxytype=multiplexor&proxyhost={host}&proxyport={port}&proxyagentid={proxyagentid}&authhost={host}&authport={port}&authagentid={authagentid}'.format(**fdict)

	print(url)

if __name__ == '__main__':
	main()