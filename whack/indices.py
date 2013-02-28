import re

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
    html_document = BeautifulSoup(index_response.text)
    return Index([
        IndexEntry(link.get_text().strip(), link.get("href"))
        for link in html_document.find_all("a")
    ])

class Index(object):
    def __init__(self, entries):
        self._entries = entries
        
    def find_by_name(self, name):
        for entry in self._entries:
            if entry.name == name:
                return entry
        return None
        
    def find_package_by_hash(self, package_hash):
        for entry in self._entries:
            if re.search("(^|-){0}.whack-package$".format(re.escape(package_hash)), entry.name):
                return entry
        return None


class IndexEntry(object):
    def __init__(self, name, url):
        self.name = name
        self.url = url
