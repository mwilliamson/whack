# whack: compile and run relocatable Linux programs

Whack allows Linux programs such as nginx and the Apache HTTP Server to be installed with a single command.
For instance, to install nginx to `~/apps/nginx`:

    whack install git+https://github.com/mwilliamson/whack-package-nginx.git ~/apps/nginx

Most Linux binaries aren't relocatable,
meaning that they're compiled for a specific path on your filesystem.
This means that if you want to install exactly the same program to a different path,
you'll need to recompile the entire program.
Whack allows you to create relocatable versions of these programs.
On the first installation, the program is compiled and copied to the target directory.
On subsequent installations,
a cached version of the application is copied to the target directory.

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

## Usage

```
whack install PACKAGE_SOURCE DESTINATION
```

For instance, to install nginx under `~/apps/nginx`:

```
whack install git+https://github.com/mwilliamson/whack-package-nginx.git ~/apps/nginx
```

nginx can then be run with the command:

```
~/apps/sbin/nginx
```

Package sources can be git or hg repositories (prefix the repository URL with `git+` and `hg+` respectively),
tarballs fetched over HTTP (detected by the `http://` prefix),
or local paths (detected by one of the prefixes `/`, `./`, or `../`).

You can pass build parameters using the argument `--add-parameter KEY=VALUE`, or with its short alias `-p KEY=VALUE`.
The build parameters that can be set depend on the package.
For instance, to install a specific version of nginx:

```
whack install git+https://github.com/mwilliamson/whack-package-nginx.git ~/apps/nginx \
    -p nginx_version=1.2.7
```

If a build parameter isn't set, a package will usually have a sensible default.

## Creating package sources

A package source describes how to go from nothing to an installed instance of a given program.
The output directory containing the installed program is referred to as a package.

The below gives a fairly thorough description of how a package is built,
but it will probably more sense once you take a look at a concrete example.
The [nginx source package](https://github.com/mwilliamson/whack-package-nginx) is a good example since it's relatively straightforward.

There are normally at least three files in each package source:

* `whack/whack.json`: a JSON file describing the package source
* `whack/downloads`: an executable file that outputs required downloads to stdout
* `whack/build`: an executable file that is executed to build the package

### whack/whack.json

`whack/whack.json` should be a JSON object containing the following properties:

* `name`: the name of the package, such as `nginx`.
  It should only contain lowercase letters, numbers, and hypens.
* `sourcePaths` (optional):
  the paths in the source package that are required to build the package.
  Defaults to `["whack"]`.
* `defaultParameters` (optional):
  an object containing the default build parameters for the package.

### Build parameters

When executing `whack/downloads` and `whack/build`,
any build parameters are passed as environment variables.
Build parameters are set according to the defaults in `whack/whack.json`.
The build parameters explicitly passed by the user are then added,
overriding any default parameters.
The name of each build parameter is converted to uppercase in the environment.
For instance, the build parameter "version" is available as the environment variable "VERSION".

### whack/downloads

Before building the package,
`whack/downloads` is executed with the output to stdout being captured.
The output should be a list of URLs that are required to build the package,
separated by new lines.
Downloads are cached,
so if you have an URL where the contents might change
(for instance, the latest tarball for a program),
you can either:

* Try to find a URL for that specific version
* Download the file manually in the build step

### Building the package

The following steps are executed to build a package:

* Read `whack/whack.json` to get a package description.
* Set the values of the build parameters based on the defaults set in `whack/whack.json` and the user-provided parameters.
* Create a temporary directory, called the build directory.
* Copy the directories and files in the source package specified by `sourcePaths` into the build directory.
* Execute `whack/downloads` with the build parameters set as environment variables,
  and download the files into the build directory.
* Execute `whack/build`:
  * The build parameters are set as environment variables
  * The current working directory is set to the build directory
  * The target directory for the package is passed as a command line argument
  
When the package is built,
any executable files should be placed in either `.bin` or `.sbin` directories,
instead of `bin` and `sbin`.
When the package is installed by Whack,
`bin` and `sbin` will contain thin wrappers that set up the filesystem correctly,
and then delegate to the equivalent executables in `.bin` and `.sbin`.
See the section "How does Whack work?" for more details.

Examples of package sources:

* [nginx](https://github.com/mwilliamson/whack-package-nginx)
* [Apache HTTP server](https://github.com/mwilliamson/whack-package-apache2)
* [Apache HTTP server with PHP5](https://github.com/mwilliamson/whack-package-apache2-mod-php5)

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
        ~/web-app/nginx

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
