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

	if postdata is None: hdr, res = http.get(uri)
	else: hdr, res = http.post(uri, postdata)

	if isinstance(res, unicode): res = res.encode('utf-8')
	return res
