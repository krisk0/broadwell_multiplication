'''
void addmul_8x3(mp_ptr rp, mp_srcptr up, mp_srcptr vp);

Multiplies 8-limb number u by 3-limb number v; adds result to 14-limb number r;
 puts result in-place onto rp. Summation is done modulo 2**(14*64).

r' := r + u * v

Take 0: not caching u.

Code targets Broadwell and Ryzen. Uses rsp[-11]..rsp[-1] as scratch:
 sc[x] = rsp[x-11]
'''

g_code = '''
!save w6
movq dd[1], t0
movq dd[2], t1
!save w7
movq dd[0], dd
xor w0, w0
movq rp, t2
mulx up[0], w0, w1         | w1 w0
mulx up[1], w2, w3         | w3 w1+w2 w0
!save w8
mulx up[2], w4, w5         | w5 w3+w4 w1+w2 w0
mulx up[3], w6, w7         | w7 w5+w6 w3+w4 w1+w2 w0
!save w9
movq w0, sc[0]             | w7 w5+w6 w3+w4 w1+w2 [1]
mulx up[4], w0, w8         | w8 w7+w0 w5+w6 w3+w4 w1+w2 [1]
!save wA
movq t0, w9                | w8 w7+w0 w5+w6 w3+w4 w1+w2 [1] w9=v[1]
adcx w2, w1                | w8 w7+w0 w5+w6 w3+w4' w1 [1] w9=v[1]
movq w1, sc[1]             | w8 w7+w0 w5+w6 w3+w4' [2] w9=v[1]
!save wB
mulx up[5], w1, w2         | w2 w8+w1 w7+w0 w5+w6 w3+w4' [2] w9=v[1]
adcx w4, w3                | w2 w8+w1 w7+w0 w5+w6' w3 [2] w9=v[1]
movq w3, sc[2]             | w2 w8+w1 w7+w0 w5+w6' [3] w9=v[1]
mulx up[6], w3, w4         | w4 w2+w3 w8+w1 w7+w0 w5+w6' [3] w9=v[1]
adcx w6, w5                | w4 w2+w3 w8+w1 w7+w0' w5 [3] w9=v[1]
movq w5, sc[3]             | w4 w2+w3 w8+w1 w7+w0' [4] w9=v[1]
mulx up[7], w5, w6         | w6 w4+w5 w2+w3 w8+w1 w7+w0' [4] w9=v[1]
movq w9, dd                | w6 w4+w5 w2+w3 w8+w1 w7+w0' [4]
mulx up[0], w9, wA         | w6 w4+w5 w2+w3 w8+w1 w7+w0' .. wA| w9| [1]
adcx w7, w0                | w6 w4+w5 w2+w3 w8+w1' w0 .. wA| w9| [1]
mulx up[1], w7, wB         | w6 w4+w5 w2+w3 w8+w1' w0 wB| wA+w7| w9| [1]
adcx w8, w1                | w6 w4+w5 w2+w3' w1 w0 wB| wA+w7| w9| [1]
mulx up[2], w8, rp         | w6 w4+w5 w2+w3' w1 w0+rp wB+w8| wA+w7| w9| [1]
adcx w3, w2                | w6 w4+w5' w2 w1 w0+rp wB+w8| wA+w7| w9| [1]
movq w0, sc[4]             | w6 w4+w5' w2 w1 rp| wB+w8| wA+w7| w9| [1]
mulx up[3], w0, w3         | w6 w4+w5' w2 w1+w3 rp+w0| wB+w8| wA+w7| w9| [1]
movq w5, sc[5]
ado3(sc[1], w9, w5)        | w6 w4+..' w2 w1+w3 rp+w0| wB+w8| wA+w7|" [2]
movq sc[5], w5             | w6 w4+w5' w2 w1+w3 rp+w0| wB+w8| wA+w7|" [2]
adcx w5, w4                | w6' w4 w2 w1+w3 rp+w0| wB+w8| wA+w7|" [2]
mulx up[4], w5, w9         | w6' w4 w2+w9 w1+w3+w5 rp+w0| wB+w8| wA+w7|" [2]
adox wA, w7                | w6' w4 w2+w9 w1+w3+w5 rp+w0| wB+w8|" w7| [2]
movq $0, wA
adcx wA, w6                | w6 w4 w2+w9 w1+w3+w5 rp+w0| wB+w8|" w7| [2]
adox wB, w8                | w6 w4 w2+w9 w1+w3+w5 rp+w0|" w8| w7| [2]
movq sc[2], wA             | w6 w4 w2+w9 w1+w3+w5 rp+w0|" w8| w7+wA [2]
adcx wA, w7                | w6 w4 w2+w9 w1+w3+w5 rp+w0|" w8|' w7 [2]
movq t1, wA                | w6 w4 w2+w9 w1+w3+w5 rp+w0|" w8|' w7 [2] wA=v[2]
movq w7, sc[2]             | w6 w4 w2+w9 w1+w3+w5 rp+w0|" w8|' [3] wA=v[2]
mulx up[5], w7, wB         | w6 w4+wB w2+w9+w7 w1+w3+w5 rp+w0|" w8|' [3] wA=v[2]
adox w0, rp                | w6 w4+wB w2+w9+w7 w1+w3+w5" rp| w8|' [3] wA=v[2]
movq sc[3], w0             | w6 w4+wB w2+w9+w7 w1+w3+w5" rp| w8+w0' [3] wA=v[2]
adcx w8, w0                | w6 w4+wB w2+w9+w7 w1+w3+w5" rp|' w0 [3] wA=v[2]
movq w0, sc[3]             | w6 w4+wB w2+w9+w7 w1+w3+w5" rp|' [4] wA=v[2]
mulx up[6], w0, w8         | w6+w8 w4+wB+w0 w2+w9+w7 w1+w3+w5" rp|' [4] wA=v[2]
adox w3, w1                | w6+w8 w4+wB+w0 w2+w9+w7" w1+w5 rp|' [4] wA=v[2]
movq sc[4], w3             | w6+w8 w4+wB+w0 w2+w9+w7" w1+w5 rp+w3' [4] wA=v[2]
adcx w3, rp                | w6+w8 w4+wB+w0 w2+w9+w7" w1+w5' rp [4] wA=v[2]
movq rp, sc[4]             | w6+w8 w4+wB+w0 w2+w9+w7" w1+w5' [5] wA=v[2]
mulx up[7], rp, w3         | w3 w6+w8+rp w4+wB+w0 w2+w9+w7" w1+w5' [5] wA=v[2]
movq wA, dd                | w3 w6+w8+rp w4+wB+w0 w2+w9+w7" w1+w5' [5]
adox w9, w2                | w3 w6+w8+rp w4+wB+w0" w2+w7 w1+w5' [5]
mulx up[0], w9, wA         | w3 w6+w8+rp w4+wB+w0" w2+w7 w1+w5' .. wA| w9| [2]
adcx w5, w1                | w3 w6+w8+rp w4+wB+w0" w2+w7' w1 .. wA| w9| [2]
adox wB, w4                | w3 w6+w8+rp" w4+w0 w2+w7' w1 .. wA| w9| [2]
mulx up[1], w5, wB         | w3 w6+w8+rp" w4+w0 w2+w7' w1 wB| wA+w5| w9| [2]
adcx w7, w2                | w3 w6+w8+rp" w4+w0' w2 w1 wB| wA+w5| w9| [2]
adox w8, w6                | w3" w6+rp w4+w0' w2 w1 wB| wA+w5| w9| [2]
mulx up[2], w7, w8         | w3" w6+rp w4+w0' w2 w1+w8 wB+w7| wA+w5| w9| [2]
adcx w4, w0                | w3" w6+rp' w0 w2 w1+w8 wB+w7| wA+w5| w9| [2]
movq $0, w4
adox w4, w3                | w3 w6+rp' w0 w2 w1+w8 wB+w7| wA+w5| w9| [2]
adcx w6, rp                | w3' rp w0 w2 w1+w8 wB+w7| wA+w5| w9| [2]
movq sc[2], w6             | w3' rp w0 w2 w1+w8 wB+w7| wA+w5| w9+w6 [2]
adox w9, w6                | w3' rp w0 w2 w1+w8 wB+w7| wA+w5|" w6 [2]
mulx up[3], w4, w9         | w3' rp w0 w2+w9 w1+w8+w4 wB+w7| wA+w5|" w6 [2]
movq w6, sc[2]
movq $0, w6                | w3' rp w0 w2+w9 w1+w8+w4 wB+w7| wA+w5|" [3]
adcx w6, w3                | w3 rp w0 w2+w9 w1+w8+w4 wB+w7| wA+w5|" [3]
adox wA, w5                | w3 rp w0 w2+w9 w1+w8+w4 wB+w7|" w5| [3]
mulx up[4], w6, wA         | w3 rp w0+wA w2+w9+w6 w1+w8+w4 wB+w7|" w5| [3]
movq w1, sc[5]             | w3 rp w0+wA w2+w9+w6 w8+w4| wB+w7|" w5| [3]
movq sc[3], w1             | w3 rp w0+wA w2+w9+w6 w8+w4| wB+w7|" w5+w1 [3]
adcx w5, w1                | w3 rp w0+wA w2+w9+w6 w8+w4| wB+w7|"' w1 [3]
movq w1, sc[3]             | w3 rp w0+wA w2+w9+w6 w8+w4| wB+w7|"' [4]
mulx up[5], w1, w5         | w3 rp+w5 w0+wA+w1 w2+w9+w6 w8+w4| wB+w7|"' [4]
adox wB, w7                | w3 rp+w5 w0+wA+w1 w2+w9+w6 w8+w4|" w7|' [4]
adox w8, w4                | w3 rp+w5 w0+wA+w1 w2+w9+w6" w4| w7|' [4]
movq sc[4], wB             | w3 rp+w5 w0+wA+w1 w2+w9+w6" w4| w7+wB' [4]
adcx wB, w7                | w3 rp+w5 w0+wA+w1 w2+w9+w6" w4|' w7 [4]
mulx up[6], w8, wB         | w3+wB rp+w5+w8 w0+wA+w1 w2+w9+w6" w4|' w7 [4]
adox w9, w2                | w3+wB rp+w5+w8 w0+wA+w1" w2+w6 w4|' w7 [4]
movq sc[5], w9             | w3+wB rp+w5+w8 w0+wA+w1" w2+w6 w4+w9' w7 [4]
adcx w9, w4                | w3+wB rp+w5+w8 w0+wA+w1" w2+w6' w4 w7 [4]
mulx up[7], w9, dd         | dd w3+wB+w9 rp+w5+w8 w0+wA+w1" w2+w6' w4 w7 [4]
adox wA, w0                | dd w3+wB+w9 rp+w5+w8" w0+w1 w2+w6' w4 w7 [4]
movq t2, wA
adcx w6, w2                | dd w3+wB+w9 rp+w5+w8" w0+w1' w2 w4 w7 [4] wA=rp
adox w5, rp                | dd w3+wB+w9" rp+w8 w0+w1' w2 w4 w7 [4] wA=rp
movq sc[3], w6
movq sc[2], w5             | dd w3+wB+w9" rp+w8 w0+w1' w2 w4 w7 w6 w5 [2] wA=rp
adcx w1, w0                | dd w3+wB+w9" rp+w8' w0 w2 w4 w7 w6 w5 [2] wA=rp
movq sc[1], w1             | dd w3+wB+w9" rp+w8' w0 w2 w4 w7 w6 w5 w1 .. wA=rp
adox wB, w3                | dd" w3+w9 rp+w8' w0 w2 w4 w7 w6 w5 w1 .. wA=rp
movq sc[0], wB             | dd" w3+w9 rp+w8' w0 w2 w4 w7 w6 w5 w1 wB  wA=rp
adcx w8, rp                | dd" w3+w9' rp w0 w2 w4 w7 w6 w5 w1 wB  wA=rp
movq $0, w8
adox w8, dd                | dd| w3+w9'| rp| w0| w2| w4| w7| w6| w5| w1| wB|  wA=rp
movq wA[0], w8             | dd| w3+w9'| rp| w0| w2| w4| w7| w6| w5| w1| wB+w8  wA=rp
adcx w9, w3                | dd|' w3| rp| w0| w2| w4| w7| w6| w5| w1| wB+w8  wA=rp
adox wB, w8                | dd|' w3| rp| w0| w2| w4| w7| w6| w5| w1|" w8  wA=rp
movq w8, wA[0]             | dd|' w3| rp| w0| w2| w4| w7| w6| w5| w1|" [1]
movq $0, wB
adcx wB, dd                | dd| w3| rp| w0| w2| w4| w7| w6| w5|" [2]
ado3(wA[1], w1, wB)
movq wA, w1                | w1=rp
ado3(w1[2], w5, wB)        | dd| w3| rp| w0| w2| w4| w7| w6|" [3]
ado3(w1[3], w6, w5)        | dd| w3| rp| w0| w2| w4| w7|" [4]
ado3(w1[4], w7, w5)        | dd| w3| rp| w0| w2| w4|" [5]
ado3(w1[5], w4, w5)        | dd| w3| rp| w0| w2|" [6]
ado3(w1[6], w2, w5)        | dd| w3| rp| w0|" [7]
ado3(w1[7], w0, w5)        | dd| w3| rp|" [8]
ado3(w1[8], rp, w5)        | dd| w3|" [9]
movq $0, w0
ado3(w1[9], w3, w5)        | dd|" [10]
ado3(w1[10], dd, w5)
ado3(w1[11], w0, w5)       | sometimes carry goes far
ado3(w1[12], w0, w5)
ado3(w1[13], w0, w5)
'''

