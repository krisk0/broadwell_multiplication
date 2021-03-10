'''
10x10 multiplication targeting Zen. Uses aligned loads of v[] into xmm's.

174 ticks on Ryzen, 194 ticks on Broadwell.
'''

g_var_map = 'rp,rdi wC,rsi wB,rbp wA,rbx w9,r12 w8,r13 w7,r14 w6,r15 ' + \
    'w0,rax w1,r8 w2,r9 w3,r10 w4,r11 w5,rcx dd,rdx sp,rsp ' + \
    ' '.join(['x%X,xmm%s' % (i, i) for i in range(16)])

"""
xmm usage:
0-4 v[]
"""

g_preamble = '''
vzeroupper
movq sp, rp[17]
movq wC, sp
movq dd, w5
and $0xF, dd
movq w5[0], dd
movq w5[1], w6        | w6=v[1]
jz align0
movq w5[2], x0
movdqa w5[3], x1
movdqa w5[5], x2
movdqa w5[7], x3
movq w5[9], x4
'''

g_load_0 = '''
align0:
movdqa w5[2], x0
movdqa w5[4], x1
movdqa w5[6], x2
movdqa w5[8], x3
'''

g_mul_01 = '''
mulx sp[0], w0, w1    | w1 w0 == w6=v[1]
mulx sp[1], w2, w3    | w3 w1+w2 w0 == w6=v[1]
xchg dd, w6           | w3 w1+w2 w0 == dd=v[1] w6=v[0]
mulx sp[0], w4, w7    | w3+w7 w1+w2+w4 w0 == dd=v[1] w6=v[0]
mulx sp[2], w8, w9    | w9 w8 w3+w7 w1+w2+w4 w0 == dd=v[1] w6=v[0]
xchg w6, dd           | w9 w8 w3+w7 w1+w2+w4 w0 == w6=v[1] dd=v[0]
mulx sp[2], wA, wB    | w9 w8+wB w3+w7+wA w1+w2+w4 w0 == w6=v[1] dd=v[0]
movq w0, rp[0]        | w9 w8+wB w3+w7+wA w1+w2+w4 .. == w6=v[1] dd=v[0]
adox w2, w1           | w9 w8+wB w3+w7+wA" w1+w4 .. == w6=v[1] dd=v[0]
mulx sp[3], w0, w2    | w9+w2 w8+wB+w0 w3+w7+wA" w1+w4 .. == w6=v[1] dd=v[0]
mulx sp[4], w5, wC    | wC w9+w2+w5 w8+wB+w0 w3+w7+wA" w1+w4 .. == w6=v[1] dd=v[0]
adox w7, w3           | wC w9+w2+w5 w8+wB+w0" w3+wA w1+w4 .. == w6=v[1] dd=v[0]
adcx w4, w1           | wC w9+w2+w5 w8+wB+w0" w3+wA' w1 .. == w6=v[1] dd=v[0]
movq w1, rp[1]        | wC w9+w2+w5 w8+wB+w0" w3+wA' [2] == w6=v[1] dd=v[0]
movq w6, rp[3]        | rp[3]=v[1]
mulx sp[5], w1, w4    | w4 wC+w1 w9+w2+w5 w8+wB+w0" w3+wA' [2] == w6=v[1] dd=v[0]
xchg w6, dd           | w4 wC+w1 w9+w2+w5 w8+wB+w0" w3+wA' [2] == w6=v[0] dd=v[1]
movq w6, rp[4]       | rp[4]=v[0]
mulx sp[4], w7, w6  | w4+w6 wC+w1+w7 w9+w2+w5 w8+wB+w0" w3+wA' [2] == dd=v[1]
adox wB, w8         | w4+w6 wC+w1+w7 w9+w2+w5" w8+w0 w3+wA' [2] ==
adcx wA, w3         | w4+w6 wC+w1+w7 w9+w2+w5" w8+w0' w3 [2] ==
movq w3, rp[2]      | w4+w6 wC+w1+w7 w9+w2+w5" w8+w0' [3] ==
movq rp[4], dd      | dd=v[0]
mulx sp[6], w3, wA  | wA w4+w6+w3 wC+w1+w7 w9+w2+w5" w8+w0' [3] == dd=v[0]
adox w9, w2         | wA w4+w6+w3 wC+w1+w7" w2+w5 w8+w0' [3] == dd=v[0]
mulx sp[7], w9, wB  | wB wA+w9 w4+w6+w3 wC+w1+w7" w2+w5 w8+w0' [3] == dd=v[0]
adcx w8, w0         | wB wA+w9 w4+w6+w3 wC+w1+w7" w2+w5' w0 [3] == dd=v[0]
movq rp[3], w8      | wB wA+w9 w4+w6+w3 wC+w1+w7" w2+w5' w0 [3] == dd=v[0] w8=v[1]
movq w0, rp[3]      | wB wA+w9 w4+w6+w3 wC+w1+w7" w2+w5' [4] == dd=v[0] w8=v[1]
adox w1, wC         | wB wA+w9 w4+w6+w3" wC+w7 w2+w5' [4] == dd=v[0] w8=v[1]
                    | xchg appears to be slightly better on Ryzen than movq
                    | Skylake seems to prefer movq
xchg dd, w0         | wB wA+w9 w4+w6+w3" wC+w7 w2+w5' [4] == w0=v[0] w8=v[1]
xchg w8, dd         | wB wA+w9 w4+w6+w3" wC+w7 w2+w5' [4] == w0=v[0] dd=v[1]
mulx sp[6], w1, w8  | wB+w8 wA+w9+w1 w4+w6+w3" wC+w7 w2+w5' [4] == w0=v[0] dd=v[1]
xchg dd, w0         | wB+w8 wA+w9+w1 w4+w6+w3" wC+w7 w2+w5' [4] == dd=v[0] w0=v[1]
adcx w5, w2         | wB+w8 wA+w9+w1 w4+w6+w3" wC+w7' w2 [4] == dd=v[0] w0=v[1]
movq w2, rp[4]      | wB+w8 wA+w9+w1 w4+w6+w3" wC+w7' [5] == dd=v[0] w0=v[1]
adox w6, w4         | wB+w8 wA+w9+w1" w4+w3 wC+w7' [5] == dd=v[0] w0=v[1]
mulx sp[8], w2, w5  | w5 wB+w8+w2 wA+w9+w1" w4+w3 wC+w7' [5] == dd=v[0] w0=v[1]
adcx wC, w7         | w5 wB+w8+w2 wA+w9+w1" w4+w3' w7 [5] == dd=v[0] w0=v[1]
movq w7, rp[5]      | w5 wB+w8+w2 wA+w9+w1" w4+w3' [6] == dd=v[0] w0=v[1]
w7:=v[2]
mulx sp[9], w6, wC  | wC w5+w6 wB+w8+w2 wA+w9+w1" w4+w3' [6] == dd=v[0] w0=v[1]
movq w0, dd
adox w9, wA         | wC w5+w6 wB+w8+w2" wA+w1 w4+w3' [6] == dd=v[1]
adcx w4, w3         | wC w5+w6 wB+w8+w2" wA+w1' w3 [6] == dd=v[1]
movq w3, rp[6]      | wC w5+w6 wB+w8+w2" wA+w1' [7] == dd=v[1] w7=v[2]
mulx sp[8], w0, w9  | wC+w9 w5+w6+w0 wB+w8+w2" wA+w1' [7] == dd=v[1] w7=v[2]
mulx sp[9], w3, w4  | w4 wC+w9+w3 w5+w6+w0 wB+w8+w2" wA+w1' [7] == dd=v[1] w7=v[2]
adox w8, wB         | w4 wC+w9+w3 w5+w6+w0" wB+w2 wA+w1' [7] == dd=v[1] w7=v[2]
adcx wA, w1         | w4 wC+w9+w3 w5+w6+w0" wB+w2' w1 [7] dd=v[1] w7=v[2]
movq w1, rp[7]      | w4 wC+w9+w3 w5+w6+w0" wB+w2' [8] dd=v[1] w7=v[2]
mulx sp[1], w8, wA  | w4 wC+w9+w3 w5+w6+w0" wB+w2' {4} wA: w8: [2] dd=v[1] w7=v[2]
adox w6, w5         | w4 wC+w9+w3" w5+w0 wB+w2' {4} wA: w8: [2] dd=v[1] w7=v[2]
adcx wB, w2         | w4 wC+w9+w3" w5+w0' w2 {4} wA: w8: [2] dd=v[1] w7=v[2]
movq w2, rp[8]      | w4 wC+w9+w3" w5+w0' {5} wA: w8: [2] dd=v[1] w7=v[2]
xchg dd, w7         | w4 wC+w9+w3" w5+w0' {5} wA: w8: [2] dd=v[2] w7=v[1]
mulx sp[0], w1, w2  | w4 wC+w9+w3" w5+w0' {5} wA+w2: w8+w1: [2] dd=v[2] w7=v[1]
mulx sp[2], w6, wB  | w4 wC+w9+w3" w5+w0' {3} wB: w6: wA+w2: w8+w1: [2] dd=v[2] w7
xchg dd, w7         | w4 wC+w9+w3" w5+w0' {3} wB: w6: wA+w2: w8+w1: [2] dd=v[1] w7
adox w9, wC         | w4" wC+w3 w5+w0' {3} wB: w6: wA+w2: w8+w1: [2] dd=v[1] w7
movq $0, w9
adcx w5, w0         | w4" wC+w3' w0 {3} wB: w6: wA+w2: w8+w1: [2] dd=v[1] w7
adox w9, w4         | w4 wC+w3' w0 {3} wB: w6: wA+w2: w8+w1: [2] dd=v[1] w7
mulx sp[3], w5, w9  | w4 wC+w3' w0 {3} wB+w9: w6+w5: wA+w2: w8+w1: [2] dd=v[1] w7
adcx wC, w3         | w4' w3 w0 {3} wB+w9: w6+w5: wA+w2: w8+w1: [2] dd=v[1] w7
movq $0, wC
adox rp[2], w8      | w4' w3 w0 {3} wB+w9: w6+w5: wA+w2:" w8+w1 [2] dd=v[1] w7
adcx wC, w4         | w4 w3 w0 {3} wB+w9: w6+w5: wA+w2:" w8+w1 [2] dd=v[1] w7
adox rp[3], wA      | w4 w3 w0 {3} wB+w9: w6+w5:" wA+w2 w8+w1 [2] dd=v[1] w7
adcx w8, w1         | w4 w3 w0 {3} wB+w9: w6+w5:" wA+w2' w1 [2] dd=v[1] w7
movq w1, rp[2]      | w4 w3 w0 {3} wB+w9: w6+w5:" wA+w2' [3] dd=v[1] w7=v[2]
mulx sp[5], w8, wC  | w4 w3 w0 .. wC: w8: wB+w9: w6+w5:" wA+w2' [3] dd=v[1] w7=v[2]
adox rp[4], w6      | w4 w3 w0 .. wC: w8: wB+w9:" w6+w5 wA+w2' [3] dd=v[1] w7=v[2]
adcx wA, w2
movq w2, rp[3]      | w4 w3 w0 .. wC: w8: wB+w9:" w6+w5' [4] dd=v[1] w7=v[2]
mulx sp[7], w1, wA  | w4 w3 w0+wA w1: wC: w8: wB+w9:" w6+w5' [4] dd=v[1] w7=v[2]
movq w7, dd         | w4 w3 w0+wA w1: wC: w8: wB+w9:" w6+w5' [4] dd=v[2]
mulx sp[4], w2, w7  | w4 w3 w0+wA w1: wC+w7: w8+w2: wB+w9:" w6+w5' [4] dd=v[2]
adox rp[5], wB      | w4 w3 w0+wA w1: wC+w7: w8+w2:" wB+w9 w6+w5' [4] dd=v[2]
adcx w6, w5
movq w5, rp[4]      | w4 w3 w0+wA w1: wC+w7: w8+w2:" wB+w9' [5] dd=v[2]
mulx sp[6], w5, w6  | w4 w3 w0+wA+w6 w1+w5: wC+w7: w8+w2:" wB+w9' [5] dd=v[2]
adox rp[6], w8      | w4 w3 w0+wA+w6 w1+w5: wC+w7:" w8+w2 wB+w9' [5] dd=v[2]
adcx wB, w9
movq w9, rp[5]      | w4 w3 w0+wA+w6 w1+w5: wC+w7:" w8+w2' [6] dd=v[2]
mulx sp[8], w9, wB  | w4+wB w3+w9 w0+wA+w6 w1+w5: wC+w7:" w8+w2' [6] dd=v[2]
adox rp[7], wC      | w4+wB w3+w9 w0+wA+w6 w1+w5:" wC+w7 w8+w2' [6] dd=v[2]
adcx w8, w2
movq w2, rp[6]      | w4+wB w3+w9 w0+wA+w6 w1+w5:" wC+w7' [7] dd=v[2]
mulx sp[9], w2, w8  | w8 w4+wB+w2 w3+w9 w0+wA+w6 w1+w5:" wC+w7' [7] dd=v[2]
adox rp[8], w1      | w8 w4+wB+w2 w3+w9 w0+wA+w6" w1+w5 wC+w7' [7] dd=v[2]
adcx wC, w7
movq w7, rp[7]      | w8 w4+wB+w2 w3+w9 w0+wA+w6" w1+w5' [8] dd=v[2]
mulx sp[7], w7, wC  | w8 w4+wB+w2 w3+w9+wC w0+wA+w6+w7" w1+w5' [8] dd=v[2]
adox wA, w0         | w8 w4+wB+w2 w3+w9+wC" w0+w6+w7 w1+w5' [8] dd=v[2]
wA:=v[3]            | w8 w4+wB+w2 w3+w9+wC" w0+w6+w7 w1+w5' [8] dd=v[2] wA=v[3]
adcx w5, w1
movq w1, rp[8]      | w8 w4+wB+w2 w3+w9+wC" w0+w6+w7' [9] dd=v[2] wA=v[3]
mulx sp[1], w5, w1  | w8 w4+wB+w2 w3+w9+wC" w0+w6+w7' {4} w1: w5: [3] dd=v[2] wA=v[3]
adox w9, w3         | w8 w4+wB+w2" w3+wC w0+w6+w7' {4} w1: w5: [3] dd=v[2] wA=v[3]
adcx w6, w0         | w8 w4+wB+w2" w3+wC' w0+w7 {4} w1: w5: [3] dd=v[2] wA=v[3]
mulx sp[3], w6, w9  | w8 w4+wB+w2" w3+wC' w0+w7 {2} w9: w6: w1: w5: [3] dd=v[2] wA
adox wB, w4         | w8" w4+w2 w3+wC' w0+w7 {2} w9: w6: w1: w5: [3] dd=v[2] wA
movq $0, wB
adox wB, w8         | w8 w4+w2' w3 w0+w7 {2} w9: w6: w1: w5: [3] dd=v[2] wA
adcx wC, w3
mulx sp[5], wB, wC  | w8 w4+w2' w3 w0+w7 wC: wB: w9: w6: w1: w5: [3] dd=v[2] wA
movq wA, dd
ado2 rp[3], w5      | w8 w4+w2' w3 w0+w7 wC: wB: w9: w6: w1:" [4] dd=v[3]
'''

