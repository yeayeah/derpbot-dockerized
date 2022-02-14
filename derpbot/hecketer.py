import urllib
from http2 import RsHttp, _parse_url
from soup_parser import soupify
import random
import rsparse
import json
try:
	import cc_markov
	import os
	markov = True
except:
	markov = False

def file_get_contents(uri):
	host, port, ssl, uri = _parse_url(uri)
	proxies = None
	http = RsHttp(host,ssl=ssl,port=port, keep_alive=True, follow_redirects=True, auto_set_cookies=True, proxies=proxies, user_agent='Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0')
	if not http.connect(): return None
	hdr, res = http.get(uri)
	if isinstance(res, unicode): res = res.encode('utf-8')
	return res

class Hecketer():
	def __init__(self):
		self.sites = ['answers', 'reddit']
		self.markov = cc_markov.MarkovChain() if markov else None
		if self.markov:
			if os.path.exists('markov.learn'):
				self.markov.add_file('markov.learn')

	def reddit_extract(self, uri):
		answers = []
		res = file_get_contents(uri)
		content = '\n'.join([ script for script in rsparse.find_all_tags(res, 'script') ])
		soup = soupify(content)
		for script in soup.find_all('script', attrs={'id':'data'}):
			contents = script.contents[0].split(' ')
			_json = json.loads( ' '.join( contents[2:] )[:-1] )
			if 'features' in _json and 'comments' in _json['features'] and 'models' in _json['features']['comments']:
				for item in _json['features']['comments']['models']:
					row = _json['features']['comments']['models'][item]
					if not 'media' in row: continue
					if not 'richtextContent' in row['media']: continue
					if not 'document' in row['media']['richtextContent']: continue
					for d in row['media']['richtextContent']:
						documents = row['media']['richtextContent'][d][0]
						try: text = documents['c'][0]['t']
						except: continue
						answers.append(text)
		return answers
				

	def ask(self, text, single=True):
		answers = []
		random.shuffle(self.sites)

		for site in self.sites:

			if site == 'reddit':
				urlencoded = urllib.quote_plus(text)
				res = file_get_contents('https://www.reddit.com/search/?q=%s' %urlencoded)
				if res is not None:
					content = '\n'.join( [ a for a in rsparse.find_all_tags(res, 'a') if a.find('/comments/') != -1 ])
					soup = soupify(content)
					uris = [ a['href'] for a in soup.find_all('a') if a['href'].find('reddit.com/r/') != -1 ]
					if not len(uris): continue
					random.shuffle(uris)
					for uri in uris:
						for answer in self.reddit_extract( uri ):
							if isinstance(answer, unicode): answer = answer.encode('utf-8').replace('\n', ' ')
							answers.append( answer )

						if len(answers) and single: break

			elif site == 'answers':
				encoded = text.replace(' ', '_')
				res = file_get_contents('https://www.answers.com/Q/%s' %encoded)
				if res is not None:
					soup = soupify(res)
					meta = soup.find('meta', property='og:description')
					reply = meta['content'] if meta else None
					if reply:
						if isinstance(reply, unicode): reply = reply.encode('utf-8')
						reply = reply.replace('\n', ' ')
						if reply.startswith('Answers'): continue
						if isinstance(reply, unicode): reply = reply.encode('utf-8')
						answers.append(reply)

			if len(answers) and single: break

		if not len(answers): return None
		if self.markov:
			for answer in answers: self.markov.add_string(answer)

		return random.choice(answers)

if __name__ == "__main__":

	heck = Hecketer()

	while 1:
		try:
			user_input = raw_input('Input: ')
			reply = heck.ask(user_input)
			if reply is None: reply = ' '.join( heck.markov.generate_text() )
			print('> %s' %reply)

		except KeyboardInterrupt:
			break
		except Exception as e:
			print('error: "%s"' %e)
