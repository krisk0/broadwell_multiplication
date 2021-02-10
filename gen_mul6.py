"""
TODO: see if push is faster than save to a xmm
      rdi -< rp
      rsi -< up
w7 -< rcx -< vp
r12, r13, r14, r15
 w8   w6   w5   w4
w5 w6 w8 saved
!save ... -- store in xmm. (movq)
"""

g_mul1='''
movq (w7), dd                  | dd = v[0]
vpxor zV, zV, zV               | zV = 0
mulx (up), w1, w0
movq w1, (rp)                  | w0
vmovdqu (w7), jV               | ready v[0]...v[3]
mulx 8(up), w1, w2             | w2 w0+w1
addq w1, w0                    | w2' w0
vmovdqu 32(w7), sV             | ready v[4], v[5]
mulx 16(up), w1, w3            | w3 w1+w2' w0
adcq w2, w1                    | w3' w1 w0
!save w6
mulx 24(up), w2, w4            | w4 w2+w3' w1 w0
adcq w3, w2                    | w4' w2 w1 w0
!save w5
mulx 32(up), w3, w6            | w6 w3+w4' w2 w1 w0
adcq w4, w3                    | w6' w3 w2 w1 w0
!save w8
mulx 40(up), w4, w5            | w5 w4+w6' w3 w2 w1 w0
adcq w6, w4                    | w5' w4 w3 w2 w1 w0
vpextrq $0x1, 128_jV, dd       | ready v[1]
adcq $0, w5                    | w5 w4 w3 w2 w1 w0
'''

"""
zV := 0
dd := v[i]
i > 1:
 q5" q4 q3 q2 q1 q0
 q6 = 0
i = 1:
 q5 q4 q3 q2 q1 q0
"""

g_muladd='''
mulx (up), q8, q7              | q5" q4 q3 q2 q1+q7 q0+q8
adcx q8, q0                    | q5" q4 q3 q2 q1+q7' q0
adox q6, q5                    | q5 q4 q3 q2 q1+q7 q0+q8
vperm2i128 $0x81, jV, jV, jV   | ready v[2], if i=1
mulx 8(up), q8, q6             | q5 q4 q3 q2+q6 q1+q8+q7' q0
adcx q7, q1                    | q5 q4 q3 q2+q6' q1+q8 q0
movq q0, @i(rp)                | q5 q4 q3 q2+q6' q1+q8
mulx 16(up), q0, q7            | q5 q4 q3+q7 q0+q2+q6' q1+q8
adox q8, q1                    | q5 q4 q3+q7 q0+q2+q6'" q1
adcx q6, q2                    | q5 q4 q3+q7' q0+q2" q1
mulx 24(up), q8, q6            | q5 q4+q6 q3+q8+q7' q0+q2" q1
adox q0, q2                    | q5 q4+q6 q3+q8+q7'" q2 q1
adcx q7, q3                    | q5 q4+q6' q3+q8" q2 q1
mulx 32(up), q0, q7            | q5+q7 q0+q4+q6' q3+q8" q2 q1
adox q8, q3                    | q5+q7 q0+q4+q6'" q3 q2 q1
adcx q6, q4                    | q5+q7' q0+q4" q3 q2 q1
mulx 40(up), q8, q6            | q6 q5+q8+q7' q0+q4" q3 q2 q1
movq 128_jV, dd                | dd := v[i+1], if i is odd
adox q0, q4                    | q6 q5+q8+q7'" q4 q3 q2 q1
movq zV, q0                    | q0 = 0
adcx q7, q5                    | q6' q5+q8" q4 q3 q2 q1
adox q8, q5                    | q6'" q5 q4 q3 q2 q1
adcx q0, q6                    | q6" q5 q4 q3 q2 q1
'''
g_permutation = '1 2 3 4 5 6 0 7 8'    # q1 instead of q0, q2 instead of q1, ...

