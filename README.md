# whack: build and install binaries with a single command

Whack allows binaries such as nginx and node.js to be installed with a single
command. For instance, to install nginx 1.2.4 to `~/apps/nginx`:

    whack install nginx=1.2.4 ~/apps/nginx
    
Where possible, the build of each application will be relocatable. On the first
installation, the application is compiled and copied to the target directory. On
subsequent installations, a cached version of the application is copied to the
target directory.


