mul_n.o: mul_n.cpp automagic/mpn_mul_n_switch.h

mul_n.lo: mul_n.cpp automagic/mpn_mul_n_switch.h

automagic/mpn_mul_n_switch.h: gen_mpn_mul_n_switch.py
	$(PYTHON2) $<
