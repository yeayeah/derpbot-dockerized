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
		if re.match(elem, domain):
			replacement = random.choice( uri_replace[elem] )
			break

	if replacement:
		uri = uri.replace(domain, replacement)
		nuri = uri

	elif re.match('(www.|)youtu.be', uri):
		uri = 'https://yewtu.be/watch?v=%s' %req
		nuri = uri

	return nuri

def event_url(arr):
	self = arr['self']
	split = arr['recv'].split(' ')
	line =  ' '.join( split[3:] ).lstrip(':')
	chan = split[2]
	proxies = None
	for uri in line.split(' '):
		if uri.find('://') == -1: continue
		nuri = _inspect_uri(uri)
		check = nuri if nuri is not None else uri
		title, desc = _get_url_title(check, proxies)

		if title is None: continue
		elif nuri is not None: self.irc.privmsg(chan, nuri)

		if desc is None: self.irc.privmsg(chan, '^ %s' % title)
		else: self.irc.privmsg(chan, '^ %s //%s' % (title, desc))
		time.sleep(0.5)

def action_url(arr):
	if arr['command'] == 'provides': return ['title', 'ud']

	self = arr['self']
	proxies = None
	if arr['command'] == 'title':

		for uri in arr['args']:
			if uri.find('://') == -1: continue
			nuri = _inspect_uri(uri)
			check = nuri if nuri is not None else uri
			title, desc = _get_url_title(check, proxies)

			if title is None: continue
			elif nuri is not None: self.irc.privmsg(arr['chan'], nuri)

			if desc is None: self.irc.privmsg(arr['chan'], '^ %s' % title)
			else: self.irc.privmsg(arr['chan'], '^ %s //%s' % (title, desc))
			time.sleep(0.5)

	elif arr['command'] == 'ud':
		for arg in arr['args']:
			uri = 'https://www.urbandictionary.com/define.php?term=%s' %arg
			title, desc = _get_url_title(uri, proxies)
			if title is None or desc is None: continue
			self.irc.privmsg(arr['chan'], '%s: %s' % (title, desc))
			time.sleep(0.5)
