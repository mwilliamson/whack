import urlparse

import requests
from bs4 import BeautifulSoup


def read_index(index_uri):
    index_response = requests.get(index_uri)
    if index_response.status_code != 200:
        # TODO: should we log and carry on? Definitely shouldn't swallow
        # silently
        raise Exception("Index {0} returned status code {1}".format(
            index_uri, index_response.status_code
        ))
    return read_index_string(index_uri, index_response.text)
    
    
def read_index_string(index_url, index_string):
    html_document = BeautifulSoup(index_string)
    
    def link_to_index_entry(link):
        url = urlparse.urljoin(index_url, link.get("href"))
        link_text = link.get_text().strip()
        return IndexEntry(link_text, url)
    
    return Index(map(link_to_index_entry, html_document.find_all("a")))
    

class Index(object):
    def __init__(self, entries):
        self._entries = entries
        
    def find_by_name(self, name):
        for entry in self._entries:
            if entry.name == name:
                return entry
        for entry in self._entries:
            url_parts = entry.url.rsplit("/", 1)
            if url_parts[-1] == name:
                return entry
        return None


class IndexEntry(object):
    def __init__(self, name, url):
        self.name = name
        self.url = url
