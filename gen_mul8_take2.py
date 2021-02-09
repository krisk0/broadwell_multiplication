'''
123 ticks on Broadwell, 112 on Ryzen
'''

"""
      rdi -< rp
      rsi -< up
      rdx -< vp

rbp rbx r12 r13 r14 r15
wB  wA  w9  w8  w7  w6    -- saved

rax r8  r9  r10 r11 rcx rsi rdi rdx
w0  w1  w2  w3  w4  w5  up  rp  dd
"""

g_var_map = 'rp,rdi up,rsi wB,rbp wA,rbx w9,r12 w8,r13 w7,r14 w6,r15 ' + \
    'w0,rax w1,r8 w2,r9 w3,r10 w4,r11 w5,rcx dd,rdx ' + \
    ' '.join(['x%X,xmm%s' % (i,i) for i in range(16)])

"""
xmm usage:
A-F save w6..wB
9 save up
9 vp[9]     (extra result)
8 vp[A]     (extra result)
0-4 v[]

extra result:
up[8..A] w0 w1 w2
vp[8..A] x9 x8 dd
"""

g_preamble = '''
vzeroupper
!save wB
movq dd, w0
and $0xF, dd
if extra: movq w0, x9
movq (w0), dd
jz align0
movdqa w0[1], x0
movdqa w0[3], x1
movdqa w0[5], x2
movq w0[7], x3
'''

g_load_0 = '''
align0:
movq w0[1], x0
movdqa w0[2], x1
movdqa w0[4], x2
movdqa w0[6], x3
'''

