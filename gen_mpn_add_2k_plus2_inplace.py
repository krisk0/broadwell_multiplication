'''
mp_limb_t mpn_add_2k_plus2_inplace(mp_ptr cp, mp_srcptr ap, uint16_t loops);

n := 4 * loops + 2, loops > 0

r := a + c where a is n-limb number at ap and c is n-limb number at cp

place n-limb result r onto cp

return carry from last addition
'''

import re, sys

def do_it(o, i):
    for j in i:
        j = re.sub('subq', 'addq', j)
        j = re.sub('sbbq', 'adcq', j)
        j = re.sub('sub_2k', 'add_2k', j)
        o.write(j)

with open(sys.argv[1], 'rb') as g_i, open(sys.argv[2], 'wb') as g_o:
    do_it(g_o, g_i)
