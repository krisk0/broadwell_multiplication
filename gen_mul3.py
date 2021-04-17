'''
void mul3(mp_ptr rp, mp_srcptr ap, mp_srcptr bp);

multiply 3-limb number a by 3-limb number b. Place 6-limb result at rp.
'''

g_var_map = 'rp,rdi up,rsi wB,rbp wA,rbx w9,r12 w8,r13 w7,r14 w6,r15 ' + \
    'w0,rax w1,r8 w2,r9 w3,r10 w4,r11 w5,rcx dd,rdx'

g_code = '''
movq dd[1], w6
movq dd[2], w7
movq dd[0], dd
movq up[0], w3               | w3=a[0] w6=b[1] w7=b[2]
xor w0, w0                   | zero flags
mulx w3, w0, w1              | w1 w0   w3=a[0] w6=b[1] w7=b[2]
movq up[1], w4               | w1 w0   w3=a[0] w4=a[1]
mulx w4, w2, w5              | w5 w1+w2 w0   w3=a[0] w4=a[1] w6=b[1] w7=b[2]
movq up[2], w8               | w5 w1+w2 w0   w3=a[0] w4=a[1] w8=a[2] w6=b[1] w7=b[2]
mulx w8, wA, wB        | wB w5+wA w1+w2 w0   w3=a[0] w4=a[1] w8=a[2] w6=b[1] w7=b[2]
movq w6, dd            | wB w5+wA w1+w2 w0   w3=a[0] w4=a[1] w8=a[2] w7=b[2]
mulx w3, w6, w9        | wB w5+wA+w9 w1+w2+w6 w0   w3=a[0] w4=a[1] w8=a[2] w7=b[2]
movq w0, rp[0]         | wB w5+wA+w9 w1+w2+w6 [1]   w3=a[0] w4=a[1] w8=a[2] w7=b[2]
movq w3, rp[1]         | rp[1]=a[0]
mulx w4, w0, w3        | wB+w3 w5+wA+w9+w0 w1+w2+w6 [1]   w4=a[1] w8=a[2] w7=b[2]
adcx w2, w1            | wB+w3 w5+wA+w9+w0' w1+w6 [1]   w4=a[1] w8=a[2] w7=b[2]
movq w4, rp[2]         | rp[2]=a[1]
mulx w8, w2, w4        | w4 wB+w3+w2 w5+wA+w9+w0' w1+w6 [1]   w8=a[2] w7=b[2]
adcx wA, w5            | w4 wB+w3+w2' w5+w9+w0 w1+w6 [1]   w8=a[2] w7=b[2]
movq w7, dd            | w4 wB+w3+w2' w5+w9+w0 w1+w6 [1]   w8=a[2]
mulx rp[1], w7, wA     | w4 wB+w3+w2+wA' w5+w9+w0+w7 w1+w6 [1]   w8=a[2]
adox w6, w1            | w4 wB+w3+w2+wA' w5+w9+w0+w7" w1 [1]   w8=a[2]
movq w1, rp[1]         | w4 wB+w3+w2+wA' w5+w9+w0+w7" [2]   w8=a[2]
mulx rp[2], w1, w6     | w4+w6 wB+w3+w2+wA+w1' w5+w9+w0+w7" [2]
mulx w8, w8, dd        | dd w4+w6+w8 wB+w3+w2+wA+w1' w5+w9+w0+w7" [2]
adcx wB, w3            | dd w4+w6+w8' w3+w2+wA+w1 w5+w9+w0+w7" [2]
adox w9, w5            | dd w4+w6+w8' w3+w2+wA+w1" w5+w0+w7 [2]
adcx w6, w4            | dd' w4+w8 w3+w2+wA+w1" w5+w0+w7 [2]
adox w2, w3            | dd' w4+w8" w3+wA+w1 w5+w0+w7 [2]
movq $0, w2            | w2=0
adcx w2, dd            | dd w4+w8" w3+wA+w1 w5+w0+w7 [2]
adcx w7, w0            | dd w4+w8" w3+wA+w1' w5+w0 [2]
adox w8, w4            | dd" w4 w3+wA+w1' w5+w0 [2]
adcx wA, w3            | dd" w4' w3+w1 w5+w0 [2]
adox w2, dd            | dd w4' w3+w1 w5+w0 [2]
adcx w2, w4            | dd' w4 w3+w1 w5+w0 [2]
adox w5, w0            | dd' w4 w3+w1" w5 [2]
movq w0, rp[2]         | dd' w4 w3+w1" [3]
adcx w2, dd            | dd w4 w3+w1" [3]
adox w3, w1            | dd w4" w1 [3]
movq w1, rp[3]
adox w2, w4            | dd" w4 [4]
movq w4, rp[4]
adox w2, dd            | dd [5]
movq dd, rp[5]
'''

import re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

g_array_patt = re.compile(r'\b(\S+)\b\[([0-9]+)\]')
def chew_line(s):
    m = g_array_patt.search(s)
    if m:
        k = int(m.group(2))
        if k:
            s = s.replace(m.group(), '%s(%s)' % (8 * k, m.group(1)))
        else:
            s = s.replace(m.group(), '(%s)' % m.group(1))
    
    return s

def do_it(o, code, var_map):
    code = [chew_line(x) for x in P.cutoff_comments(code)]
    P.cook_asm(o, code, var_map, True)

if __name__ == '__main__':
    with open(sys.argv[1], 'wb') as g_o:
        do_it(g_o, g_code, g_var_map)
