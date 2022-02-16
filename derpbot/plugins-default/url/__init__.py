from soup_parser import soupify
import re
import time
import random
import misc

def _get_url_title(uri, proxies=None):
	title = None
	desc = None
	res = misc.file_get_contents(uri, proxies=proxies)
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
	if self.irc.nick != self.irc.mynick: return
	split = arr['recv'].split(' ')
	line =  ' '.join( split[3:] ).lstrip(':')
	chan = split[2]
	for uri in line.split(' '):
		if uri.find('://') == -1: continue
		nuri = _inspect_uri(uri)
		check = nuri if nuri is not None else uri
		title, desc = _get_url_title(check, proxies=self.args.http_proxy)

		if title is None: continue
		elif nuri is not None: self.irc.privmsg(chan, nuri)

		if desc is None: self.irc.privmsg(chan, '^ %s' % title)
		else: self.irc.privmsg(chan, '^ %s //%s' % (title, desc))
		time.sleep(0.5)

def action_url(arr):
	if arr['command'] == 'provides': return ['title', 'ud']

	self = arr['self']
	if arr['command'] == 'title':

		for uri in arr['args']:
			if uri.find('://') == -1: continue
			nuri = _inspect_uri(uri)
			check = nuri if nuri is not None else uri
			title, desc = _get_url_title(check, proxies=self.args.http_proxy)

			if title is None: continue
			elif nuri is not None: self.irc.privmsg(arr['chan'], nuri)

			if desc is None: self.irc.privmsg(arr['chan'], '^ %s' % title)
			else: self.irc.privmsg(arr['chan'], '^ %s //%s' % (title, desc))
			time.sleep(0.5)

	elif arr['command'] == 'ud':
		arg = '+'.join(arr['args'])
		uri = 'https://www.urbandictionary.com/define.php?term=%s' %arg
		_, desc = _get_url_title(uri, proxies=self.args.http_proxy)
		if desc: self.irc.privmsg(arr['chan'], '%s' % desc)
