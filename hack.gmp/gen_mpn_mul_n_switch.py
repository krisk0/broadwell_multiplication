import re

def browse_h(n, p):
    p = re.compile(r'#define\s+%s\s+(\S+\b)' % p)
    with open(n, 'rb') as i:
        for j in i:
            m = p.search(j)
            if m:
                return int(m.group(1))

def do_it(o, limit):
    o.write('switch(n) {\n')
    for i in range(limit + 1):
        o.write('case %d: toom22_3arg_t<%d>(p, a, b); return;\n' % (i, i))
    o.write('}\n')

#This file runs from ./mpn. So gmp-mparam.h is at ..
g_toom33_threshold = browse_h('../gmp-mparam.h', 'MUL_TOOM33_THRESHOLD')

with open('automagic/mpn_mul_n_switch.h', 'wb') as g_o:
    do_it(g_o, g_toom33_threshold)
