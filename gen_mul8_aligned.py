'''
8x8 multiplication targeting Ryzen. Uses aligned loads of v[] into xmm's.

96 ticks on Ryzen, 104-105 on Skylake

TODO: speed-up for Skylake using rsp as pointer to u[]

Ryzen seems to be ok with 'xchg s0, dd' when dd is not ready yet. Skylake seems to
 dislike it, but time loss is a fraction of tick (approximately 2/6).
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
movq dd, w0
and $0xF, dd
if extra: movq w0, x9
movq w0[0], dd
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

# TODO: g_mul_01 should be different for Broadwell and Zen
g_mul_01 = '''
mulx up[0], w0, w1        | w1 w0
mulx up[1], w2, w3        | w3 w1+w2 w0
mulx up[2], w4, w5        | w5 w3+w4 w1+w2 w0
mulx up[3], wA, wB        | wB w5+wA w3+w4 w1+w2 w0
movq w0, rp[0]            | wB w5+wA w3+w4 w1+w2 ..
mulx up[4], w0, w9        | w9 wB+w0 w5+wA w3+w4 w1+w2 ..
adcx w2, w1               | w9 wB+w0 w5+wA w3+w4' w1 ..
movq w1, rp[1]            | w9 wB+w0 w5+wA w3+w4' [2]
w1:=v[1]
mulx up[5], w2, w8        | w8 w9+w2 wB+w0 w5+wA w3+w4' [2] w1
adcx w4, w3               | w8 w9+w2 wB+w0 w5+wA' [3] w1
movq w3, rp[2]
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
ado2 rp[1], w1            | wA' w6 ^4 w2+w7 w0+wB+w4 w5+w8: w3+w9:" [2]
movq $0, w1
adcx w1, wA               | wA w6 ^4 w2+w7 w0+wB+w4 w5+w8: w3+w9:" [2]
| TODO: maybe sum w3+w9 right now?
movq w6, rp[5]            | wA ^5 ^4 w2+w7 w0+wB+w4 w5+w8: w3+w9:" [2]
mulx up[4], w1, w6        | wA ^5 ^4+w6 w2+w7+w1 w0+wB+w4 w5+w8: w3+w9:" [2]
adox w9, w3               | wA ^5 ^4+w6 w2+w7+w1 w0+wB+w4 w5+w8:" w3: [2]
w9:=v[2]                  | wA ^5 ^4+w6 w2+w7+w1 w0+wB+w4 w5+w8:" w3: [2] w9
|
| Replacing rp[6] with a xmm makes no difference on Skylake, slows down the
|  subroutine on Ryzen by 2 ticks
|
movq wA, rp[6]            | ^6 ^5 ^4+w6 w2+w7+w1 w0+wB+w4 w5+w8:" w3: [2] w9
adc2 rp[2], w3            | ^6 ^5 ^4+w6 w2+w7+w1 w0+wB+w4 w5+w8:"' [3] w9
adox w8, w5               | ^6 ^5 ^4+w6 w2+w7+w1 w0+wB+w4" w5:' [3] w9
mulx up[5], w3, w8        | ^6 ^5+w8 ^4+w6+w3 w2+w7+w1 w0+wB+w4" w5:' [3] w9
adox wB, w0               | ^6 ^5+w8 ^4+w6+w3 w2+w7+w1" w0+w4 w5:' [3] w9
mulx up[6], wA, wB        | ^6+wB ^5+w8+wA ^4+w6+w3 w2+w7+w1" w0+w4 w5:' [3] w9
adc2 rp[3], w5            | ^6+wB ^5+w8+wA ^4+w6+w3 w2+w7+w1" w0+w4' [4] w9
adox w7, w2               | ^6+wB ^5+w8+wA ^4+w6+w3" w2+w1 w0+w4' [4] w9
mulx up[7], w5, w7        | w7 ^6+wB+w5 ^5+w8+wA ^4+w6+w3" w2+w1 w0+w4' [4] w9
movq w9, dd               | w7 ^6+wB+w5 ^5+w8+wA ^4+w6+w3" w2+w1 w0+w4' [4]
adcx w4, w0               | w7 ^6+wB+w5 ^5+w8+wA ^4+w6+w3" w2+w1' w0 [4]
|
| Save sp into x8, use sp instead of up, use up instead of rp[4]. Result: no
|  difference on Skylake, 3 ticks slowdown on Ryzen
|
adox rp[4], w6            | w7 ^6+wB+w5 ^5+w8+wA" w6+w3 w2+w1' w0 [4]
adcx w2, w1               | w7 ^6+wB+w5 ^5+w8+wA" w6+w3' w1 w0 [4]
adox rp[5], w8            | w7 ^6+wB+w5" w8+wA w6+w3' w1 w0 [4]
movq rp[6], w2            | w7 w2+wB+w5" w8+wA w6+w3' w1 w0 [4]
'''

'''
i >= 2
multiplied by v[0], .. v[i-1]
data lies like that: s7 s2+sB+s5" s8+sA s6+s3' s1 s0 .. .. [i] dd=v[i]
'''

g_mul_2 = '''
                         | 9-10 ticks on Ryzen
                         | s7 s2+sB+s5" s8+sA s6+s3' s1 s0 [2] {i}
