'''
11x11 multiplication. Different code for Broadwell and Ryzen.

With this subroutine, 22x22 multiplication becomes slightly slower on Skylake (3-10
 ticks) and noticeably slower on Ryzen (approx by 80 ticks)
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P
import gen_mul7_t03 as E

g_var_map = 'rp,rdi up,rsi wB,rbp wA,rbx w9,r12 w8,r13 w7,r14 w6,r15 ' + \
    'w0,rax w1,r8 w2,r9 w3,r10 w4,r11 w5,rcx dd,rdx sp,rsp'

g_stack_taken = 0xE8

"""
xmm usage:
0-5 v[]
9 rp
10-15 save registers

memory layout:
sp[0]
uu[0] .. uu[11] rr[0] .. rr[21]
"""

g_save_regs_max = 15

# inspired by GCC binary code of memcpy(stack var, source, 88)
g_memcpy_11 = '''
vzeroupper
!save w6
movq up, w0
sub $@stack_taken, sp
and $0xF, w0
jz u_align_0
movq up[0], w0
movq up[1], w1
!save w7
movq up[2], w2
movq up[3], w3
!save w8
movq up[4], w4
movq up[5], w5
!save w9
movq up[6], w6
movq up[7], w7
movq up[8], w8
movq up[9], w9
movq up[10], wC
| TODO: use different code on Broadwell
movq w0, sp[0]
movq w1, sp[1]
movq w2, sp[2]
movq w3, sp[3]
movq w4, sp[4]
movq w5, sp[5]
movq w6, sp[6]
movq w7, sp[7]
movq w8, sp[8]
movq w9, sp[9]
movq wC, sp[10]
jmp done_memcpy_u
u_align_0:
dqa_or_aps up[0], x0
if !amd: movq up[10], w0
dqa_or_aps up[2], x1                | movdqa on Broadwell, movaps on Ryzen
dqa_or_aps up[4], x2
dqa_or_aps up[6], x3
dqa_or_aps up[8], x4
if amd: movq up[10], w0
movq w0, sp[10]
!save w7
movaps x0, sp[0]
movaps x1, sp[2]
!save w8
movaps x2, sp[4]
movaps x3, sp[6]
!save w9
movaps x4, sp[8]
done_memcpy_u:
!save wA
'''

g_v_load_1 = '''
movq dd, w0
and $0xF, dd
!save wB
movq w0[0], dd
jz v_align_0
dqa_or_aps w0[1], x0        | x0=v[1..2]
dqa_or_aps w0[3], x1        | x1=v[3..4]
dqa_or_aps w0[5], x2        | x2=v[5..6]
dqa_or_aps w0[7], x3        | x3=v[7..8]
dqa_or_aps w0[9], x4        | x4=v[9..10]
'''

g_v_load_0 = '''
v_align_0:
movq w0[1], x0              | x0=v[1]
dqa_or_aps w0[2], x1        | x1=v[2..3]
dqa_or_aps w0[4], x2        | x2=v[4..5]
dqa_or_aps w0[6], x3        | x3=v[6..7]
dqa_or_aps w0[8], x4        | x4=v[8..9]
movq w0[10], x5             | x5=v[10]
'''

g_mul_0 = '''
movq rp, x9                 | x9=rp
mulx sp[0], w0, w1          | w1 w0
mulx sp[1], w2, w3          | w3 w1+w2 w0
mulx sp[2], w4, w5          | w5 w3+w4 w1+w2 w0
mulx sp[3], w6, w7          | w7 w5+w6 w3+w4 w1+w2 w0
movq w0, rr[0]              | w7 w5+w6 w3+w4 w1+w2 [1]
mulx sp[4], w0, w8          | w8 w7+w0 w5+w6 w3+w4 w1+w2 [1]
adcx w2, w1                 | w8 w7+w0 w5+w6 w3+w4' w1 [1]
movq w1, rr[1]              | w8 w7+w0 w5+w6 w3+w4' [2]
mulx sp[5], w1, w2          | w2 w8+w1 w7+w0 w5+w6 w3+w4' [2]
adcx w4, w3                 | w2 w8+w1 w7+w0 w5+w6' w3 [2]
movq w3, rr[2]              | w2 w8+w1 w7+w0 w5+w6' [3]
mulx sp[6], w3, w4          | w4 w2+w3 w8+w1 w7+w0 w5+w6' [3]
adcx w6, w5                 | w4 w2+w3 w8+w1 w7+w0' w5 [3]
movq w5, rr[3]              | w4 w2+w3 w8+w1 w7+w0' [4]
mulx sp[7], w5, w6          | w6 w4+w5 w2+w3 w8+w1 w7+w0' [4]
rp:=v[1]
adcx w7, w0
movq w0, rr[4]              | w6 w4+w5 w2+w3 w8+w1' [5] rp=v[1]
mulx sp[8], w0, w7          | w7 w6+w0 w4+w5 w2+w3 w8+w1' [5] rp=v[1]
mulx sp[9], w9, wA          | wA w7+w9 w6+w0 w4+w5 w2+w3 w8+w1' [5] rp=v[1]
adcx w8, w1                 | wA w7+w9 w6+w0 w4+w5 w2+w3' w1 [5] rp=v[1]
mulx sp[10], wB, up         | up wA+wB w7+w9 w6+w0 w4+w5 w2+w3' w1 [5] rp=v[1]
movq rp, dd                 | wC wA+wB w7+w9 w6+w0 w4+w5 w2+w3' w1 [5]
'''

'''
i >= 1
multiplied by v[0], .. v[i-1]
data lies like that: sC sA+sB s7+s9 s6+s0 s4+s5 s2+s3' s1 [4+i] dd=v[i]
'''

g_mul_1_zen = '''
                        | sC sA+sB s7+s9 s6+s0 s4+s5 s2+s3' s1 [4+i]
mulx sp[0], s8, sD      | sC sA+sB s7+s9 s6+s0 s4+s5 s2+s3' s1 .. .. sD| s8| [i]
movq s1, rr[i+4]        | sC sA+sB s7+s9 s6+s0 s4+s5 s2+s3' .. .. .. sD| s8| [i]
adcx s3, s2             | sC sA+sB s7+s9 s6+s0 s4+s5' s2 .. .. .. sD| s8| [i]
mulx sp[1], s1, s3      | sC sA+sB s7+s9 s6+s0 s4+s5' s2 .. .. s3| sD+s1| s8| [i]
movq s2, rr[i+5]        | sC sA+sB s7+s9 s6+s0 s4+s5' .. .. .. s3| sD+s1| s8| [i]
adcx s5, s4             | sC sA+sB s7+s9 s6+s0' s4 .. .. .. s3| sD+s1| s8| [i]
mulx sp[2], s2, s5      | sC sA+sB s7+s9 s6+s0' s4 .. .. s5| s3+s2| sD+s1| s8| [i]
movq s4, rr[i+6]        | sC sA+sB s7+s9 s6+s0' .. .. .. s5| s3+s2| sD+s1| s8| [i]
adcx s6, s0             | sC sA+sB s7+s9' s0 .. .. .. s5| s3+s2| sD+s1| s8| [i]
mulx sp[3], s4, s6      | sC sA+sB s7+s9' s0 .. .. s6| s5+s4| s3+s2| sD+s1| s8| [i]
movq s0, rr[i+7]        | sC sA+sB s7+s9' .. .. .. s6| s5+s4| s3+s2| sD+s1| s8| [i]
ado3(rr[i], s8, s0)     | sC sA+sB s7+s9' .. .. .. s6| s5+s4| s3+s2| sD+s1|" [i+1]
adcx s9, s7             | sC sA+sB' s7 .. .. .. s6| s5+s4| s3+s2| sD+s1|" [i+1]
mulx sp[4], s0, s8      | sC sA+sB' s7 .. .. s8| s6+s0| s5+s4| s3+s2| sD+s1|" [i+1]
adox sD, s1             | sC sA+sB' s7 .. .. s8| s6+s0| s5+s4| s3+s2|" s1| [i+1]
mulx sp[5], s9, sD      | sC sA+sB' s7 .. sD| s8+s9| s6+s0| s5+s4| s3+s2|" s1| [i+1]
adcx sB, sA             | sC' sA s7 .. sD| s8+s9| s6+s0| s5+s4| s3+s2|" s1| [i+1]
adox s3, s2             | sC' sA s7 .. sD| s8+s9| s6+s0| s5+s4|" s2| s1| [i+1]
movq $0, s3
adcx s3, sC             | sC sA s7 .. sD| s8+s9| s6+s0| s5+s4|" s2| s1| [i+1]
mulx sp[6], s3, sB      | sC sA s7 sB| sD+s3| s8+s9| s6+s0| s5+s4|" s2| s1| [i+1]
adox s5, s4             | sC sA s7 sB| sD+s3| s8+s9| s6+s0|" s4| s2| s1| [i+1]
adc3(rr[i+1], s1, s5)   | sC sA s7 sB| sD+s3| s8+s9| s6+s0|" s4| s2|' [i+2]
mulx sp[7], s1, s5      | sC sA s7+s5 sB+s1| sD+s3| s8+s9| s6+s0|" s4| s2|' [i+2]
adox s6, s0             | sC sA s7+s5 sB+s1| sD+s3| s8+s9|" s0| s4| s2|' [i+2]
adc3(rr[i+2], s2, s6)   | sC sA s7+s5 sB+s1| sD+s3| s8+s9|" s0| s4|' [i+3]
s6:=v[i+1]              | sC sA s7+s5 sB+s1| sD+s3| s8+s9|" s0| s4|' [i+3] s6=v[i+1]
adox s9, s8             | sC sA s7+s5 sB+s1| sD+s3|" s8| s0| s4|' [i+3] s6=v[i+1]
adc3(rr[i+3], s4, s2)   | sC sA s7+s5 sB+s1| sD+s3|" s8| s0|' [i+4] s6=v[i+1]
mulx sp[8], s2, s4      | sC sA+s4 s7+s5+s2 sB+s1| sD+s3|" s8| s0|' [i+4] s6=v[i+1]
adox sD, s3             | sC sA+s4 s7+s5+s2 sB+s1|" s3| s8| s0|' [i+4] s6=v[i+1]
adc3(rr[i+4], s0, s9)   | sC sA+s4 s7+s5+s2 sB+s1|" s3| s8|' [i+5] s6=v[i+1]
mulx sp[9], s0, s9      | sC+s9 sA+s4+s0 s7+s5+s2 sB+s1|" s3| s8|' [i+5] s6=v[i+1]
adox sB, s1             | sC+s9 sA+s4+s0 s7+s5+s2" s1| s3| s8|' [i+5] s6=v[i+1]
mulx sp[10], sB, sD     | sD sC+s9+sB sA+s4+s0 s7+s5+s2" s1| s3| s8|' [i+5] s6=v[i+1]
movq s6, dd             | sD sC+s9+sB sA+s4+s0 s7+s5+s2" s1| s3| s8|' [i+5]
adc3(rr[i+5], s8, s6)   | sD sC+s9+sB sA+s4+s0 s7+s5+s2" s1| s3|' [i+6]
'''

g_mul_1_bwl = '''
                        | sC sA+sB s7+s9 s6+s0 s4+s5 s2+s3' s1 [4+i]
