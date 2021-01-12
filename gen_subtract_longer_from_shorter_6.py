'''
subtract from 6-limb number a 5-limb number b.

a is at a_p. b is at a_p + 48
'''

g_code = '''
movq 0(ap), w0
movq 1(ap), w1
movq 2(ap), w2
movq 3(ap), w3
subq 0(bp), w0
sbbq 1(bp), w1
sbbq 2(bp), w2
sbbq 3(bp), w3
movq w0, 0(rp)
movq w1, 1(rp)
movq w2, 2(rp)
movq w3, 3(rp)
movq 4(ap), w0
movq 5(ap), w1
sbbq 4(bp), w0
sbbq $0, w1
movq w0, 4(rp)
movq w1, 5(rp)
'''

import sys
sys.dont_write_bytecode = 1

import gen_subtract_longer_from_shorter_7 as F

if __name__ == '__main__':
    with open(sys.argv[1], 'wb') as g_o:
        F.do_it(g_o, g_code, 6)
