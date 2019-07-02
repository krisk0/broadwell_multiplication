"""
      rdi -< rp
      rsi -< up
w7 -< rcx -< vp
rbx, rbp, r12, r13, r14, r15         saved
 wA   w9   w8   w6   w5   w4
@save ... -- store in stack (push)
!save ... -- store in xmm. (vmovq)
"""

g_mul1='''
movq (w7), dd
@save w5
vpxor vZ, vZ, vZ               | vZ := 0
vmovdqu (w7), jV               | ready v[0]...v[3]
mulx (up), w1, w0
movq w1, (rp)                  | w0
vmovdqu 32(w7), sV             | ready v[4]...v[7]
mulx 8(up), w1, w2             | w2 w0+w1
addq w1, w0                    | w2' w0
|--
mulx 16(up), w1, w3            | w3 w1+w2' w0
adcq w2, w1                    | w3' w1 w0
!save w6
mulx 24(up), w2, w4            | w4 w2+w3' w1 w0
adcq w3, w2                    | w4' w2 w1 w0
!save w8
mulx 32(up), w3, w5            | w5 w3+w4' w2 w1 w0
adcq w4, w3                    | w5' w3 w2 w1 w0
!save w9
mulx 40(up), w4, w6            | w6 w4+w5' w3 w2 w1 w0
adcq w5, w4                    | w6' w4 w3 w2 w1 w0
!save wA
mulx 48(up), w5, w8            | w8 w5+w6' w4 w3 w2 w1 w0
adcq w6, w5                    | w8' w5 w4 w3 w2 w1 w0
|--
mulx 56(up), w6, w7            | w7 w6+w8' w5 w4 w3 w2 w1 w0
vpextrq $0x1,128_jV, dd        | ready v[1]
adcq w8, w6                    | w7' w6 w5 w4 w3 w2 w1 w0
adcq $0, w7                    | w7 w6 w5 w4 w3 w2 w1 w0
'''

"""
! vZ := 0
! wA := 0
! dd := v[i]
! w7" w6 w5 w4 w3 w2 w1 w0
"""

g_muladd='''
                               | q7" q6 q5 q4 q3 q2 q1 q0
| precondition: w<p[7]>" w<p[6]> ... w<p[0]>, w<p[10]> is zero or i=1
mulx (up), q8, q9              | q7" q6 q5 q4 q3 q2 q1+q9 q0+q8
adox qA, q7                    | q7 q6 q5 q4 q3 q2 q1+q9 q0+q8
adcx q8, q0                    | q7 q6 q5 q4 q3 q2 q1+q9' q0
vperm2i128 $0x81,jV,jV,jV      | ready v[i+1], i odd
mulx 8(up), q8, qA             | q7 q6 q5 q4 q3 q2+qA q1+q8+q9' q0
adcx q9, q1                    | q7 q6 q5 q4 q3 q2+qA' q1+q8 q0
movq q0, @i(rp)                | q7 q6 q5 q4 q3 q2+qA' q1+q8
mulx 16(up), q0, q9            | q7 q6 q5 q4 q3+q9 q0+q2+qA'" q1
adox q8, q1                    | q7 q6 q5 q4 q3 q2+qA'" q1
adcx qA, q0                    | q7 q6 q5 q4 q3+q9' q0+q2" q1
mulx 24(up), q8, qA            | q7 q6 q5 q4+qA q3+q8+q9' q0+q2" q1
adox q2, q0                    | q7 q6 q5 q4+qA q3+q8+q9'" q0 q1
adcx q9, q3                    | q7 q6 q5 q4+qA' q3+q8" q0 q1
mulx 32(up), q2, q9            | q7 q6 q5+q9 q2+q4+qA' q3+q8" q0 q1
adox q8, q3                    | q7 q6 q5+q9 q2+q4+qA'" q3 q0 q1
adcx qA, q4                    | q7 q6 q5+q9' q2+q4" q3 q0 q1
mulx 40(up), q8, qA            | q7 q6+qA q5+q8+q9' q2+q4" q3 q0 q1
adox q4, q2                    | q7 q6+qA q5+q8+q9'" q2 q3 q0 q1
adcx q9, q5                    | q7 q6+qA' q5+q8" q2 q3 q0 q1
mulx 48(up), q4, q9            | q7+q9 q4+q6+qA' q5+q8" q2 q3 q0 q1
adox q8, q5                    | q7+q9 q4+q6+qA'" q5 q2 q3 q0 q1
adcx qA, q6                    | q7+q9' q4+q6" q5 q2 q3 q0 q1
mulx 56(up), q8, qA            | qA q7+q8+q9' q4+q6" q5 q2 q3 q0 q1
adox q6, q4                    | qA q7+q8+q9'" q4 q5 q2 q3 q0 q1
movq vZ, q6                    | q6 := 0
adcx q9, q7                    | qA' q7+q8" q4 q5 q2 q3 q0 q1
movq 128_jV, dd                | dd := v[i+1], i odd
adox q8, q7                    | qA'" q7 q4 q5 q2 q3 q0 q1
adcx q6, qA                    | qA" q7 q4 q5 q2 q3 q0 q1          q6 = 0
'''
g_permutation = '1 0 3 2 5 4 7 10 8 9 6'