adcx s3, s2             | sC sA+sB s7+s9 s6+s0 s4+s5' s2 s1 [4+i]
movq s2, rr[i+4]        | sC sA+sB s7+s9 s6+s0 s4+s5' ^4 s1 [4+i]
mulx sp[0], s8, sD      | sC sA+sB s7+s9 s6+s0 s4+s5' ^4 s1 .. .. sD| s8| [i]
movq rr[i], s2          | sC sA+sB s7+s9 s6+s0 s4+s5' ^4 s1 .. .. sD| s8+s2 [i]
adcx s5, s4             | sC sA+sB s7+s9 s6+s0' s4 ^4 s1 .. .. sD| s8+s2 [i]
movq s4, rr[i+5]        | sC sA+sB s7+s9 s6+s0' ^5 ^4 s1 .. .. sD| s8+s2 [i]
mulx sp[1], s4, s5      | sC sA+sB s7+s9 s6+s0' ^5 ^4 s1 .. s5| sD+s4| s8+s2 [i]
adcx s6, s0             | sC sA+sB s7+s9' s0 ^5 ^4 s1 .. s5| sD+s4| s8+s2 [i]
movq s0, rr[i+6]        | sC sA+sB s7+s9' ^6 ^5 ^4 s1 .. s5| sD+s4| s8+s2 [i]
mulx sp[2], s0, s6      | sC sA+sB s7+s9' ^6 ^5 ^4 s1 s6| s5+s0| sD+s4| s8+s2 [i]
adcx s9, s7             | sC sA+sB' s7 ^6 ^5 ^4 s1 s6| s5+s0| sD+s4| s8+s2 [i]
movq s7, rr[i+7]        | sC sA+sB' ^7 ^6 ^5 ^4 s1 s6| s5+s0| sD+s4| s8+s2 [i]
mulx sp[3], s7, s9      | sC sA+sB' ^7 ^6 ^5 ^4 s1+s9 s6+s7| s5+s0| sD+s4| s8+s2 [i]
adox s8, s2             | sC sA+sB' ^7 ^6 ^5 ^4 s1+s9 s6+s7| s5+s0| sD+s4|" s2 [i]
movq s2, rr[i]          | sC sA+sB' ^7 ^6 ^5 ^4 s1+s9 s6+s7| s5+s0| sD+s4|" [i+1]
mulx sp[4], s2, s8    | sC sA+sB' ^7 ^6 ^5 ^4+s8 s1+s9+s2 s6+s7| s5+s0| sD+s4|" [i+1]
adcx sB, sA           | sC' sA ^7 ^6 ^5 ^4+s8 s1+s9+s2 s6+s7| s5+s0| sD+s4|" [i+1]
movq rr[i+1], sB      | sC' sA ^7 ^6 ^5 ^4+s8 s1+s9+s2 s6+s7| s5+s0| sD+s4|" [i+1]
adox sD, s4           | sC' sA ^7 ^6 ^5 ^4+s8 s1+s9+s2 s6+s7| s5+s0|" s4+sB [i+1]
movq $0, sD
adcx sD, sC           | sC sA ^7 ^6 ^5 ^4+s8 s1+s9+s2 s6+s7| s5+s0|" s4+sB [i+1]
adox s5, s0           | sC sA ^7 ^6 ^5 ^4+s8 s1+s9+s2 s6+s7|" s0| s4+sB [i+1]
mulx sp[5], s3, s5    | sC sA ^7 ^6 ^5+s5 ^4+s8+s3 s1+s9+s2 s6+s7|" s0| s4+sB [i+1]
adcx sB, s4
movq rr[i+2], sB
movq s4, rr[i+1]      | sC sA ^7 ^6 ^5+s5 ^4+s8+s3 s1+s9+s2 s6+s7|" s0+sB' [i+2]
adox s7, s6           | sC sA ^7 ^6 ^5+s5 ^4+s8+s3 s1+s9+s2" s6| s0+sB' [i+2]
mulx sp[6], s4, s7    | sC sA ^7 ^6+s7 ^5+s5+s4 ^4+s8+s3 s1+s9+s2" s6| s0+sB' [i+2]
adcx sB, s0           | sC sA ^7 ^6+s7 ^5+s5+s4 ^4+s8+s3 s1+s9+s2" s6|' s0 [i+2]
movq rr[i+3], sB      | sC sA ^7 ^6+s7 ^5+s5+s4 ^4+s8+s3 s1+s9+s2" s6+sB' s0 [i+2]
adox s9, s1           | sC sA ^7 ^6+s7 ^5+s5+s4 ^4+s8+s3" s1+s2 s6+sB' s0 [i+2]
movq rr[i+4], s9      | sC sA ^7 ^6+s7 ^5+s5+s4 s9+s8+s3" s1+s2 s6+sB' s0 [i+2]
movq s0, rr[i+2]      | sC sA ^7 ^6+s7 ^5+s5+s4 s9+s8+s3" s1+s2 s6+sB' [i+3]
mulx sp[7], s0, sD    | sC sA ^7+sD ^6+s7+s0 ^5+s5+s4 s9+s8+s3" s1+s2 s6+sB' [i+3]
adcx sB, s6           | sC sA ^7+sD ^6+s7+s0 ^5+s5+s4 s9+s8+s3" s1+s2' s6 [i+3]
movq s6, rr[i+3]      | sC sA ^7+sD ^6+s7+s0 ^5+s5+s4 s9+s8+s3" s1+s2' [i+4]
| TODO: can extract v[i+1] later
s6:=v[i+1]
adox s9, s8           | sC sA ^7+sD ^6+s7+s0 ^5+s5+s4" s8+s3 s1+s2' [i+4]
movq rr[i+5], s9      | sC sA ^7+sD ^6+s7+s0 s9+s5+s4" s8+s3 s1+s2' [i+4]
movq sA, rr[i+5]      | sC ^5 ^7+sD ^6+s7+s0 s9+s5+s4" s8+s3 s1+s2' [i+4]
mulx sp[8], sA, sB    | sC ^5+sB ^7+sD+sA ^6+s7+s0 s9+s5+s4" s8+s3 s1+s2' [i+4]
adcx s2, s1           | sC ^5+sB ^7+sD+sA ^6+s7+s0 s9+s5+s4" s8+s3' s1 [i+4]
movq s1, rr[i+4]      | sC ^5+sB ^7+sD+sA ^6+s7+s0 s9+s5+s4" s8+s3' [i+5]
movq rr[i+6], s2      | sC ^5+sB ^7+sD+sA s2+s7+s0" s5+s4 s8+s3' [i+5]
adox s9, s5           | sC ^5+sB ^7+sD+sA s2+s7+s0" s5+s4 s8+s3' [i+5]
mulx sp[9], s1, s9    | sC+s9 ^5+sB+s1 ^7+sD+sA s2+s7+s0" s5+s4 s8+s3' [i+5]
adcx s8, s3           | sC+s9 ^5+sB+s1 ^7+sD+sA s2+s7+s0" s5+s4' s3 [i+5]
movq rr[i+5], s8      | sC+s9 s8+sB+s1 ^7+sD+sA s2+s7+s0" s5+s4' s3 [i+5]
movq s3, rr[i+5]      | sC+s9 s8+sB+s1 ^7+sD+sA s2+s7+s0" s5+s4' [i+6]
movq rr[i+7], s3      | sC+s9 s8+sB+s1 s3+sD+sA s2+s7+s0" s5+s4' [i+6]
adox s7, s2           | sC+s9 s8+sB+s1 s3+sD+sA" s2+s0 s5+s4' [i+6]
adcx s5, s4           | sC+s9 s8+sB+s1 s3+sD+sA" s2+s0' s4 [i+6]
mulx sp[10], s5, s7   | s7 sC+s9+s5 s8+sB+s1 s3+sD+sA" s2+s0' s4 [i+6]
movq s6, dd
adox sD, s3           | s7 sC+s9+s5 s8+sB+s1" s3+sA s2+s0' s4 [i+6]
'''

g_mul_2_zen = '''
                      | i >= 2
                      | sD sC+s9+sB sA+s4+s0 s7+s5+s2" s1| s3|' [i+5]
