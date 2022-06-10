import urllib
from soup_parser import soupify
import misc
import random
import rsparse
import json

try:
	import cc_markov
	import os
	markov = True
except:
	markov = False

class Hecketer():
	def __init__(self, learn=True, return_asap=True, proxies=None):
		self.learn = learn
		self.return_asap = return_asap
		self.sites = ['answers', 'reddit', 'ddg', 'ask']
		self.markov = cc_markov.MarkovChain() if markov else None
		self.proxies = proxies
		if self.markov and self.learn:
			if os.path.exists('markov.learn'):
				self.markov.add_file('markov.learn')

	def set_sites(self, sites):
		self.sites = [ i.strip() for i in str(sites).split(',') ]

	def _ask_reddit(self, text, answers=[]):
		def reddit_extract(uri):
			answers = []
			res = misc.file_get_contents(uri, proxies=self.proxies)
			if res is None: return None
			contents = '\n'.join([ script for script in rsparse.find_all_tags(res, 'script') ])
			soup = soupify(contents)
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
		urlencoded = urllib.quote_plus(text)
		res = misc.file_get_contents('https://www.reddit.com/search/?q=%s' %urlencoded, proxies=self.proxies)
		if res is None: return None
		contents = '\n'.join( [ a for a in rsparse.find_all_tags(res, 'a') if a.find('/comments/') != -1 ])
		soup = soupify(contents)
		uris = [ a['href'] for a in soup.find_all('a') if a['href'].find('reddit.com/r/') != -1 ]
		if not len(uris): return None
		for reply in reddit_extract( random.choice(uris) ):
			reply = self.check_reply(reply)
			if reply is not None: answers.append(reply)

		return answers if len(answers) else None

	def _ask_answers(self, text, answers=[]):
		encoded = text.replace(' ', '_')
		res = misc.file_get_contents('https://www.answers.com/Q/%s' %encoded, proxies=self.proxies)
		if res is None: return None
		soup = soupify(res)
		meta = soup.find('meta', property='og:description')
		reply = self.check_reply( meta['content']) if meta else None
		if reply is not None: answers.append(reply)
		return answers if len(answers) else None

	def _ask_ddg(self, text, answers=[]):
		encoded = urllib.quote_plus(text).replace('%20', '+')
		res = misc.file_get_contents('https://html.duckduckgo.com/html/', postdata={'q': encoded, 'b': ''}, proxies=self.proxies)
		if res is None: return None
		contents = '\n'.join([ a for a in rsparse.find_all_tags(res, 'a') ])
		soup = soupify(contents)
		for a in soup.find_all('a', attrs={'class': 'result__snippet'}):
			reply = self.check_reply( a.get_text() )
			if reply is not None: answers.append(reply)
		return answers if len(answers) else None

	def _ask_ask(self, text, answers=[]):
		encoded = urllib.quote_plus(text)
		res = misc.file_get_contents('https://www.ask.com/web?q=%s&ad=dirN&o=0' % encoded, proxies=self.proxies)
		if res is None: return None
		contents = '\n'.join( [ p for p in rsparse.find_all_tags(res, 'p') if p.find('PartialSearchResults-item-abstract') != -1 ])
		soup = soupify(contents)
		for p in soup.find_all('p', attrs={'class':'PartialSearchResults-item-abstract'}):
			reply = self.check_reply( p.get_text() )
			if reply is not None and not reply.endswith('...'): answers.append(reply)
		return answers if len(answers) else None

	def ask(self, text):
		answers = []
		random.shuffle(self.sites)

		## FIXME: try to understand why sometimes reddit fails with
		## 'NoneType' object is not iterable

		for site in self.sites:

			if site == 'reddit':
				try: answers = self._ask_reddit(text, answers)
				except: answers = []

			elif site == 'answers':
				try: answers = self._ask_answers(text, answers)
				except: answers = []

			elif site == 'ddg':
				try: answers = self._ask_ddg(text, answers)
				except: answers = []

			elif site == 'ask':
				try: answers = self._ask_ask(text, answers)
				except: answers = []

			if answers is None: answers = []
			elif len(answers) and self.return_asap: break

		if answers is None or not len(answers):
			answers = [ ' '.join( self.markov.generate_text() ) ]

		return random.choice(answers)

	def check_reply(self, reply):
		if isinstance(reply, unicode): reply = reply.encode('utf-8')
		reply = reply.replace('\n', ' ')
		return None if reply.startswith('Answers') or reply.endswith('...') else reply

if __name__ == "__main__":

	heck = Hecketer(learn=False, return_asap=False)

	while 1:
		try:
			user_input = raw_input('Input: ')
			reply = heck.ask(user_input)
			print('> %s' %reply)

		except KeyboardInterrupt:
			break
		except Exception as e:
			print('error: "%s"' %e)