g_tail='''
                               | q7" q6 q5 q4 q3 q2 q1 q0
mulx (up), q8, q9              | q7" q6 q5 q4 q3 q2 q1+q9 q0+q8
adox qA, q7                    | q7 q6 q5 q4 q3 q2 q1+q9 q0+q8
adcx q8, q0                    | q7 q6 q5 q4 q3 q2 q1+q9' q0
mulx 8(up), q8, qA             | q7 q6 q5 q4 q3 q2+qA q1+q8+q9' q0
adcx q9, q1                    | q7 q6 q5 q4 q3 q2+qA' q1+q8 q0
movq q0, 56(rp)                | q7 q6 q5 q4 q3 q2+qA' q1+q8
mulx 16(up), q0, q9            | q7 q6 q5 q4 q3+q9 q0+q2+qA'" q1
adox q8, q1                    | q7 q6 q5 q4 q3 q2+qA'" q1
adcx qA, q0                    | q7 q6 q5 q4 q3+q9' q0+q2" q1
mulx 24(up), q8, qA            | q7 q6 q5 q4+qA q3+q8+q9' q0+q2" q1
movq q1, 64(rp)                | q7 q6 q5 q4+qA q3+q8+q9' q0+q2"
adox q2, q0                    | q7 q6 q5 q4+qA q3+q8+q9'" q0
adcx q9, q3                    | q7 q6 q5 q4+qA' q3+q8" q0
!restore q1
mulx 32(up), q2, q9            | q7 q6 q5+q9 q2+q4+qA' q3+q8" q0
movq q0, 72(rp)                | q7 q6 q5+q9 q2+q4+qA' q3+q8"
adox q8, q3                    | q7 q6 q5+q9 q2+q4+qA'" q3
!restore q0
adcx qA, q4                    | q7 q6 q5+q9' q2+q4" q3
mulx 40(up), q8, qA            | q7 q6+qA q5+q8+q9' q2+q4" q3
movq q3, 80(rp)                | q7 q6+qA q5+q8+q9' q2+q4" q3
adox q4, q2                    | q7 q6+qA q5+q8+q9'" q2
adcx q9, q5                    | q7 q6+qA' q5+q8" q2
movq q2, 88(rp)                | q7 q6+qA' q5+q8"
!restore q3
mulx 48(up), q4, q9            | q7+q9 q4+q6+qA' q5+q8"
!restore q2
adox q8, q5                    | q7+q9 q4+q6+qA'" q5
adcx qA, q6                    | q7+q9' q4+q6" q5
mulx 56(up), q8, qA            | qA q7+q8+q9' q4+q6" q5
movq vZ, dd
movq q5, 96(rp)                | qA q7+q8+q9' q4+q6"
!restore q5
adox q6, q4                    | qA q7+q8+q9'" q4
adcx q9, q7                    | qA' q7+q8" q4
adox q8, q7                    | qA'" q7 q4
!restore q6
movq q4, 104(rp)               | qA'" q7
!restore q8
!restore q4
adcx dd, qA
adox qA, dd                    | dd q7
!restore qA
movq q7, 112(rp)               | dd
!restore q9                    | moved here so movq xmm, reg are better spread
!restore q7
movq dd, 120(rp)
'''
# TODO: tail of g_tail looks unoptimal

