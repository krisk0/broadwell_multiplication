'''
void mul7_2arg(mp_ptr rp, mp_srcptr ap);

Multiplies 7-limb number at ap by 7-limb number at ap+7. Puts 14-limb result into rp.
'''

g_var_map = 'rp,rdi up,rsi wB,rbp wA,rbx w9,r12 w8,r13 w7,r14 w6,r15 ' + \
    'w0,rax w1,r8 w2,r9 w3,r10 w4,r11 w5,rcx dd,rdx'

g_mul_01 = '''
vzeroupper
!save w6
dd:=v[0]
!save w7
mulx (up), w1, w2        | w2 w1
!save w8
mulx 8(up), w3, w4       | w4 w2+w3 w1
!save w9
mulx 16(up), w5, w6      | w6 w4+w5 w2+w3 w1
!save wA
mulx 24(up), w7, w8      | w8 w6+w7 w4+w5 w2+w3 w1
movq w1, 0(rp)           | w8 w6+w7 w4+w5 w2+w3 {1}
!save wB
mulx 32(up), w1, w9      | w9 w8+w1 w6+w7 w4+w5 w2+w3 {1}
addq w3, w2              | w9 w8+w1 w6+w7 w4+w5' w2 {1}
mulx 40(up), w3, wA      | wA w9+w3 w8+w1 w6+w7 w4+w5' w2 {1}
mulx 48(up), w0, wB      | wB wA+w0 w9+w3 w8+w1 w6+w7 w4+w5' w2 {1}
dd:=v[1]
adcq w5, w4              | wB wA+w0 w9+w3 w8+w1 w6+w7' w4 w2 {1}
adcq w7, w6              | wB wA+w0 w9+w3 w8+w1' w6 w4 w2 {1}
mulx (up), w5, w7        | wB wA+w0 w9+w3 w8+w1' w6 w4+w7 w2+w5 {1}
adcq w8, w1              | wB wA+w0 w9+w3' w1 w6 w4+w7 w2+w5 {1}
adcq w9, w3              | wB wA+w0' w3 w1 w6 w4+w7 w2+w5 {1}
mulx 8(up), w8, w9       | wB wA+w0' w3 w1 w6+w9 w4+w7+w8 w2+w5 {1}
adcq wA, w0              | wB' w0 w3 w1 w6+w9 w4+w7+w8 w2+w5 {1}
adcq $0, wB              | wB w0 w3 w1 w6+w9 w4+w7+w8 w2+w5 {1}
adox w5, w2              | wB w0 w3 w1 w6+w9 w4+w7+w8" w2 {1}
mulx 16(up), w5, wA      | wB w0 w3 w1+wA w6+w9+w5 w4+w7+w8" w2 {1}
movq w2, 1(rp)           | wB w0 w3 w1+wA w6+w9+w5 w4+w7+w8" {2}
movq w4, 2(rp)           | wB w0 w3 w1+wA w6+w9+w5 w7+w8|" {2}
mulx 24(up), w2, w4      | wB w0 w3+w4 w1+wA+w2 w6+w9+w5 w7+w8|" {2}
movq w6, 3(rp)           | wB w0 w3+w4 w1+wA+w2 w9+w5| w7+w8|" {2}
movq w1, 4(rp)           | wB w0 w3+w4 wA+w2| w9+w5| w7+w8|" {2}
mulx 32(up), w1, w6      | wB w0+w6 w3+w4+w1 wA+w2| w9+w5| w7+w8|" {2}
adox w8, w7              | wB w0+w6 w3+w4+w1 wA+w2| w9+w5|" w7| {2}
mulx 40(up), w8, dd      | wB+dd w0+w6+w8 w3+w4+w1 wA+w2| w9+w5|" w7| {2}
adox w9, w5              | wB+dd w0+w6+w8 w3+w4+w1 wA+w2|" w5| w7| {2}
movq 2(rp), w9           | wB+dd w0+w6+w8 w3+w4+w1 wA+w2|" w5| w7+w9 {2}
adcx w9, w7              | wB+dd w0+w6+w8 w3+w4+w1 wA+w2|" w5|' w7 {2}
movq 4(rp), w9           | wB+dd w0+w6+w8 w3+w4+w1 w9+wA+w2" w5|' w7 {2}
adox wA, w9              | wB+dd w0+w6+w8 w3+w4+w1" w9+w2 w5|' w7 {2}
movq 3(rp), wA           | wB+dd w0+w6+w8 w3+w4+w1" w9+w2 w5+wA' w7 {2}
adcx wA, w5              | wB+dd w0+w6+w8 w3+w4+w1" w9+w2' w5 w7 {2}
wA:=v[1]
adox w4, w3              | wB+dd w0+w6+w8" w3+w1 w9+w2' w5 w7 {2}
xchg dd, wA              | wB+wA w0+w6+w8" w3+w1 w9+w2' w5 w7 {2}
adcx w9, w2              | wB+wA w0+w6+w8" w3+w1' w2 w5 w7 {2}
mulx 48(up), w4, w9      | w9 wB+wA+w4 w0+w6+w8" w3+w1' w2 w5 w7 {2}
dd:=v[2]
adox w6, w0              | w9 wB+wA+w4" w0+w8 w3+w1' w2 w5 w7 {2}
adcx w3, w1              | w9 wB+wA+w4" w0+w8' w1 w2 w5 w7 {2}
'''

