import os
import json
import requests as rq

user = 'user'
pswd = 'pass'
url  = 'http://127.0.0.1'
ctf_dir = './my-ctf'  # the dir to store the challenges (will be created)

s = rq.Session()

def pprint_json(text):
	print(json.dumps(text, indent=2))

def get_nonce():
	res = s.get(url+'/login').text
	pattern = 'name="nonce" value="'
	start = res.find(pattern) + len(pattern)
	end = start + res[start:].find('"')
	nonce = res[start:end]
	# print(nonce)
	return nonce

def get_CSRFtoken(res):
	pattern = '\'csrfNonce\': "'
	start = res.find(pattern) + len(pattern)
	end = start + res[start:].find('"')
	csrf_token = res[start:end]
	# print(csrf_token)
	return csrf_token

def login(user, pswd):
	nonce = get_nonce()
	res = s.post(
		url+'/login',
		headers={
			'Content-Type': 'application/x-www-form-urlencoded'},
		data={
			'name': user,
			'password': pswd,
			'nonce': nonce},
		allow_redirects=True
	)
	csrf_token = get_CSRFtoken(res.text)
	return csrf_token

def challenges():
	res = s.get(url+'/api/v1/challenges')
	res = json.loads(res.text)
	if res['success'] != True:
		print('[-] Failed to read the challenges.')
		exit(1)
	challs = res['data']
	# pprint_json(challs)
	return challs

def get_challenge_info(chall):
	res = s.get(url+f'/api/v1/challenges/{chall["id"]}')
	api_res = json.loads(res.text)
	if api_res['success'] != True:
		print(f'[-] Failed to read the challenge, challenge id: {chall["id"]}')
		exit(1)
	chall_info = api_res['data']
	return chall_info

def store_challenge(chall_info):
	name       = chall_info['name']
	value      = chall_info['value']
	description = chall_info['description'].replace('\x0d', '')
	category   = chall_info['category']
	files      = chall_info['files']
	print(chall_info['id'], name, category)
	dir_path = f'{ctf_dir}/{category}/{name}/'
	os.makedirs(dir_path, exist_ok=True)
	for file_url in files:
		# download challenge
		res = rq.get(url+file_url)
		file_name = file_url[file_url.rfind('/'):] if '?' not in file_url else file_url[file_url.rfind('/'):file_url.find('?')]
		with open(dir_path+file_name, 'wb') as f:
			f.write(res.content)
		# write description
		with open(dir_path+'readme.md', 'w') as f:
			f.write(f'''\
## {name}
- value: {value}
### Description
{description}
''')

print('[*] Logging in...')
csrf_token = login(user, pswd)
s.headers.update({'CSRF-Token': csrf_token})
challs = challenges()

os.mkdir(ctf_dir)
for chall in challs:
	print('[*] Crawling the challenges...')
	chall_info = get_challenge_info(chall)
	store_challenge(chall_info)

s.close()