g_mul_3 = '''
                   | i >= 3
                   | s8 s4+s2' s3 s0+s7 sC: sB: s9: s6: s1:" [i+1] dd=v[i]
rp[i+8]:=v[i+1]    | TODO: move this line
mulx sp[5], s5, sA | s8 s4+s2' s3 s0+s7+sA sC+s5: sB: s9: s6: s1:" [i+1] dd=v[i]
adcx s4, s2        | s8' s4 s3 s0+s7+sA sC+s5: sB: s9: s6: s1:" [i+1] dd=v[i]
movq $0, s4
adox rp[i+1], s1
movq s1, rp[i+1]   | s8' s2 s3 s0+s7+sA sC+s5: sB: s9: s6:" [i+2] dd=v[i]
adcx s4, s8        | s8 s3 s3 s0+s7+sA sC+s5: sB: s9: s6:" [i+2] dd=v[i]
mulx sp[7], s1, s4 | s8 s2+s4 s3+s1 s0+s7+sA sC+s5: sB: s9: s6:" [i+2] dd=v[i]
adox rp[i+2], s6
movq s6, rp[i+2]   | s8 s2+s4 s3+s1 s0+s7+sA sC+s5: sB: s9:" [i+3] dd=v[i]
adcx s7, s0        | s8 s2+s4 s3+s1' s0+wA sC+s5: sB: s9:" [i+3] dd=v[i]
mulx sp[9], s6, s7 | s7 s8+s6 s2+s4 s3+s1' s0+wA sC+s5: sB: s9:" [i+3]
ado2 rp[i+3], s9   | s7 s8+s6 s2+s4 s3+s1' s0+wA sC+s5: sB:" [i+4]
movq $0, s9
adcx s9, s3        | s7 s8+s6 s2+s4' s3+s1 s0+sA sC+s5: sB:" [i+4]
ado2 rp[i+4], sB   | s7 s8+s6 s2+s4' s3+s1 s0+sA sC+s5:" [i+5]
mulx sp[0], s9, sB | s7 s8+s6 s2+s4' s3+s1 s0+sA sC+s5:" {3} sB: s9: [i]
adox s5, sC        | s7 s8+s6 s2+s4' s3+s1 s0+sA" sC: {3} sB: s9: [i]
adcx s2, s4        | s7 s8+s6' s4 s3+s1 s0+sA" sC: {3} sB: s9: [i]
mulx sp[1], s2, s5 | s7 s8+s6' s4 s3+s1 s0+sA" sC: {2} s5: sB+s2: s9: [i]
adox sA, s0        | s7 s8+s6' s4 s3+s1" s0 sC: {2} s5: sB+s2: s9: [i]
adcx s6, s8        | s7' s8 s4 s3+s1" s0 sC: {2} s5: sB+s2: s9: [i]
mulx sp[3], s6, sA | s7' s8 s4 s3+s1" s0 sC: sA: s6: s5: sB+s2: s9: [i]
adox s1, s3        | s7' s8 s4" s3 s0 sC: sA: s6: s5: sB+s2: s9: [i]
movq $0, s1
adcx s1, s7        | s7 s8 s4" s3 s0 sC: sA: s6: s5: sB+s2: s9: [i]
adc2 rp[i], s9     | s7 s8 s4" s3 s0 sC: sA: s6: s5: sB+s2:' [i+1]
mulx sp[2], s1, s9 | s7 s8 s4" s3 s0 sC: sA: s6+s9: s5+s1: sB+s2:' [i+1]
adcx s2, sB        | s7 s8 s4" s3 s0 sC: sA: s6+s9: s5+s1:' sB: [i+1]
movq $0, s2
adox s2, s4        | s7 s8" s4 s3 s0 sC: sA: s6+s9: s5+s1:' sB: [i+1]
movq s4, rp[i+6]   | s7 s8" ^6 s3 s0 sC: sA: s6+s9: s5+s1:' sB: [i+1]
adcx rp[i+2], s5   | s7 s8" ^6 s3 s0 sC: sA: s6+s9:' s5+s1 sB: [i+1]
mulx sp[4], s2, s4 | s7 s8" ^6 s3 s0 sC+s4: sA+s2: s6+s9:' s5+s1 sB: [i+1] left 6 8
movq s3, rp[i+7]   | s7 s8" ^6 ^7 s0 sC+s4: sA+s2: s6+s9:' s5+s1 sB: [i+1]
movq $0, s3
adox s3, s8        | s7" s8 ^6 ^7 s0 sC+s4: sA+s2: s6+s9:' s5+s1 sB: [i+1]
adcx rp[i+3], s6   | s7" s8 ^6 ^7 s0 sC+s4: sA+s2:' s6+s9 s5+s1 sB: [i+1]
adox s3, s7        | s7 s8 ^6 ^7 s0 sC+s4: sA+s2:' s6+s9 s5+s1 sB: [i+1]
adcx rp[i+4], sA   | s7 s8 ^6 ^7 s0 sC+s4:' sA+s2 s6+s9 s5+s1 sB: [i+1]
ado2 rp[i+1], sB   | s7 s8 ^6 ^7 s0 sC+s4:' sA+s2 s6+s9 s5+s1" [i+2]
mulx sp[6], s3, sB | s7 s8 ^6 ^7+sB s0+s3 sC+s4:' sA+s2 s6+s9 s5+s1" [i+2]
adcx rp[i+5], sC   | s7 s8 ^6 ^7+sB s0+s3' sC+s4 sA+s2 s6+s9 s5+s1" [i+2]
adox s1, s5
movq s5, rp[i+2]   | s7 s8 ^6 ^7+sB s0+s3' sC+s4 sA+s2 s6+s9" [i+3]
movq rp[i+7], s1   | s7 s8 ^6 s1+sB s0+s3' sC+s4 sA+s2 s6+s9" [i+3]
adox s9, s6
movq s6, rp[i+3]   | s7 s8 ^6 s1+sB s0+s3' sC+s4 sA+s2" [i+4]
mulx sp[8], s5, s6 | s7 s8+s6 ^6+s5 s1+sB s0+s3' sC+s4 sA+s2" [i+4]
movq rp[i+8], dd
adox s2, sA
movq sA, rp[i+4]   | s7 s8+s6 ^6+s5 s1+sB s0+s3' sC+s4" [i+5]
movq sC, rp[i+5]   | s7 s8+s6 ^6+s5 s1+sB s0+s3' s4:" [i+5]
'''