'''
i >= 2
multiplied by v[0], .. v[i-1]
data lies like that: s9 sB+sA+s4" s0+s8' s1 s2 s5 s7 {i} dd=v[i]
'''

g_muladd = '''
                         | s9 sB+sA+s4" s0+s8' s1 s2 s5 s7 {i}
mulx (up), s3, s6        | s9 sB+sA+s4" s0+s8' s1 s2 s5+s6 s7+s3 {i}
adox sB, sA              | s9" sA+s4 s0+s8' s1 s2 s5+s6 s7+s3 {i}
adcx s8, s0              | s9" sA+s4' s0 s1 s2 s5+s6 s7+s3 {i}
movq $0, s8
adox s8, s9              | s9 sA+s4' s0 s1 s2 s5+s6 s7+s3 {i}
mulx 8(up), s8, sB       | s9 sA+s4' s0 s1 s2+sB s5+s6+s8 s7+s3 {i}
adcx sA, s4              | s9' s4 s0 s1 s2+sB s5+s6+s8 s7+s3 {i}
movq s5, i+1(rp)         | s9' s4 s0 s1 s2+sB s6+s8| s7+s3 {i}
mulx 16(up), s5, sA      | s9' s4 s0 s1+sA s2+sB+s5 s6+s8| s7+s3 {i}
adox s7, s3              | s9' s4 s0 s1+sA s2+sB+s5 s6+s8|" s3 {i}
movq s3, i(rp)           | s9' s4 s0 s1+sA s2+sB+s5 s6+s8|" {i+1}
movq $0, s7
adcx s7, s9              | s9 s4 s0 s1+sA s2+sB+s5 s6+s8|" {i+1}
mulx 24(up), s3, s7      | s9 s4 s0+s7 s1+sA+s3 s2+sB+s5 s6+s8|" {i+1}
movq s2, i+2(rp)         | s9 s4 s0+s7 s1+sA+s3 sB+s5| s6+s8|" {i+1}
movq s1, i+3(rp)         | s9 s4 s0+s7 sA+s3| sB+s5| s6+s8|" {i+1}
mulx 32(up), s1, s2      | s9 s4+s2 s0+s7+s1 sA+s3| sB+s5| s6+s8|" {i+1}
adox s8, s6              | s9 s4+s2 s0+s7+s1 sA+s3| sB+s5|" s6| {i+1}
adox sB, s5              | s9 s4+s2 s0+s7+s1 sA+s3|" s5| s6| {i+1}
movq i+1(rp), s8         | s9 s4+s2 s0+s7+s1 sA+s3|" s5| s6+s8 {i+1}
adcx s8, s6              | s9 s4+s2 s0+s7+s1 sA+s3|" s5|' s6 {i+1}
mulx 40(up), s8, sB      | s9+sB s4+s2+s8 s0+s7+s1 sA+s3|" s5|' s6 {i+1}
adox sA, s3              | s9+sB s4+s2+s8 s0+s7+s1" s3| s5|' s6 {i+1}
movq i+2(rp), sA         | s9+sB s4+s2+s8 s0+s7+s1" s3| s5+sA' s6 {i+1}
adcx sA, s5              | s9+sB s4+s2+s8 s0+s7+s1" s3|' s5 s6 {i+1}
adox s7, s0              | s9+sB s4+s2+s8" s0+s1 s3|' s5 s6 {i+1}
mulx 48(up), s7, sA      | sA s9+sB+s7 s4+s2+s8" s0+s1 s3|' s5 s6 {i+1}
movq i+3(rp), dd         | sA s9+sB+s7 s4+s2+s8" s0+s1 s3+dd' s5 s6 {i+1}
adcx dd, s3              | sA s9+sB+s7 s4+s2+s8" s0+s1' s3 s5 s6 {i+1}
dd:=v[i+1]
adox s4, s2              | sA s9+sB+s7" s2+s8 s0+s1' s3 s5 s6 {i+1}
adcx s1, s0              | sA s9+sB+s7" s2+s8' s0 s3 s5 s6 {i+1}
'''