mulx up[0], s4, s9       | s7 s2+sB+s5" s8+sA s6+s3' s1 s0 s9: s4: {i}
adcx s3, s6              | s7 s2+sB+s5" s8+sA' s6 s1 s0 s9: s4: {i}
adox sB, s2              | s7" s2+s5 s8+sA' s6 s1 s0 s9: s4: {i}
mulx up[1], s3, sB       | s7" s2+s5 s8+sA' s6 s1 s0+sB s9+s3: s4: {i}
adcx sA, s8              | s7" s2+s5' s8 s6 s1 s0+sB s9+s3: s4: {i}
movq $0, sA
adox sA, s7              | s7 s2+s5' s8 s6 s1 s0+sB s9+s3: s4: {i} sA=0
adcx s5, s2              | s7' s2 s8 s6 s1 s0+sB s9+s3: s4: {i} sA=0
ado2 rp[i], s4           | s7' s2 s8 s6 s1 s0+sB s9+s3:" {i+1} sA=0
mulx up[2], s4, s5       | s7' s2 s8 s6 s1+s5 s0+sB+s4 s9+s3:" {i+1} sA=0
adcx sA, s7              | s7 s2 s8 s6 s1+s5 s0+sB+s4 s9+s3:" {i+1} sA=0
adox s9, s3              | s7 s2 s8 s6 s1+s5 s0+sB+s4" s3: {i+1} sA=0
mulx up[3], sA, s9       | s7 s2 s8 s6+s9 s1+s5+sA s0+sB+s4" s3: {i+1}
adc2 rp[i+1], s3         | s7 s2 s8 s6+s9 s1+s5+sA s0+sB+s4"' .. {i+1}
adox sB, s0              | s7 s2 s8 s6+s9 s1+s5+sA" s0+s4' .. {i+1}
mulx up[4], s3, sB       | s7 s2 s8+sB s6+s9+s3 s1+s5+sA" s0+s4' .. {i+1}
adcx s4, s0              | s7 s2 s8+sB s6+s9+s3 s1+s5+sA"' s0 .. {i+1}
adox s5, s1              | s7 s2 s8+sB s6+s9+s3" s1+sA' s0 .. {i+1}
|
| Save sp into a xmm, use sp instead of up, use up to extract v[i+1]. Result: no
|  difference on Skylake, loss of 4 ticks on Ryzen.
| Save sp into rp[], use sp instead of up, use up to extract v[i+1]. Result: 
|  loss of 2 ticks on Ryzen (when only muliplying by v[0..3]).
|
| Ryzen has problems with mulx sp[]? with saving/restoring sp?
|
mulx up[5], s4, s5       | s7 s2+s5 s8+sB+s4 s6+s9+s3" s1+sA' s0 .. {i+1}
| moving line below up brings no gain
movq s0, rp[i+2]         | s7 s2+s5 s8+sB+s4 s6+s9+s3" s1+sA' [2] {i+1}
s0:=v[i+1]               | s7 s2+s5 s8+sB+s4 s6+s9+s3" s1+sA' [2] {i+1} s0=v[i+1]
adcx s1, sA              | s7 s2+s5 s8+sB+s4 s6+s9+s3"' sA [2] {i+1} s0=v[i+1]
adox s9, s6              | s7 s2+s5 s8+sB+s4" s6+s3' sA [2] {i+1} s0=v[i+1]
mulx up[6], s1, s9       | s7+s9 s2+s5+s1 s8+sB+s4" s6+s3' sA [2] {i+1} s0=v[i+1]
adcx s3, s6              | s7+s9 s2+s5+s1 s8+sB+s4"' s6 sA [2] {i+1} s0=v[i+1]
adox sB, s8              | s7+s9 s2+s5+s1" s8+s4' s6 sA [2] {i+1} s0=v[i+1]
mulx up[7], s3, sB       | sB s7+s9+s3 s2+s5+s1" s8+s4' s6 sA [2] {i+1} s0=v[i+1]
movq s0, dd
adox s5, s2              | sB s7+s9+s3" s2+s1 s8+s4' s6 sA [2] {i+1} s0=v[i+1]
'''

"""
old s7 s2+sB+s5" s8+sA s6+s3' s1 s0
new sB s7+s9+s3" s2+s1 s8+s4' s6 sA
          0 1 2 3 4 5 6 7 8 9 A B                    """
g_perm = 'A 6 7 4 0 3 8 B 2 5 1 9'   # can swap 0 and 5

g_tail_noextra = '''
                         | s7+s9 s2+s5+s1" s8+s4' s6 sA {i+3}
