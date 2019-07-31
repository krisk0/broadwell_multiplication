"""
mpn_bdiv_dbm1c_4k(r_p, u_p, n, m_m)

exactly divide n-limb number at u_p by k, store result at r_p. n is multiple of four.
 m_m * k == -1 (mod 2**64)
"""

#use tail-plus-one-pointer for loop termination
g_code_0 = '''
mov (up), aa
xor hh,hh                        | hh = 0
lea (up,nn,8),nn                 | nn points one limb past tail of number u

.align 32                        | precondition: up and rp shifted by 4*i
                                 | 0 <= 4*i < n
                                 | u_p[4*i] loaded into aa
loop:
mul mm
sub aa, hh
mov 8(up), aa                    | TODO: shift this 2 lines down and check throughput
mov hh, (rp)
sbb dd, hh

mul mm
sub aa, hh
mov 16(up), aa
mov hh, 8(rp)
sbb dd, hh

mul mm
sub aa, hh
mov 24(up), aa
lea 32(up), up
mov hh, 16(rp)
sbb dd, hh

mul mm
sub aa, hh
mov hh, 24(rp)
lea 32(rp), rp
sbb dd, hh

cmp up, nn
mov (up), aa
jne loop
'''

# use ecx for nn, decrease nn, use jecxz for loop termination
g_code_1 = '''
xor hh,hh                        | hh = 0

.align 32                        | precondition: up and rp shifted by 4*i
                                 | 0 <= 4*i <= n
loop:
jecxz tail

mov (up), aa
mul mm
sub aa, hh
mov hh, (rp)
sbb dd, hh

mov 8(up), aa
mul mm
sub aa, hh
mov hh, 8(rp)
sbb dd, hh

lea -4(nn),nn

mov 16(up), aa
mul mm
sub aa, hh
mov hh, 16(rp)
sbb dd, hh

lea 32(up), up
mov -8(up), aa
mul mm
sub aa, hh
mov hh, 24(rp)
sbb dd, hh

lea 32(rp), rp
jmp loop
tail:
'''

# grow index to zero, 'jnz loop' terminates loop
g_code = '''
mov (up), aa
mul mm
xor hh,hh                        | hh = 0
lea (up,nn,8), up                | up now one limb past tail of u
lea (rp,nn,8), rp
neg nn
jmp enter_here

.align 16
loop:
mov (up,nn,8), aa
mul mm
enter_here:
sub aa, hh
mov hh, (rp,nn,8)
sbb dd, hh

mov 8(up,nn,8), aa
mul mm
sub aa, hh
mov hh, 8(rp,nn,8)
sbb dd, hh

mov 16(up,nn,8), aa
mul mm
sub aa, hh
mov hh, 16(rp,nn,8)
sbb dd, hh

mov 24(up,nn,8), aa
mul mm
sub aa, hh
mov hh, 24(rp,nn,8)
sbb dd, hh

add $4, nn
jnz loop
'''

# mulx instead of mul. TODO: use one more register, pair store instructions.
# This variant appears to be 6 ticks better than __gmpn_bdiv_dbm1c() for n=60
g_code = '''
xor hh,hh                        | hh = 0
lea (rp,nn,8), rp
| GCC creates specialization of mpn_bdiv_dbm1c_4k_func() with fixed mm, so there is
|   movabs $0x5555555555555555,%rdx
| so we move mulx (up)... slightly lower
mulx (up), aa, dd
lea (up,nn,8), up                | up now one limb past tail of u
neg nn
jmp enter_here

.align 16
loop:
mulx (up,nn,8), aa, dd
enter_here:
sub aa, hh
mov hh, (rp,nn,8)
sbb dd, hh

mulx 8(up,nn,8), aa, dd
sub aa, hh
mov hh, 8(rp,nn,8)
sbb dd, hh

mulx 16(up,nn,8), aa, dd
sub aa, hh
mov hh, 16(rp,nn,8)
sbb dd, hh

mulx 24(up,nn,8), aa, dd
sub aa, hh
mov hh, 24(rp,nn,8)
sbb dd, hh

add $4, nn
jnz loop
'''

g_wr_code = '''
#define mpn_bdiv_dbm1c_4k_wr(r, u, n, m)
    {
        mp_ptr bdiv_dbm1c_4k_r = r;
        mp_srcptr bdiv_dbm1c_4k_u = u;
        mp_limb_t bdiv_dbm1c_4k_m = m;
        mp_limb_t bdiv_dbm1c_4k_n = n;
        mpn_bdiv_dbm1c_4k(bdiv_dbm1c_4k_r, bdiv_dbm1c_4k_u, bdiv_dbm1c_4k_n,
                bdiv_dbm1c_4k_m);
'''

g_func_code = '''
void
__attribute__ ((noinline))
mpn_bdiv_dbm1c_4k_func(mp_ptr r_p, mp_srcptr u_p, mp_limb_t n, mp_limb_t m) {
    mpn_bdiv_dbm1c_4k(r_p, u_p, n, m);
}
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

def do_it(tgt):
    data = {
            'macro_name': 'mpn_bdiv_dbm1c_4k',
            'input_output': ['rp +r r_p', 'up +r u_p', 'mm +d m_m', 'nn +r n'],
            'clobber': 'memory cc %rax %rcx %r8',
            'source': os.path.basename(sys.argv[0]),
            'code_language': 'asm',
            'macro_parameters': 'r_p u_p n m_m',
            }

    code = re.sub(r'\baa\b', '%%rax', g_code.strip())
    code = re.sub(r'\bdd\b', '%%rcx', code)
    code = re.sub(r'\bhh\b', '%%r8', code)
    for i in 'loop tail enter_here'.split(' '):
        code = re.sub(r'\b%s\b' % i, i + '%=', code + ' ').rstrip()
    for v in 'rp up mm nn'.split(' '):
        code = re.sub(r'\b%s\b' % v, '%%[%s]' % v, code)

    P.write_cpp_code(tgt, code, data)
    tgt.write('\n')
    for i in g_wr_code.strip().split('\n'):
        tgt.write(P.append_backslash(i, 88))
    tgt.write('    }\n')
    tgt.write(g_func_code)

g_tgt = sys.argv[1]

try:
    os.makedirs(os.path.dirname(g_tgt))
except:
    pass

with open(g_tgt, 'wb') as g_o:
    do_it(g_o)
