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

