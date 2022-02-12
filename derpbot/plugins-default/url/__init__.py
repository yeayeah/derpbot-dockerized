import rocksock
from http2 import RsHttp, _parse_url
from soup_parser import soupify
import re
import time
import random

def _get_url_title(uri, proxies=None):
	title = None
	desc = None
	host, port, ssl, uri = _parse_url(uri)
	http = RsHttp(host,ssl=ssl,port=port, keep_alive=True, follow_redirects=True, auto_set_cookies=True, proxies=proxies, user_agent='Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0')
	if not http.connect(): return None
	hdr, res = http.get(uri)
	res = res.encode('utf-8') if isinstance(res, unicode) else res
	soup = soupify(res)
	title = soup.body.find('title')
	if title is None: return None, None
	title = title.get_text()
	if title is None: return None, None

	title = title.encode('utf-8') if isinstance(title, unicode) else title
	title = title.replace('\n', ' ')

	d = soup.find('meta', property='og:description')
	desc = d['content'] if d else None
	if desc:
		if isinstance(desc, unicode): desc = desc.encode('utf-8')
		desc = desc.replace('\n', ' ')

	return title, desc


def action_url(arr):
	if arr['command'] == 'provides': return ['title', 'ud']

	uri_replace = {
		'(www.|)youtube.com': ['yewtu.be'],
		'(www.|)reddit.com': ['libredd.it'],
		'(www.|)twitter.com': ['nitter.net', 'nitter.fdn.fr', 'nitter.pussthecat.org'],
	}
	self = arr['self']
	proxies = None
	if arr['command'] == 'title':

		for uri in arr['args']:
			if uri.find('://') == -1: continue
			nuri = None
			replacement = None

			split = uri.split('/')
			domain = split[2]
			req = '/' if len(split) <= 3 else '/%s' % '/'.join(split[3:])

			for elem in uri_replace.keys():
				if re.match(elem, domain):
					replacement = random.choice( uri_replace[elem] )
					break

			if replacement:
				uri = uri.replace(domain, replacement)
				nuri = uri

			elif re.match('(www.|)youtu.be', uri):
				uri = 'https://yewtu.be/watch?v=%s' %req
				nuri = uri

			title, desc = _get_url_title(uri, proxies)

			if title is None: continue
			elif nuri is not None: self.irc.socket.send('PRIVMSG %s :%s\n' % (arr['chan'], nuri))

			if desc is None: self.irc.socket.send('PRIVMSG %s :^ %s\n' % (arr['chan'], title))
			else: self.irc.socket.send('PRIVMSG %s :^ %s // %s\n' % (arr['chan'], title, desc))
			time.sleep(0.5)

	elif arr['command'] == 'ud':
		for arg in arr['args']:
			uri = 'https://www.urbandictionary.com/define.php?term=%s' %arg
			title, desc = _get_url_title(uri, proxies)
			if title is None or desc is None: continue
			self.irc.socket.send('PRIVMSG %s :%s: %s\n' % (arr['chan'], title, desc))
			time.sleep(0.5)
