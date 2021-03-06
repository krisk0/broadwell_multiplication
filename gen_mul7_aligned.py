'''
7x7 multiplication that avoids movdqu. ?88 ticks on Skylake, ?77 on Ryzen
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P
import gen_mul7_t03 as E

g_preamble = '''
vzeroupper
movq dd, w0
and $0xF, dd
movq (w0), dd
jz align0
movdqa 8(w0), t0         | t0=v[1..2]
movdqa 24(w0), t1        | t1=v[3..4]
movdqa 40(w0), t2        | t2=v[5..6]
'''

g_load0 = '''
movq 8(w0), t0           | t0=v[1]
movdqa 16(w0), t1        | t1=v[2..3]
movdqa 32(w0), t2        | t2=v[4..5]
movq 48(w0), t3          | t3=v[6]
'''

def extract_v(i, t, align):
    if i == 1:
        return 'movq t0, ' + t
    if align == 8:
        if (i == 2):
            return 'pextrq $0x1, t0, ' + t
        if (i == 3):
            return 'movq t1, ' + t
        if (i == 4):
            return 'pextrq $0x1, t1, ' + t
        if (i == 5):
            return 'movq t2, ' + t
        if (i == 6):
            return 'pextrq $0x1, t2, ' + t
    if (i == 2):
        return 'movq t1, ' + t
    if (i == 3):
        return 'pextrq $0x1, t1, ' + t
    if (i == 4):
        return 'movq t2, ' + t
    if (i == 5):
        return 'pextrq $0x1, t2, ' + t
    if (i == 6):
        return 'movq t3, ' + t

def replace_extract_v(cc, shift):
    rr = []
    for c in cc:
        if c.find(':=v[2]') != -1:
            c = extract_v(2, c[:2], shift)
        rr.append(c)
    return rr

def mul1_code(i, jj, p, align):
    rr = ['# mul_add %s' % i]
    for j in jj:
        if j.find(':=v[i+1]') != -1:
            j = extract_v(i + 1, j[:2], align)
            if not j:
                continue
        rr.append(j)

    #print post_condition(i, ' pre', '''s8" s0+s5 s9+s6' s3 s1 s2 s4''', p)

    # apply permutation p, replace i(rp)
    for y in range(len(rr)):
        src = E.apply_s_permutation(rr[y], p)
        for x in range(1, 9):
            ' replace i+x with 8*(i+x) '
            src = src.replace('i+%s(' % x, '%s(' % (8 * (i + x)))
        ' replace i with 8*i '
        src = src.replace('i(', '%s(' % (8 * i))
        rr[y] = src.rstrip()

    #print post_condition(i, 'post', '''s2' s8+s4 s0+s7" s6 s3 s1 sB''', p)

    return rr

def alignment_code(shift):
    p = list(range(12))
    m2 = P.cutoff_comments(E.g_muladd_2)
    m3 = P.swap_adox_adcx(m2)
    code = mul1_code(2, m2, p, shift)
    q = [int(x, 16) for x in E.g_perm.split(' ')]
    for i in range(3, 6):
        p = P.composition(p, q)
        if i & 1:
            code += mul1_code(i, m3, p, shift)
        else:
            code += mul1_code(i, m2, p, shift)

    tail = E.cook_tail(m2)
    p = P.composition(p, q)
    code += mul1_code(6, tail, p, shift)

    return code

def do_it(o):
    mul_01 = P.cutoff_comments(E.g_mul_01)
    mul_01 = P.starting_from(mul_01, 'mulx')
    mul_01 = P.replace_in_string_array(mul_01, 'pextrq $0x1, t0, w8', 'w8:=v[2]')
    code = P.cutoff_comments(g_preamble)
    code += replace_extract_v(mul_01, 8)
    code += alignment_code(8)
    # TODO: is it possible to shorten binary code by jmp to common part?
    code += P.g_std_end + ['retq', 'align0:']

    code += P.cutoff_comments(g_load0)
    code += replace_extract_v(mul_01, 0)
    code += alignment_code(0)

    P.cook_asm(o, code, E.g_var_map, True)

if __name__ == '__main__':
    with open(sys.argv[1], 'wb') as g_out:
        do_it(g_out)
