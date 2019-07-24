'''
mpn_add_inplace(tgt, src, n)
Like mpn_sub_inpace. Addition instead of subtraction
'''

import re, sys

g_tgt = sys.argv[2]

try:
    os.makedirs(os.path.dirname(g_tgt))
except:
    pass

g_src = sys.argv[1]

def do_it(o, i):
    for j in i:
        j = re.sub('subq', 'addq', j)
        j = re.sub('sbbq', 'adcq', j)
        j = re.sub('mpn_sub', 'mpn_add', j)
        o.write(j)

with open(g_src, 'rb') as g_i, open(g_tgt, 'wb') as g_o:
    do_it(g_o, g_i)
