import asyncio
import websockets
import json

from multiplexor.operator.external.sspi import *
from ldap3 import Server, Connection, ALL, NTLM



if __name__ == '__main__':
	
	
	
	server = Server('10.10.10.2', get_info=ALL)
	try:
		import ldap3.utils.ntlm
	except Exception as e:
		print('Failed to import winsspi module!')
		raise e
	#monkey-patching NTLM client with winsspi's implementation
	ldap3.utils.ntlm.NtlmClient = LDAP3NTLMSSPI
	c = Connection(server, user="test\\test", password="aaa", authentication=NTLM)
	c.bind()
	
	print(server.info)