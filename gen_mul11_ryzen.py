'''
11x11 multiplication targeting Zen. Uses aligned loads of v[] into xmm's.

203-205 ticks on Skylake, 189 ticks on Ryzen

22x22 multiplication benchmarks:
                          Skylake Ryzen
without this subroutine     879     807
with this subroutine      759-761   755
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
movdqa w5[9], x4
'''

g_load_0 = '''
align0:
movdqa w5[2], x0
movdqa w5[4], x1
movdqa w5[6], x2
movdqa w5[8], x3
movq w5[10], x4
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
mulx sp[4], w7, w6  | w4+w6 wC+w1+w7 w9+w2+w5 w8+wB+w0" w3+wA' [2] ==
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
mulx sp[9], w7, wC  | wC w5+w7 wB+w8+w2 wA+w9+w1" w4+w3' [6] == dd=v[0] w0=v[1]
adox w9, wA         | wC w5+w7 wB+w8+w2" wA+w1 w4+w3' [6] == dd=v[0] w0=v[1]
adcx w4, w3         | wC w5+w7 wB+w8+w2" wA+w1' w3 [6] == dd=v[0] w0=v[1]
mulx sp[10], w4, w9 | w9 wC+w4 w5+w7 wB+w8+w2" wA+w1' w3 [6] == dd=v[0] w0=v[1]
movq w0, dd         | w9 wC+w4 w5+w7 wB+w8+w2" wA+w1' w3 [6] == dd=v[1]
mulx sp[1], w0, w6  | w9 wC+w4 w5+w7 wB+w8+w2" wA+w1' w3 .. .. w6: w0: [2]
adox wB, w8         | w9 wC+w4 w5+w7" w8+w2 wA+w1' w3 .. .. w6: w0: [2]
adcx wA, w1         | w9 wC+w4 w5+w7" w8+w2' w1 w3 .. .. w6: w0: [2]
mulx sp[8], wA, wB  | w9 wC+w4+wB w5+w7+wA" w8+w2' w1 w3 .. .. w6: w0: [2]
adox w7, w5         | w9 wC+w4+wB" w5+wA w8+w2' w1 w3 .. .. w6: w0: [2]
adcx w8, w2         | w9 wC+w4+wB" w5+wA' w2 w1 w3 .. .. w6: w0: [2]
mulx sp[3], w7, w8  | w9 wC+w4+wB" w5+wA' w2 w1 w3 w8: w7: w6: w0: [2]
adox wC, w4         | w9" w4+wB w5+wA' w2 w1 w3 w8: w7: w6: w0: [2]
movq w3, rp[6]
movq w1, rp[7]
rp[8]:=v[2]
movq $0, wC
adox wC, w9         | w9 w4+wB w5+wA' w2 .. .. w8: w7: w6: w0: [2]
mulx sp[5], wC, w3  | w9 w4+wB w5+wA' w2 w3: wC: w8: w7: w6: w0: [2]
adox rp[2], w0
movq w0, rp[2]      | w9 w4+wB w5+wA' w2 w3: wC: w8: w7: w6:" [3]
mulx sp[7], w0, w1  | w9 w4+wB w5+wA+w1' w2+w0 w3: wC: w8: w7: w6:" [3]
adcx wA, w5         | w9 w4+wB' w5+w1 w2+w0 w3: wC: w8: w7: w6:" [3]
adox rp[3], w6
movq w6, rp[3]      | w9 w4+wB' w5+w1 w2+w0 w3: wC: w8: w7:" [4]
mulx sp[9], w6, wA  | w9+wA w4+wB+w6' w5+w1 w2+w0 w3: wC: w8: w7:" [4]
adcx wB, w4         | w9+wA' w4+w6 w5+w1 w2+w0 w3: wC: w8: w7:" [4]
adox rp[4], w7
movq w7, rp[4]      | w9+wA' w4+w6 w5+w1 w2+w0 w3: wC: w8:" [5]
mulx sp[10], w7, wB | wB w9+wA+w7' w4+w6 w5+w1 w2+w0 w3: wC: w8:" [5]
movq rp[8], dd
adox rp[5], w8
movq w8, rp[5]      | wB w9+wA+w7' w4+w6 w5+w1 w2+w0 w3: wC:" [6]
movq w2, rp[8]      | wB w9+wA+w7' w4+w6 w5+w1 w0: w3: wC:" [6]
'''