g_mul_4 = '''
                   | i>=4
                   | s7 s8+s6 ^5+s5 s1+sB s0+s3' s4:" [i+4] dd=v[i]
rp[i+8]:=v[i+1]
mulx sp[5], s2, sA | s7 s8+s6 ^5+s5 s1+sB+sA s0+s3+s2' s4:" [i+4]
mulx sp[7], s9, sC | s7 s8+s6+sC ^5+s5+s9 s1+sB+sA s0+s3+s2' s4:" [i+4]
adcx s3, s0        | s7 s8+s6+sC ^5+s5+s9 s1+sB+sA' s0+s2 s4:" [i+4]
ado2 rp[i+4], s4   | s7 s8+s6+sC ^5+s5+s9 s1+sB+sA' s0+s2" [i+5]
mulx sp[9], s3, s4 | s4 s7+s3 s8+s6+sC ^5+s5+s9 s1+sB+sA' s0+s2" [i+5]
adcx sB, s1        | s4 s7+s3 s8+s6+sC ^5+s5+s9' s1+sA s0+s2" [i+5]
adcx rp[i+5], s5   | s4 s7+s3 s8+s6+sC' s5+s9 s1+sA s0+s2" [i+5]
adox s2, s0        | s4 s7+s3 s8+s6+sC' s5+s9 s1+sA" s0 [i+5]
movq s0, rp[i+5]   | s4 s7+s3 s8+s6+sC' s5+s9 s1+sA" [i+6]
mulx sp[0], s0, s2 | s4 s7+s3 s8+s6+sC' s5+s9 s1+sA" {4} s2: s0: [i]
adcx s6, s8        | s4 s7+s3' s8+sC s5+s9 s1+sA" {4} s2: s0: [i]
adox sA, s1        | s4 s7+s3' s8+sC s5+s9" s1 {4} s2: s0: [i]
movq s1, rp[i+6]   | s4 s7+s3' s8+sC s5+s9" {5} s2: s0: [i]
mulx sp[8], sA, sB | s4 s7+s3+sB' s8+sC+sA s5+s9" {5} s2: s0: [i]
movq $0, s1
adcx s3, s7        | s4' s7+sB s8+sC+sA s5+s9" {5} s2: s0: [i]
adox s9, s5        | s4' s7+sB s8+sC+sA" s5 {5} s2: s0: [i]
movq s5, rp[i+7]   | s4' s7+sB s8+sC+sA" {6} s2: s0: [i]
mulx sp[1], s3, s6 | s4' s7+sB s8+sC+sA" {5} s6: s2+s3: s0: [i]
adcx s1, s4        | s4 s7+sB s8+sC+sA" {5} s6: s2+s3: s0: [i]
adox sC, s8        | s4 s7+sB" s8+sA {5} s6: s2+s3: s0: [i]
mulx sp[3], s1, s9 | s4 s7+sB" s8+sA {3} s9: s1: s6: s2+s3: s0: [i]
adc2 rp[i], s0     | s4 s7+sB" s8+sA {3} s9: s1: s6: s2+s3:' [i+1]
mulx sp[2], s0, sC | s4 s7+sB" s8+sA {3} s9: s1+sC: s6+s0: s2+s3:' [i+1]
adc2 rp[i+1], s2   | s4 s7+sB" s8+sA {3} s9: s1+sC: s6+s0:' s3: [i+1]
mulx sp[4], s2, s5 | s4 s7+sB" s8+sA {2} s5: s9+s2: s1+sC: s6+s0:' s3: [i+1]
adox sB, s7        | s4" s7 s8+sA {2} s5: s9+s2: s1+sC: s6+s0:' s3: [i+1]
movq $0, sB
adox sB, s4        | s4 s7 s8+sA {2} s5: s9+s2: s1+sC: s6+s0:' s3: [i+1]
adc2 rp[i+2], s6   | s4 s7 s8+sA {2} s5: s9+s2: s1+sC:' s0: s3: [i+1]
mulx sp[6], s6, sB | s4 s7 s8+sA sB: s6: s5: s9+s2: s1+sC:' s0: s3: [i+1]
movq rp[i+8], dd
ado2 rp[i+1], s3   | s4 s7 s8+sA sB: s6: s5: s9+s2: s1+sC:' s0:" [i+2]
adc2 rp[i+3], s1   | s4 s7 s8+sA sB: s6: s5: s9+s2:' sC: s0:" [i+2]
'''