# mul8_broadwell_store_once() wants registers not expressions, so wrap it up
g_wr_code = '''
#define mul8_broadwell_store_once_wr(r, u, v)
    {
        auto mul8_broadwell_store_once_wr_r = r;
        auto mul8_broadwell_store_once_wr_u = u;
        auto mul8_broadwell_store_once_wr_v = v;
        mul8_broadwell_store_once(mul8_broadwell_store_once_wr_r,
                mul8_broadwell_store_once_wr_u,
                mul8_broadwell_store_once_wr_v);
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

def cutoff_comments(s):
    result = [P.strip_off_comment(x) for x in s.split('\n')]
    return [x for x in result if x]

g_save_pattern = re.compile('.save w(.)')
def save_registers(xx):
    # returns dictionary that lists saved registers
    n = len(xx)
    result = {}
    for i in range(n):
        x = xx[i]
        m = g_save_pattern.match(x)
        if not m:
            continue
        m = m.group(1)
        if x[0] == '@':
            xx[i] = 'push w' + m
            result['w' + m] = None
        else:
            xx[i] = 'movq w@, s@'.replace('@', m)
            result['w' + m] = 's' + m
    return result

def mul1_code(v_index, src, perm):
    tgt = []
    for l in src:
        if (v_index == 1) and (l == 'adox qA, q7'):
            # precondition is different, no carry there. Remove this instruction
            continue
        if (v_index % 2 == 0) or (v_index == 3):
            # vperm2i128 not needed
            if l[:10] == 'vperm2i128':
                continue
        tgt.append(l)
    tgt = '\n'.join(tgt) + ' '
    for i in range(11):
        j = '%X' % perm[i]
        k = '%X' % i
        tgt = re.sub(r'\bq%s\b' % k, 'w' + j, tgt)
    if v_index >= 3:
        # v comes from vS, not jV
        tgt = re.sub(r'\bjV\b', 'sV', tgt)
        tgt = re.sub(r'\b128_jV\b', '128_sV', tgt)
    if (v_index % 2 == 0):
        # replace 'movq 128_xV, dd' with 'vpextrq $0x1,128_xV,dd'
        for x in 'js':
            tgt = tgt.replace('movq 128_%sV, dd' % x, 'vpextrq $0x1,128_%sV,dd' % x)
    tgt = tgt.replace('@i', '%s' % (8 * v_index))
    return tgt.rstrip()

def append_save_registers(tgt, i, vv):
    for v in vv:
        if not v:
            continue
        i -= 1
        tgt[v] = i

def replace_wi(src, mapping):
    src += ' '
    for k,v in mapping.items():
        src = re.sub(r'\bw%X\b' % k, '%%' + v, src)
    return src.rstrip()

def replace_ymm(src, mapping):
    src += ' '
    for k,v in mapping.items():
        if v >= 14:
            # only two 256-bit registers used
            src = re.sub(r'\b128_%s\b' % k, '%%' + ('xmm%s' % v), src)
            src = re.sub(r'\b%s\b' % k, '%%' + ('ymm%s' % v), src)
        else:
            src = re.sub(r'\b%s\b' % k, '%%' + ('xmm%s' % v), src)
    return src.rstrip()

def cook_asm(out, code, save):
    ymm_map = {'jV': 15, 'sV': 14, 'vZ': 13}
    append_save_registers(ymm_map, 12, save.values())
    scratch = ['%%ymm%s' % i for i in ymm_map.values()]
    rr_map = {7: 'rcx', 10: 'rbx', 9: 'rbp', 8: 'r12', 6: 'r13', 5: 'r14'}
    scratch_map = {0: 'rax', 1: 'r8', 2: 'r9', 3: 'r10', 4: 'r11'}
    scratch += ['%' + i for i in scratch_map.values()]
    rr_map.update(scratch_map)
    code = replace_wi(code, rr_map)
    code = replace_ymm(code, ymm_map)
    code = re.sub(r'\bdd\b', '%%rdx', code)
    for v in 'up', 'rp':
        code = re.sub(r'\b%s\b' % v, '%%[%s]' % v, code)
    data = {
            'input': ['up S u_p', 'rp D r_p'],
            'input_output': ['vp +c v_p'],
            'clobber': 'cc memory rdx ' + ' '.join(scratch),
            'macro_name': 'mul8_broadwell_store_once',
            'macro_parameters': 'r_p u_p v_p',
            'source': os.path.basename(sys.argv[0]),
            'code_language': 'asm',
            }
    P.write_cpp_code(out, code, data)
    out.write('\n')
    for i in g_wr_code.strip().split('\n'):
        out.write(P.append_backslash(i, 77))
    out.write('    }\n')

def do_it(out):
    mul1 = cutoff_comments(g_mul1)
    muladd = cutoff_comments(g_muladd)
    tail = cutoff_comments(g_tail)

    xmm_save = save_registers(mul1)
    meat = mul1[:]

    permutation = list(range(11))
    s = [int(y) for y in g_permutation.split(' ')]
    for i in range(1, 7):
        meat += mul1_code(i, muladd, permutation).split('\n')
        # yy := composition of permutation and s: yy(i) == s(permutation(i))
        yy = [s[j] for j in permutation]
        permutation = yy
    tail = mul1_code(7, tail, permutation)
    for k,v in xmm_save.items():
        if v is None:
            tail = tail.replace('!restore ' + k, 'pop %s      | restore' % k)
        else:
            tail = tail.replace('!restore ' + k, 'movq %s, %s | restore' % (v, k))
    tail = tail.replace('!restore', '|restore')
    meat += tail.split('\n')
    cook_asm(out, '\n'.join(meat), xmm_save)

with open(sys.argv[1], 'wb') as g_out:
    do_it(g_out)
