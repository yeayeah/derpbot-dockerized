import rocksock
from http2 import RsHttp, _parse_url
from soup_parser import soupify

def action_translate(arr):
	if arr['command'] == 'provides': return ['translate']
	self = arr['self']

	lang = arr['args'][0]
	text = ' '.join( arr['args'][1:])
	from_language, to_language = lang.split(':')

	proxies = None
	host, port, ssl, uri = _parse_url('https://simplytranslate.org/?engine=libre')
	http = RsHttp(host,ssl=ssl,port=port, keep_alive=True, follow_redirects=True, auto_set_cookies=True, proxies=proxies, user_agent='Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0')
	if not http.connect(): return {'reply': 'error, failed to fetch from url', 'self': self }
	hdr, res = http.post(uri, values={'from_language': from_language, 'to_language': to_language, 'input': text})

	soup = soupify(res)
	for ta in soup.find('textarea', attrs={'class': 'translation'}):
		translation = ta.get_text()
		if translation is not None: return {'reply': translation }