g_mul_01 = '''
mulx up[0], w0, w1        | w1 w0
mulx up[1], w2, w3        | w3 w1+w2 w0
!save wA
mulx up[2], w4, w5        | w5 w3+w4 w1+w2 w0
mulx up[3], wA, wB        | wB w5+wA w3+w4 w1+w2 w0
!save w9
movq w0, rp[0]            | wB w5+wA w3+w4 w1+w2 ..
mulx up[4], w0, w9        | w9 wB+w0 w5+wA w3+w4 w1+w2 ..
!save w8
adcx w2, w1               | w9 wB+w0 w5+wA w3+w4' w1 ..
movq w1, rp[1]            | w9 wB+w0 w5+wA w3+w4' [2]
!save w7
w1:=v[1]
mulx up[5], w2, w8        | w8 w9+w2 wB+w0 w5+wA w3+w4' [2] w1
adcx w4, w3               | w8 w9+w2 wB+w0 w5+wA' [3] w1
movq w3, rp[2]
!save w6
mulx up[6], w4, w6        | w6 w8+w4 w9+w2 wB+w0 w5+wA' [3] w1
adcx wA, w5               | w6 w8+w4 w9+w2 wB+w0' w5 [3] w1
mulx up[7], w7, wA        | wA w6+w7 w8+w4 w9+w2 wB+w0' w5 [3] w1
movq w1, dd               | wA w6+w7 w8+w4 w9+w2 wB+w0' w5 [3]
adcx wB, w0               | wA w6+w7 w8+w4 w9+w2' w0 w5 [3]
mulx up[0], w1, w3        | wA w6+w7 w8+w4 w9+w2' w0 w5 w3: w1: ..
adcx w9, w2               | wA w6+w7 w8+w4' w2 w0 w5 w3: w1: ..
movq w5, rp[3]            | wA w6+w7 w8+w4' w2 w0 .. w3: w1: ..
mulx up[1], w9, w5        | wA w6+w7 w8+w4' w2 w0 w5: w3+w9: w1: ..
adcx w8, w4               | wA w6+w7' w4 w2 w0 w5: w3+w9: w1: ..
mulx up[2], w8, wB        | wA w6+w7' w4 w2 w0+wB w5+w8: w3+w9: w1: ..
adcx w7, w6               | wA' w6 w4 w2 w0+wB w5+w8: w3+w9: w1: ..
movq w4, rp[4]            | wA' w6 ^4 w2 w0+wB w5+w8: w3+w9: w1: ..
mulx up[3], w4, w7        | wA' w6 ^4 w2+w7 w0+wB+w4 w5+w8: w3+w9: w1: ..
adox rp[1], w1            | wA' w6 ^4 w2+w7 w0+wB+w4 w5+w8: w3+w9:" w1 ..
movq w1, rp[1]            | wA' w6 ^4 w2+w7 w0+wB+w4 w5+w8: w3+w9:" [2]
movq $0, w1
adcx w1, wA               | wA w6 ^4 w2+w7 w0+wB+w4 w5+w8: w3+w9:" [2]
| TODO: maybe sum w3+w9 right now?
movq w6, rp[5]            | wA ^5 ^4 w2+w7 w0+wB+w4 w5+w8: w3+w9:" [2]
mulx up[4], w1, w6        | wA ^5 ^4+w6 w2+w7+w1 w0+wB+w4 w5+w8: w3+w9:" [2]
adox w9, w3               | wA ^5 ^4+w6 w2+w7+w1 w0+wB+w4 w5+w8:" w3: [2]
w9:=v[2]                  | wA ^5 ^4+w6 w2+w7+w1 w0+wB+w4 w5+w8:" w3: [2] w9
movq wA, rp[6]            | ^6 ^5 ^4+w6 w2+w7+w1 w0+wB+w4 w5+w8:" w3: [2] w9
adcx rp[2], w3            | ^6 ^5 ^4+w6 w2+w7+w1 w0+wB+w4 w5+w8:"' w3 [2] w9
movq w3, rp[2]            | ^6 ^5 ^4+w6 w2+w7+w1 w0+wB+w4 w5+w8:"' [3] w9
adox w8, w5               | ^6 ^5 ^4+w6 w2+w7+w1 w0+wB+w4" w5:' [3] w9
mulx up[5], w3, w8        | ^6 ^5+w8 ^4+w6+w3 w2+w7+w1 w0+wB+w4" w5:' [3] w9
adox wB, w0               | ^6 ^5+w8 ^4+w6+w3 w2+w7+w1" w0+w4 w5:' [3] w9
mulx up[6], wA, wB        | ^6+wB ^5+w8+wA ^4+w6+w3 w2+w7+w1" w0+w4 w5:' [3] w9
adcx rp[3], w5            | ^6+wB ^5+w8+wA ^4+w6+w3 w2+w7+w1" w0+w4' w5 [3] w9
movq w5, rp[3]            | ^6+wB ^5+w8+wA ^4+w6+w3 w2+w7+w1" w0+w4' [4] w9
adox w7, w2               | ^6+wB ^5+w8+wA ^4+w6+w3" w2+w1 w0+w4' [4] w9
mulx up[7], w5, w7        | w7 ^6+wB+w5 ^5+w8+wA ^4+w6+w3" w2+w1 w0+w4' [4] w9
movq w9, dd               | w7 ^6+wB+w5 ^5+w8+wA ^4+w6+w3" w2+w1 w0+w4' [4]
adcx w4, w0               | w7 ^6+wB+w5 ^5+w8+wA ^4+w6+w3" w2+w1' w0 [4]
adox rp[4], w6            | w7 ^6+wB+w5 ^5+w8+wA" w6+w3 w2+w1' w0 [4]
'''

'''
i >= 2
multiplied by v[0], .. v[i-1]
data lies like that:   s7 ^4+sB+s5 ^3+s8+sA" s6+s3 s2+s1' s0 .. [i+1] dd=v[i]
desired postcondition: -- ^5+--+-- ^4+--+--  --+-- --+--' .. .. [i+1] dd=v[i+1]
'''

