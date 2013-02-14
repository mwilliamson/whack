WHACK_RUN_SOURCE_HASH=$(shell sha1sum whack-run.c | sed -n 's/\(\S*\).*/\1/p')

whack-run: whack-run.c
	gcc whack-run.c -owhack-run -Wall -Werror -std=gnu99 -DWHACK_RUN_SOURCE_HASH=\"$(WHACK_RUN_SOURCE_HASH)\"

install: whack-run
	mkdir -p /usr/local/whack
	cp whack-run /usr/local/bin/whack-run
	chmod +s /usr/local/bin/whack-run
