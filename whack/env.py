import six


def params_to_env(params):
    return dict(
        (name.upper(), str(value))
        for name, value in six.iteritems(params or {})
    )