g_mul_2 = '''
                          | s7 ^4+sB+s5 ^3+s8+sA" s6+s3 s2+s1' s0 .. .. [i]
mulx up[0], s4, s9        | s7 ^4+sB+s5 ^3+s8+sA" s6+s3' s1 s0 s9: s4: [i]
adcx s2, s1               | s7 ^4+sB+s5 ^3+s8+sA" s6+s3' s1 s0 s9: s4: [i]
adox rp[i+3], s8          | s7 ^4+sB+s5" s8+sA s6+s3' s1 s0 s9: s4: [i]
movq s8, rp[i+3]          | s7 ^4+sB+s5" ^3+sA s6+s3' s1 s0 s9: s4: [i]
mulx up[1], s2, s8        | s7 ^4+sB+s5" ^3+sA s6+s3' s1 s0+s8 s9+s2: s4: [i]
adcx s6, s3               | s7 ^4+sB+s5" ^3+sA' s3 s1 s0+s8 s9+s2: s4: [i]
adox rp[i+4], sB          | s7" sB+s5 ^3+sA' s3 s1 s0+s8 s9+s2: s4: [i]
movq sB, rp[i+4]          | s7" ^4+s5 ^3+sA' s3 s1 s0+s8 s9+s2: s4: [i]
mulx up[2], s6, sB        | s7" ^4+s5 ^3+sA' s3 s1+sB s0+s8+s6 s9+s2: s4: [i]
adcx rp[i+3], sA          | s7" ^4+s5' sA s3 s1+sB s0+s8+s6 s9+s2: s4: [i]
movq sA, rp[i+3]          | s7" ^4+s5' ^3 s3 s1+sB s0+s8+s6 s9+s2: s4: [i]
movq $0, sA
adox sA, s7               | s7 ^4+s5' ^3 s3 s1+sB s0+s8+s6 s9+s2: s4: [i]
movq s3, rp[i+2]          | s7 ^4+s5' ^3 ^2 s1+sB s0+s8+s6 s9+s2: s4: [i]
mulx up[3], s3, sA        | s7 ^4+s5' ^3 ^2+sA s1+sB+s3 s0+s8+s6 s9+s2: s4: [i]
adcx rp[i+4], s5          | s7' s5 ^3 ^2+sA s1+sB+s3 s0+s8+s6 s9+s2: s4: [i]
adox rp[i], s4            | s7' s5 ^3 ^2+sA s1+sB+s3 s0+s8+s6 s9+s2:" s4 [i]
movq s4, rp[i]            | s7' s5 ^3 ^2+sA s1+sB+s3 s0+s8+s6 s9+s2:" [i+1]
movq $0, s4
adcx s4, s7               | s7 s5 ^3 ^2+sA s1+sB+s3 s0+s8+s6 s9+s2:" [i+1]
movq s7, rp[i+5]          | ^5 s5 ^3 ^2+sA s1+sB+s3 s0+s8+s6 s9+s2:" [i+1]
mulx up[4], s4, s7        | ^5 s5 ^3+s7 ^2+sA+s4 s1+sB+s3 s0+s8+s6 s9+s2:" [i+1]
adox s9, s2               | ^5 s5 ^3+s7 ^2+sA+s4 s1+sB+s3 s0+s8+s6" s2: [i+1]
movq s5, rp[i+4]
s5:=v[i+1]
adox s8, s0               | ^5 ^4 ^3+s7 ^2+sA+s4 s1+sB+s3" s0+s6 s2: [i+1] s5
mulx up[5], s8, s9        | ^5 ^4+s9 ^3+s7+s8 ^2+sA+s4 s1+sB+s3" s0+s6 s2: [i+1] s5
adcx rp[i+1], s2          | ^5 ^4+s9 ^3+s7+s8 ^2+sA+s4 s1+sB+s3" s0+s6' s2 [i+1] s5
movq s2, rp[i+1]          | ^5 ^4+s9 ^3+s7+s8 ^2+sA+s4 s1+sB+s3" s0+s6' .. [i+1] s5
adox sB, s1               | ^5 ^4+s9 ^3+s7+s8 ^2+sA+s4" s1+s3 s0+s6' .. [i+1] s5
mulx up[6], s2, sB        | ^5+sB ^4+s9+s2 ^3+s7+s8 ^2+sA+s4" s1+s3 s0+s6' [i+2] s5
adcx s6, s0               | ^5+sB ^4+s9+s2 ^3+s7+s8 ^2+sA+s4" s1+s3' s0 [i+2] s5
adox rp[i+2], sA          | ^5+sB ^4+s9+s2 ^3+s7+s8" sA+s4 s1+s3' s0 [i+2] s5
movq s0, rp[i+2]          | ^5+sB ^4+s9+s2 ^3+s7+s8" sA+s4 s1+s3' .. .. [i+1] s5
mulx up[7], s0, s6        | s6 ^5+sB+s0 ^4+s9+s2 ^3+s7+s8" sA+s4 s1+s3' [i+3] s5
movq s5, dd               | s6 ^5+sB+s0 ^4+s9+s2 ^3+s7+s8" sA+s4 s1+s3' .. .. [i+1]
adcx s3, s1               | s6 ^5+sB+s0 ^4+s9+s2 ^3+s7+s8" sA+s4' s1 .. .. [i+1]
adox rp[i+3], s7          | s6 ^5+sB+s0 ^4+s9+s2" s7+s8 sA+s4' s1 .. .. [i+1]
'''

