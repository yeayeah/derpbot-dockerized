import rocksock
from http2 import RsHttp, _parse_url
from soup_parser import soupify

def action_url(args):
	if args['command'] == 'provides': return ['title']