g_mul_5 = '''
                   | i >= 5
                   | s4 s7 s8+sA sB: s6: s5: s9+s2:' sC: s0:" [i+1] dd=v[i]
rp[i+9]:=v[i+1]
mulx sp[4], s1, s3 | s4 s7 s8+sA sB: s6+s3: s5+s1: s9+s2:' sC: s0:" [i+1]
ado2 rp[i+1], s0   | s4 s7 s8+sA sB: s6+s3: s5+s1: s9+s2:' sC:" [i+2]
adc2 rp[i+3], s9   | s4 s7 s8+sA sB: s6+s3: s5+s1:' s2: sC:" [i+2]
mulx sp[6], s0, s9 | s4 s7 s8+sA+s9 sB+s0: s6+s3: s5+s1:' s2: sC:" [i+2]
ado2 rp[i+2], sC   | s4 s7 s8+sA+s9 sB+s0: s6+s3: s5+s1:' s2:" [i+3]
adc2 rp[i+4], s5   | s4 s7 s8+sA+s9 sB+s0: s6+s3:' s1: s2:" [i+3]
mulx sp[8], s5, sC | s4+sC s7+s5 s8+sA+s9 sB+s0: s6+s3:' s1: s2:" [i+3]
ado2 rp[i+3], s2   | s4+sC s7+s5 s8+sA+s9 sB+s0: s6+s3:' s1:" [i+4]
adc2 rp[i+5], s6   | s4+sC s7+s5 s8+sA+s9 sB+s0:' s3: s1:" [i+4]
mulx sp[9], s2, s6 | s6 s4+sC+s2 s7+s5 s8+sA+s9 sB+s0:' s3: s1:" [i+4]
ado2 rp[i+4], s1   | s6 s4+sC+s2 s7+s5 s8+sA+s9 sB+s0:' s3:" [i+5]
adc2 rp[i+6], sB   | s6 s4+sC+s2 s7+s5 s8+sA+s9' s0: s3:" [i+5]
mulx sp[7], s1, sB | s6 s4+sC+s2 s7+s5+sB s8+sA+s9+s1' s0: s3:" [i+5]
ado2 rp[i+5], s3   | s6 s4+sC+s2 s7+s5+sB s8+sA+s9+s1' s0:" [i+6]
adcx sA, s8        | s6 s4+sC+s2 s7+s5+sB' s8+s9+s1 s0:" [i+6]
mulx sp[0], s3, sA | s6 s4+sC+s2 s7+s5+sB' s8+s9+s1 s0:" {4} sA: s3: [i]
ado2 rp[i+6], s0   | s6 s4+sC+s2 s7+s5+sB' s8+s9+s1" {5} sA: s3: [i]
adcx s5, s7        | s6 s4+sC+s2' s7+sB s8+s9+s1" {5} sA: s3: [i]
mulx sp[1], s0, s5 | s6 s4+sC+s2' s7+sB s8+s9+s1" {4} s5: sA+s0: s3: [i]
adox s9, s8        | s6 s4+sC+s2' s7+sB" s8+s1 {4} s5: sA+s0: s3: [i]
movq s8, rp[i+7]   | s6 s4+sC+s2' s7+sB" s1: {4} s5: sA+s0: s3: [i]
mulx sp[2], s8, s9 | s6 s4+sC+s2' s7+sB" s1: {3} s9: s5+s8: sA+s0: s3: [i]
adcx sC, s4        | 
movq s4, rp[i+8]   | s6' ^8+s2 s7+sB" s1: {3} s9: s5+s8: sA+s0: s3: [i]
mulx sp[3], s4, sC | s6' ^8+s2 s7+sB" s1: {2} sC: s9+s4: s5+s8: sA+s0: s3: [i]
adox sB, s7        | s6' ^8+s2" s7 s1: {2} sC: s9+s4: s5+s8: sA+s0: s3: [i]
movq $0, sB
adcx sB, s6        | s6 ^8+s2" s7 s1: {2} sC: s9+s4: s5+s8: sA+s0: s3: [i]
adox rp[i+8], s2   | s6" s2 s7 s1: {2} sC: s9+s4: s5+s8: sA+s0: s3: [i]
adc2 rp[i], s3     | s6" s2 s7 s1: {2} sC: s9+s4: s5+s8: sA+s0:' [i+1]
adox sB, s6        | s6 s2 s7 s1: {2} sC: s9+s4: s5+s8: sA+s0:' [i+1]
movq s6, rp[i+8]   | ^8 s2 s7 s1: {2} sC: s9+s4: s5+s8: sA+s0:' [i+1]
mulx sp[5], s3, sB | ^8 s2 s7 s1: sB: s3: sC: s9+s4: s5+s8: sA+s0:' [i+1]
movq rp[i+9], dd
adcx s0, sA        | ^8 s2 s7 s1: sB: s3: sC: s9+s4: s5+s8:' sA: [i+1]
'''

