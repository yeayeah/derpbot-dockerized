import urllib
from http2 import RsHttp, _parse_url
from soup_parser import soupify
import random
import rsparse
import json
import re

def nickmask(data):
	_, line = data.split(':')
	return line.split('!')

def file_get_contents(uri, postdata=None, proxies=None):
	host, port, ssl, uri = _parse_url(uri)
	http = RsHttp(host,ssl=ssl,port=port, keep_alive=True, follow_redirects=True, auto_set_cookies=True, proxies=proxies, user_agent='Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0')
	try: http.connect()
	except Exception as e: return None

	if postdata is None: hdr, res = http.get(uri)
	else: hdr, res = http.post(uri, postdata)

	if isinstance(res, unicode): res = res.encode('utf-8')
	return res

def isop(self, chan, nick):
	return True if 'op' in self.nicklist[chan][nick] else False

def is_ignored_string(self, chan, string):
	try: ignores = self.settings[chan]['ignore']['string']
	except: return False
	for match in ignores:
		if re.search(match, string): return True
	return False

def is_ignored_nick(self, nick, chan=None):
	if not chan:
		for match in self.ignorelist:
			if re.search(match, nick.lower()): return True

	elif chan in self.settings and 'ignore' in self.settings[chan] and 'nick' in self.settings[chan]['ignore']:
		for n in self.settings[chan]['ignore']['nicks']:
			if re.search(n, nick.lower()): return True
	return False

def is_ignored_mask(self, nick, chan=None):
	pass
