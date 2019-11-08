import asyncio
import websockets
import json

from multiplexor.plugins.sspi.pluginprotocol import *

class SSPINTLMClient:
	def __init__(self, url):
		self.server_url = url
		self.transport = None
		self.data = None
		
	async def connect(self):
		self.transport = await websockets.connect(self.server_url)
		
	async def authenticate(self):
		ac = SSPINTLMAuthCmd()
		ac.client_name = None
		ac.cred_usage = '3'
		await self.transport.send(json.dumps(ac.to_dict()))
		data = await self.transport.recv()
		rply = SSPIPluginCMD.from_dict(json.loads(data))
		self.data = rply.authdata
		
	async def challenge(self, challenge):
		ac = SSPINTLMChallengeCmd()
		ac.cred_usage = '3'
		ac.token = base64.b64encode(challenge).decode()
		await self.transport.send(json.dumps(ac.to_dict()))
		data = await self.transport.recv()
		rply = SSPIPluginCMD.from_dict(json.loads(data))
		self.data = rply.authdata

	async def get_sessionkey(self):
		ac = SSPIGetSessionKeyCmd()
		await self.transport.send(json.dumps(ac.to_dict()))
		data = await self.transport.recv()
		rply = SSPIPluginCMD.from_dict(json.loads(data))
		self.data = rply.session_key
	

if __name__ == '__main__':
	from ntlm_test import *
	#testing dumb interface between asynchronous ans synchronous stuff :(
	#a lot of libraries are still synchronous
	ntlm_handler = NTLMAUTHHandler()
	ntlm_handler.setup({ 'ntlm_downgrade': False, 'extended_security': False})
	
	url = 'ws://127.0.0.1:53436'
	client = SSPINTLMClient(url)
	asyncio.get_event_loop().run_until_complete(client.connect())
	asyncio.get_event_loop().run_until_complete(client.authenticate())
	
	status, challenge, t = ntlm_handler.do_AUTH(base64.b64decode(client.data))
	
	asyncio.get_event_loop().run_until_complete(client.challenge(challenge))
	
	status, challenge, creds = ntlm_handler.do_AUTH(base64.b64decode(client.data))
	for cred in creds:
		print(str(cred.to_credential()))
	
	print()
	