mulx sp[0], s6, s8    | sD sC+s9+sB sA+s4+s0 s7+s5+s2" s1| s3|' .. .. .. s8| s6| [i]
adox s7, s5           | sD sC+s9+sB sA+s4+s0" s5+s2 s1| s3|' .. .. .. s8| s6| [i]
adc3(rr[i+5], s3, s7) | sD sC+s9+sB sA+s4+s0" s5+s2 s1|' [4] s8| s6| [i]
mulx sp[1], s3, s7    | sD sC+s9+sB sA+s4+s0" s5+s2 s1|' [3] s7| s8+ss| s6| [i]
adox sA, s4           | sD sC+s9+sB" s4+s0 s5+s2 s1|' [3] s7| s8+ss| s6| [i]
adc3(rr[i+6], s1, sA) | sD sC+s9+sB" s4+s0 s5+s2' [4] s7| s8+s3| s6| [i]
mulx sp[2], s1, sA    | sD sC+s9+sB" s4+s0 s5+s2' [3] sA| s7+s1| s8+s3| s6| [i]
adox sC, s9           | sD" s9+sB s4+s0 s5+s2' [3] sA| s7+s1| s8+s3| s6| [i]
adcx s5, s2           | sD" s9+sB s4+s0' s2 [3] sA| s7+s1| s8+s3| s6| [i]
movq $0, sC
adox sC, sD           | sD s9+sB s4+s0' s2 [3] sA| s7+s1| s8+s3| s6| [i]
mulx sp[3], s5, sC    | sD s9+sB s4+s0' s2 [2] sC| sA+s5| s7+s1| s8+s3| s6| [i]
adcx s4, s0           | sD s9+sB' s0 s2 [2] sC| sA+s5| s7+s1| s8+s3| s6| [i]
ado3(rr[i], s6, s4)   | sD s9+sB' s0 s2 [2] sC| sA+s5| s7+s1| s8+s3|" [i+1]
mulx sp[4], s4, s6    | sD s9+sB' s0 s2 .. s6| sC+s4| sA+s5| s7+s1| s8+s3|" [i+1]
adcx sB, s9           | sD' s9 s0 s2 .. s6| sC+s4| sA+s5| s7+s1| s8+s3|" [i+1]
movq $0, sB
adox s8, s3           | sD' s9 s0 s2 .. s6| sC+s4| sA+s5| s7+s1|" s3| [i+1]
adcx sB, sD           | sD s9 s0 s2 .. s6| sC+s4| sA+s5| s7+s1|" s3| [i+1]
mulx sp[5], s8, sB    | sD s9 s0 s2 sB| s6+s8| sC+s4| sA+s5| s7+s1|" s3| [i+1]
adox s7, s1           | sD s9 s0 s2 sB| s6+s8| sC+s4| sA+s5|" s1| s3| [i+1]
adc3(rr[i+1], s3, s7) | sD s9 s0 s2 sB| s6+s8| sC+s4| sA+s5|" s1|' [i+2]
mulx sp[6], s3, s7    | sD s9 s0 s2+s7 sB+s3| s6+s8| sC+s4| sA+s5|" s1|' [i+2]
adox sA, s5           | sD s9 s0 s2+s7 sB+s3| s6+s8| sC+s4|" s5| s1|' [i+2]
adc3(rr[i+2], s1, sA) | sD s9 s0 s2+s7 sB+s3| s6+s8| sC+s4|" s5|' [i+3]
mulx sp[7], s1, sA    | sD s9 s0+sA s2+s7+s1 sB+s3| s6+s8| sC+s4|" s5|' [i+3]
adox s4, sC           | sD s9 s0+sA s2+s7+s1 sB+s3| s6+s8|" sC| s5|' [i+3]
adc3(rr[i+3], s5, s4) | sD s9 s0+sA s2+s7+s1 sB+s3| s6+s8|" sC|' [i+4]
s4:=v[i+1]            | sD s9 s0+sA s2+s7+s1 sB+s3| s6+s8|" sC|' [i+4] s4=v[i+1]
adox s8, s6           | sD s9 s0+sA s2+s7+s1 sB+s3|" s6| sC|' [i+4] s4=v[i+1]
adc3(rr[i+4], sC, s8) | sD s9 s0+sA s2+s7+s1 sB+s3|" s6|' [i+5] s4=v[i+1]
mulx sp[8], sC, s5    | sD s9+s5 s0+sA+sC s2+s7+s1 sB+s3|" s6|' [i+5] s4=v[i+1]
adox s3, sB           | sD s9+s5 s0+sA+sC s2+s7+s1" sB| s6|' [i+5] s4=v[i+1]
adc3(rr[i+5], s6, s8) | sD s9+s5 s0+sA+sC s2+s7+s1" sB|' [i+6] s4=v[i+1]
mulx sp[9], s6, s8    | sD+s8 s9+s5+s6 s0+sA+sC s2+s7+s1" sB|' [i+6] s4=v[i+1]
adox s7, s2           | sD+s8 s9+s5+s6 s0+sA+sC" s2+s1 sB|' [i+6] s4=v[i+1]
mulx sp[10], s7, s3   | s3 sD+s8+s7 s9+s5+s6 s0+sA+sC" s2+s1 sB|' [i+6] s4=v[i+1]
movq s4, dd           | s3 sD+s8+s7 s9+s5+s6 s0+sA+sC" s2+s1 sB|' [i+6]
movq s1, rr[i+7]      | s3 sD+s8+s7 s9+s5+s6 s0+sA+sC" s2| sB|' [i+6]
'''

"""
old sD sC+s9+sB sA+s4+s0 s7+s5+s2" s1| s3|' == s6 s8
new s3 sD+s8+s7 s9+s5+s6 s0+sA+sC" s2| sB|' == s1 s4
              0 1 2 3 4 5 6 7 8 9 A B C D                             """
g_perm_zen = '6 2 C B 5 A 1 0 4 8 9 7 D 3'

g_mul_9_zen_piece2 = '''
| s0->WB s1->W0 s2->W6 s3->WC s4->WA s5->W9 s6->W7 s7->W3 s8->W5 s9->W4 sA->W8 sB->WD sC->W1 sD->W2
| After adc3(rr[i+4], sC, s8):
|                              sD s9 s0+sA s2+s7+s1 sB+s3|" s6|' == s4=v[10]
|                              w2 w4 wB+w8 w6+w3+w0 wD+wC|" w7|' == wA=v[10]
|                              s8=w5=rcx, i=9
movq x0, w5           | w2 w4 wB+w8 w6+w3+w0 wD+wC|" w7|' == wA=v[10] w5=jump_cond
adox wD, wC           | w2 w4 wB+w8 w6+w3+w0" wC| w7|' == wA=v[10] w5=jump_cond
mulx sp[8], w1, w9    | w2 w4+w9 wB+w8+w1 w6+w3+w0" wC| w7|' == wA=v[10] w5=jump_cond
adox w6, w3           | w2 w4+w9 wB+w8+w1" w3+w0 wC| w7|' [14] wA w5
adc3(rr[i+5], w7, w6) | w2 w4+w9 wB+w8+w1" w3+w0 wC|' [15] wA=v[10] w5=jump_cond
mulx sp[9], w6, w7    | w2+w7 w4+w9+w6 wB+w8+w1" w3+w0 wC|' [15] wA w5
adox wB, w8           | w2+w7 w4+w9+w6" w8+w1 w3+w0 wC|' [15] wA w5
adc3(rr[i+6], wC, wD) | w2+w7 w4+w9+w6" w8+w1 w3+w0' [16] wA w5
mulx sp[10], wC, wD   | wD w2+w7+wC w4+w9+w6" w8+w1 w3+w0' [16] wA w5
movq wA, dd           | wD w2+w7+wC w4+w9+w6" w8+w1 w3+w0' [16] w5=jump_cond
if !aligned: jrcxz mul_10_aligned_gate_0 | one extra jump due to limitiation of jrcxz
if aligned: jrcxz mul_10_aligned_gate_1
jmp mul_10_unaligned
if !aligned: mul_10_aligned_gate_0:
if aligned: mul_10_aligned_gate_1:
jmp mul_10_aligned
'''

g_mul_10_zen = '''
if aligned: mul_10_aligned:
if !aligned: mul_10_unaligned:
                      | wD w2+w7+wC w4+w9+w6" w8+w1 w3+w0' [16]