g_mul_2 = '''
mulx sp[0], w2, w8  | wB w9+wA+w7' w4+w6 w5+w1 w0: w3: wC:" .. .. w8: w2: [2]
adox rp[6], wC
movq wC, rp[6]      | wB w9+wA+w7' w4+w6 w5+w1 w0: w3:" .. .. .. w8: w2: [2]
movq w5, rp[9]      | wB w9+wA+w7' w4+w6 w1: w0: w3:" .. .. .. w8: w2: [2]
mulx sp[1], w5, wC  | wB w9+wA+w7' w4+w6 w1: w0: w3:" .. .. wC: w8+w5: w2: [2]
adcx wA, w9         | wB' w9+w7 w4+w6 w1: w0: w3:" .. .. wC: w8+w5: w2: [2]
adox rp[7], w3      | wB' w9+w7 w4+w6 w1: w0:" w3 .. .. wC: w8+w5: w2: [2]
movq w3, rp[7]      | wB' w9+w7 w4+w6 w1: w0:" [3] wC: w8+w5: w2: [2]
movq $0, wA
adcx wA, wB         | wB w9+w7 w4+w6 w1: w0:" [3] wC: w8+w5: w2: [2]
mulx sp[2], w3, wA  | wB w9+w7 w4+w6 w1: w0:" [2] wA: wC+w3: w8+w5: w2: [2]
adox rp[8], w0
movq w0, rp[8]      | wB w9+w7 w4+w6 w1:" [3] wA: wC+w3: w8+w5: w2: [2]
rp[10]:=v[3]
adcx rp[2], w2
movq w2, rp[2]      | wB w9+w7 w4+w6 w1:" [3] wA: wC+w3: w8+w5:' [3]
mulx sp[3], w0, w2  | wB w9+w7 w4+w6 w1:" [2] w2 wA+w0: wC+w3: w8+w5:' [3]
adox rp[9], w1      | wB w9+w7 w4+w6" w1 [2] w2 wA+w0: wC+w3: w8+w5:' [3]
adcx w8, w5         | wB w9+w7 w4+w6" w1 [2] w2 wA+w0: wC+w3:' w5: [3]
adox w6, w4         | wB w9+w7" w4 w1 [2] w2 wA+w0: wC+w3:' w5: [3]
mulx sp[4], w6, w8  | wB w9+w7" w4 w1 .. w8: w2+w6 wA+w0: wC+w3:' w5: [3]
adcx wC, w3         | wB w9+w7" w4 w1 .. w8: w2+w6 wA+w0:' w3: w5: [3]
adox w9, w7         | wB" w7 w4 w1 .. w8: w2+w6 wA+w0:' w3: w5: [3]
mulx sp[5], w9, wC  | wB" w7 w4 w1 wC: w8+w9: w2+w6 wA+w0:' w3: w5: [3]
adcx wA, w0         | wB" w7 w4 w1 wC: w8+w9: w2+w6' w0: w3: w5: [3]
movq $0, wA
adox wA, wB         | wB w7 w4 w1 wC: w8+w9: w2+w6' w0: w3: w5: [3]
adcx w6, w2         | wB w7 w4 w1 wC: w8+w9:' w2 w0: w3: w5: [3]
mulx sp[6], w6, wA  | wB w7 w4 w1+wA wC+w6: w8+w9:' w2 w0: w3: w5: [3]
adox rp[3], w5
movq w5, rp[3]      | wB w7 w4 w1+wA wC+w6: w8+w9:' w2 w0: w3:" [4]
adcx w9, w8         | wB w7 w4 w1+wA wC+w6:' w8: w2 w0: w3:" [4]
mulx sp[7], w5, w9  | wB w7 w4+w9 w1+wA+w5 wC+w6:' w8: w2 w0: w3" [4]
adox rp[4], w3      | wB w7 w4+w9 w1+wA+w5 wC+w6:' w8: w2 w0:" w3 [4]
movq w3, rp[4]      | wB w7 w4+w9 w1+wA+w5 wC+w6:' w8: w2 w0:" [5]
adcx wC, w6         | wB w7 w4+w9 w1+wA+w5' w6: w8: w2 w0:" [5]
mulx sp[8], w3, wC  | wB w7+wC w4+w9+w3 w1+wA+w5' w6: w8: w2 w0:" [5]
adox rp[5], w0
movq w0, rp[5]      | wB w7+wC w4+w9+w3 w1+wA+w5' w6: w8: w2" [6]
adox rp[6], w2
movq w2, rp[6]      | wB w7+wC w4+w9+w3 w1+wA+w5' w6: w8:" [7]
mulx sp[9], w0, w2  | wB+w2 w7+wC+w0 w4+w9+w3 w1+wA+w5' w6: w8:" [7]
adcx wA, w1         | wB+w2 w7+wC+w0 w4+w9+w3' w1+w5 w6: w8:" [7]
adox rp[7], w8      | wB+w2 w7+wC+w0 w4+w9+w3' w1+w5 w6:" w8 [7]
movq w8, rp[7]      | wB+w2 w7+wC+w0 w4+w9+w3' w1+w5 w6:" [8]
mulx sp[10], w8, wA | wA wB+w2+w8 w7+wC+w0 w4+w9+w3' w1+w5 w6:" [8]
adcx w9, w4         | wA wB+w2+w8 w7+wC+w0' w4+w3 w1+w5 w6:" [8]
adox rp[8], w6      | wA wB+w2+w8 w7+wC+w0' w4+w3 w1+w5" w6 [8]
movq rp[10], dd
movq w6, rp[8]      | wA wB+w2+w8 w7+wC+w0' w4+w3 w1+w5" [9]
'''

