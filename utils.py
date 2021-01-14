import json
import urllib

def get_room_server(main_server, room):
    '''main_server should include scheme e.g. "http://cytu.be"
    
    is blocking
    '''
    url = urllib.parse.urlparse(main_server)
    url = urllib.parse.ParseResult(url.scheme, url.netloc, f'/socketconfig/{room}.json', url.params, url.query, url.fragment)
    url = urllib.parse.urlunparse(url)
    with urllib.request.urlopen(url) as response:
        r = json.loads(response.read())
    return r['servers'][0]['url']