"""
old: s9 sB+sA+s4" s0+s8' s1 s2 s5 s7
new: sA s9+sB+s7" s2+s8' s0 s3 s5 s6
          0 1 2 3 4 5 6 7 8 9 A B          """
g_perm = '2 0 3 1 7 5 4 6 8 A B 9'

g_tail = '''
movq sA, dd              | dd s9+sB+s7" s2+s8' s0 s3 s5 s6 {i+1}
movq s6, i+1(rp)         | dd s9+sB+s7" s2+s8' s0 s3 s5 {i+2}
movq s5, i+2(rp)         | dd s9+sB+s7" s2+s8' s0 s3 {i+3}
movq s9, s5              | dd s5+sB+s7" s2+s8' s0 s3 {i+3}
movq s3, i+3(rp)         | dd s5+sB+s7" s2+s8' s0 {i+4}
movq s0, i+4(rp)         | dd" s5+s7 s2+s8' {i+5}
adox sB, s5
adcx s8, s2              | dd" s5+s7' s2 {i+5}
movq $0, s0
adox s0, dd              | dd s5+s7' s2 {i+5}
| TODO: special care for s7?
movq s2, i+5(rp)
adcx s7, s5              | dd' s5 {i+6}
movq s5, i+6(rp)
adcq $0, dd
movq dd, i+7(rp)
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P
import gen_mul7_t03 as E

def extract_v(i, t):
    if i < 7:
        return 'movq %s(up), %s' % ((7 + i) * 8, t)

g_v_patt = re.compile(r'(.+):=v\[(.+)]')
g_iplus_patt = re.compile(r'i\+(.+?)\b')
g_rp_patt = re.compile(r'\b([0-9]+)\b\(rp\)')
g_v_patt = re.compile(r'(.+):=v\[(.+)\]')
def evaluate_row(i, s):
    # evaluate i and i+smth
    m = g_iplus_patt.search(s)
    if m:
        s = s.replace(m.group(), '%s' % (int(m.group(1)) + i))
    s = re.sub(r'\bi\b', '%s' % i, s)

    # evaluate x(rp)
    m = g_rp_patt.search(s)
    if m:
        try:
            j = int(m.group(1))
            if j:
                s = s.replace(m.group(), '%s(rp)' % (8 * j))
            else:
                s = s.replace(m.group(), '(rp)')
        except:
            pass

    # evaluate y:=v[x]
    m = g_v_patt.match(s)
    if m:
        s = extract_v(int(m.group(2)), m.group(1))

    return s

def mul_add_code(i, jj, p):
    if i:
        rr = ['# mul_add %s' % i]
    else:
        rr = []

    for j in jj:
        k = evaluate_row(i, j)
        if k:
            rr.append(k)

    return [E.apply_s_permutation(x, p) for x in rr]

def cook_asm(o, code, var_map):
    xmm_save = P.save_registers_in_xmm(code, 9)

    P.insert_restore(code, xmm_save)
    code = '\n'.join(code)
    for k,v in xmm_save.items():
        code = code.replace('!restore ' + k, 'movq %s, %s' % (v, k))

    code = P.replace_symbolic_names_wr(code, var_map)

    comment = P.g_autogenerated_patt % os.path.basename(sys.argv[0])
    o.write(comment.replace('//', '#'))
    P.write_asm_procedure_header(o, P.guess_subroutine_name(sys.argv[1]))
    P.write_asm_inside(o, code + '\nretq')

def do_it(o, mul_01, muladd, tail, perm, var_map):
    p = list(range(12))
    code = mul_add_code(0, P.cutoff_comments(mul_01), p)
    mm = P.cutoff_comments(muladd)
    code += mul_add_code(2, mm, p)
    q = [int(x, 16) for x in perm.split(' ')]
    for i in range(3, 6):
        p = P.composition(p, q)
        code += mul_add_code(i, mm, p)
    mm += P.cutoff_comments(tail)
    p = P.composition(p, q)
    code += mul_add_code(6, mm, p)
    cook_asm(o, code, var_map)

if __name__ == '__main__':
    with open(sys.argv[1], 'wb') as g_out:
        do_it(g_out, g_mul_01, g_muladd, g_tail, g_perm, g_var_map)
