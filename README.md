# whack: build and install binaries with a single command

Whack allows binaries such as nginx and node.js to be installed with a single
command. For instance, to install nginx 1.2.6 to `~/apps/nginx`:

    whack install git+https://github.com/mwilliamson/whack-package-nginx.git \
        -p nginx_version=1.2.6 ~/apps/nginx

On the first installation, the application is compiled and copied to the target
directory. On subsequent installations, a cached version of the application is
copied to the target directory.

## Installation

Before you can use Whack, you need to install a utility called `whack-run`. You
can download Whack from [GitHub][github] or [PyPI][pypi]. Then, from within
Whack's source directory:

```
cd whack-run
make
```

And as root:

```
make install
```

This installs the binary `whack-run` to `/usr/local/bin`. Once `whack-run` has
been installed, you can install Whack as an ordinary Python package:

```
pip install whack
```

[github]: https://github.com/mwilliamson/whack
[pypi]: https://pypi.python.org/pypi/whack
