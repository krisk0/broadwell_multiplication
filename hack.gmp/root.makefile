BUILT_SOURCES += mpn/magic.initiated

mpn/magic.initiated: Makefile
	>$@
	$(PYTHON2) mpn/initiate_unroll.py $(MPN_PATH)