movq rr[0], x2
if !aligned: movq rr[9], x0 | x0 [9]
adox w9, w4           | wD w2+w7+wC" w4+w6 w8+w1 w3+w0' [16]
adcx w3, w0           | wD w2+w7+wC" w4+w6 w8+w1' w0 [16]
mulx sp[0], w3, w9    | wD w2+w7+wC" w4+w6 w8+w1' w0 [4] w9| w3| [10]
adox w7, w2           | wD" w2+wC w4+w6 w8+w1' w0 [4] w9| w3| [10]
adcx w8, w1           | wD" w2+wC w4+w6' w1 w0 [4] w9| w3| [10]
mulx sp[1], w7, w8    | wD" w2+wC w4+w6' w1 w0 [3] w8| w9+w7| w3| [10]
if !aligned: movq $0, w5
adox w5, wD           | wD w2+wC w4+w6' w1 w0 [3] w8| w9+w7| w3| [10]
adcx w6, w4           | wD w2+wC' w4 w1 w0 [3] w8| w9+w7| w3| [10]
mulx sp[2], w5, w6    | wD w2+wC' w4 w1 w0 [2] w6| w8+w5| w9+w7| w3| [10]
mulx sp[3], wA, wB    | wD w2+wC' w4 w1 w0 .. wB| w6+wA| w8+w5| w9+w7| w3| [10]
movq wD, rr[0]        | ^^ w2+wC' w4 w1 w0 .. wB| w6+wA| w8+w5| w9+w7| w3| [10]
movq rr[10], wD       | ^^ w2+wC' w4 w1 w0 .. wB| w6+wA| w8+w5| w9+w7| w3+wD [10]
adox wD, w3           | ^^ w2+wC' w4 w1 w0 .. wB| w6+wA| w8+w5| w9+w7|" w3 [10]
if !aligned: pinsrq $1, w3, x0 | x0_x0 [9]
if aligned: movq w3, x0        | x0 [10]
                      | ^^ w2+wC' w4 w1 w0 .. wB| w6+wA| w8+w5| w9+w7|" [11]
movq rr[0], wD        | wD w2+wC' w4 w1 w0 .. wB| w6+wA| w8+w5| w9+w7|" [11]
adcx wC, w2           | wD' w2 w4 w1 w0 .. wB| w6+wA| w8+w5| w9+w7|" [11]
mulx sp[4], w3, wC    | wD' w2 w4 w1 w0 wC| wB+w3| w6+wA| w8+w5| w9+w7|" [11]
adox w9, w7           | wD' w2 w4 w1 w0 wC| wB+w3| w6+wA| w8+w5|" w7| [11]
movq $0, w9
adcx w9, wD           | wD w2 w4 w1 w0 wC| wB+w3| w6+wA| w8+w5|" w7| [11]
movq wD, rr[0]        | ^0 w2 w4 w1 w0 wC| wB+w3| w6+wA| w8+w5|" w7| [11]
mulx sp[5], w9, wD    | ^0 w2 w4 w1 w0+wD wC+w9| wB+w3| w6+wA| w8+w5|" w7| [11]
adox w8, w5           | ^0 w2 w4 w1 w0+wD wC+w9| wB+w3| w6+wA|" w5| w7| [11]
movq rr[11], w8       | ^0 w2 w4 w1 w0+wD wC+w9| wB+w3| w6+wA|" w5| w7+w8 [11]
adcx w8, w7           | ^0 w2 w4 w1 w0+wD wC+w9| wB+w3| w6+wA|" w5|' w7 [11]
if !aligned: movq w7, x1       | x1 x0_x0 [9]
if aligned: pinsrq $1, w7, x0  | x0_x0 [10]
                      | ^0 w2 w4 w1 w0+wD wC+w9| wB+w3| w6+wA|" w5|' [12]
mulx sp[6], w7, w8    | ^0 w2 w4 w1+w8 w0+wD+w7 wC+w9| wB+w3| w6+wA|" w5|' [12]
adox wA, w6           | ^0 w2 w4 w1+w8 w0+wD+w7 wC+w9| wB+w3|" w6| w5|' [12]
movq rr[12], wA       | ^0 w2 w4 w1+w8 w0+wD+w7 wC+w9| wB+w3|" w6| w5+wA' [12]
adcx wA, w5           | ^0 w2 w4 w1+w8 w0+wD+w7 wC+w9| wB+w3|" w6|' w5 [12]
movq w5, x3           | ^0 w2 w4 w1+w8 w0+wD+w7 wC+w9| wB+w3|" w6|' [13]
| if !aligned:                   x3 x1 x0_x0 [9]
| if aligned:                    x3 x0_x0 [10]
mulx sp[7], wA, w5    | ^0 w2 w4+w5 w1+w8+wA w0+wD+w7 wC+w9| wB+w3|" w6|' [13]
adox wB, w3           | ^0 w2 w4+w5 w1+w8+wA w0+wD+w7 wC+w9|" w3| w6|' [13]
movq rr[13], wB       | ^0 w2 w4+w5 w1+w8+wA w0+wD+w7 wC+w9|" w3| w6+wB' [13]
adcx wB, w6           | ^0 w2 w4+w5 w1+w8+wA w0+wD+w7 wC+w9|" w3|' w6 [13]
movq w6, x4           | ^0 w2 w4+w5 w1+w8+wA w0+wD+w7 wC+w9|" w3|' [14]
| if !aligned:                   x4 x3 x1 x0_x0 [9]
| if aligned:                    x4 x3 x0_x0 [10]
mulx sp[8], w6, wB    | ^0 w2+wB w4+w5+w6 w1+w8+wA w0+wD+w7 wC+w9|" w3|' [14]
adox w9, wC           | ^0 w2+wB w4+w5+w6 w1+w8+wA w0+wD+w7" wC| w3|' [14]
movq rr[14], w9       | ^0 w2+wB w4+w5+w6 w1+w8+wA w0+wD+w7" wC| w3+w9' [14]
adcx w9, w3           | ^0 w2+wB w4+w5+w6 w1+w8+wA w0+wD+w7" wC|' w3 [14]
movq w3, x5           | ^0 w2+wB w4+w5+w6 w1+w8+wA w0+wD+w7" wC|' [15]
| if !aligned:                   x5 x4 x3 x1 x0_x0 [8] x2
| if aligned:                    x5 x4 x3 x0_x0 [10]
if !aligned: movdqa rr[1], x6  | x5 x4 x3 x1 x0_x0 [6] x6_x6 x2
if aligned: movq rr[1], w3
if aligned: pinsrq $1, w3, x2  | x5 x4 x3 x0_x0 [8] x2_x2
mulx sp[9], w9, w3    | ^0+w3 w2+wB+w9 w4+w5+w6 w1+w8+wA w0+wD+w7" wC|' [15]
adox wD, w0           | ^0+w3 w2+wB+w9 w4+w5+w6 w1+w8+wA" w0+w7 wC|' [15]
movq rr[15], wD       | ^0+w3 w2+wB+w9 w4+w5+w6 w1+w8+wA" w0+w7 wC+wD' [15]
adcx wD, wC           | ^0+w3 w2+wB+w9 w4+w5+w6 w1+w8+wA" w0+w7' wC [15]
mulx sp[10], wD, dd   | dd ^0+w3+wD w2+wB+w9 w4+w5+w6 w1+w8+wA" w0+w7' wC [15]
adox w1, w8           | dd ^0+w3+wD w2+wB+w9 w4+w5+w6" w8+wA w0+w7' wC [15]
movq x9, w1           | dd ^0+w3+wD w2+wB+w9 w4+w5+w6" w8+wA w0+w7' wC [15] w1=rp
adcx w0, w7           | dd ^0+w3+wD w2+wB+w9 w4+w5+w6" w8+wA' w7 wC [15] w1=rp
movq rr[0], w0        | dd w0+w3+wD w2+wB+w9 w4+w5+w6" w8+wA' w7 wC [15] w1=rp
if !aligned: movdqa rr[3], x7  | x5 x4 x3 x1 x0_x0 [4] x7_x7 x6_x6 x2
if aligned: movq rr[2], x6   | x5 x4 x3 x0_x0 [7] x6 x2_x2
adox w5, w4           | dd w0+w3+wD w2+wB+w9" w4+w6 w8+wA' w7 wC [15] w1=rp
if !aligned: movdqa rr[5], x8  | x5 x4 x3 x1 x0_x0 [2] x8_x8 x7_x7 x6_x6 x2
if aligned: movq rr[3], x7   | x5 x4 x3 x0_x0 [6] x7 x6 x2_x2
adcx wA, w8           | dd w0+w3+wD w2+wB+w9" w4+w6' w8 w7 wC [15] w1=rp
if !aligned: movdqa rr[7], x9  | x5 x4 x3 x1 x0_x0 x9_x9 x8_x8 x7_x7 x6_x6 x2
if aligned: movq rr[3], x7     | x5 x4 x3 x0_x0 [6] x7 x6 x2_x2
adox wB, w2           | dd w0+w3+wD" w2+w9 w4+w6' w8 w7 wC [15] w1=rp
if aligned: movq rr[4], x8     | x5 x4 x3 x0_x0 [5] x8 x7 x6 x2_x2
adcx w6, w4           | dd w0+w3+wD" w2+w9' w4 w8 w7 wC [15] w1=rp
if aligned: movq rr[5], x9     | x5 x4 x3 x0_x0 [4] x9 x8 x7 x6 x2_x2
adox w3, w0           | dd" w0+wD w2+w9' w4 w8 w7 wC [15] w1=rp

