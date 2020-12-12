'''
8x8 multiplication targeting Ryzen and Skylake, modification of mul8_zen. Uses
 aligned loads of v[] into xmm's.
 
100 ticks on Ryzen, 111 on Skylake
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P
import gen_mul8_zen as E

g_preamble = '''
vzeroupper
movq dd, w0
and $0xF, dd
movq (w0), dd
jz align0
'''

g_load0 = '''
movq 8(w0), t0
!save w9
movdqa 16(w0), t1
movdqa 32(w0), t2
!save w5
movdqa 48(w0), t3
'''

def extract_v(i, t, align):
    if (i == 1):
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
        if (i == 7):
            return 'movq t3, ' + t
    else:
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
        if (i == 7):
            return 'pextrq $0x1, t3, ' + t

def mul1_code(i, jj, p, align):
    rr = ['# mul_add %s %s' % (align, i)]
    for j in jj:
        if j.find(':=v[i+1]') != -1:
            j = extract_v(i + 1, j[:2], align)
            if not j:
                continue
        rr.append(j)

    if i == 7:
        rr = rr[:-1] + P.cutoff_comments(E.g_tail)

    # apply permutation p, replace i(rp)
    for y in range(len(rr)):
        src = rr[y]
        for x in range(12):
            a = '%X' % x
            b = '%X' % p[x]
            src = re.sub(r'\bs%s\b' % a, 'w' + b, src)
        src += ' '
        for x in range(1, 9):
            ' replace i+x with 8*(i+x) '
            src = src.replace('i+%s(' % x, '%s(' % (8 * (i + x)))
        ' replace i with 8*i '
        src = src.replace('i(', '%s(' % (8 * i)) + ' '
        rr[y] = src.rstrip()

    return rr

def save_in_xmm(code, f):
    for i in range(len(code)):
        m = P.g_xmm_save_pattern.match(code[i])
        if not m:
            continue
        m = m.group(1)
        code[i] = 'movq %s, %s' % (m, f[m])

def cook_asm(o, code, xmm_save):
    code = '\n'.join(code)
    for k,v in xmm_save.items():
        code = code.replace('!restore ' + k, 'movq %s, %s' % (v, k))

    code = P.replace_symbolic_names_wr(code, E.g_reg_map)
    code = code.replace('movdqu', 'movdqa')

    comment = P.g_autogenerated_patt % os.path.basename(sys.argv[0])
    o.write(comment.replace('//', '#'))
    P.write_asm_procedure_header(o, P.guess_subroutine_name(sys.argv[1]))
    P.write_asm_inside(o, code + '\nretq')

def alignment_code(shift):
    p = list(range(12))
    m = P.cutoff_comments(E.g_muladd_2)
    code = mul1_code(2, m, p, shift)
    q = [int(x, 16) for x in E.g_perm.split(' ')]
    for i in range(3, 8):
        p = P.composition(p, q)
        code += mul1_code(i, m, p, shift)
    return code

def starting_from(cc, s):
    i = [i for i in range(len(cc)) if cc[i].find(s) != -1][0]
    return cc[i:]

def replace_el(cc, el, rr):
    return '\n'.join(cc).replace(el, rr).split('\n')

def replace_extract_v(cc, shift):
    rr = []
    for c in cc:
        if c.find(':=v[2]') != -1:
            c = extract_v(2, c[:2], shift)
        rr.append(c)
    return rr

def do_it(o):
    mul_01 = P.cutoff_comments(E.g_mul_01)[3:]
    mul_01 = replace_el(mul_01, 'pextrq $0x1, t0, w3', 'w3:=v[2]')
    code = P.cutoff_comments(g_preamble) + replace_extract_v(mul_01, 8)
    code += alignment_code(8)
    code += ['retq', 'align0:']

    xmm_save = P.save_registers_in_xmm(P.cutoff_comments(E.g_mul_01), 9)
    P.insert_restore(code, xmm_save)

    code += P.cutoff_comments(g_load0)
    mul_01= starting_from(mul_01, 'mulx')
    code += replace_extract_v(mul_01, 0)
    code += alignment_code(0)

    save_in_xmm(code, xmm_save)
    P.insert_restore(code, xmm_save)

    cook_asm(o, code, xmm_save)

with open(sys.argv[1], 'wb') as g_out:
    do_it(g_out)
