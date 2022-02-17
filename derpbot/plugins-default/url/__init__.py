from soup_parser import soupify
import re
import time
import random
import misc

def _get_url_title(uri, proxies=None):
	filetype = misc.file_get_contents_type(uri, proxies=proxies)
	if not filetype: return None, None
	elif filetype.lower().find('html') == -1: return None, None
	title = None
	desc = None
	res = misc.file_get_contents(uri, proxies=proxies)
	if res is None: return None, None
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

def _update_self(self, chan):
	if not hasattr(self, 'settings'): self.settings = dict()
	if not chan in self.settings: self.settings[chan] = dict()
	if not 'p_url' in self.settings[chan]: self.settings[chan]['p_url'] = []
	return self

def event_url(arr):
	if arr['event'] != 'PRIVMSG': return None
	self = arr['self']
	if self.irc.nick != self.irc.mynick: return None
	split = arr['recv'].split(' ')
	chan = split[2]
	self = _update_self(self, chan)
	line =  ' '.join( split[3:] ).lstrip(':')
	for uri in line.split(' '):
		if uri.find('://') == -1: continue
		domain = uri.split('/')[2]
		if domain.find('/') != -1: domain, _ = domain.split('/')
		skip = False
		for rgx in self.settings[chan]['p_url']:
			if not re.search(rgx, uri): continue
			skip = True
			break
		if skip: continue
		nuri = _inspect_uri(uri)
		check = nuri if nuri is not None else uri
		title, desc = _get_url_title(check, proxies=self.args.http_proxy)

		if title is None: continue
		elif nuri is not None: self.irc.privmsg(chan, nuri)

		if desc is None: self.irc.privmsg(chan, '^ %s' % title)
		else: self.irc.privmsg(chan, '^ %s //%s' % (title, desc))
		time.sleep(0.5)

def action_url(arr):
	provides = ['title', 'ud', 'ignore', 'unignore']
	if arr['command'] == 'provides': return provides
	elif not arr['command'] in provides: return

	chan = arr['chan']
	nick = arr['nick']
	self = _update_self(arr['self'], chan)
	if arr['command'] == 'title':

		for uri in arr['args']:
			if uri.find('://') == -1: continue
			_,_, domain = uri.split('/')
			if domain.find('/') != -1: domain, _ = domain.split('/')
			skip = False
			for rgx in self.settings[chan]['p_url']:
				if not re.search(rgx, uri): continue
				skip = True
				break
			if skip: continue
			nuri = _inspect_uri(uri)
			check = nuri if nuri is not None else uri
			title, desc = _get_url_title(check, proxies=self.args.http_proxy)

			if title is None: continue
			elif nuri is not None: self.irc.privmsg(chan, nuri)

			if desc is None: self.irc.privmsg(chan, '^ %s' % title)
			else: self.irc.privmsg(chan, '^ %s //%s' % (title, desc))
			time.sleep(0.5)
		return None

	elif arr['command'] == 'ud':
		arg = '+'.join(arr['args'])
		uri = 'https://www.urbandictionary.com/define.php?term=%s' %arg
		_, desc = _get_url_title(uri, proxies=self.args.http_proxy)
		if desc: self.irc.privmsg(chan, '%s' % desc)
		return None

	elif arr['command'] == 'ignore':
		added = []
		foo = [ i for i  in arr['args'][1:] if not i in self.settings[chan]['p_url'] ]
		if len(foo):
			self.settings[chan]['p_url'].extend(foo)
			self.irc.privmsg(chan, 'ignore(add): `%s`' % '`, `'.join( foo ))
			
	elif arr['command'] == 'unignore':
		self.settings[chan]['p_url'] = [ i for i in self.settings[chan]['p_url'] if not i in arr['args'] ]

	return {'self': self}
