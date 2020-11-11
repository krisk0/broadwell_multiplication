'''
AMD Zen is faster than Intel Broadwell (in arithmetic operations per tick).
 However Zen dislikes immediate use of mulx result while Broadwell likes it.
 For this reason, low-level subroutines like mul6_zen must be rewritten.
'''

"""
      rdi -< rp
      rsi -< up
w7 -< rcx -< vp

rbp rbx r12 r13 r14 r15
wB  wA  w9  w8  w6  w5    -- saved

rax r8  r9  r10 r11
w0  w1  w2  w3  w4
"""

g_mul0='''
movq (w7), dd                  | dd = v[0]
vpxor zV, zV, zV               | zV = 0
!save w5
vmovdqu (w7), jV               | ready v[0]...v[3]
mulx (up), w0, w1              | w1 w0
!save w6
vmovdqu 32(w7), sV             | ready v[4], v[5]
mulx 8(up), w2, w3             | w3 w1+w2 w0
!save w8
mulx 16(up), w4, w5            | w5 w3+w4 w1+w2 w0
movq w0, (rp)                  | w5 w3+w4 w1+w2
!save w9
xorq w8, w8                    | zero flags
mulx 24(up), w6, w7            | w7 w5+w6 w3+w4 w1+w2
adcx w2, w1                    | w7 w5+w6 w3+w4' w1
mulx 32(up), w0, w8            | w8 w0+w7 w5+w6 w3+w4' w1
!save wA
adcx w4, w3                    | w8 w0+w7 w5+w6' w3 w1
mulx 40(up), w2, w9            | w9 w2+w8 w0+w7 w5+w6' w3 w1
!save wB
adcx w6, w5                    | w9 w2+w8 w0+w7' w5 w3 w1
vpextrq $0x1, 128_jV, dd       | ready v[1]
adcx w7, w0                    | w9 w2+w8' w0 w5 w3 w1
'''

"""
zV = 0
dd = v[i]
q9 q2+q8' q0 q5 q3 q1
OF = 0
"""

g_muladd='''
                               | q9 q2+q8' q0 q5 q3 q1
mulx (up), q4, q6              | q9 q2+q8' q0 q5 q3+q6 q1+q4
adcx q8, q2                    | q9' q2 q0 q5 q3+q6 q1+q4
mulx 8(up), q7, q8             | q9' q2 q0 q5+q8 q3+q6+q7 q1+q4
vperm2i128 $0x81, jV, jV, jV   | ready v[i+1], if i is odd
adcq $0, q9                    | q9 q2 q0 q5+q8 q3+q6+q7 q1+q4
mulx 16(up), qA, qB            | q9 q2 q0+qB q5+q8+qA q3+q6+q7 q1+q4
adcx q4, q1                    | q9 q2 q0+qB q5+q8+qA q3+q6+q7' q1
adcx q7, q3                    | q9 q2 q0+qB q5+q8+qA' q3+q6 q1
mulx 24(up), q4, q7            | q9 q2+q7 q0+q4+qB q5+q8+qA' q3+q6 q1
adox q6, q3                    | q9 q2+q7 q0+q4+qB q5+q8+qA'" q3 q1
adcx qA, q5                    | q9 q2+q7 q0+q4+qB' q5+q8" q3 q1
mulx 32(up), q6, qA            | q9+qA q2+q6+q7 q0+q4+qB' q5+q8" q3 q1
adcx qB, q0                    | q9+qA q2+q6+q7' q0+q4 q5+q8" q3 q1
adox q8, q5                    | q9+qA q2+q6+q7' q0+q4" q5 q3 q1
movq q1, @i(rp)                | q9+qA q2+q6+q7' q0+q4" q5 q3
mulx 40(up), q1, q8            | q8 q9+qA+q1 q2+q6+q7' q0+q4" q5 q3
adcx q7, q2                    | q8 q9+qA+q1' q2+q6 q0+q4" q5 q3
movq zV, q7                    | q7 = 0
adox q4, q0                    | q8 q9+qA+q1' q2+q6" q0 q5 q3
movq 128_jV, dd                | dd = v[i+1], if i is odd
adox q6, q2                    | q8 q9+qA+q1'" q2 q0 q5 q3
adox qA, q9                    | q8" q9+q1' q2 q0 q5 q3
adox q7, q8                    | q8 q9+q1' q2 q0 q5 q3
'''

'                             8->9 9->8 1->2 2->0 0->5 5->3 3->1'

g_permutation = '2 3 1 5 4 0 6 7 9 8 A B'

