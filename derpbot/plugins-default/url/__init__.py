import rocksock
from http2 import RsHttp, _parse_url
from soup_parser import soupify
import re

def action_url(arr):
	if arr['command'] == 'provides': return ['title']

	uri_replace = {
		'(www.|)youtube.com': ['yewtu.be'],
		'(www.|)reddit.com': ['libredd.it'],
		'(www.|)twitter.com': ['nitter.net', 'nitter.fdn.fr', 'nitter.pussthecat.org'],
	}
	self = arr['self']
	if arr['command'] == 'url':

		for uri in arr['args']:
			if uri.find('://') == -1: continue
			nuri = None
			replacement = None
			proto, _, domain, req = uri.split('/')

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
			proxies = None
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
					return nuri, title

		return None, None
