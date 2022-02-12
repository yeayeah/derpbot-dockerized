import rocksock
from http2 import RsHttp, _parse_url
from soup_parser import soupify
import re
import time

def action_url(arr):
	if arr['command'] == 'provides': return ['title']

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

			for elem in uri_replace:
				if re.match(elem, uri):
					replacement = random.choice( uri_replace[elem] )
					break

			if replacement:
				uri = uri.replace(domain, replacement)
				nuri = uri

			elif re.match('(www.|)youtu.be', uri):
				uri = 'https://yewtu.be/watch?v=%s' %req
				nuri = uri

			host, port, ssl, uri = _parse_url(uri)
			http = RsHttp(host,ssl=ssl,port=port, keep_alive=True, follow_redirects=True, auto_set_cookies=True, proxies=proxies, user_agent='Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0')
			if not http.connect(): continue
			hdr, res = http.get(uri)
			res = res.encode('utf-8') if isinstance(res, unicode) else res
			soup = soupify(res)
			title = soup.body.find('title')
			if title is not None:
				title = title.get_text()
				if title is not None:
					title = title.encode('utf-8') if isinstance(title, unicode) else title
					title = title.replace('\n', ' ')
					if nuri is not None: self.irc.socket.send('PRIVMSG %s :%s\n' % (arr['chan'], nuri))
					self.irc.socket.send('PRIVMSG %s :^ %s\n' % (arr['chan'], title))
					time.sleep(0.5)
