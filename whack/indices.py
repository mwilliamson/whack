import urlparse

import requests
from bs4 import BeautifulSoup
import dodge

from .common import SOURCE_URI_SUFFIX, PACKAGE_URI_SUFFIX
from . import slugs
from .platform import Platform


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
    
    def find_package_source_by_name(self, name):
        package_source_filename = name + SOURCE_URI_SUFFIX
        return self._find_by_name(package_source_filename)
        
    def find_package(self, params_hash, platform):
        def _is_package(entry_name):
            if entry_name.endswith(PACKAGE_URI_SUFFIX):
                package_name = entry_name[:-len(PACKAGE_URI_SUFFIX)]
                parts = slugs.split(package_name)
                if len(parts) < 4:
                    return False
                else:
                    entry_params_hash = parts[-1]
                    entry_platform = parts[-4:-1]
                    return (
                        entry_params_hash == params_hash and
                        platform.can_use(Platform.load_list(entry_platform))
                    )
            else:
                return False
        
        return self._find(_is_package)
    
    def _find_by_name(self, name):
        return self._find(lambda entry_name: entry_name == name)
        
    def _find(self, predicate):
        for entry in self._entries:
            if predicate(entry.name):
                return entry
                
        for entry in self._entries:
            url_parts = entry.url.rsplit("/", 1)
            if predicate(url_parts[-1]):
                return entry
                
        return None


class IndexEntry(object):
    def __init__(self, name, url):
        self.name = name
        self.url = url
