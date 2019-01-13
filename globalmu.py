import requests
import threading
import time
import json


#Parse basic settings
vote_ids = [38,48,52,53]
proxies = []
black_list = []
accounts = []
balance = {}

with open("proxies.txt") as fo:
	proxies = fo.read().splitlines()

print(proxies)

with open("blacklist.txt") as fo:
	black_list = fo.read().splitlines()

with open("balance.json") as fo:
	balance = json.loads(fo.read())


with open("accounts.txt") as fo:
	lines = fo.read().splitlines()
	for line in lines:
		accounts += line.split(" ")

def vote(username,password, proxies, lock):
	sess = requests.session()

	print("Voting for acc: "+username)

	proxy = None
	if username not in balance:
		balance[username] = 0
	try:
		sess.post('https://globalmu.net/account-panel/login', {
			  "username" :  username,
			  "password": password,
			  "server": 'X50'
			}, timeout=10)

		lock.acquire()
		while len(proxies) > 0:
			proxy = proxies.pop(0)
			if proxy not in black_list:
				break
		lock.release()

		if proxy is not None:
			for id in vote_ids:
				#try until succeed
				success = False
				while not success and len(proxies) > 0:
					bonus = vote_request(sess,id, proxy)
					if bonus != -1:
						success = True
						balance[username] += bonus
						if proxy not in black_list: # add latest proxy if hasnt been added
							lock.acquire()
							black_list.append(proxy)
							with open("blacklist.txt", "a+") as f:
								f.write(proxy+"\n")
								print("Blacklisting: "+proxy)
							lock.release()
					else:
						lock.acquire()
						proxy = proxies.pop(0)
						lock.release()
						time.sleep(1)
						continue
			lock.acquire()
			with open("balance.json", "w") as f:
				f.write(json.dumps(balance))
			lock.release()
			print("Finished voting for:" +username);
	except Exception as e:
		print(e)

def vote_request(sess, id, proxy):
	print("using proxy: "+proxy)
	try: 
		result = sess.post('https://globalmu.net/ajax/vote',
			{
				"vote": id
			}, proxies={'https':proxy}, timeout=10).json()

		if 'success' in result: 
			return 10
	except Exception as e:
		print(e)
		return -1
	return 0


lock = threading.Lock()
n_threads = 5
for t in range(0,len(accounts),2 * n_threads):
	threads = []
	for i in range(t,t+2*n_threads,2):
		try :
			thread = threading.Thread(target = vote, args=(accounts[i],accounts[i+1],proxies, lock,))
			threads.append(thread)
			thread.start()
			time.sleep(2)
		except:
			continue

	for thread in threads:
		thread.join()


