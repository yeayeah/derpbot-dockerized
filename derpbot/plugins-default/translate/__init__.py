from soup_parser import soupify
import misc

def action_translate(arr):
	if arr['command'] == 'provides': return ['translate']
	self = arr['self']

	lang = arr['args'][0]
	text = ' '.join( arr['args'][1:])
	from_language, to_language = lang.split(':')

	res = misc.file_get_contents('https://simplytranslate.org/?engine=libre', {'from_language':from_language, 'to_language':to_language, 'input': text}, proxies=self.args.http_proxy)

	soup = soupify(res)
	for ta in soup.find_all('textarea', attrs={'class': 'translation'}):
		translation = ''.join( ta.contents )
		if translation is not None:
			if isinstance(translation, unicode): translation = translation.encode('utf-8')
			return {'reply': translation }
