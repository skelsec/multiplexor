

import requests 
URL = "http://127.0.0.1:8765/alma"
PARAMS = {'data':'asdfq4t134to9013jg[oqaike;vmaq;eo54itj1	34oin;'} 
r = requests.post(url = URL, data = PARAMS)
print(r.text)