g_mul_6 = '''
                   | i >= 6
                   | ^7 s2 s7 s1: sB: s3: sC: s9+s4: s5+s8:' sA: [i]
rp[i+8]:=v[i+1]
mulx sp[3], s0, s6 | ^7 s2 s7 s1: sB: s3+s6: sC+s0: s9+s4: s5+s8:' sA: [i]
ado2 rp[i], sA     | ^7 s2 s7 s1: sB: s3+s6: sC+s0: s9+s4: s5+s8:'" [i+1]
adcx s8, s5        | ^7 s2 s7 s1: sB: s3+s6: sC+s0: s9+s4:' s5:" [i+1]
mulx sp[5], s8, sA | ^7 s2 s7 s1+sA: sB+s8: s3+s6: sC+s0: s9+s4:' s5:" [i+1]
adcx s4, s9        | ^7 s2 s7 s1+sA: sB+s8: s3+s6: sC+s0:' s9: s5:" [i+1]
ado2 rp[i+1], s5   | ^7 s2 s7 s1+sA: sB+s8: s3+s6: sC+s0:' s9:" [i+2]
mulx sp[7], s4, s5 | ^7 s2+s5 s7+s4 s1+sA: sB+s8: s3+s6: sC+s0:' s9:" [i+2]
adc2 rp[i+3], sC   | ^7 s2+s5 s7+s4 s1+sA: sB+s8: s3+s6:' s0: s9:" [i+2]
ado2 rp[i+2], s9   | ^7 s2+s5 s7+s4 s1+sA: sB+s8: s3+s6:' s0:" [i+3]
mulx sp[9], s9, sC | sC ^7+s9 s2+s5 s7+s4 s1+sA: sB+s8: s3+s6:' s0:" [i+3]
adc2 rp[i+4], s3   | sC ^7+s9 s2+s5 s7+s4 s1+sA: sB+s8:' s6: s0:" [i+3]
ado2 rp[i+3], s0   | sC ^7+s9 s2+s5 s7+s4 s1+sA: sB+s8:' s6:" [i+4]
mulx sp[6], s0, s3 | sC ^7+s9 s2+s5 s7+s4+s3 s1+sA+s0: sB+s8:' s6:" [i+4]
adcx s8, sB        | sC ^7+s9 s2+s5 s7+s4+s3 s1+sA+s0:' sB: s6:" [i+4]
ado2 rp[i+4], s6   | sC ^7+s9 s2+s5 s7+s4+s3 s1+sA+s0:' sB:" [i+5]
mulx sp[8], s6, s8 | sC ^7+s9+s8 s2+s5+s6 s7+s4+s3 s1+sA+s0:' sB:" [i+5]
adcx sA, s1        | sC ^7+s9+s8 s2+s5+s6 s7+s4+s3' s1+s0: sB:" [i+5]
ado2 rp[i+5], sB   | sC ^7+s9+s8 s2+s5+s6 s7+s4+s3' s1+s0:" [i+6]
mulx sp[0], sA, sB | sC ^7+s9+s8 s2+s5+s6 s7+s4+s3' s1+s0:" {4} sB: sA: [i]
adcx s4, s7        | sC ^7+s9+s8 s2+s5+s6' s7+s3 s1+s0:" {4} sB: sA: [i]
ado2 rp[i+6], s1   | sC ^7+s9+s8 s2+s5+s6' s7+s3" s0: {4} sB: sA: [i]
mulx sp[1], s1, s4 | sC ^7+s9+s8 s2+s5+s6' s7+s3" s0: {3} s4: sB+s1: sA: [i]
adcx s5, s2        | sC ^7+s9+s8' s2+s6 s7+s3" s0: {3} s4: sB+s1: sA: [i]
adox s3, s7        | sC ^7+s9+s8' s2+s6" s7 s0: {3} s4: sB+s1: sA: [i]
mulx sp[2], s3, s5 | sC ^7+s9+s8' s2+s6" s7 s0: {2} s5: s4+s3: sB+s1: sA: [i]
adcx rp[i+7], s9   | sC' s9+s8 s2+s6" s7 s0: {2} s5: s4+s3: sB+s1: sA: [i]
adox s6, s2        | sC' s9+s8" s2 s7 s0: {2} s5: s4+s3: sB+s1: sA: [i]
movq s7, rp[i+7]   | sC' s9+s8" s2 .. s0: {2} s5: s4+s3: sB+s1: sA: [i]
mulx sp[4], s6, s7 | sC' s9+s8" s2 .. s0: s7: s6: s5: s4+s3: sB+s1: sA: [i]
movq rp[i+8], dd
movq s2, rp[i+8]   | sC' s9+s8" .. .. s0: s7: s6: s5: s4+s3: sB+s1: sA: [i]
movq $0, s2
adcx s2, sC        | sC s9+s8" .. .. s0: s7: s6: s5: s4+s3: sB+s1: sA: [i]
adox s8, s9        | sC" s9 .. .. s0: s7: s6: s5: s4+s3: sB+s1: sA: [i]
'''

