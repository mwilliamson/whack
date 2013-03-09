# whack: build and install binaries with a single command

Whack allows binaries such as nginx and node.js to be installed with a single
command. For instance, to install nginx to `~/apps/nginx`:

    whack install git+https://github.com/mwilliamson/whack-package-nginx.git ~/apps/nginx

On the first installation, the application is compiled and copied to the target
directory. On subsequent installations, a cached version of the application is
copied to the target directory.

## Installation

Before you can use Whack, you need to install a utility called `whack-run`. You
can download [whack-run][] from GitHub:

```
$ curl -L https://github.com/mwilliamson/whack-run/archive/1.0.0.tar.gz > whack-run-1.0.0.tar.gz
$ tar xzf whack-run-1.0.0.tar.gz
$ cd whack-run-1.0.0
$ make
```

And as root:

```
# make install
```

This installs the binary `whack-run` to `/usr/local/bin`. Once `whack-run` has
been installed, you can install Whack as an ordinary Python package:

```
pip install whack
```

[whack-run]: https://github.com/mwilliamson/whack-run

## How does Whack work?

Many Linux applications can be compiled and installed by running the following
commands, or similar:

```
$ ./configure
$ make
$ make install
```

This usually installs the application under `/usr/local`. However, sometimes we
want to install isolated instances of an application without being root. For
instance, if we're developing a web application that uses Apache, it's helpful
to have an isolated installation of Apache. We can change the installation
prefix when running `./configure`:

```
$ ./configure --prefix=/home/user/projects/web-app/apache
$ make
$ make install
```

While this works, it requires us to re-compile the application whenever we
want to install it in a different location. Depending on the application,
compilation can take a quite a while.

Whack solves this problem by using `unshare` and `mount` to change the
filesystem for a single process. Each application is compiled with its
prefix set to `/usr/local/whack`. Before running the binary for an application,
Whack uses the `unshare` syscall to create a private mount namespace. This
means that any `mount` calls only have visible effects within that process. We
then mount the directory that the application was installed in onto
`/usr/local/whack`, and `exec` the binary.

For instance, say we've installed nginx to `~/web-app/nginx` by running

    whack install git+https://github.com/mwilliamson/whack-package-nginx.git \
        -p nginx_version=1.2.6 ~/web-app/nginx

The actual nginx binary can be found in `~/web-app/nginx/.sbin` (note that the
binary is in a directory called `.sbin`, not `sbin`). If we try to
run `~/web-app/nginx/.sbin/nginx` directly, we'll get an error:

```
$ ~/web-app/nginx/.sbin/nginx
nginx: [alert] could not open error log file: open() "/usr/local/whack/logs/error.log" failed (2: No such file or directory)
2013/02/18 11:25:17 [emerg] 11586#0: open() "/usr/local/whack/conf/nginx.conf" failed (2: No such file or directory)
```

nginx expects to be installed under `/usr/local/whack`, but it's actually
installed under `~/web-app/nginx`. To run nginx successfully, we need to use
`whack-run`:

```
$ whack-run ~/web-app/nginx ~/web-app/nginx/.sbin/nginx
```

When using `whack-run`, the following happens:

1. `whack-run` calls `unshare(CLONE_NEWNS)`, creating a private mount namespace.
  
2. `whack-run` mounts `~/web-app/nginx` onto `/usr/local/whack`. Since we called
  `unshare` earlier, this mount is only visible to this process.
  
3. `whack-run` drops its user and group privileges. `whack-run` is installed
  with the `setuid` bit set so it can call `unshare` and `mount`.

4. `whack-run` calls `exec` with the arguments it was passed i.e.
  `exec ~/web-app/nginx/.sbin/nginx`

Using `whack-run` to run nginx is a bit tedious. However, we can call
`~/web-app/nginx/sbin/nginx` directly (instead of `~/web-app/nginx/.sbin/nginx`),
which will call `whack-run` with appropriate arguments.

Although `whack-run` has the `setuid` bit set, it only uses root privileges
to call `unshare` and `mount`. After that, user and group privileges are dropped.