'''
i >= 3
multiplied by v[0], .. v[i-1]
data lies like that: sA sB+s2+s8 s7+sC+s0' s4+s3 s1+s5" [6+i] dd=v[i]
sC not ready, should be ready after one mulx
'''

g_mul_3 = '''
                   | sA sB+s2+s8 s7+sC+s0' s4+s3 s1+s5" [6+i]
mulx sp[0], s6, s9 | sA sB+s2+s8 s7+sC+s0' s4+s3 s1+s5" [4] s9: s6: [i]
adcx sC, s7        | sA sB+s2+s8' s7+s0 s4+s3 s1+s5" [4] s9: s6: [i]
adox s5, s1        | sA sB+s2+s8' s7+s0 s4+s3" s1 [4] s9: s6: [i]
mulx sp[1], s5, sC | sA sB+s2+s8' s7+s0 s4+s3" s1 [3] sC: s9+s5: s6: [i]
adcx sB, s2        | sA' s2+s8 s7+s0 s4+s3" s1 [3] sC: s9+s5: s6: [i]
adox s4, s3        | sA' s2+s8 s7+s0" s3 s1 [3] sC: s9+s5: s6: [i]
movq $0, sB
adcx sB, sA        | sA s2+s8 s7+s0" s3 s1 [3] sC: s9+s5: s6: [i]
mulx sp[2], s4, sB | sA s2+s8 s7+s0" s3 s1 [2] sB: sC+s4: s9+s5: s6: [i]
adox s7, s0        | sA s2+s8" s0 s3 s1 [2] sB: sC+s4: s9+s5: s6: [i]
adcx rp[i], s6
movq s6, rp[i]     | sA s2+s8" s0 s3 s1 [2] sB: sC+s4: s9+s5:' [i+1]
mulx sp[3], s6, s7 | sA s2+s8" s0 s3 s1 .. s7: sB+s6: sC+s4: s9+s5:' [i+1]
adox s8, s2        | sA" s2 s0 s3 s1 .. s7: sB+s6: sC+s4: s9+s5:' [i+1]
| s5 might be not ready
adcx s9, s5        | sA" s2 s0 s3 s1 .. s7: sB+s6: sC+s4:' s5: [i+1]
movq $0, s9
adox s9, sA        | sA s2 s0 s3 s1 .. s7: sB+s6: sC+s4:' s5: [i+1]
mulx sp[4], s8, s9 | sA s2 s0 s3 s1 s9: s7+s8: sB+s6: sC+s4:' s5: [i+1]
adcx sC, s4        | sA s2 s0 s3 s1 s9: s7+s8: sB+s6:' s4: s5: [i+1]
adox rp[i+1], s5
movq s5, rp[i+1]   | sA s2 s0 s3 s1 s9: s7+s8: sB+s6:' s4:" [i+2]
mulx sp[5], s5, sC | sA s2 s0 s3 s1+sC s9+s5: s7+s8: sB+s6:' s4:" [i+2]
| s6 might be not ready
adcx sB, s6        | sA s2 s0 s3 s1+sC s9+s5: s7+s8:' s6: s4:" [i+2]
adox rp[i+2], s4
movq s4, rp[i+2]   | sA s2 s0 s3 s1+sC s9+s5: s7+s8:' s6:" [i+3]
mulx sp[6], s4, sB | sA s2 s0 s3+sB s1+sC+s4 s9+s5: s7+s8:' s6:" [i+3]
adcx rp[i+4], s7   | sA s2 s0 s3+sB s1+sC+s4 s9+s5:' s7+s8: s6:" [i+3]
adox rp[i+3], s6
movq s6, rp[i+3]   | sA s2 s0 s3+sB s1+sC+s4 s9+s5:' s7+s8" [i+4]
movq sA, rp[i+6]   | ^6 s2 s0 s3+sB s1+sC+s4 s9+s5:' s7+s8" [i+4]
|rp[i+7]:=v[i+7]
mulx sp[7], s6, sA | ^6 s2 s0+sA s3+sB+s6 s1+sC+s4 s9+s5:' s7+s8" [i+4]
adcx s9, s5        | ^6 s2 s0+sA s3+sB+s6 s1+sC+s4' s5: s7+s8" [i+4]
s9:=v[i+1]
if tail_jump: jmp tail
if tail_here: tail:
adox s8, s7        | ^6 s2 s0+sA s3+sB+s6 s1+sC+s4' s5:" s7 [i+4]
movq s7, rp[i+4]   | ^6 s2 s0+sA s3+sB+s6 s1+sC+s4' s5:" [i+5]
mulx sp[8], s7, s8 | ^6 s2+s8 s0+sA+s7 s3+sB+s6 s1+sC+s4' s5:" [i+5] s9
adcx sC, s1        | ^6 s2+s8 s0+sA+s7 s3+sB+s6' s1+s4 s5:" [i+5] s9
adox rp[i+5], s5   | ^6 s2+s8 s0+sA+s7 s3+sB+s6' s1+s4" s5 [i+5] s9
movq s5, rp[i+5]   | ^6 s2+s8 s0+sA+s7 s3+sB+s6' s1+s4" [i+6] s9
mulx sp[9], s5, sC | ^6+sC s2+s8+s5 s0+sA+s7 s3+sB+s6' s1+s4" [i+6] s9
adcx sB, s3        | ^6+sC s2+s8+s5 s0+sA+s7' s3+s6 s1+s4" [i+6] s9
adox s4, s1        | ^6+sC s2+s8+s5 s0+sA+s7' s3+s6" s1 [i+6] s9
mulx sp[10], s4, sB | sB ^6+sC+s4 s2+s8+s5 s0+sA+s7' s3+s6" s1 [i+6] s9
if i<10: movq s9, dd | sB ^6+sC+s4 s2+s8+s5 s0+sA+s7' s3+s6" s1 [i+6]
movq rp[i+6], s9   | sB s9+sC+s4 s2+s8+s5 s0+sA+s7' s3+s6" s1 [i+6]
adcx sA, s0        | sB s9+sC+s4 s2+s8+s5' s0+s7 s3+s6" s1 [i+6]
movq s1, rp[i+6]   | sB s9+sC+s4 s2+s8+s5' s0+s7 s3+s6" [i+7]
'''