g_mul_7 = '''
                   | i >= 7
                   | sC" s9 .. .. s0: s7: s6: s5: s4+s3: sB+s1: sA: [i-1] dd=v[i]
rp[i+8]:=v[i+1]
mulx sp[2], s2, s8 | sC" s9 .. .. s0: s7: s6+s8: s5+s2: s4+s3: sB+s1: sA: [i-1]
adc2 rp[i-1], sA   | sC" s9 .. .. s0: s7: s6+s8: s5+s2: s4+s3: sB+s1:' [i]
movq $0, sA
adox sA, sC        | sC s9 .. .. s0: s7: s6+s8: s5+s2: s4+s3: sB+s1:' [i]
adcx s1, sB        | sC s9 .. .. s0: s7: s6+s8: s5+s2: s4+s3:' sB: [i]
mulx sp[4], s1, sA | sC s9 .. .. s0+sA: s7+s1: s6+s8: s5+s2: s4+s3:' sB: [i]
ado2 rp[i], sB     | sC s9 .. .. s0+sA: s7+s1: s6+s8: s5+s2: s4+s3:'" [i+1]
adcx s3, s4        | sC s9 .. .. s0+sA: s7+s1: s6+s8: s5+s2:' s4:" [i+1]
mulx sp[6], s3, sB | sC s9 sB: s3: s0+sA: s7+s1: s6+s8: s5+s2:' s4:" [i+1]
adc2 rp[i+2], s5   | sC s9 sB: s3: s0+sA: s7+s1: s6+s8:' s2: s4:" [i+1]
ado2 rp[i+1], s4   | sC s9 sB: s3: s0+sA: s7+s1: s6+s8:' s2:" [i+2]
mulx sp[5], s4, s5 | sC s9 sB: s3+s5: s0+sA+s4: s7+s1: s6+s8:' s2:" [i+2]
adc2 rp[i+3], s6   | sC s9 sB: s3+s5: s0+sA+s4: s7+s1:' s8: s2:" [i+2]
ado2 rp[i+2], s2   | sC s9 sB: s3+s5: s0+sA+s4: s7+s1:' s8:" [i+3]
mulx sp[7], s2, s6 | sC s9+s6 sB+s2: s3+s5: s0+sA+s4: s7+s1:' s8:" [i+3]
adcx s1, s7        | sC s9+s6 sB+s2: s3+s5: s0+sA+s4:' s7: s8:" [i+3]
ado2 rp[i+3], s8   | sC s9+s6 sB+s2: s3+s5: s0+sA+s4:' s7:" [i+4]
mulx sp[9], s1, s8 | s8 sC+s1 s9+s6 sB+s2: s3+s5: s0+sA+s4:' s7:" [i+4]
adcx sA, s0        | s8 sC+s1 s9+s6 sB+s2: s3+s5:' s0+s4: s7:" [i+4]
ado2 rp[i+4], s7   | s8 sC+s1 s9+s6 sB+s2: s3+s5:' s0+s4:" [i+5]
mulx sp[8], s7, sA | s8 sC+s1+sA s9+s6+s7 sB+s2: s3+s5:' s0+s4:" [i+5]
adc2 rp[i+6], s3   | s8 sC+s1+sA s9+s6+s7 sB+s2:' s5: s0+s4:" [i+5]
adox s4, s0        | s8 sC+s1+sA s9+s6+s7 sB+s2:' s5:" s0: [i+5]
mulx sp[0], s3, s4 | s8 sC+s1+sA s9+s6+s7 sB+s2:' s5:" s0: {3} s4: s3: [i]
adcx s2, sB        | s8 sC+s1+sA s9+s6+s7' sB: s5:" s0: {3} s4: s3: [i]
ado2 rp[i+6], s5   | s8 sC+s1+sA s9+s6+s7' sB:" .. s0: {3} s4: s3: [i]
mulx sp[1], s2, s5 | s8 sC+s1+sA s9+s6+s7' sB:" .. s0: {2} s5: s4+s2: s3: [i]
adcx s6, s9        | s8 sC+s1+sA' s9+s7 sB:" .. s0: {2} s5: s4+s2: s3: [i]
ado2 rp[i+7], sB   | s8 sC+s1+sA' s9+s7" .. .. s0: {2} s5: s4+s2: s3: [i]
mulx sp[3], s6, sB | s8 sC+s1+sA' s9+s7" .. .. s0: sB: s6: s5: s4+s2: s3: [i]
movq rp[i+8], dd
adcx s1, sC        | s8' sC+sA s9+s7" .. .. s0: sB: s6: s5: s4+s2: s3: [i]
movq $0, s1
adox s7, s9        | s8' sC+sA" s9 .. .. s0: sB: s6: s5: s4+s2: s3: [i]
movq s9, rp[i+8]   | s8' sC+sA" .. .. .. s0: sB: s6: s5: s4+s2: s3: [i]
'''

