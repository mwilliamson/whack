import os
import hashlib

class Hasher(object):
    def __init__(self):
        self._hash = hashlib.sha1()
    
    def update(self, arg):
        self._hash.update(_sha1(arg))
    
    def update_with_dir(self, dir_path):
        for file_path in _all_files(dir_path):
            self.update(os.path.relpath(file_path, dir_path))
            self.update(open(file_path).read())
    
    def hexdigest(self):
        return self._hash.hexdigest()

def _all_files(top):
    all_files = []
    
    for root, dirs, files in os.walk(top):
        for name in files:
            all_files.append(os.path.join(root, name))
    
    return sorted(all_files)

def _sha1(str):
    return hashlib.sha1(str).hexdigest()