"""
old   sA sB+s2+s8 s7+sC+s0' s4+s3 s1+s5"
new   sB s9+sC+s4 s2+s8+s5' s0+s7 s3+s6"
          0 1 2 3 4 5 6 7 8 9 A B C                    """
g_perm = '5 3 C 7 0 6 A 2 4 1 B 9 8'   # can swap A and 1

g_tail = '''
movq rp[i+7], sp
adox s6, s3        | sB s9+sC+s4 s2+s8+s5' s0+s7" s3 [i+7]
movq s3, rp[i+7]   | sB s9+sC+s4 s2+s8+s5' s0+s7" [i+8]
adcx s8, s2        | sB s9+sC+s4' s2+s5 s0+s7" [i+8]
adox s7, s0        | sB s9+sC+s4' s2+s5" s0 [i+8]
movq s0, rp[i+8]   | sB s9+sC+s4' s2+s5" [i+9]
adcx sC, s9        | sB' s9+s4 s2+s5" [i+9]
movq $0, s0
adox s5, s2        | sB' s9+s4" s2 [i+9]
movq s2, rp[i+9]   | sB' s9+s4" [i+10]
adcx s0, sB        | sB s9+s4" [i+10]
adox s9, s4        | sB" s4 [i+10]
movq s4, rp[i+10]  | sB" [i+11]
adox s0, sB
movq sB, rp[i+11]
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P
import gen_mul7_t03 as A
import gen_mul8_aligned as E

def extract_v(i, alignment, tgt):
    if (i < 2) or (i > 11) or (alignment == None):
        return ''
    i -= 2
    if alignment:
        # 0 1_2 3_4 ... 7_8
        if i == 0:
            return 'movq x0, ' + tgt
        i -= 1
        # 0_1-<x1 2_3-<x2 ...
        j = i / 2 + 1
    else:
        # 0_1 2_3 4_5 ...
        j = i / 2
    if i & 1:
        return 'pextrq $0x1, x%s, %s' % (j, tgt)
    else:
        return 'movq x%s, %s' % (j, tgt)

def cook_tail(m3, alignment, p):
    rr = chew_code(m3, 10, alignment, p) + chew_code(g_tail, 10, alignment, p)[1:]
    # omit everything after jmp
    j = [j for j in range(len(rr)) if rr[j].find('jmp ') != -1]
    if j:
        j = j[0] + 1
        rr = rr[:j]
    return rr

def alignment_code(alignment):
    if alignment:
        code = []
    else:
        code = chew_code(g_load_0, None, 0, None)

    code += chew_code(g_mul_01, 0, alignment, None)
    code += chew_code(g_mul_2, 2, alignment, None)
    p = list(range(0xC + 1))
    q = [int(x, 16) for x in g_perm.split(' ')]
    m3 = P.cutoff_comments(g_mul_3)
    for i in range(3, 10):
        code += chew_code(m3, i, alignment, p)
        p = P.composition(p, q)
    code += cook_tail(m3, alignment, p)
    return code

def evaluate_row(s, i, alignment):
    m = E.g_if_patt.match(s)
    if m:
        d = {\
               'i<10' : i < 10,
               'tail_jump' : (i == 10) and (alignment != 0),
               'tail_here' : (i == 10) and (alignment == 0),
            }
        s = E.evaluate_if(s, d, m.group(1), m.group(2))

    m = E.g_iplus_patt.search(s)
    if m:
        s = s.replace(m.group(), '%s' % (int(m.group(1)) + i))
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

    return s

def chew_code(src, i, alignment, p):
    if not isinstance(src, list):
        src = P.cutoff_comments(src)

    if i:
        rr = ['# mul_add %s' % i]
    else:
        rr = []

    for j in src:
        k = evaluate_row(j, i, alignment)
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

def do_it(o):
    code = chew_code(g_preamble, 0, None, None)
    code += alignment_code(8)
    code += alignment_code(0)
    P.cook_asm(o, code, g_var_map, True)

def show_postcondition():
    p = list(range(0xC + 1))
    q = [int(x, 16) for x in g_perm.split(' ')]
    assert len(p) == len(q)
    b = '''sA sB+s2+s8 s7+sC+s0' s4+s3 s1+s5"'''
    l = '''sB s9+sC+s4 s2+s8+s5' s0+s7 s3+s6"'''
    for i in range(3, 11):
        print 'i=%X pre' % i, A.apply_s_permutation(b, p)
        if i == 10:
            break
        pst = A.apply_s_permutation(l, p)
        print 'i=%X pst' % i, pst
        pst = P.replace_symbolic_names_wr(pst, g_var_map).replace('%', '')
        print 'pst again', pst
        p = P.composition(p, q)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        show_postcondition()
        sys.exit(0)

    with open(sys.argv[1], 'wb') as g_out:
        do_it(g_out)
