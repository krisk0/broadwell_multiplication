'''
void mul2(mp_ptr rp, mp_srcptr ap, mp_srcptr bp);

multiply 2-limb number a by 2-limb number b. Place 4-limb result at rp.
'''

g_var_map = 'rp,rdi up,rsi w0,rax w1,r8 w2,r9 w3,r10 w4,r11 w5,rcx dd,rdx'

g_code = '''
movq dd[1], w5
movq dd[0], dd
xor w0, w0
mulx up[0], w0, w1           | w1 w0   w5=b[1]
mulx up[1], w2, w3           | w3 w1+w2 w0   w5=b[1]
movq w5, dd                  | w3 w1+w2 w0
mulx up[0], w4, w5           | w3+w5 w1+w2+w4 w0
mulx up[1], up, dd           | dd w3+w5+up w1+w2+w4 w0
movq w0, rp[0]
movq $0, w0
adcx w2, w1                  | dd w3+w5+up' w1+w4 [1]
adcx w5, w3                  | dd' w3+up w1+w4 [1]
adox w4, w1                  | dd' w3+up" w1 [1]
movq w1, rp[1]               | dd' w3+up" [2]
adcx w0, dd                  | dd w3+up" [2]
adox up, w3                  | dd" w3 [2]
movq w3, rp[2]
adox w0, dd
movq dd, rp[3]
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
    P.cook_asm(o, code, var_map, False)

if __name__ == '__main__':
    with open(sys.argv[1], 'wb') as g_o:
        do_it(g_o, g_code, g_var_map)