if aligned: movq rr[6], w3     | x5 x4 x3 x0_x0 [3] w3 x9 x8 x7 x6 x2_x2
adcx w9, w2           | dd" w0+wD' w2 w4 w8 w7 wC [15] w1=rp
if !aligned: movq x2, w1[0]    | x5 x4 x3 x1 x0_x0 x9_x9 x8_x8 x7_x7 x6_x6 [1]
if aligned: movq rr[7], w9     | x5 x4 x3 x0_x0 [2] w9 w3 x9 x8 x7 x6 x2_x2
movq $0, w5           | dd" w0+wD' w2 w4 w8 w7 wC [15] w1 w3 w9 w5
adox w5, dd           | dd w0+wD' w2 w4 w8 w7 wC [15] w1 w3 w9 w5
if aligned: movq rr[8], w6     | x5 x4 x3 x0_x0 .. w6 w9 w3 x9 x8 x7 x6 x2_x2
adcx wD, w0           | dd' w0 w2 w4 w8 w7 wC [15] w1 w2 w3 w5
if aligned: movq rr[9], wD     | x5 x4 x3 x0_x0 wD w6 w9 w3 x9 x8 x7 x6 x2_x2
if !aligned: movdqa x6, w1[1]  | x5 x4 x3 x1 x0_x0 x9_x9 x8_x8 x7_x7 [3]
if !aligned: movdqa x7, w1[3]  | x5 x4 x3 x1 x0_x0 x9_x9 x8_x8 [5]
if aligned: movdqa x2, w1[0]   | x5 x4 x3 x0_x0 wD w6 w9 w3 x9 x8 x7 x6 [2]
if aligned: movq x6, w1[2]     | x5 x4 x3 x0_x0 wD w6 w9 w3 x9 x8 x7 [3]
if aligned: movq x7, w1[3]     | x5 x4 x3 x0_x0 wD w6 w9 w3 x9 x8 [4]
adcx w5, dd           | dd w0 w2 w4 w8 w7 wC [15]
movq w8, w5           | dd w0 w2 w4 w5 w7 wC [15]
if !aligned: movdqa x8, w1[5]  | x5 x4 x3 x1 x0_x0 x9_x9 [7]
if !aligned: movdqa x9, w1[7]  | x5 x4 x3 x1 x0_x0 [9]
if !aligned: movdqa x0, w1[9]  | x5 x4 x3 x1 [11]
if !aligned: movq x1, w1[11]  | x5 x4 x3 [12]
if !aligned: movq x3, w1[12]  | x5 x4 [13]
if !aligned: movq x4, w1[13]  | x5 [14]
if !aligned: movq x5, w1[14]
if aligned: movq x8, w1[4]     | x5 x4 x3 x0_x0 wD w6 w9 w3 x9 [5]
if aligned: movq x9, w1[5]     | x5 x4 x3 x0_x0 wD w6 w9 w3 [6]
if aligned: movq w3, w1[6]     | x5 x4 x3 x0_x0 wD w6 w9 [7]
if aligned: movq w9, w1[7]     | x5 x4 x3 x0_x0 wD w6 [8]
if aligned: movq w6, w1[8]     | x5 x4 x3 x0_x0 wD [9]
if aligned: movq wD, w1[9]     | x5 x4 x3 x0_x0 [10]
if aligned: movdqa x0, w1[10]  | x5 x4 x3 [12]
if aligned: movq x3, w1[12]    | x5 x4 [13]
if aligned: movq x4, w1[13]    | x5 [14]
if aligned: movq x5, w1[14]
movq wC, w1[15]       | dd w0 w2 w4 w5 w7 [16]
movq w7, w1[16]       | dd w0 w2 w4 w5 [17]
movq w5, w1[17]       | dd w0 w2 w4 [18]
movq w4, w1[18]       | dd w0 w2 [19]
movq w2, w1[19]       | dd w0 [20]
movq w0, w1[20]       | dd [20]
movq dd, w1[21]
if !aligned: jmp all_done
| TODO: reduce code size by sharing 7 movq lines above
'''

g_mul_2_bwl = '''
                      | i >= 2
                      | s7 sC+s9+s5 s8+sB+s1" s3+sA s2+s0' s4 [i+5]