mulx up[7], s3, dd       | dd s7+s9+s3 s2+s5+s1" s8+s4' s6 sA {i+3}
adox s5, s2              | dd s7+s9+s3" s2+s1 s8+s4' s6 sA {i+3}
movq sA, rp[i+3]         | dd s7+s9+s3" s2+s1 s8+s4' s6 {i+4}
adcx s4, s8              | dd s7+s9+s3" s2+s1' s8 s6 {i+4}
movq s6, rp[i+4]         | dd s7+s9+s3" s2+s1' s8 {i+5}
adox s9, s7              | dd" s7+s3 s2+s1' s8 {i+5}
movq s8, rp[i+5]         | dd" s7+s3 s2+s1' {i+6}
movq $0, s8
adcx s1, s2              | dd" s7+s3' s2 {i+6}
adox s8, dd              | dd s7+s3' s2 {i+6}
movq s2, rp[i+6]         | dd s7+s3' {i+7}
adcx s3, s7              | dd' s7 {i+7}
movq s7, rp[i+7]
adcx s8, dd
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
g_ad2_patt = re.compile(r'(ad[co])2 (.+), (.+)')
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

    m = g_ad2_patt.match(s)
    if m:
        return \
                [
                    '%sx %s, %s' % (m.group(1), m.group(2), m.group(3)),
                    'movq %s, %s' % (m.group(3), m.group(2))
                ]

    return [s]

def chew_code(src, i, extra, aligned, p):
    if not isinstance(src, list):
        src = P.cutoff_comments(src)

    if i:
        rr = ['# mul_add %s' % i]
    else:
        rr = []

    for j in src:
        for k in evaluate_row(j, i, extra, aligned):
            if k:
                rr.append(k)

    if not p:
        return rr
    re = []
    for x in rr:
        if x[0] == '#':
            re.append(x)
        else:
            re.append(E.apply_s_permutation(x, p))
    return re

def form_tail(ss, extra):
    if extra:
        assert 0
    else:
        return ss[:-3] + P.cutoff_comments(g_tail_noextra)

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

def do_it(o, extra):
    code = chew_code(g_preamble, 0, extra, None, None)
    code += alignment_code(8, extra)
    code += alignment_code(0, extra)
    P.cook_asm(o, code, g_var_map, True)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        show_postcondition()
        sys.exit(0)

    g_extra = sys.argv[1][-3:] == '.ss'
    with open(sys.argv[1], 'wb') as g_out:
        do_it(g_out, g_extra)
