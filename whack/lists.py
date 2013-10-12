import six

__all__ = ["map"]


_map = map

if six.PY3:
    def map(*args, **kwargs):
        return list(_map(*args, **kwargs))
else:
    map = _map
