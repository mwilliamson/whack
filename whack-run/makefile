whack-run: whack-run.c
	gcc whack-run.c -owhack-run -Wall -Werror -std=gnu99

install: whack-run
	mkdir -p /usr/local/whack
	cp whack-run /usr/local/bin/whack-run
	chmod +s /usr/local/bin/whack-run
