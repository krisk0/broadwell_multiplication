'''
6x6 multiplication targeting AMD. 60 ticks on Ryzen, 87 on Broadwell.

Ticks reported by benchm48_toom22_t.exe on Ryzen when using this subroutine: ?2820.
'''

"""
      rdi -< rp
      rsi -< up
      rdx -< (vp)

rbp rbx r12 r13 r14 r15
wB  wA  w9  w8  w6  w5    -- saved

rax r8  r9  r10 r11 rcx rsi rdi rdx
w0  w1  w2  w3  w4  w7  up  rp  dd
"""

g_mul0='''
movq dd, wB
movq (dd), dd                  | dd = v[0]
mulx (up), w0, w1              | w1 w0
mulx 8(up), w2, w3             | w3 w1+w2 w0
mulx 16(up), w4, w7            | w7 w3+w4 w1+w2 w0
mulx 24(up), w6, w8            | w8 w6+w7 w3+w4 w1+w2 w0
addq w2, w1                    | w8 w6+w7 w3+w4' w1 w0
movq w0, (rp)                  | w8 w6+w7 w3+w4' w1
mulx 32(up), w0, w2            | w2 w0+w8 w6+w7 w3+w4' w1
mulx 40(up), w5, w9            | w9 w5+w2 w0+w8 w6+w7 w3+w4' w1
movq w1, 8(rp)                 | w9 w5+w2 w0+w8 w6+w7 w3+w4'
adcq w4, w3                    | w9 w5+w2 w0+w8 w6+w7' w3
movq w3, 16(rp)                | w9 w5+w2 w0+w8 w6+w7'
movq 8(wB), dd                 | dd = v[1]
adcq w7, w6                    | w9 w5+w2 w0+w8' w6
movq w6, 24(rp)                | w9 w5+w2 w0+w8'
adcq w8, w0                    | w9 w5+w2' w0
movq w0, 32(rp)                | w9 w5+w2'
adcq w5, w2                    | w9' w2
movq w2, 40(rp)
                               | result in memory, except for senior word, which is
                               |  in w9 (should go to 48(rp)), dd=v[i]
'''

g_muladd='''
mulx (up), w0, w1              | w1 w0
mulx 8(up), w2, w3             | w3 w1+w2 w0
adcq $0, w9                    |
mulx 16(up), w4, w5            | w5 w3+w4 w1+w2 w0
mulx 24(up), w6, w7            | w7 w5+w6 w3+w4 w1+w2 w0
addq w0, i(rp)                 | w7 w5+w6 w3+w4 w1+w2'
adcq w2, w1                    | w7 w5+w6 w3+w4' w1
mulx 32(up), w0, w2            | w2+w9 w0+w7 w5+w6 w3+w4' w1
mulx 40(up), w8, wA            | wA w2+w8 w0+w7 w5+w6 w3+w4' w1
movq i+1(wB), dd               | dd=v[i+1]
adcq w4, w3                    | wA w2+w8+w9 w0+w7 w5+w6' w3 w1
adcq w6, w5                    | wA w2+w8+w9 w0+w7' w5 w3 w1
adcq w7, w0                    | wA w2+w8+w9' w0 w5 w3 w1
adcq w9, w2                    | wA' w2+w8 w0 w5 w3 w1
adcq $0, wA                    | wA w2+w8 w0 w5 w3 w1
addq w1, i+1(rp)               | wA w2+w8 w0 w5 w3'
adcq w3, i+2(rp)               | wA w2+w8 w0 w5'
movq wA, w9                    | w9 w2+w8 w0 w5'
adcq w5, i+3(rp)               | w9 w2+w8 w0'
adcq w0, i+4(rp)               | w9 w2+w8'
adcq w8, w2                    | w9' w2
movq w2, i+5(rp)               | w9'
'''

g_tail = '''
adcq $0, w9
movq w9, 88(rp)
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

def mul1_code(i, jj):
    rr = []
    for j in jj:
        for x in range(1, 6):
            ' replace i+x with 8*(i+x) '
            j = j.replace('i+%s(' % x, '%s(' % (8 * (i + x)))
        ' replace i with 8*i '
        j = j.replace('i(', '%s(' % (8 * i))
        rr.append(j)
    return rr

g_var_map = 'rp,rdi up,rsi w7,rcx wB,rbp wA,rbx w9,r12 w8,r13 w6,r14 w5,r15 ' + \
        'w0,rax w1,r8 w2,r9 w3,r10 w4,r11 dd,rdx'

def do_it(o):
    meat = P.cutoff_comments(g_mul0)
    muladd = P.cutoff_comments(g_muladd)
    tail = P.cutoff_comments(g_tail)

    for i in range(1, 6):
        meat += mul1_code(i, muladd)
    meat += tail
    P.cook_asm(o, meat, g_var_map, True)

with open(sys.argv[1], 'wb') as g_out:
    do_it(g_out)