mulx sp[0], s6, sD    | s7 sC+s9+s5 s8+sB+s1" s3+sA s2+s0' s4 [3] sD| s6| [i]
adcx s2, s0           | s7 sC+s9+s5 s8+sB+s1" s3+sA' s0 s4 [3] sD| s6| [i]
adox sB, s8           | s7 sC+s9+s5" s8+s1 s3+sA' s0 s4 [3] sD| s6| [i]
mulx sp[1], s2, sB    | s7 sC+s9+s5" s8+s1 s3+sA' s0 s4 [2] sB| sD+s2| s6| [i]
adcx sA, s3           | s7 sC+s9+s5" s8+s1' s3 s0 s4 [2] sB| sD+s2| s6| [i]
adox sC, s9           | s7" s9+s5 s8+s1' s3 s0 s4 [2] sB| sD+s2| s6| [i]
mulx sp[2], sA, sC    | s7" s9+s5 s8+s1' s3 s0 s4 .. sC| sB+sA| sD+s2| s6| [i]
adcx s8, s1           | s7" s9+s5' s1 s3 s0 s4 .. sC| sB+sA| sD+s2| s6| [i]
movq s3, rr[i+5]      | s7" s9+s5' s1 ^5 s0 s4 .. sC| sB+sA| sD+s2| s6| [i]
movq rr[i], s3        | s7" s9+s5' s1 ^5 s0 s4 .. sC| sB+sA| sD+s2| s6+s3 [i]
movq $0, s8
adox s8, s7           | s7 s9+s5' s1 ^5 s0 s4 .. sC| sB+sA| sD+s2| s6+s3 [i]
adcx s9, s5           | s7' s5 s1 ^5 s0 s4 .. sC| sB+sA| sD+s2| s6+s3 [i]
mulx sp[3], s8, s9    | s7' s5 s1 ^5 s0 s4 s9| sC+s8| sB+sA| sD+s2| s6+s3 [i]
adox s6, s3           | s7' s5 s1 ^5 s0 s4 s9| sC+s8| sB+sA| sD+s2|" s3 [i]
movq $0, s6
adcx s6, s7           | s7 s5 s1 ^5 s0 s4 s9| sC+s8| sB+sA| sD+s2|" s3 [i]
movq s3, rr[i]        | s7 s5 s1 ^5 s0 s4 s9| sC+s8| sB+sA| sD+s2|" [i+1]
mulx sp[4], s3, s6    | s7 s5 s1 ^5 s0 s4+s6 s9+s3| sC+s8| sB+sA| sD+s2|" [i+1]
adox sD, s2           | s7 s5 s1 ^5 s0 s4+s6 s9+s3| sC+s8| sB+sA|" s2| [i+1]
movq rr[i+1], sD      | s7 s5 s1 ^5 s0 s4+s6 s9+s3| sC+s8| sB+sA|" s2+sD [i+1]
movq s1, rr[i+6]      | s7 s5 ^6 ^5 s0 s4+s6 s9+s3| sC+s8| sB+sA|" s2+sD [i+1]
movq s5, rr[i+7]      | s7 ^7 ^6 ^5 s0 s4+s6 s9+s3| sC+s8| sB+sA|" s2+sD [i+1]
mulx sp[5], s1, s5    | s7 ^7 ^6 ^5 s0+s5 s4+s6+s1 s9+s3| sC+s8| sB+sA|" s2+sD [i+1]
adox sB, sA           | s7 ^7 ^6 ^5 s0+s5 s4+s6+s1 s9+s3| sC+s8|" sA| s2+sD [i+1]
movq rr[i+2], sB      | s7 ^7 ^6 ^5 s0+s5 s4+s6+s1 s9+s3| sC+s8|" sA+sB s2+sD [i+1]
adcx sD, s2
movq s2, rr[i+1]      | s7 ^7 ^6 ^5 s0+s5 s4+s6+s1 s9+s3| sC+s8|" sA+sB' [i+2]
movq rr[i+3], s2      | s7 ^7 ^6 ^5 s0+s5 s4+s6+s1 s9+s3| sC+s8+s2" sA+sB' [i+2]
adox sC, s8           | s7 ^7 ^6 ^5 s0+s5 s4+s6+s1 s9+s3|" s8+s2 sA+sB' [i+2]
mulx sp[6], sC, sD    | s7 ^7 ^6 ^5+sD s0+s5+sC s4+s6+s1 s9+s3|" s8+s2 sA+sB' [i+2]
adcx sB, sA           | s7 ^7 ^6 ^5+sD s0+s5+sC s4+s6+s1 s9+s3|" s8+s2' sA [i+2]
adox s9, s3           | s7 ^7 ^6 ^5+sD s0+s5+sC s4+s6+s1" s3| s8+s2' sA [i+2]
movq sA, rr[i+2]      | s7 ^7 ^6 ^5+sD s0+s5+sC s4+s6+s1" s3| s8+s2' [i+3]
movq rr[i+4], sA      | s7 ^7 ^6 ^5+sD s0+s5+sC s4+s6+s1" s3+sA s8+s2' [i+3]
mulx sp[7], s9, sB    | s7 ^7 ^6+sB ^5+sD+s9 s0+s5+sC s4+s6+s1" s3+sA s8+s2' [i+3]
adcx s8, s2           | s7 ^7 ^6+sB ^5+sD+s9 s0+s5+sC s4+s6+s1" s3+sA' s2 [i+3]
adox s6, s4           | s7 ^7 ^6+sB ^5+sD+s9 s0+s5+sC" s4+s1 s3+sA' s2 [i+3]
movq s2, rr[i+3]      | s7 ^7 ^6+sB ^5+sD+s9 s0+s5+sC" s4+s1 s3+sA' [i+4]
| TODO: can extract v[i+1] later
s2:=v[i+1]
mulx sp[8], s6, s8    | s7 ^7+s8 ^6+sB+s6 ^5+sD+s9 s0+s5+sC" s4+s1 s3+sA' [i+4] s2=v
adcx sA, s3           | s7 ^7+s8 ^6+sB+s6 ^5+sD+s9 s0+s5+sC" s4+s1' s3 [i+4] s2=v
adox s5, s0           | s7 ^7+s8 ^6+sB+s6 ^5+sD+s9" s0+sC s4+s1' s3 [i+4] s2=v
movq s3, rr[i+4]      | s7 ^7+s8 ^6+sB+s6 ^5+sD+s9" s0+sC s4+s1' [i+5] s2=v[i+1]
movq rr[i+5], s3      | s7 ^7+s8 ^6+sB+s6 sD+s9+s3" s0+sC s4+s1' [i+5] s2=v[i+1]
mulx sp[9], s5, sA    | s7+sA ^7+s8+s5 ^6+sB+s6 sD+s9+s3" s0+sC s4+s1' [i+5] s2=v
adcx s4, s1           | s7+sA ^7+s8+s5 ^6+sB+s6 sD+s9+s3" s0+sC' s1 [i+5] s2=v[i+1]
adox sD, s9           | s7+sA ^7+s8+s5 ^6+sB+s6" s9+s3 s0+sC' s1 [i+5] s2=v[i+1]
mulx sp[10], s4, sD   | sD s7+sA+s4 ^7+s8+s5 ^6+sB+s6" s9+s3 s0+sC' s1 [i+5] s2=v
movq s2, dd           | sD s7+sA+s4 ^7+s8+s5 ^6+sB+s6" s9+s3 s0+sC' s1 [i+5]
movq rr[i+6], s2      | sD s7+sA+s4 ^7+s8+s5 sB+s6+s2" s9+s3 s0+sC' s1 [i+5]
movq s1, rr[i+5]      | sD s7+sA+s4 ^7+s8+s5 sB+s6+s2" s9+s3 s0+sC' [i+6]
movq rr[i+7], s1      | sD s7+sA+s4 s8+s5+s1 sB+s6+s2" s9+s3 s0+sC' [i+6]
adcx sC, s0           | sD s7+sA+s4 s8+s5+s1 sB+s6+s2" s9+s3' s0 [i+6]
adox sB, s6           | sD s7+sA+s4 s8+s5+s1" s6+s2 s9+s3' s0 [i+6]
'''

"""
old s7 sC+s9+s5 s8+sB+s1" s3+sA s2+s0' s4 == s6 sD
new sD s7+sA+s4 s8+s5+s1" s6+s2 s9+s3' s0 == sC sB
              0 1 2 3 4 5 6 7 8 9 A B C D"""
g_perm_bwl = '3 1 9 6 0 4 C D 8 A 2 5 7 B'

g_mul_9_bwl_piece0 = '''
movq $0xF, s6
movq s6, x0           | x0=0xF
'''

g_mul_9_bwl_piece1 = ['pand x9, x0']

g_mul_9_bwl_piece2 = '''
| movq s3, rr[i+4]    | s7 ^7+s8 ^6+sB+s6 ^5+sD+s9" s0+sC s4+s1' [i+5] s2=v[i+1]
movq x0, s3           | s3=rp & 0xF
movq s7, x0           | x0 ^7+s8 ^6+sB+s6 ^5+sD+s9" s0+sC s4+s1' [i+5] s2=v s3
movq rr[i+5], s7      | x0 ^7+s8 ^6+sB+s6 sD+s9+s7" s0+sC s4+s1' [i+5] s2=v s3
mulx sp[9], s5, sA    | x0+sA ^7+s8+s5 ^6+sB+s6 sD+s9+s7" s0+sC s4+s1' [i+5] s2=v s3
adcx s4, s1           | x0+sA ^7+s8+s5 ^6+sB+s6 sD+s9+s7" s0+sC' s1 [i+5] s2=v s3
adox sD, s9           | x0+sA ^7+s8+s5 ^6+sB+s6" s9+s7 s0+sC' s1 [i+5] s2=v s3
movq s1, rr[i+5]      | x0+sA ^7+s8+s5 ^6+sB+s6" s9+s7 s0+sC' [i+6] s2=v s3
movq rr[i+6], s1      | x0+sA ^7+s8+s5 sB+s6+s1" s9+s7 s0+sC' [i+6] s2=v s3
mulx sp[10], s4, sD   | sD x0+sA+s4 ^7+s8+s5 sB+s6+s1" s9+s7 s0+sC' [i+6] s2=v s3
movq s2, dd           | sD x0+sA+s4 ^7+s8+s5 sB+s6+s1" s9+s7 s0+sC' [i+6] s3
adcx s0, sC           | sD x0+sA+s4 ^7+s8+s5 sB+s6+s1" s9+s7' sC [i+6] s3
movq s3, s0           | sD x0+sA+s4 ^7+s8+s5 sB+s6+s1" s9+s7' sC [i+6] s0
adox sB, s6           | sD x0+sA+s4 ^7+s8+s5" s6+s1 s9+s7' sC [i+6] s0
movq x0, s2           | sD sA+s4+s2 ^7+s8+s5" s6+s1 s9+s7' sC [i+6] s0
movq rr[i+7], sB      | sD sA+s4+s2 s8+s5+sB" s6+s1 s9+s7' sC [i+6] s0=rcx=rp & 0xF
if !aligned: jrcxz mul_10_aligned_gate_0
if aligned: jrcxz mul_10_aligned_gate_1
jmp mul_10_unaligned
if !aligned: mul_10_aligned_gate_0:
if aligned: mul_10_aligned_gate_1:
jmp mul_10_aligned
'''

#TODO: replace movdqa reg, mem with movaps and benchmark

g_mul_10_bwl = '''
if aligned: mul_10_aligned:
if !aligned: mul_10_unaligned:
                      | sD sA+s4+s2 s8+s5+sB" s6+s1 s9+s7' sC [15]
                      | wC w2+wB+w9 w8+wD+w7" w0+w1 wA+w6' w3 [15]
movq x9, w5
if !aligned: movdqa rr[1], x0
if !aligned: movdqa rr[3], x1 | x1_x1 x0_x0 __
if aligned: movq rr[0], x0
adcx wA, w6
mulx sp[0], w4, wA    | wC w2+wB+w9 w8+wD+w7" w0+w1' w6 w3 [3] wA| w4| [10] w5
adox wD, w8           | wC w2+wB+w9" w8+w7 w0+w1' w6 w3 [3] wA| w4| [10] w5
adcx w1, w0           | wC w2+wB+w9" w8+w7' w0 w6 w3 [3] wA| w4| [10] w5
mulx sp[1], w1, wD    | wC w2+wB+w9" w8+w7' w0 w6 w3 [2] wD| wA+w1| w4| [10] w5
adox wB, w2           | wC" w2+w9 w8+w7' w0 w6 w3 [2] wD| wA+w1| w4| [10] w5
adcx w8, w7           | wC" w2+w9' w7 w0 w6 w3 [2] wD| wA+w1| w4| [10] w5
mulx sp[2], wB, w8    | wC" w2+w9' w7 w0 w6 w3 .. w8| wD+wB| wA+w1| w4| [10] w5
movq w7, rr[15]       | wC" w2+w9' ^F w0 w6 w3 .. w8| wD+wB| wA+w1| w4| [10] w5
movq rr[10], w7       | wC" w2+w9' ^F w0 w6 w3 .. w8| wD+wB| wA+w1| w4+w7 [10] w5
movq w0, w5[9]        | wC" w2+w9' ^F %9 w6 w3 .. w8| wD+wB| wA+w1| w4+w7 [10] w5
movq $0, w0
adox w0, wC           | wC w2+w9' ^F %9 w6 w3 .. w8| wD+wB| wA+w1| w4+w7 [10] w5
adcx w9, w2           | wC' w2 ^F %9 w6 w3 .. w8| wD+wB| wA+w1| w4+w7 [10] w5
mulx sp[3], w0, w9    | wC' w2 ^F %9 w6 w3 w9| w8+w0| wD+wB| wA+w1| w4+w7 [10] w5
adox w7, w4           | wC' w2 ^F %9 w6 w3 w9| w8+w0| wD+wB| wA+w1|" w4 [10] w5
movq $0, w7
adcx w7, wC           | wC w2 ^F %9 w6 w3 w9| w8+w0| wD+wB| wA+w1|" w4 [10] w5
movq rr[11], w7       | wC w2 ^F %9 w6 w3 w9| w8+w0| wD+wB| wA+w1+w7" w4 [10] w5
if !aligned: vmovdqa rr[5], x2 | x2_x2 x1_x1 x0_x0 __
if aligned: movq w4, w5[10]
if !aligned: movq w4, rr[10]
                      | wC w2 ^F %9 w6 w3 w9| w8+w0| wD+wB| wA+w1+w7" [11] w5
