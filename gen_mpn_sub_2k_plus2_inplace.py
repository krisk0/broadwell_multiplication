'''
mp_limb_t mpn_sub_2k_plus2_inplace(mp_ptr cp, mp_srcptr ap, uint16_t loops);

n := 4 * loops + 2, loops > 0

r := a - c where a is n-limb number at ap and c is n-limb number at cp

place n-limb result r onto cp

return carry from last subtraction (zero or one)
'''

g_var_map = 'cp,rdi ap,rsi lc,dx w0,r10 w1,r8 w2,r9 w3,rax'

g_code = '''
movq (ap), w0
movq 8(ap), w1      | (w1) (w0)
xor w2, w2
.align 32
loop:
sbbq (cp), w0
sbbq 8(cp), w1
movq 16(ap), w2
movq 24(ap), w3     | (w3) (w2) w1 w0
lea 32(ap), ap
sbbq 16(cp), w2
sbbq 24(cp), w3     | w3 w2 w1 w0
movq w0, (cp)
movq w1, 8(cp)      | w3 w2
movq (ap), w0
movq 8(ap), w1      | (w1) (w0) w3 w2
movq w2, 16(cp)
movq w3, 24(cp)     | (w1) (w0)
dec lc
lea 32(cp), cp
jne loop
movq $0, w3
sbbq (cp), w0
sbbq 8(cp), w1      | w1 w0
movq w0, (cp)
movq w1, 8(cp)
adc $0, %ax
'''

g_code_fast = '''
| Inspired by GMP's mpn_sub_n for Zen
| Benchmark result: no gain no loss on Broadwell, loss of 14 ticks on Ryzen
|  compared to home-brewed code above
movq (ap), w0
movq 8(ap), w1
xor w2, w2
dec lc
mov 16(ap), w2
mov 24(ap), w3      | (w3) (w2) (w1) (w0)
jz tail
.align 32
loop:               | (w3) (w2) (w1) (w0)
sbbq (cp), w0
sbbq 8(cp), w1
sbbq 16(cp), w2
sbbq 24(cp), w3
movq w0, (cp)
lea 32(ap), ap
movq w1, 8(cp)
movq w2, 16(cp)
dec lc
movq w3, 24(cp)
lea 32(cp), cp
movq (ap), w0
movq 8(ap), w1
mov 16(ap), w2
mov 24(ap), w3      | (w3) (w2) (w1) (w0)
jne loop
mov 16(ap), w2
mov 24(ap), w3      | (w3) (w2) (w1) (w0)
tail:
sbbq (cp), w0
sbbq 8(cp), w1
sbbq 16(cp), w2
sbbq 24(cp), w3     | w3 w2 w1 w0
movq w0, (cp)
movq w1, 8(cp)      | w3 w2
movq 32(ap), w0
movq 40(ap), w1     | (w1) (w0) w3 w2
movq w2, 16(cp)
movq w3, 24(cp)
movq $0, w3
sbbq 32(cp), w0
sbbq 40(cp), w1
movq w0, 32(cp)
movq w1, 40(cp)
adc $0, %ax
'''

import sys
sys.dont_write_bytecode = 1

import gen_mpn_add_4k_plus2_4arg as F

with open(sys.argv[1], 'wb') as g_out:
    F.do_it(g_out, g_code, g_var_map)