#TODO: spread the 4 !restore
g_tail = '''
!restore q6
!restore q7
!restore qA
!restore qB
                               | q9 q2+q8' q0 q5 q3 q1
|get rid of trailing movq %xmm...
movq q9, q4                    | q4 q2+q8' q0 q5 q3 q1
!restore q9
movq q1, 48(rp)                | q4 q2+q8' q0 q5 q3
!restore q1
adcx q8, q2                    | q4' q2 q0 q5 q3
!restore q8
movq q3, 56(rp)                | q4' q2 q0 q5
!restore q3
movq q5, 64(rp)                | q4' q2 q0
!restore q5
adcq $0, q4                    | q4 q2 q0
movq q0, 72(rp)                | q4 q2
!restore q0
movq q2, 80(rp)                | q4
!restore q2
movq q4, 88(rp)                | q4
!restore q4
'''

# mul6_zen() wants registers not expressions, so wrap it up
g_wr_code = '''
#define mul6_zen_wr(r, u, v)
    {
        auto mul6_zen_wr_r = r;
        auto mul6_zen_wr_u = u;
        auto mul6_zen_wr_v = v;
        mul6_zen(mul6_zen_wr_r, mul6_zen_wr_u, mul6_zen_wr_v);
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P
import gen_mul8_store1 as E

def mul1_code(v_index, src, perm):
    tgt = []
    for l in src:
        # vperm2i128 only needed for v_index = 1
        if (v_index != 1) and (l[:10] == 'vperm2i128'):
            continue
        # new dd value not needed for v_index = 5
        if (v_index == 5) and (l == 'movq 128_jV, dd'):
            continue
        tgt.append(l)
    tgt = '\n'.join(tgt) + ' '
    for i in range(len(perm)):
        j = '%X' % perm[i]
        k = '%X' % i
        tgt = re.sub(r'\bq%s\b' % k, 'w' + j, tgt)
    if (v_index % 2 == 0):
        # replace 'movq 128_xV, dd' with 'vpextrq $0x1,128_xV,dd'
        tgt = tgt.replace('movq 128_jV, dd', 'vpextrq $0x1,128_jV,dd')
    if v_index >= 3:
        # v comes from sV, not jV
        tgt = re.sub(r'\b128_jV\b', 'sV', tgt)
    # TODO: cut off smth for v_index=5?
    return tgt.replace('@i', '%s' % (8 * v_index)).rstrip()

def cook_asm(out, code, save):
    ymm_map = {'jV': 15, 'sV': 14, 'zV': 13}
    E.append_save_registers(ymm_map, 12, save.values())
    scratch = ['%%ymm%s' % i for i in ymm_map.values()]
    rr_map = {7: 'rcx', 10: 'rbx', 11: 'rbp', 9: 'r12', 8: 'r13', 6: 'r14', 5: 'r15'}
    scratch_map = {0: 'rax', 1: 'r8', 2: 'r9', 3: 'r10', 4: 'r11'}
    scratch += ['%' + i for i in scratch_map.values()]
    rr_map.update(scratch_map)
    code = E.replace_wi(code, rr_map)
    code = E.replace_ymm(code, 15, ymm_map)       # only one 32-bit register
    code = re.sub(r'\bdd\b', '%%rdx', code)
    for v in 'up', 'rp':
        code = re.sub(r'\b%s\b' % v, '%%[%s]' % v, code)
    data = {
        'input': ['up S u_p', 'rp D r_p'],
        'input_output': ['vp +c v_p'],
        'clobber': 'cc memory %rdx ' + ' '.join(scratch),
        'macro_name': 'mul6_zen',
        'macro_parameters': 'r_p u_p v_p',
        'source': os.path.basename(sys.argv[0]),
        'code_language': 'asm',
    }
    P.write_cpp_code(out, code, data)
    out.write('\n')
    for i in g_wr_code.strip().split('\n'):
        out.write(P.append_backslash(i, 88))
    out.write('    }\n')

def do_it(o):
    meat = P.cutoff_comments(g_mul0)
    muladd = P.cutoff_comments(g_muladd)
    tail = P.cutoff_comments(g_tail)

    xmm_save = P.save_registers(meat)

    s = [int(y, 0x10) for y in g_permutation.split(' ')]
    p = list(range(len(s)))
    for i in range(1, 6):
        meat += mul1_code(i, muladd, p).split('\n')
        # y := composition of p and s: y(i) == s(permutation(i))
        y = [s[j] for j in p]
        p = y
    tail = mul1_code(999, tail, p)
    for k,v in xmm_save.items():
        tail = tail.replace('!restore ' + k, 'movq %s, %s | restore' % (v, k))
    tail = tail.replace('!restore', '|restore')
    meat += tail.split('\n')
    cook_asm(o, '\n'.join(meat), xmm_save)

with open(sys.argv[1], 'wb') as g_out:
    do_it(g_out)