import re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P
import gen_mul7_2arg as S
import gen_mul7_t03 as E

g_array_patt = re.compile(r'\b(\S+)\b\[(.+)\]')
g_ado3_patt = re.compile(r'ado3\((.+), (.+), (.+)\)')
g_sc_patt = re.compile(r'sc\[(.+)\]')
def evaluate_row(s):
    m = g_ado3_patt.match(s)
    if m:
        return [\
                evaluate_row('movq %s, %s' % (m.group(1), m.group(3)))[0],\
                'adox %s, %s' % (m.group(2), m.group(3)),\
                evaluate_row('movq %s, %s' % (m.group(3), m.group(1)))[0]\
               ]
    
    m = g_sc_patt.search(s)
    if m:
        s = s.replace(m.group(), ('st[%s]' % (int(m.group(1)) - 11)))
    
    m = g_array_patt.search(s)
    if m:
        k = int(m.group(2))
        if k:
            s = s.replace(m.group(), '%s(%s)' % (8 * k, m.group(1)))
        else:
            s = s.replace(m.group(), '(%s)' % m.group(1))
    
    return [s]

def do_it(o, code, var_map):
    r = []
    for c in P.cutoff_comments(code):
        r += evaluate_row(c)
    S.cook_asm(o, r, var_map)

if __name__ == '__main__':
    with open(sys.argv[1], 'wb') as g_o:
        do_it(g_o, g_code, E.g_var_map + ' st,rsp')
