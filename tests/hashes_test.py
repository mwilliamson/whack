from nose.tools import istest, assert_equal

from whack.hashes import Hasher

@istest
def hashing_the_same_single_value_gives_the_same_hash():
    def create_hash():
        hasher = Hasher()
        hasher.update("one")
        return hasher.hexdigest()
    
    assert_equal(create_hash(), create_hash())