"""
old s7 ^4+sB+s5 ^3+s8+sA" s6+s3 s2+s1' s0 .. .. [i]
new s6 ^5+sB+s0 ^4+s9+s2" s7+s8 sA+s4' s1 .. .. [i+1]
          0 1 2 3 4 5 6 7 8 9 A B                    """
g_perm = '1 4 A 8 3 0 7 6 9 5 2 B'   # can swap 3 and 5

g_tail_noextra = '''
| adox s9, s2             | ^5 s5 ^3+s7 ^2+sA+s4 s1+sB+s3 s0+s8+s6" s2: [i+1]
adox s8, s0               | ^5 s5 ^3+s7 ^2+sA+s4 s1+sB+s3" s0+s6 s2: [i+1]
mulx up[5], s8, s9        | ^5 s5+s9 ^3+s7+s8 ^2+sA+s4 s1+sB+s3" s0+s6 s2: [i+1]
adcx rp[i+1], s2          | ^5 s5+s9 ^3+s7+s8 ^2+sA+s4 s1+sB+s3" s0+s6' s2 [i+1]
movq s2, rp[i+1]          | ^5 s5+s9 ^3+s7+s8 ^2+sA+s4 s1+sB+s3" s0+s6' [i+2]
adox sB, s1               | ^5 s5+s9 ^3+s7+s8 ^2+sA+s4" s1+s3 s0+s6' [i+2]
mulx up[6], s2, sB        | ^5+sB s5+s9+s2 ^3+s7+s8 ^2+sA+s4" s1+s3 s0+s6' [i+2]
adcx s6, s0
adox rp[i+2], sA          | ^5+sB s5+s9+s2 ^3+s7+s8" sA+s4 s1+s3' s0 [i+2]
movq s0, rp[i+2]          | ^5+sB s5+s9+s2 ^3+s7+s8" sA+s4 s1+s3' [i+3]
adcx s3, s1               | ^5+sB s5+s9+s2 ^3+s7+s8" sA+s4' s1 [i+3]
movq sB, s3               | ^5+s3 s5+s9+s2 ^3+s7+s8" sA+s4' s1 [i+3]
adox rp[i+3], s7          | ^5+s3 s5+s9+s2" s7+s8 sA+s4' s1 [i+3]
movq s1, rp[i+3]          | ^5+s3 s5+s9+s2" s7+s8 sA+s4' [i+4]
mulx up[7], s1, dd        | dd ^5+s3+s1 s5+s9+s2" s7+s8 sA+s4' [i+4]
adcx sA, s4               | dd ^5+s3+s1 s5+s9+s2" s7+s8' s4 [i+4]
movq s4, rp[i+4]          | dd ^5+s3+s1 s5+s9+s2" s7+s8' [i+5]
adox s5, s9               | dd ^5+s3+s1" s9+s2 s7+s8' [i+5]
adcx s8, s7               | dd ^5+s3+s1" s9+s2' s7 [i+5]
adox rp[i+5], s3          | dd" s3+s1 s9+s2' s7 [i+5]
movq s7, rp[i+5]          | dd" s3+s1 s9+s2' [i+6]
adcx s2, s9               | dd" s3+s1' s9 [i+6]
movq s9, rp[i+6]          | dd" s3+s1' [i+7]
movq $0, sA
adox sA, dd               | dd s3+s1' [i+7]
adcx s3, s1               | dd' s3 [i+7]
movq s1, rp[i+7]          | dd' [i+8]
adcx sA, dd
movq dd, rp[i+8]
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P
import gen_mul7_t03 as E
import gen_mul11 as C

def show_postcondition():
    p = list(range(0xB + 1))
    q = [int(x, 16) for x in g_perm.split(' ')]
    b = '''s7 ^4+sB+s5 ^3+s8+sA" s6+s3 s2+s1' s0'''
    l = '''s6 ^5+sB+s0 ^4+s9+s2" s7+s8 sA+s4' s1'''
    for i in range(2, 8):
        print 'i=%X pre' % i, E.apply_s_permutation(b, p)
        if i < 7:
            print 'i=%X pst' % i, E.apply_s_permutation(l, p)
        else:
            k = ' '.join(['s%X' % j for j in range(0xB + 1)])
            print k, '\n' + E.apply_s_permutation(k, p)
        p = P.composition(p, q)

