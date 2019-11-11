import asyncio
import websockets
import json
import base64

from multiplexor.plugins.sspi.pluginprotocol import *
from ntlm_test import *
from winsspi.common.gssapi.asn1_structs import *

ntlm_handler = NTLMAUTHHandler()
"""
if version == NTLMVersionCheck.NTLMv1:
	setup_params = { 'ntlm_downgrade': True, 'extended_security': False}
	credtype = netntlm
elif version == NTLMVersionCheck.NTLMv1_LM:
	setup_params = { 'ntlm_downgrade': True, 'extended_security': False}
	credtype = netlm
elif version == NTLMVersionCheck.NTLMv2:
	setup_params = { 'ntlm_downgrade': False, 'extended_security': False}
	credtype = netntlmv2
elif version == NTLMVersionCheck.NTLMv1_ESS:
	setup_params = { 'ntlm_downgrade': False, 'extended_security': True}
	credtype = netntlm_ess
"""

ntlm_handler.setup({ 'ntlm_downgrade': False, 'extended_security': False})
"""
ca = ClientAuth()
r, newbuf = ca.authorize()
status, challenge, t = ntlm_handler.do_AUTH(newbuf[0].Buffer)
r, newbuf = ca.authorize(challenge)
status, challenge, creds = ntlm_handler.do_AUTH(newbuf[0].Buffer)	
for cred in creds:
	if isinstance(cred, credtype):
		return cred

return None
"""

class SSPIAuth:
	def __init__(self):
		self.port = '55065'
		self.server_url = 'ws://127.0.0.1:' + self.port
		
	async def run(self):
		self.ws = await websockets.connect(self.server_url)
		
		"""
		spn_principal = 'srv_http@TEST'
		ac = SSPIKerberosAuthCmd()
		ac.client_name = None
		ac.cred_usage = '3'
		ac.target_name = spn_principal
		await self.ws.send(json.dumps(ac.to_dict()))
		data = await self.ws.recv()
		rply = SSPIPluginCMD.from_dict(json.loads(data))
		#print(rply.authdata)
		
		token = InitialContextToken.load(base64.b64decode(rply.authdata))
		#print(token.native['innerContextToken'])
		
		
		
		"""
		ac = SSPINTLMAuthCmd()
		ac.client_name = None
		ac.cred_usage = '3'
		await self.ws.send(json.dumps(ac.to_dict()))
		data = await self.ws.recv()
		rply = SSPIPluginCMD.from_dict(json.loads(data))
		#print(rply.authdata)
		
		status, challenge, t = ntlm_handler.do_AUTH(base64.b64decode(rply.authdata))

		ac = SSPINTLMChallengeCmd()
		ac.cred_usage = '3'
		ac.token = base64.b64encode(challenge).decode()
		await self.ws.send(json.dumps(ac.to_dict()))
		data = await self.ws.recv()
		rply = SSPIPluginCMD.from_dict(json.loads(data))
		#print(rply.authdata)
		
		status, challenge, creds = ntlm_handler.do_AUTH(base64.b64decode(rply.authdata))
		#for cred in creds:
		#	print(str(cred.to_credential()))
		
		
		
	
		

if __name__ == '__main__':
	ss = SSPIAuth()
	
	loop = asyncio.get_event_loop()
	loop.run_until_complete(ss.run())