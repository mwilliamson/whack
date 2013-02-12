whack-run-with-whack-root: whack-run-with-whack-root.c
	gcc whack-run-with-whack-root.c -owhack-run-with-whack-root -Wall -Werror -std=gnu99

install: whack-run-with-whack-root
	mkdir -p /usr/local/whack
	cp whack-run-with-whack-root /usr/local/bin/whack-run-with-whack-root
	chmod +s /usr/local/bin/whack-run-with-whack-root