def extract_v(i, aligned, tgt):
    if (i <= 0) or (i > 7) or (aligned == None):
        return
    if not aligned:
        i -= 1
        # 0,1 -> x0,    2,3 -> x1
        if i & 1:
            return 'pextrq $0x1, x%s, %s' % (i / 2, tgt)
        else:
            return 'movq x%s, %s' % (i / 2, tgt)
    if i == 1:
        return 'movq x0, ' + tgt
    i -= 2          # 0,1 -> x1,    2,3 -> x2
    j = i / 2 + 1
    if i & 1:
        return 'pextrq $0x1, x%s, %s' % (j, tgt)
    else:
        return 'movq x%s, %s' % (j, tgt)

def evaluate_if(s, dd, cond, stmt):
    yes = True
    if cond[0] == '!':
        yes = False
        cond = cond[1:]
    try:
        how = dd[cond]
    except:
        return s
    if how == yes:
        return stmt
    return ''

g_array_patt = re.compile(r'\b([a-zA-Z0-9]+)\b\[(.+?)\]')
g_v_patt = re.compile(r'(.+):=v\[(.+)\]')
g_iplus_patt = re.compile(r'i\+(.+?)\b')
g_if_patt = re.compile(r'if (.+): (.+)')
def evaluate_row(s, i, extra, aligned):
    m = g_if_patt.match(s)
    if m:
        s = evaluate_if(s, {'extra': extra}, m.group(1), m.group(2))
    
    m = g_iplus_patt.search(s)
    if m:
        s = s.replace(m.group(), '%s' % (int(m.group(1)) + i))
    s = re.sub(r'\bi\b', '%s' % i, s)

    m = g_v_patt.match(s)
    if m:
        return [extract_v(int(m.group(2)), aligned, m.group(1))]
    
    m = g_array_patt.search(s)
    if m:
        j = int(m.group(2))
        if j == 0:
            s = s.replace(m.group(), '(%s)' % m.group(1))
        else:
            s = s.replace(m.group(), '%s(%s)' % (j * 8, m.group(1)))

    return [s]

def chew_code(src, i, extra, aligned, p):
    if not isinstance(src, list):
        src = P.cutoff_comments(src)

    if i:
        rr = ['# mul_add %s' % i]
    else:
        rr = []

    for j in src:
        k = evaluate_row(j, i, extra, aligned)
        if k and (k != [None]) and (k != ['']):
            rr += k

    if p:
        re = []
        for x in rr:
            if x[0] == '#':
                re.append(x)
            else:
                re.append(E.apply_s_permutation(x, p))
        return re
    return rr

def form_tail(ss, extra):
    if extra:
        assert 0
    else:
        i = ss.index('adox s9, s2') + 1
        return ss[:i] + P.cutoff_comments(g_tail_noextra)

def alignment_code(alignment, extra):
    if alignment:
        code = []
    else:
        code = chew_code(g_load_0, None, extra, True, None)
    
    code += chew_code(g_mul_01, 0, extra, not alignment, None)
    m2 = P.cutoff_comments(g_mul_2)
    m7 = form_tail(m2, extra)
    p = list(range(0xB + 1))
    q = [int(i, 16) for i in g_perm.split(' ')]
    # TODO: jump to tail earlier, to reduce code size
    for i in range(2, 7):
        code += chew_code(m2, i, extra, not alignment, p)
        p = P.composition(p, q)
    if alignment:
        code.append('jmp tail')
    else:
        code.append('tail:')
        code += chew_code(m7, 7, extra, None, p)
    return code

g_save_patt = re.compile(r'\!save (.+)')
def insert_save(cc, dd):
    for i in range(len(cc)):
        m = g_save_patt.match(cc[i])
        if m:
            m = m.group(1)
            try:
                r = dd[m]
                cc[i] = 'movq %s, %s' % (m, r)
            except:
                pass

def do_it(o, extra):
    code = chew_code(g_preamble, 0, extra, None, None)
    code += alignment_code(8, extra)
    xmm_save = P.save_registers_in_xmm(code, 15)
    code += alignment_code(0, extra)
    P.insert_restore(code, xmm_save)
    # TODO: do without insert_save()
    insert_save(code, xmm_save)
    C.cook_asm(o, code, g_var_map)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        show_postcondition()
        sys.exit(0)

    g_extra = sys.argv[1][-3:] == '.ss'
    with open(sys.argv[1], 'wb') as g_out:
        do_it(g_out, g_extra)
