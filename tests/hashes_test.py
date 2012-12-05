import os
import tempfile
import shutil
import uuid

from nose.tools import istest, assert_equal, assert_not_equal

from whack.hashes import Hasher

@istest
def hashing_the_same_single_value_gives_the_same_hash():
    def create_hash():
        hasher = Hasher()
        hasher.update("one")
        return hasher.hexdigest()
    
    assert_equal(create_hash(), create_hash())

@istest
def hashing_multiple_values_in_the_same_order_gives_the_same_hash():
    def create_hash():
        hasher = Hasher()
        hasher.update("one")
        hasher.update("two")
        return hasher.hexdigest()
    
    assert_equal(create_hash(), create_hash())
    
@istest
def hashing_multiple_values_in_different_order_gives_different_hash():
    first_hasher = Hasher()
    first_hasher.update("one")
    first_hasher.update("two")
    
    second_hasher = Hasher()
    second_hasher.update("two")
    second_hasher.update("one")
    
    assert_not_equal(first_hasher.hexdigest(), second_hasher.hexdigest())

@istest
def hash_of_directories_are_the_same_if_they_have_the_same_files():
    with TestRunner() as test_runner:
        first_hash = test_runner.hash_for_files({"hello": "Hello world!"})
        second_hash = test_runner.hash_for_files({"hello": "Hello world!"})
        
        assert_equal(first_hash, second_hash)
        
@istest
def hash_of_directories_are_different_if_they_have_different_file_names():
    with TestRunner() as test_runner:
        first_hash = test_runner.hash_for_files({"one": "Hello world!"})
        second_hash = test_runner.hash_for_files({"two": "Hello world!"})
        
        assert_not_equal(first_hash, second_hash)
        
@istest
def hash_of_directories_are_different_if_they_have_different_file_contents():
    with TestRunner() as test_runner:
        first_hash = test_runner.hash_for_files({"hello": "Hello world!"})
        second_hash = test_runner.hash_for_files({"hello": "Goodbye world!"})
        
        assert_not_equal(first_hash, second_hash)

class TestRunner(object):
    def __init__(self):
        self._test_dir = tempfile.mkdtemp()
    
    def hash_for_files(self, files):
        files_dir = self.create_files(files)
        
        hasher = Hasher()
        hasher.update_with_dir(files_dir)
        return hasher.hexdigest()
    
    def create_files(self, files):
        root = os.path.join(self._test_dir, str(uuid.uuid4()))
        os.mkdir(root)
        for name, contents in files.iteritems():
            path = os.path.join(root, name)
            open(path, "w").write(contents)
        return root
    
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        shutil.rmtree(self._test_dir)
