.PHONY: magic

mul_n.o: mul_n.cpp magic

mul_n.lo: mul_n.cpp magic

automagic/mpn_mul_n_switch.h: gen_mpn_mul_n_switch.py
	$(PYTHON2) $<

magic: automagic/mpn_mul_n_switch.h
