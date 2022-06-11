import urllib
import random
import rsparse
import json
import re
from http2 import RsHttp, _parse_url
from soup_parser import soupify

def _inspect_uri(uri):
	nuri = None
	replacement = None
	uri_replace = {
		'(www.|)youtube.com': ['yewtu.be'],
		'(www.|)reddit.com': ['libredd.it'],
		'(www.|)twitter.com': ['nitter.net', 'nitter.fdn.fr', 'nitter.pussthecat.org'],
	}

	split = uri.split('/')
	domain = split[2]
	req = '/' if len(split) <= 3 else '/%s' % '/'.join(split[3:])

	for elem in uri_replace.keys():
		if re.search(elem, domain):
			replacement = random.choice( uri_replace[elem] )
			break

	if replacement:
		uri = uri.replace(domain, replacement)
		nuri = uri

	elif re.search('(www.|)youtu.be', uri):
		uri = 'https://yewtu.be/watch?v=%s' %req.lstrip('/')
		nuri = uri

	return nuri
def nickmask(data):
	return data[1:].split('!')

def file_get_contents(uri, postdata=None, proxies=None):
	host, port, ssl, uri = _parse_url(uri)
	http = RsHttp(host,ssl=ssl,port=port, keep_alive=True, follow_redirects=True, auto_set_cookies=True, proxies=proxies, user_agent='Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0')
	try: http.connect()
	except Exception as e: return None

	if postdata is None: hdr, res = http.get(uri)
	else: hdr, res = http.post(uri, postdata)

	if isinstance(res, unicode): res = res.encode('utf-8')
	return res

def file_get_contents_type(uri, proxies=None):
	host, port, ssl, uri = _parse_url(uri)
	http = RsHttp(host,ssl=ssl,port=port, keep_alive=True, follow_redirects=True, auto_set_cookies=True, proxies=proxies, user_agent='Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0')
	try: http.connect()
	except Exception as e:
		if hasattr(e, 'message'): print('fgct: %s' %e.message)
		else: print('fgct: %s' %e)
		return None
	res = http.head(uri)
	if res is None: return None
	if isinstance(res, unicode): res = res.encode('utf-8')
	for line in res.split('\n'):
		try: item, value = line.split(':')
		except: continue
		if item.strip().lower() == 'content-type': return value.strip()
	return None

def isop(self, chan, nick):
	return True if 'op' in self.nicklist[chan][nick] else False

def is_ignored_string(self, chan, string):
	try: ignores = self.settings[chan]['ignore']['string']
	except: return False
	for match in ignores:
		if re.search(match, string): return True
	return False

def is_ignored_nick(self, nick, chan=None):
	if chan in self.settings and 'ignore' in self.settings[chan] and 'nick' in self.settings[chan]['ignore']:
		for n in self.settings[chan]['ignore']['nicks']:
			if re.search(n, nick.lower()): return True
	return False

def is_ignored_mask(self, nick, chan=None):
	pass