g_tail = '''
                               | q6 = 0
                               | q5" q4 q3 q2 q1 q0
mulx (up), q7, q8              | q5" q4 q3 q2 q1+q8 q0+q7
adcx q7, q0                    | q5" q4 q3 q2 q1+q8' q0
adox q6, q5                    | q5 q4 q3 q2 q1+q8' q0
mulx 8(up), q6, q7             | q5 q4 q3 q2+q7 q1+q6+q8' q0
adcx q8, q1                    | q5 q4 q3 q2+q7' q1+q6 q0
movq q0, 40(rp)                | q5 q4 q3 q2+q7' q1+q6
mulx 16(up), q0, q8            | q5 q4 q3+q8 q0+q2+q7' q1+q6
adox q6, q1                    | q5 q4 q3+q8 q0+q2+q7'" q1
adcx q7, q2                    | q5 q4 q3+q8' q0+q2" q1
mulx 24(up), q6, q7            | q5 q4+q7 q3+q6+q8' q0+q2" q1
adox q2, q0                    | q5 q4+q7 q3+q6+q8'" q0 q1
adcx q8, q3                    | q5 q4+q7' q3+q6" q0 q1
mulx 32(up), q2, q8            | q5+q8 q2+q4+q7' q3+q6" q0 q1
adox q6, q3                    | q5+q8 q2+q4+q7'" q3 q0 q1
movq q1, 48(rp)
movq q0, 56(rp)                | q5+q8 q2+q4+q7'" q3
!restore q1
adcx q7, q4                    | q5+q8' q2+q4" q3
!restore q7
mulx 40(up), q0, q6            | q6 q0+q5+q8' q2+q4" q3
movq zV, dd                    | dd = 0
adox q4, q2                    | q6 q0+q5+q8'" q2 q3
!restore q4
adcx q8, q5                    | q6' q0+q5" q2 q3
!restore q8
adox q5, q0                    | q6'" q0 q2 q3
!restore q5
movq q3, 64(rp)
movq q2, 72(rp)                | q6'" q0
!restore q3
!restore q2
adcx dd, q6                    | q6" q0
adox dd, q6                    | q6 q0
movq q0, 80(rp)
movq q6, 88(rp)                | result saved
!restore q0
!restore q6
'''

# mul6_broadwell() wants registers not expressions, so wrap it up
g_wr_code = '''
#define mul6_broadwell_wr(r, u, v)
    {
        auto mul6_broadwell_wr_r = r;
        auto mul6_broadwell_wr_u = u;
        auto mul6_broadwell_wr_v = v;
        mul6_broadwell(mul6_broadwell_wr_r, mul6_broadwell_wr_u, mul6_broadwell_wr_v);
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P
import gen_mul8_store1 as E

W_COUNT = 9                     # w0 .. w8

def mul1_code(v_index, src, perm):
    tgt = []
    for l in src:
        if (v_index == 1) and (l == 'adox q6, q5'):
            # precondition is different, no carry there. Remove this instruction
            continue
        # vperm2i128 only needed for v_index = 1
        if (l[:10] == 'vperm2i128') and (v_index != 1):
                continue
        tgt.append(l)
    tgt = '\n'.join(tgt) + ' '
    for i in range(W_COUNT):
        j = '%X' % perm[i]
        k = '%X' % i
        tgt = re.sub(r'\bq%s\b' % k, 'w' + j, tgt)
    if (v_index % 2 == 0):
        # replace 'movq 128_xV, dd' with 'vpextrq $0x1,128_xV,dd'
        for x in 'js':
            tgt = tgt.replace('movq 128_%sV, dd' % x, 'vpextrq $0x1,128_%sV,dd' % x)
    if v_index >= 3:
        # v comes from sV, not jV
        tgt = re.sub(r'\b128_jV\b', 'sV', tgt)
    return tgt.replace('@i', '%s' % (8 * v_index)).rstrip()

def cook_asm(out, code, save):
    ymm_map = {'jV': 15, 'sV': 14, 'zV': 13}
    E.append_save_registers(ymm_map, 12, save.values())
    scratch = ['%%ymm%s' % i for i in ymm_map.values()]
    rr_map = {7: 'rcx', 10: 'rbx', 9: 'rbp', 8: 'r12', 6: 'r13', 5: 'r14'}
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
            'macro_name': 'mul6_broadwell',
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
    meat = P.cutoff_comments(g_mul1)
    muladd = P.cutoff_comments(g_muladd)
    tail = P.cutoff_comments(g_tail)

    xmm_save = P.save_registers(meat)

    permutation = list(range(W_COUNT))
    s = [int(y) for y in g_permutation.split(' ')]
    for i in range(1, 5):
        meat += mul1_code(i, muladd, permutation).split('\n')
        # yy := composition of permutation and s: yy(i) == s(permutation(i))
        yy = [s[j] for j in permutation]
        permutation = yy
    tail = mul1_code(5, tail, permutation)
    for k,v in xmm_save.items():
        if v is None:
            tail = tail.replace('!restore ' + k, 'pop %s      | restore' % k)
        else:
            tail = tail.replace('!restore ' + k, 'movq %s, %s | restore' % (v, k))
    tail = tail.replace('!restore', '|restore')
    meat += tail.split('\n')
    cook_asm(o, '\n'.join(meat), xmm_save)

with open(sys.argv[1], 'wb') as g_out:
    do_it(g_out)