g_mul_8 = '''
                   | i = 8
                   | s8' sC+sA" .. .. .. s0: sB: s6: s5: s4+s2: s3: [i-1] dd=v[i]
rp[i+8]:=v[i+1]
if tail_jump: jmp tail
if tail_here: tail:
mulx sp[1], s7, s9 | s8' sC+sA" .. .. .. s0: sB: s6+s9: s5+s7: s4+s2: s3: [i-1]
adcx s1, s8        | s8 sC+sA" .. .. .. s0: sB: s6+s9: s5+s7: s4+s2: s3: [i-1]
adox sA, sC        | s8" sC .. .. .. s0: sB: s6+s9: s5+s7: s4+s2: s3: [i-1]
mulx sp[3], s1, sA | s8" sC .. .. .. s0+sA: sB+s1: s6+s9: s5+s7: s4+s2: s3: [i-1]
adc2 rp[i-1], s3   | s8" sC .. .. .. s0+sA: sB+s1: s6+s9: s5+s7: s4+s2:' [i]
movq $0, s3
adox s3, s8        | s8 sC .. .. .. s0+sA: sB+s1: s6+s9: s5+s7: s4+s2:' [i]
adcx s2, s4        | s8 sC .. .. .. s0+sA: sB+s1: s6+s9: s5+s7:' s4: [i]
mulx sp[5], s2, s3 | s8 sC .. s3: s2: s0+sA: sB+s1: s6+s9: s5+s7:' s4: [i]
ado2 rp[i], s4     | s8 sC .. s3: s2: s0+sA: sB+s1: s6+s9: s5+s7:'" [i+1]
adc2 rp[i+1], s5   | s8 sC .. s3: s2: s0+sA: sB+s1: s6+s9:' s7:" [i+1]
mulx sp[4], s4, s5 | s8 sC .. s3: s2+s5: s0+sA+s4: sB+s1: s6+s9:' s7:" [i+1]
adc2 rp[i+2], s6   | s8 sC .. s3: s2+s5: s0+sA+s4: sB+s1:' s9: s7:" [i+1]
ado2 rp[i+1], s7   | s8 sC .. s3: s2+s5: s0+sA+s4: sB+s1:' s9:" [i+2]
mulx sp[6], s6, s7 | s8 sC s7: s3+s6: s2+s5: s0+sA+s4: sB+s1:' s9:" [i+2]
adcx s1, sB        | s8 sC s7: s3+s6: s2+s5: s0+sA+s4:' sB: s9:" [i+2]
ado2 rp[i+2], s9   | s8 sC s7: s3+s6: s2+s5: s0+sA+s4:' sB:" [i+3]
mulx sp[7], s9, s1 | s8 sC+s1 s7+s9: s3+s6: s2+s5: s0+sA+s4:' sB:" [i+3]
adcx sA, s0        | s8 sC+s1 s7+s9: s3+s6: s2+s5:' s0+s4: sB:" [i+3]
ado2 rp[i+3], sB   | s8 sC+s1 s7+s9: s3+s6: s2+s5:' s0+s4:" [i+4]
mulx sp[8], sA, sB | s8+sB sC+s1+sA s7+s9: s3+s6: s2+s5:' s0+s4:" [i+4]
adc2 rp[i+5], s2   | s8+sB sC+s1+sA s7+s9: s3+s6:' s5: s0+s4:" [i+4]
adox s4, s0        | s8+sB sC+s1+sA s7+s9: s3+s6:' s5:" s0: [i+4]
mulx sp[9], s2, s4 | s4 s8+sB+s2 sC+s1+sA s7+s9: s3+s6:' s5:" s0: [i+4]
adcx s6, s3        | s4 s8+sB+s2 sC+s1+sA s7+s9:' s3: s5:" s0: [i+4]
ado2 rp[i+5], s5   | s4 s8+sB+s2 sC+s1+sA s7+s9:' s3:" .. s0: [i+4]
mulx sp[0], s5, s6 | s4 s8+sB+s2 sC+s1+sA s7+s9:' s3:" .. s0: {2} s6: s5: [i]
adcx s9, s7        | s4 s8+sB+s2 sC+s1+sA' s7: s3:" .. s0: {2} s6: s5: [i]
ado2 rp[i+6], s3   | s4 s8+sB+s2 sC+s1+sA' s7:" .. .. s0: {2} s6: s5: [i]
mulx sp[2], s3, s9 | s4 s8+sB+s2 sC+s1+sA' s7:" .. .. s0: s9: s3: s6: s5: [i]
adcx s1, sC        | s4 s8+sB+s2' sC+sA s7:" .. .. s0: s9: s3: s6: s5: [i]
ado2 rp[i+7], s7   | s4 s8+sB+s2' sC+sA" {3} s0: s9: s3: s6: s5: [i]
movq rp[i+8], dd
'''

