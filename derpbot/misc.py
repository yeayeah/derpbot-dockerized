import urllib
from http2 import RsHttp, _parse_url
from soup_parser import soupify
import random
import rsparse
import json

def nickmask(data):
	_, line = data.split(':')
	return line.split('!')

def file_get_contents(uri, postdata=None, proxies=None):
	host, port, ssl, uri = _parse_url(uri)
	http = RsHttp(host,ssl=ssl,port=port, keep_alive=True, follow_redirects=True, auto_set_cookies=True, proxies=proxies, user_agent='Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0')
	if not http.connect(): return None

	try:
		if postdata is None: hdr, res = http.get(uri)
		else: hdr, res = http.post(uri, postdata)

		if isinstance(res, unicode): res = res.encode('utf-8')
		return res
	except Exception as e:
		if hasattr(e, 'message'): print('file_get_contents(error): %s' %e.message)
		else: print('file_get_contents(error): %s' %message)

def isop(self, chan, nick):
	return True if 'op' in self.nicklist[chan][nick] else False

def is_ignored_str(self, chan, string):
	try: ignores = self.settings[chan]['ignore']
	except: return False
	for ignore in ignores:
		if hasattr(ignore, 'string') and re.match(ignore['string'], string): return True
	return False