adox wA, w1           | wC w2 ^F %9 w6 w3 w9| w8+w0| wD+wB|" w1+w7 [11] w5
mulx sp[4], w4, wA    | wC w2 ^F %9 w6 w3+wA w9+w4| w8+w0| wD+wB|" w1+w7 [11] w5
adcx w7, w1           | wC w2 ^F %9 w6 w3+wA w9+w4| w8+w0| wD+wB|"' w1 [11] w5
movq rr[12], w7       | wC w2 ^F %9 w6 w3+wA w9+w4| w8+w0| wD+wB+w7"' w1 [11] w5
adox wD, wB           | wC w2 ^F %9 w6 w3+wA w9+w4| w8+w0|" wB+w7' w1 [11] w5
movq w1, w5[11]       | wC w2 ^F %9 w6 w3+wA w9+w4| w8+w0|" wB+w7' [12] w5
mulx sp[5], w1, wD    | wC w2 ^F %9 w6+wD w3+wA+w1 w9+w4| w8+w0|" wB+w7' [12] w5
adcx wB, w7           | wC w2 ^F %9 w6+wD w3+wA+w1 w9+w4| w8+w0|"' w7 [12] w5
movq rr[13], wB       | wC w2 ^F %9 w6+wD w3+wA+w1 w9+w4| w8+w0+wB"' w7 [12] w5
adox w8, w0           | wC w2 ^F %9 w6+wD w3+wA+w1 w9+w4|" w0+wB' w7 [12] w5
movq rr[14], w8       | wC w2 ^F %9 w6+wD w3+wA+w1 w9+w4+w8" w0+wB' w7 [12] w5
movq w7, w5[12]       | wC w2 ^F %9 w6+wD w3+wA+w1 w9+w4+w8" w0+wB' [13] w5
adox w9, w4           | wC w2 ^F %9 w6+wD w3+wA+w1" w4+w8 w0+wB' [13] w5
mulx sp[6], w7, w9    | wC w2 ^F %9+w9 w6+wD+w7 w3+wA+w1" w4+w8 w0+wB' [13] w5
adcx wB, w0           | wC w2 ^F %9+w9 w6+wD+w7 w3+wA+w1" w4+w8' w0 [13] w5
movq w5[9], wB        | wC w2 ^F w9+wB w6+wD+w7 w3+wA+w1" w4+w8' w0 [13] w5
movq w0, w5[13]       | wC w2 ^F w9+wB w6+wD+w7 w3+wA+w1" w4+w8' [14] w5
adox wA, w3           | wC w2 ^F w9+wB w6+wD+w7" w3+w1 w4+w8' [14] w5
mulx sp[7], w0, wA    | wC w2 ^F+wA w9+wB+w0 w6+wD+w7" w3+w1 w4+w8' [14] w5
adcx w8, w4           | wC w2 ^F+wA w9+wB+w0 w6+wD+w7" w3+w1' w4 [14] w5
movq w4, w5[14]       | wC w2 ^F+wA w9+wB+w0 w6+wD+w7" w3+w1' [15] w5
mulx sp[8], w4, w8    | wC w2+w8 ^F+wA+w4 w9+wB+w0 w6+wD+w7" w3+w1' [15] w5
adox wD, w6           | wC w2+w8 ^F+wA+w4 w9+wB+w0" w6+w7 w3+w1' [15] w5
movq rr[15], wD       | wC w2+w8 wD+wA+w4 w9+wB+w0" w6+w7 w3+w1' [15] w5
adcx w3, w1
movq w1, w5[15]       | wC w2+w8 wD+wA+w4 w9+wB+w0" w6+w7' [16] w5
mulx sp[9], w1, w3    | wC+w3 w2+w8+w1 wD+wA+w4 w9+wB+w0" w6+w7' [16] w5
adox wB, w9           | wC+w3 w2+w8+w1 wD+wA+w4" w9+w0 w6+w7' [16] w5
mulx sp[10], wB, dd   | dd wC+w3+wB w2+w8+w1 wD+wA+w4" w9+w0 w6+w7' [16] w5
if !aligned: movdqa rr[7], x3 |
if !aligned: movdqa rr[9], x4 | x4_x4 x3_x3 x2_x2 x1_x1 x0_x0 __
adcx w7, w6           | dd wC+w3+wB w2+w8+w1 wD+wA+w4" w9+w0' w6 [16] w5
if aligned: movq rr[1], w7
if aligned: movq rr[2], x1 | ... x1 w7 x0
adox wA, wD           | dd wC+w3+wB w2+w8+w1" wD+w4 w9+w0' w6 [16] w5
movq w6, w5[16]       | dd wC+w3+wB w2+w8+w1" wD+w4 w9+w0' [17] w5
if aligned: movq rr[3], w6    | ... w6 x1 w7 x0
if !aligned: movq rr[0], w6   | x4_x4 x3_x3 x2_x2 x1_x1 x0_x0 w6
if aligned: pinsrq $1, w7, x0 | ... w6 x1 x0_x0
adcx w9, w0           | dd wC+w3+wB w2+w8+w1" wD+w4' w0 [17] w5
if aligned: movq rr[4], x2    | ... x2 w6 x1 x0_x0
movq w0, w5[17]       | dd wC+w3+wB w2+w8+w1" wD+w4' [18] w5
if aligned: movq rr[5], w0    | ... w0 x2 w6 x1 x0_x0
adox w8, w2           | dd wC+w3+wB" w2+w1 wD+w4' [18] w5
if aligned: pinsrq $1, w6, x1 | ... w0 x2 x1_x1 x0_x0
if aligned: movq rr[6], x3    | ... x3 w0 x2 x1_x1 x0_x0
adcx wD, w4
movq w4, w5[18]       | dd wC+w3+wB" w2+w1' [19] w5
if aligned: movq rr[7], w4    | ... w4 x3 w0 x2 x1_x1 x0_x0
if aligned: pinsrq $1, w0, x2 | ... w4 x3 x2_x2 x1_x1 x0_x0
adox wC, w3           | dd" w3+wB w2+w1' [19] w5
if aligned: movq rr[8], x4    | .. x4 w4 x3 x2_x2 x1_x1 x0_x0
adcx w2, w1           | dd" w3+wB' w1 [19] w5
if aligned: movq rr[9], w2    | w2 x4 w4 x3 x2_x2 x1_x1 x0_x0
if aligned: pinsrq $1, w4, x3 | w2 x4 x3_x3 x2_x2 x1_x1 x0_x0
movq w1, w5[19]       | dd" w3+wB' [20] w5
if !aligned: movq w6, w5[0]
if !aligned: movdqa x0, w5[1] | x4_x4 x3_x3 x2_x2 x1_x1 [3]
if aligned: movdqa x0, w5[0]
if aligned: movdqa x1, w5[2]   | w2 x4 x3_x3 x2_x2 [4]
if aligned: pinsrq $1, w2, x4  | x4_x4 x3_x3 x2_x2 [4]
movq $0, w0
adox w0, dd           | dd w3+wB' [20] w5
adcx wB, w3           | dd' w3 [20] w5
if !aligned: movdqa x1, w5[3]
if !aligned: movdqa x2, w5[5] | x4_x4 x3_x3 [7]
if aligned: movdqa x2, w5[4]
if aligned: movdqa x3, w5[6]  | x4_x4 [8]
movq w3, w5[20]
adcx w0, dd           | dd [21] w5
if !aligned: movdqa x3, w5[7]
if !aligned: movdqa x4, w5[9]
if aligned: movdqa x4, w5[8]
movq dd, w5[21]
if !aligned: jmp all_done
'''

def extract_v(t, i, a):
    if (i <= 0) or (i >= 11):
        return
    if a:
        i -= 1    # 0,1 -> x0,    2,3 -> x1
        if i & 1:
            return 'pextrq $0x1, x%s, %s' % (i / 2, t)
        else:
            return 'movq x%s, %s' % (i / 2, t)
    if i == 1:
        return 'movq x0, ' + t
    if i == 10:
        return 'movq x5, ' + t
    i -= 2       # 0,1 -> x1,    2,3 -> x2
    if i & 1:
        return 'pextrq $0x1, x%s, %s' % (i / 2 + 1, t)
    else:
        return 'movq x%s, %s' % (i / 2 + 1, t)

def evaluate_if(s, how, maybe_excl, body):
    if how is None:
        return s
    if how and (maybe_excl == '!'):
        return ''
    if (not how) and (maybe_excl == ''):
        return ''
    if how and (maybe_excl == ''):
        return body
    if (not how) and (maybe_excl == '!'):
        return body
    return s

g_movdqa_patt = re.compile('^movdqa ')
def replace_movdqa_with_movaps(s):
    m = g_movdqa_patt.match(s)
    if not m:
        return s
    return s.replace('movdqa', 'movaps')

g_movdqa_to_mem_patt = re.compile('^movdqa x')
def replace_movdqa_to_mem_with_movaps(s):
    m = g_movdqa_to_mem_patt.match(s)
    if not m:
        return s
    return s.replace('movdqa', 'movaps')

g_v_patt = re.compile(r'(.+):=v\[(.+)\]')
g_iplus_patt = re.compile(r'i\+(.+?)\b')
g_if_aligned_patt = re.compile(r'if (.*?)aligned: (.+)')
g_if_amd_patt = re.compile(r'if (.*?)amd: (.+)')
g_rr_array = re.compile(r'rr\[(.+?)\]')                  # rr[x] := sp[11+x]
g_array_patt = re.compile(r'\b([a-zA-Z0-9]+)\b\[(.+?)\]')
g_adx3_patt = re.compile(r'ad(\S)3\((.+?), (.+?), (.+?)\)')
g_dqa_or_aps_patt = re.compile('dqa_or_aps')
def evaluate_row(s, i, amd, aligned):
    m = g_if_aligned_patt.match(s)
    if m:
        s = evaluate_if(s, aligned, m.group(1), m.group(2))

    m = g_if_amd_patt.match(s)
    if m:
        s = evaluate_if(s, amd, m.group(1), m.group(2))

    m = g_iplus_patt.search(s)
    if m:
        s = s.replace(m.group(), '%s' % (int(m.group(1)) + i))
    s = re.sub(r'\bi\b', '%s' % i, s)

    m = g_v_patt.match(s)
    if m:
        return [extract_v(m.group(1), int(m.group(2)), not aligned)]

    m = g_dqa_or_aps_patt.search(s)
    if m:
        if amd:
            s = s.replace(m.group(), 'movaps')
        else:
            s = s.replace(m.group(), 'movdqa')

    m = g_rr_array.search(s)
    if m:
        s = s.replace(m.group(), 'sp[%s]' % (11 + int(m.group(1))))

    m = g_array_patt.search(s)
    if m:
        j = int(m.group(2))
        if j == 0:
            s = s.replace(m.group(), '(%s)' % m.group(1))
        else:
            s = s.replace(m.group(), '%s(%s)' % (j * 8, m.group(1)))

    m = g_adx3_patt.match(s)
    if m:
        return [
                'ad%sx %s, %s' % (m.group(1), m.group(2), m.group(3)),
                'movq %s, %s' % (m.group(3), m.group(2)),
               ]
    '''
                'movq %s, %s' % (m.group(2), m.group(4)),
                'ad%sx %s, %s' % (m.group(1), m.group(3), m.group(4)),
                'movq %s, %s' % (m.group(4), m.group(2)),
    '''

    # Replace (some of) movdqa with movaps
    '''
    movaps instead of movdqa makes code slower on Ryzen, slightly faster on Skylake
    if amd:
        s = replace_movdqa_with_movaps(s)
    '''
    s = replace_movdqa_to_mem_with_movaps(s)

    return [s]

def chew_code(src, amd, i, aligned, p):
    if not isinstance(src, list):
        src = P.cutoff_comments(src)

    if i:
        rr = ['# mul_add %s' % i]
        if p:
            e = '# '
            for x in range(len(p)):
                e += 's%X->W%X ' % (x, p[x])
            rr.append(e)
    else:
        rr = []

    for j in src:
        k = evaluate_row(j, i, amd, aligned)
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

def cook_asm(o, code, var_map):
    code = '\n'.join(code)

    code = P.replace_symbolic_names_wr(code, var_map)

    comment = P.g_autogenerated_patt % os.path.basename(sys.argv[0])
    o.write(comment.replace('//', '#'))
    P.write_asm_procedure_header(o, P.guess_subroutine_name(sys.argv[1]))
    P.write_asm_inside(o, code + '\nretq')

def inject(tt, subs, what):
    i = [i for i in range(len(tt)) if tt[i].find(subs) != -1][0] + 1
    return tt[:i] + what + tt[i:]

def form_m9(src, amd):
    if amd:
        rez = P.cutoff_comments(g_mul_9_bwl_piece0) + src
        p = 'adc3(rr[i+4], sC, s8)'
        i = [i for i in range(len(rez)) if rez[i].find(p) != -1][0] + 1
        rez = rez[:i] + P.cutoff_comments(g_mul_9_zen_piece2)
    else:
        rez = P.cutoff_comments(g_mul_9_bwl_piece0) + src
        i = [i for i in range(len(rez)) if rez[i].find('movq s3, rr[i+4]') != -1]
        i = i[0] + 1
        rez = rez[:i] + P.cutoff_comments(g_mul_9_bwl_piece2)
    rez = inject(rez, 'mulx sp[3]', g_mul_9_bwl_piece1)
    return rez

def v_alignment_code(amd, v_alignment, xmm_save):
    aligned = not v_alignment

    if aligned:
        code = chew_code(g_v_load_0, amd, 0, aligned, None)
    else:
        code = []
    code += chew_code(g_mul_0, amd, 0, aligned, None)

    if amd:
        m_1 = P.cutoff_comments(g_mul_1_zen)
        m_2 = P.cutoff_comments(g_mul_2_zen)
        m_A = P.cutoff_comments(g_mul_10_zen)
        q = [int(i, 16) for i in g_perm_zen.split(' ')]
    else:
        m_1 = P.cutoff_comments(g_mul_1_bwl)
        m_2 = P.cutoff_comments(g_mul_2_bwl)
        m_A = P.cutoff_comments(g_mul_10_bwl)
        q = [int(i, 16) for i in g_perm_bwl.split(' ')]
    m_9 = form_m9(m_2, amd)

    p = list(range(0xD + 1))

    code += chew_code(m_1, amd, 1, aligned, p)
    code += chew_code(m_2, amd, 2, aligned, p)
    for i in range(3, 9):
        p = P.composition(p, q)
        code += chew_code(m_2, amd, i, aligned, p)
    p = P.composition(p, q)
    code += chew_code(m_9, amd, 9, aligned, p)

    if aligned:
        code += chew_code(m_A, amd, 10, False, None)
        P.insert_restore(code, xmm_save)
        code += chew_code(m_A, amd, 10, True, None)
        P.insert_restore(code, xmm_save)
    return code

def do_it(o, amd):
    var_map = g_var_map
    for i in range(16):
        var_map += ' x%X,xmm%s' % (i, i)
    code = g_memcpy_11.replace('@stack_taken', '%s' % g_stack_taken)
    code = chew_code(code + g_v_load_1, amd, 0, None, None)

    xmm_save = P.save_registers_in_xmm(code, g_save_regs_max)
    code += v_alignment_code(amd, 8, xmm_save) + v_alignment_code(amd, 0, xmm_save)
    P.save_in_xmm(code, xmm_save)

    code = '\n'.join(code)
    code = re.sub(r'\bwC\b', 'up', code)
    code = re.sub(r'\bwD\b', 'rp', code)
    code = code.split('\n')

    code += ['all_done:', 'add $%s,sp' % g_stack_taken]
    cook_asm(o, code, var_map)

def show_postcondition():
    p = list(range(0xD + 1))
    q = [int(x, 16) for x in g_perm_bwl.split(' ')]
    b = '''s7 sC+s9+s5 s8+sB+s1" s3+sA s2+s0' s4 == s6 sD'''
    l = '''sD s7+sA+s4 s8+s5+s1" s6+s2 s9+s3' s0 == sC sB'''
    l9 = '''sD sA+s4+s2 s8+s5+sB" s6+s1 s9+s7' sC'''
    print 'Broadwell'
    for i in range(2, 10):
        print 'i=%X pre' % i, E.apply_s_permutation(b, p)
        if i == 9:
            print E.apply_s_permutation(l9, p)
        print 'i=%X pst' % i, E.apply_s_permutation(l, p)
        p = P.composition(p, q)
    p = list(range(0xD + 1))
    b = '''sD sC+s9+sB sA+s4+s0 s7+s5+s2" s1| s3|' == s6 s8'''
    l = '''s3 sD+s8+s7 s9+s5+s6 s0+sA+sC" s2| sB|' == s1 s4'''
    l9 = '''sD s9 s0+sA s2+s7+s1 sB+s3|" s6|' == s4=v[10]'''
    q = [int(x, 16) for x in g_perm_zen.split(' ')]
    print '\nZen'
    for i in range(2, 10):
        print 'i=%X pre' % i, E.apply_s_permutation(b, p)
        if i == 9:
            print E.apply_s_permutation(l9, p)
        print 'i=%X pst' % i, E.apply_s_permutation(l, p)
        p = P.composition(p, q)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        show_postcondition()
        sys.exit(0)

    g_amd = sys.argv[1].find('zen') != -1
    with open(sys.argv[1], 'wb') as g_out:
        do_it(g_out, g_amd)