g_mul_9 = '''
                   | i = 9
                   | s4 s8+sB+s2' sC+sA" {3} s0: s9: s3: s6: s5: [i-1]
mulx sp[0], s7, s1 | s4 s8+sB+s2' sC+sA" {3} s0: s9: s3+s1: s6+s7: s5: [i-1]
adcx sB, s8        | s4' s8+s2 sC+sA" {3} s0: s9: s3+s1: s6+s7: s5: [i-1]
movq $0, sB
adox sA, sC        | s4' s8+s2" sC {3} s0: s9: s3+s1: s6+s7: s5: [i-1]
movq sC, rp[i+7]   | s4' s8+s2" {4} s0: s9: s3+s1: s6+s7: s5: [i-1]
mulx sp[2], sA, sC | s4' s8+s2" {4} s0+sC: s9+sA: s3+s1: s6+s7: s5: [i-1]
adcx sB, s4        | s4 s8+s2" {4} s0+sC: s9+sA: s3+s1: s6+s7: s5: [i-1]
adox s2, s8        | s4" s8 {4} s0+sC: s9+sA: s3+sC: s6+s7: s5: [i-1]
mulx sp[4], s2, sB | s4" s8 .. .. sB: s2: s0+sC: s9+sA: s3+s1: s6+s7: s5: [i-1]
adc2 rp[i-1], s5   | s4" s8 .. .. sB: s2: s0+sC: s9+sA: s3+s1: s6+s7:' [i]
movq $0, s5
adox s5, s4        | s4 s8 .. .. sB: s2: s0+sC: s9+sA: s3+s1: s6+s7:' [i]
adc2 rp[i], s6     | s4 s8 .. .. sB: s2: s0+sC: s9+sA: s3+s1:' s7: [i]
mulx sp[3], s5, s6 | s4 s8 .. .. sB: s2+s6: s0+sC+s5: s9+sA: s3+s1:' s7: [i]
adc2 rp[i+1], s3   | s4 s8 .. .. sB: s2+s6: s0+sC+s5: s9+sA:' s1: s7: [i]
ado2 rp[i], s7     | s4 s8 .. .. sB: s2+s6: s0+sC+s5: s9+sA:' s1:" [i+1]
mulx sp[5], s3, s7 | s4 s8 .. s7: sB+s3: s2+s6: s0+sC+s5: s9+sA:' s1:" [i+1]
adcx sA, s9        | s4 s8 .. s7: sB+s3: s2+s6: s0+sC+s5:' s9: s1:" [i+1]
ado2 rp[i+1], s1   | s4 s8 .. s7: sB+s3: s2+s6: s0+sC+s5:' s9:" [i+2]
mulx sp[6], s1, sA | s4 s8 sA: s7+s1: sB+s3: s2+s6: s0+sC+s5:' s9:" [i+2]
adcx sC, s0        | s4 s8 sA: s7+s1: sB+s3: s2+s6:' s0+s5: s9:" [i+2]
ado2 rp[i+2], s9   | s4 s8 sA: s7+s1: sB+s3: s2+s6:' s0+s5:" [i+3]
mulx sp[7], s9, sC | s4 s8+sC sA+s9: s7+s1: sB+s3: s2+s6:' s0+s5:" [i+3]
adc2 rp[i+4], s2   | s4 s8+sC sA+s9: s7+s1: sB+s3:' s6: s0+s5:" [i+3]
adox s5, s0        | s4 s8+sC sA+s9: s7+s1: sB+s3:' s6:" s0: [i+3]
mulx sp[8], s2, s5 | s4+s5 s8+sC+s2 sA+s9: s7+s1: sB+s3:' s6:" s0: [i+3]
adcx s3, sB        | s4+s5 s8+sC+s2 sA+s9: s7+s1:' sB: s6:" s0: [i+3]
ado2 rp[i+4], s6   | s4+s5 s8+sC+s2 sA+s9: s7+s1:' sB:" .. s0: [i+3]
mulx sp[9], s3, s6 | s6 s4+s5+s3 s8+sC+s2 sA+s9: s7+s1:' sB:" .. s0: [i+3]
adcx s1, s7        | s6 s4+s5+s3 s8+sC+s2 sA+s9:' s7: sB:" .. s0: [i+3]
adox rp[i+5], sB   | s6 s4+s5+s3 s8+sC+s2 sA+s9:' s7:" sB .. s0: [i+3]
mulx sp[1], s1, dd | s6 s4+s5+s3 s8+sC+s2 sA+s9:' s7:" sB .. s0: dd: s1: [i+1]
adcx s9, sA        | s6 s4+s5+s3 s8+sC+s2' sA: s7:" sB .. s0: dd: s1: [i+1]
adox rp[i+6], s7   | s6 s4+s5+s3 s8+sC+s2' sA:" s7 sB .. s0: dd: s1: [i+1]
| delay 1 tick?
adcx sC, s8        | s6 s4+s5+s3' s8+s2 sA:" s7 sB .. s0: dd: s1: [i+1]
movq rp[i+1], sC   | s6 s4+s5+s3' s8+s2 sA:" s7 sB .. s0: dd: s1+sC [i+1]
adox rp[i+7], sA   | s6 s4+s5+s3' s8+s2" sA s7 sB .. s0: dd: s1+sC [i+1]
movq rp[i+8], sp
adcx s5, s4        | s6' s4+s3 s8+s2" sA s7 sB .. s0: dd: s1+sC [i+1]
movq $0, s5
adox s2, s8        | s6' s4+s3" s8 sA s7 sB .. s0: dd: s1+sC [i+1]
movq rp[i+2], s2   | s6' s4+s3" s8 sA s7 sB .. s0: dd+s2 s1+sC [i+1]
adcx s5, s6        | s6 s4+s3" s8 sA s7 sB .. s0: dd+s2 s1+sC [i+1]
adox s3, s4        | s6" s4 s8 sA s7 sB .. s0: dd+s2 s1+sC [i+1]
movq rp[i+3], s3   | s6" s4 s8 sA s7 sB .. s0+s3 dd+s2 s1+sC [i+1]
adcx sC, s1        | s6" s4 s8 sA s7 sB .. s0+s3 dd+s2' s1 [i+1]
movq s1, rp[i+1]   | s6" s4 s8 sA s7 sB .. s0+s3 dd+s2' [i+2]
movq rp[i+4], s1   | s6" s4 s8 sA s7 sB s1 s0+s3 dd+s2' [i+2]
adox s5, s6        | s6 s4 s8 sA s7 sB s1 s0+s3 dd+s2' [i+2]
adcx s2, dd        | s6 s4 s8 sA s7 sB s1 s0+s3' dd [i+2]
movq dd, rp[i+2]   | s6 s4 s8 sA s7 sB s1 s0+s3' [i+3]
adcx s3, s0        | s6 s4 s8 sA s7 sB s1' s0 [i+3]
movq s0, rp[i+3]   | s6 s4 s8 sA s7 sB s1' [i+4]
adcx s5, s1        | s6 s4 s8 sA s7 sB' s1 [i+4]
movq s1, rp[i+4]   | s6 s4 s8 sA s7 sB' [i+5]
| TODO: branch on carry here
got_carry:
adcx s5, sB
movq sB, rp[i+5]   | s6 s4 s8 sA s7' [i+6]
adcx s5, s7
movq s7, rp[i+6]   | s6 s4 s8 sA' [i+7]
adcx s5, sA
movq sA, rp[i+7]   | s6 s4 s8' [i+8]
adcx s5, s8
movq s8, rp[i+8]   | s6 s4' [i+9]
adcx s5, s4
movq s4, rp[i+9]   | s6' [i+10]
adcx s5, s6
movq s6, rp[i+10]
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P
import gen_mul7_t03 as A
import gen_mul8_aligned as E
import gen_mul11_ryzen as L

def extract_v(i, alignment, tgt):
    if (i < 2) or (i > 9) or (alignment == None):
        return 'Bad extract v'
    return L.extract_v(i, alignment, tgt)

g_iplus_minus_patt = re.compile(r'\bi([\+\-])\b([0-9]+)\b')
g_ad2_patt = re.compile(r'(ad[co])2 (.+), (.+)')
def evaluate_row(s, i, alignment):
    m = E.g_if_patt.match(s)
    if m:
        d = \
                {\
                    'tail_jump' : (i == 8) and (alignment != 0),
                    'tail_here' : (i == 8) and (alignment == 0),
                }
        s = E.evaluate_if(s, d, m.group(1), m.group(2))

    if i is not None:
        while True:
            m = g_iplus_minus_patt.search(s)
            if not m:
                break
            if m.group(1) == '+':
                s = s.replace(m.group(), '%s' % (i + int(m.group(2))))
            else:
                s = s.replace(m.group(), '%s' % (i - int(m.group(2))))
        s = re.sub(r'\bi\b', '%s' % i, s)

    m = E.g_v_patt.match(s)
    if m:
        s = extract_v(int(m.group(2)), alignment, m.group(1))

    m = E.g_array_patt.search(s)
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

def chew_code(src, i, alignment, p):
    if not isinstance(src, list):
        src = P.cutoff_comments(src)

    if i:
        rr = ['# mul_add %s' % i]
    else:
        rr = []

    for j in src:
        for k in evaluate_row(j, i, alignment):
            if k:
                rr.append(k)

    if not p:
        return rr
    re = []
    for x in rr:
        if x[0] == '#':
            re.append(x)
        else:
            re.append(A.apply_s_permutation(x, p))
    return re

def alignment_code(alignment):
    if alignment:
        code = chew_code(g_preamble, None, None, None)
    else:
        code = chew_code(g_load_0, None, None, None)
    p = list(range(0xC + 1))
    code += chew_code(g_mul_01, None, alignment, None)
    code += chew_code(g_mul_3, 3, alignment, p)
    code += chew_code(g_mul_4, 4, alignment, p)
    code += chew_code(g_mul_5, 5, alignment, p)
    code += chew_code(g_mul_6, 6, alignment, p)
    code += chew_code(g_mul_7, 7, alignment, p)
    if alignment:
        fresh = chew_code(g_mul_8, 8, alignment, p)
        code += L.remove_after_jmp(fresh)
    else:
        code += chew_code(g_mul_8, 8, alignment, p)
    if not alignment:
        code += chew_code(g_mul_9, 9, alignment, p)
    return code

def do_it(o):
    code = alignment_code(8) + alignment_code(0)
    P.cook_asm(o, code, g_var_map, True)

if __name__ == '__main__':
    with open(sys.argv[1], 'wb') as g_out:
        do_it(g_out)
