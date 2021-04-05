'''
10x10 multiplication targeting Zen. Uses aligned loads of v[] into xmm's.

171 ticks on Ryzen, 198 ticks on Skylake.
'''

"""
xmm usage:
0-5 v[]
"""

g_preamble = '''
vzeroupper
movq sp, rp[15]
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

g_mul_012 = '''
mulx sp[0], w0, w1    | w1 w0 == dd=v[0] w6=v[1]
mulx sp[1], w2, w3    | w3 w1+w2 w0 == dd=v[0] w6=v[1]
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
adcx w7, wC         | w5 wB+w8+w2 wA+w9+w1" w4+w3' wC [5] == dd=v[0] w0=v[1]
movq wC, rp[5]      | w5 wB+w8+w2 wA+w9+w1" w4+w3' [6] == dd=v[0] w0=v[1]
mulx sp[9], w7, wC  | wC w5+w7 wB+w8+w2 wA+w9+w1" w4+w3' [6] == dd=v[0] w0=v[1]
movq w0, dd         | wC w5+w7 wB+w8+w2 wA+w9+w1" w4+w3' [6] == dd=v[1]
mulx sp[9], w0, w6  | w6 wC+w0 w5+w7 wB+w8+w2 wA+w9+w1" w4+w3' [6] == dd=v[1]
adox w9, wA         | w6 wC+w0 w5+w7 wB+w8+w2" wA+w1 w4+w3' [6] == dd=v[1]
adcx w3, w4         | w6 wC+w0 w5+w7 wB+w8+w2" wA+w1' w4 [6] == dd=v[1]
mulx sp[8], w3, w9  | w6 wC+w0+w9 w5+w7+w3 wB+w8+w2" wA+w1' w4 [6] == dd=v[1]
adox w8, wB         | w6 wC+w0+w9 w5+w7+w3" wB+w2 wA+w1' w4 [6] == dd=v[1]
adcx w1, wA         | w6 wC+w0+w9 w5+w7+w3" wB+w2' wA w4 [6] dd=v[1]
mulx sp[1], w1, w8  | w6 wC+w0+w9 w5+w7+w3" wB+w2' wA w4 {2} w8: w1: [2] dd=v[1]
adox w7, w5         | w6 wC+w0+w9" w5+w3 wB+w2' wA w4 {2} w8: w1: [2] dd=v[1]
w7:=v[2]
adcx w2, wB         | w6 wC+w0+w9" w5+w3' wB wA w4 {2} w8: w1: [2] dd=v[1] w7
movq wB, rp[6]      | w6 wC+w0+w9" w5+w3' ^6 wA w4 {2} w8: w1: [2] dd=v[1] w7
mulx sp[3], w2, wB  | w6 wC+w0+w9" w5+w3' ^6 wA w4 wB: w2: w8: w1: [2] dd=v[1] w7
adox w0, wC         | w6" wC+w9 w5+w3' ^6 wA w4 wB: w2: w8: w1: [2] dd=v[1] w7
movq $0, w0
adcx w3, w5         | w6" wC+w9' w5 ^6 wA w4 wB: w2: w8: w1: [2] dd=v[1] w7
adox w0, w6         | w6 wC+w9' w5 ^6 wA w4 wB: w2: w8: w1:" [2] dd=v[1] w7
mulx sp[5], w0, w3  | w6 wC+w9' w5 ^6 wA+w3 w4+w0 wB: w2: w8: w1:" [2] dd=v[1] w7
adcx w9, wC         | w6' wC w5 ^6 wA+w3 w4+w0 wB: w2: w8: w1:" [2] dd=v[1] w7
ado2 rp[2], w1      | w6' wC w5 ^6 wA+w3 w4+w0 wB: w2: w8:" [3] dd=v[1] w7
mulx sp[7], w1, w9  | w6' wC w5+w9 ^6+w1 wA+w3 w4+w0 wB: w2: w8:" [3] dd=v[1] w7
movq w7, dd         | w6' wC w5+w9 ^6+w1 wA+w3 w4+w0 wB: w2: w8:" [3] dd=v[2]
ado2 rp[3], w8      | w6' wC w5+w9 ^6+w1 wA+w3 w4+w0 wB: w2:" [4] dd=v[2]
mulx sp[0], w7, w8  | w6' wC w5+w9 ^6+w1 wA+w3 w4+w0 wB: w2:" w8: w7: [2] dd=v[2]
ado2 rp[4], w2      | w6' wC w5+w9 ^6+w1 wA+w3 w4+w0 wB:" .. w8: w7: [2] dd=v[2]
movq $0, w2
ado2 rp[5], wB      | w6' wC w5+w9 ^6+w1 wA+w3 w4+w0" .. .. w8: w7: [2] dd=v[2]
adcx w2, w6         | w6 wC w5+w9 ^6+w1 wA+w3 w4+w0" .. .. w8: w7:' [2] dd=v[2]
mulx sp[2], w2, wB  | w6 wC w5+w9 ^6+w1 wA+w3 w4+w0" wB: w2: w8: w7:' [2] dd=v[2]
adox w0, w4         | w6 wC w5+w9 ^6+w1 wA+w3" w4 wB: w2: w8: w7:' [2] dd=v[2]
adc2 rp[2], w7      | w6 wC w5+w9 ^6+w1 wA+w3" w4 wB: w2: w8:' [3] dd=v[2]
mulx sp[8], w0, w7  | w6+w7 wC+w0 w5+w9 ^6+w1 wA+w3" w4 wB: w2: w8:' [3] dd=v[2]
adox w3, wA         | w6+w7 wC+w0 w5+w9 ^6+w1" wA w4 wB: w2: w8:' [3] dd=v[2]
adc2 rp[3], w8      | w6+w7 wC+w0 w5+w9 ^6+w1" wA w4 wB: w2:' [4] dd=v[2]
mulx sp[4], w3, w8  | w6+w7 wC+w0 w5+w9 ^6+w1" wA+w8 w4+w3 wB: w2:' [4] dd=v[2]
ado2 rp[6], w1      | w6+w7 wC+w0 w5+w9" ^6 wA+w8 w4+w3 wB: w2:' [4] dd=v[2]
adc2 rp[4], w2      | w6+w7 wC+w0 w5+w9" ^6 wA+w8 w4+w3 wB:' [5] dd=v[2]
mulx sp[9], w1, w2  | w2 w6+w7+w1 wC+w0 w5+w9" ^6 wA+w8 w4+w3 wB:' [5] dd=v[2]
adox w9, w5         | w2 w6+w7+w1 wC+w0" w5 ^6 wA+w8 w4+w3 wB:' [5] dd=v[2]
adc2 rp[5], wB      | w2 w6+w7+w1 wC+w0" w5 ^6 wA+w8 w4+w3' [6] dd=v[2]
mulx sp[6], w9, wB  | w2 w6+w7+w1 wC+w0" w5+wB ^6+w9 wA+w8 w4+w3' [6] dd=v[2]
adox w0, wC         | w2 w6+w7+w1" wC w5+wB ^6+w9 wA+w8 w4+w3' [6] dd=v[2]
adcx w3, w4         | w2 w6+w7+w1" wC w5+wB ^6+w9 wA+w8' w4 [6] dd=v[2]
mulx sp[1], w0, w3  | w2 w6+w7+w1" wC w5+wB ^6+w9 wA+w8' w4 .. w3: w0: [3] dd=v[2]
adox w7, w6         | w2" w6+w1 wC w5+wB ^6+w9 wA+w8' w4 .. w3: w0: [3] dd=v[2]
movq w6, rp[7]      | w2" ^7+w1 wC w5+wB ^6+w9 wA+w8' w4 .. w3: w0: [3] dd=v[2]
w7:=v[3]
movq $0, w6
adcx w8, wA         | w2" ^7+w1 wC w5+wB ^6+w9' wA w4 .. w3: w0: [3] dd=v[2]
adox w6, w2         | w2 ^7+w1 wC w5+wB ^6+w9' wA w4 .. w3: w0:" [3] dd=v[2]
movq w2, rp[8]      | ^8 ^7+w1 wC w5+wB ^6+w9' wA w4 .. w3: w0:" [3] dd=v[2]
mulx sp[7], w6, w8  | ^8 ^7+w1 wC+w8 w5+wB+w6 ^6+w9' wA w4 .. w3: w0:" [3] dd=v[2]
adc2 rp[6], w9      | ^8 ^7+w1 wC+w8 w5+wB+w6' ^6 wA w4 .. w3: w0:" [3] dd=v[2]
mulx sp[3], w2, w9  | ^8 ^7+w1 wC+w8 w5+wB+w6' ^6 wA w4+w9 w2: w3: w0:" [3] dd=v[2]
adcx wB, w5         | ^8 ^7+w1 wC+w8' w5+w6 ^6 wA w4+w9 w2: w3: w0:" [3] dd=v[2]
ado2 rp[3], w0      | ^8 ^7+w1 wC+w8' w5+w6 ^6 wA w4+w9 w2: w3:" [4] dd=v[2]
mulx sp[5], w0, wB  | ^8 ^7+w1 wC+w8' w5+w6 ^6+wB wA+w0 w4+w9 w2: w3:" [4] dd=v[2]
movq w7, dd
adcx w8, wC         | ^8 ^7+w1' wC w5+w6 ^6+wB wA+w0 w4+w9 w2: w3:" [4] dd=v[3]
'''

g_mul_3 = '''
                   | i >= 3
                   | ^5 ^4+s1' sC s5+s6 ^3+sB sA+s0 s4+s9 s2: s3:" [i+1] dd=v[i]
mulx sp[0], s7, s8 | ^5 ^4+s1' sC s5+s6 ^3+sB sA+s0 s4+s9 s2: s3+s8:" s7: [i]
ado2 rp[i+1], s3   | ^5 ^4+s1' sC s5+s6 ^3+sB sA+s0 s4+s9 s2:" s8: s7: [i]
adc2 rp[i+4], s1   | ^5' ^4 sC s5+s6 ^3+sB sA+s0 s4+s9 s2:" s8: s7: [i]
mulx sp[2], s1, s3 | ^5' ^4 sC s5+s6 ^3+sB sA+s0 s4+s9+s3 s2+s1:" s8: s7: [i]
ado2 rp[i+2], s2   | ^5' ^4 sC s5+s6 ^3+sB sA+s0 s4+s9+s3" s1: s8: s7: [i]
movq $0, s2
adc2 rp[i+5], s2   | ^5 ^4 sC s5+s6 ^3+sB sA+s0 s4+s9+s3" s1: s8: s7:' [i]
movq sC, rp[i+6]   | ^5 ^4 ^6 s5+s6 ^3+sB sA+s0 s4+s9+s3" s1: s8: s7:' [i]
mulx sp[7], s2, sC | ^5 ^4+sC ^6+s2 s5+s6 ^3+sB sA+s0 s4+s9+s3" s1: s8: s7:' [i]
adox s9, s4        | ^5 ^4+sC ^6+s2 s5+s6 ^3+sB sA+s0" s4+s3 s1: s8: s7:' [i]
adc2 rp[i], s7     | ^5 ^4+sC ^6+s2 s5+s6 ^3+sB sA+s0" s4+s3 s1: s8:' [i+1]
mulx sp[4], s7, s9 | ^5 ^4+sC ^6+s2 s5+s6 ^3+sB+s9 sA+s0+s7" s4+s3 s1: s8:' [i+1]
adc2 rp[i+1], s8   | ^5 ^4+sC ^6+s2 s5+s6 ^3+sB+s9 sA+s0+s7" s4+s3 s1:' [i+2]
adox s0, sA        | ^5 ^4+sC ^6+s2 s5+s6 ^3+sB+s9" sA+s7 s4+s3 s1:' [i+2]
mulx sp[6], s0, s8 | ^5 ^4+sC ^6+s2+s8 s5+s6+s0 ^3+sB+s9" sA+s7 s4+s3 s1:' [i+2]
adc2 rp[i+2], s1   | ^5 ^4+sC ^6+s2+s8 s5+s6+s0 ^3+sB+s9" sA+s7 s4+s3' [i+3]
adox rp[i+3], sB   | ^5 ^4+sC ^6+s2+s8 s5+s6+s0" sB+s9 sA+s7 s4+s3' [i+3]
adcx s3, s4        | ^5 ^4+sC ^6+s2+s8 s5+s6+s0" sB+s9 sA+s7' s4 [i+3]
movq s4, rp[i+3]   | ^5 ^4+sC ^6+s2+s8 s5+s6+s0" sB+s9 sA+s7' [i+4]
movq rp[i+6], s4   | ^5 ^4+sC s4+s2+s8 s5+s6+s0" sB+s9 sA+s7' [i+4]
mulx sp[9], s1, s3 | s3 ^5+s1 ^4+sC s4+s2+s8 s5+s6+s0" sB+s9 sA+s7' [i+4]
adox s6, s5        | s3 ^5+s1 ^4+sC s4+s2+s8" s5+s0 sB+s9 sA+s7' [i+4]
adcx s7, sA        | s3 ^5+s1 ^4+sC s4+s2+s8" s5+s0 sB+s9' sA [i+4]
movq rp[i+4], s7   | s3 ^5+s1 s7+sC s4+s2+s8" s5+s0 sB+s9' sA [i+4]
movq sA, rp[i+4]   | s3 ^5+s1 s7+sC s4+s2+s8" s5+s0 sB+s9' [i+5]
mulx sp[8], s6, sA | s3 ^5+s1+sA s7+sC+s6 s4+s2+s8" s5+s0 sB+s9' [i+5]
adox s2, s4        | s3 ^5+s1+sA s7+sC+s6" s4+s8 s5+s0 sB+s9' [i+5]
movq s5, rp[i+6]   | s3 ^5+s1+sA s7+sC+s6" s4+s8 s0: sB+s9' [i+5]
s2:=v[i+1]         | s3 ^5+s1+sA s7+sC+s6" s4+s8 s0: sB+s9' [i+5] s2
adcx s9, sB        | s3 ^5+s1+sA s7+sC+s6" s4+s8 s0:' sB [i+5] s2
mulx sp[1], s5, s9 | s3 ^5+s1+sA s7+sC+s6" s4+s8 s0:' sB {2} s9: s5: [i+1] s2
adox sC, s7        | s3 ^5+s1+sA" s7+s6 s4+s8 s0:' sB {2} s9: s5: [i+1] s2
adc2 rp[i+6], s0   | s3 ^5+s1+sA" s7+s6 s4+s8' .. sB {2} s9: s5: [i+1] s2
mulx sp[3], s0, sC | s3 ^5+s1+sA" s7+s6 s4+s8' .. sB sC: s0: s9: s5: [i+1] s2
adox rp[i+5], s1   | s3" s1+sA s7+s6 s4+s8' .. sB sC: s0: s9: s5: [i+1] s2
movq sB, rp[i+5]   | s3" s1+sA s7+s6 s4+s8' .. .. sC: s0: s9: s5: [i+1] s2
adcx s8, s4        | s3" s1+sA s7+s6' s4 .. .. sC: s0: s9: s5: [i+1] s2
movq s4, rp[i+7]   | s3" s1+sA s7+s6' .. .. .. sC: s0: s9: s5: [i+1] s2
mulx sp[5], s8, sB | s3" s1+sA s7+s6' .. sB: s8: sC: s0: s9: s5: [i+1] s2
movq s2, dd        | s3" s1+sA s7+s6' .. sB: s8: sC: s0: s9: s5: [i+1]
movq $0, s2
adox s2, s3        | s3 s1+sA s7+s6' .. sB: s8: sC: s0: s9: s5:" [i+1]
'''

g_mul_4 = '''
                   | i >= 4
                   | s3 s1+sA s7+s6' .. sB: s8: sC: s0: s9: s5:" [i] dd=v[i]
mulx sp[0], s2, s4 | s3 s1+sA s7+s6' .. sB: s8: sC: s0: s9+s4: s5+s2:" [i]
adcx s6, s7        | s3 s1+sA' s7 .. sB: s8: sC: s0: s9+s4: s5+s2:" [i]
ado2 rp[i], s5     | s3 s1+sA' s7 .. sB: s8: sC: s0: s9+s4:" s2: [i]
mulx sp[2], s5, s6 | s3 s1+sA' s7 .. sB: s8: sC+s6: s0+s5: s9+s4:" s2: [i]
adcx sA, s1        | s3' s1 s7 .. sB: s8: sC+s6: s0+s5: s9+s4:" s2: [i]
ado2 rp[i+1], s9   | s3' s1 s7 .. sB: s8: sC+s6: s0+s5:" s4: s2: [i]
mulx sp[6], s9, sA | s3' s1 s7+sA s9: sB: s8: sC+s6: s0+s5:" s4: s2: [i]
movq s7, rp[i+7]   | s3' s1 sA: s9: sB: s8: sC+s6: s0+s5:" s4: s2: [i]
movq $0, s7
adcx s7, s3        | s3 s1 sA: s9: sB: s8: sC+s6: s0+s5:" s4: s2:' [i]
ado2 rp[i+2], s0   | s3 s1 sA: s9: sB: s8: sC+s6:" s5: s4: s2:' [i]
mulx sp[4], s0, s7 | s3 s1 sA: s9: sB+s7: s8+s0: sC+s6:" s5: s4: s2:' [i]
adc2 rp[i], s2     | s3 s1 sA: s9: sB+s7: s8+s0: sC+s6:" s5: s4:' [i+1]
ado2 rp[i+3], sC   | s3 s1 sA: s9: sB+s7: s8+s0:" s6: s5: s4:' [i+1]
mulx sp[8], s2, sC | s3+sC s1+s2 sA: s9: sB+s7: s8+s0:" s6: s5: s4:' [i+1]
adc2 rp[i+1], s4   | s3+sC s1+s2 sA: s9: sB+s7: s8+s0:" s6: s5:' [i+2]
ado2 rp[i+4], s8   | s3+sC s1+s2 sA: s9: sB+s7:" s0: s6: s5:' [i+2]
mulx sp[5], s4, s8 | s3+sC s1+s2 sA: s9+s8: sB+s7+s4:" s0: s6: s5:' [i+2]
adc2 rp[i+2], s5   | s3+sC s1+s2 sA: s9+s8: sB+s7+s4:" s0: s6:' [i+3]
ado2 rp[i+5], sB   | s3+sC s1+s2 sA: s9+s8:" s7+s4: s0: s6:' [i+3]
mulx sp[7], s5, sB | s3+sC s1+s2+sB sA+s5: s9+s8:" s7+s4: s0: s6:' [i+3]
adc2 rp[i+3], s6   | s3+sC s1+s2+sB sA+s5: s9+s8:" s7+s4: s0:' [i+4]
s6:=v[i+1]
ado2 rp[i+6], s9   | s3+sC s1+s2+sB sA+s5:" s8: s7+s4: s0:' [i+4]
movq s3, rp[i+8]   | ^8+sC s1+s2+sB sA+s5:" s8: s7+s4: s0:' [i+4]
mulx sp[9], s3, s9 | s9 ^8+sC+s3 s1+s2+sB sA+s5:" s8: s7+s4: s0:' [i+4]
adc2 rp[i+4], s0   | s9 ^8+sC+s3 s1+s2+sB sA+s5:" s8: s7+s4:' [i+5]
ado2 rp[i+7], sA   | s9 ^8+sC+s3 s1+s2+sB" s5: s8: s7+s4:' [i+5]
mulx sp[1], s0, sA | s9 ^8+sC+s3 s1+s2+sB" s5: s8: s7+s4:' {2} sA: s0: [i+1]
adcx s4, s7        | s9 ^8+sC+s3 s1+s2+sB" s5: s8:' s7: {2} sA: s0: [i+1]
adox s2, s1        | s9 ^8+sC+s3" s1+sB s5: s8:' s7: {2} sA: s0: [i+1]
mulx sp[3], s2, s4 | s9 ^8+sC+s3" s1+sB s5: s8:' s7: s4: s2: sA: s0: [i+1]
movq s6, dd
adc2 rp[i+6], s8   | s9 ^8+sC+s3" s1+sB s5:' .. s7: s4: s2: sA: s0: [i+1]
'''

g_mul_5 = '''
                   | i >= 5
                   | s9 ^7+sC+s3" s1+sB s5:' .. s7: s4: s2: sA: s0: [i] dd=v[i]
mulx sp[0], s6, s8 | s9 ^7+sC+s3" s1+sB s5:' .. s7: s4: s2: sA+s8: s0+s6: [i]
adox rp[i+7], sC   | s9" sC+s3 s1+sB s5:' .. s7: s4: s2: sA+s8: s0+s6: [i]
adc2 rp[i+6], s5   | s9" sC+s3 s1+sB' .. .. s7: s4: s2: sA+s8: s0+s6: [i]
movq $0, s5
adox s5, s9        | s9 sC+s3 s1+sB' .. .. s7: s4: s2: sA+s8: s0+s6:" [i]
adcx sB, s1        | s9 sC+s3' s1 .. .. s7: s4: s2: sA+s8: s0+s6:" [i]
mulx sp[2], s5, sB | s9 sC+s3' s1 .. .. s7: s4+sB: s2+s5: sA+s8: s0+s6:" [i]
ado2 rp[i], s0     | s9 sC+s3' s1 .. .. s7: s4+sB: s2+s5: sA+s8:" s6: [i]
adcx s3, sC        | s9' sC s1 .. .. s7: s4+sB: s2+s5: sA+s8:" s6: [i]
mulx sp[5], s0, s3 | s9' sC s1 s3: s0: s7: s4+sB: s2+s5: sA+s8:" s6: [i]
ado2 rp[i+1], sA   | s9' sC s1 s3: s0: s7: s4+sB: s2+s5:" s8: s6: [i]
movq $0, sA
adcx sA, s9        | s9 sC s1 s3: s0: s7: s4+sB: s2+s5:" s8: s6:' [i]
ado2 rp[i+2], s2   | s9 sC s1 s3: s0: s7: s4+sB:" s5: s8: s6:' [i]
mulx sp[4], s2, sA | s9 sC s1 s3: s0+sA: s7+s2: s4+sB:" s5: s8: s6:' [i]
adc2 rp[i], s6     | s9 sC s1 s3: s0+sA: s7+s2: s4+sB:" s5: s8:' [i+1]
ado2 rp[i+3], s4   | s9 sC s1 s3: s0+sA: s7+s2:" sB: s5: s8:' [i+1]
mulx sp[7], s4, s6 | s9 sC+s6 s1+s4 s3: s0+sA: s7+s2:" sB: s5: s8:' [i+1]
adc2 rp[i+1], s8   | s9 sC+s6 s1+s4 s3: s0+sA: s7+s2:" sB: s5:' [i+2]
ado2 rp[i+4], s7   | s9 sC+s6 s1+s4 s3: s0+sA:" s2: sB: s5:' [i+2]
mulx sp[6], s7, s8 | s9 sC+s6 s1+s4+s8 s3+s7: s0+sA:" s2: sB: s5:' [i+2]
adc2 rp[i+2], s5   | s9 sC+s6 s1+s4+s8 s3+s7: s0+sA:" s2: sB:' [i+3]
ado2 rp[i+5], s0   | s9 sC+s6 s1+s4+s8 s3+s7:" sA: s2: sB:' [i+3]
mulx sp[9], s0, s5 | s5 s9+s0 sC+s6 s1+s4+s8 s3+s7:" sA: s2: sB:' [i+3]
adc2 rp[i+3], sB   | s5 s9+s0 sC+s6 s1+s4+s8 s3+s7:" sA: s2:' [i+4]
sB:=v[i+1]
ado2 rp[i+6], s3   | s5 s9+s0 sC+s6 s1+s4+s8" s7: sA: s2:' [i+4]
movq s9, rp[i+7]   | s5 ^7+s0 sC+s6 s1+s4+s8" s7: sA: s2:' [i+4]
mulx sp[8], s3, s9 | s5 ^7+s0+s9 sC+s6+s3 s1+s4+s8" s7: sA: s2:' [i+4]
adc2 rp[i+4], s2   | s5 ^7+s0+s9 sC+s6+s3 s1+s4+s8" s7: sA:' [i+5]
adox s4, s1        | s5 ^7+s0+s9 sC+s6+s3" s1+s8 s7: sA:' [i+5]
mulx sp[1], s2, s4 | s5 ^7+s0+s9 sC+s6+s3" s1+s8 s7: sA:' {2} s4: s2: [i+1]
adc2 rp[i+5], sA   | s5 ^7+s0+s9 sC+s6+s3" s1+s8 s7:' {3} s4: s2: [i+1]
adox s6, sC        | s5 ^7+s0+s9" sC+s3 s1+s8 s7:' {3} s4: s2: [i+1]
mulx sp[3], s6, sA | s5 ^7+s0+s9" sC+s3 s1+s8 s7:' .. sA: s6: s4: s2: [i+1]
movq sB, dd
adc2 rp[i+6], s7   | s5 ^7+s0+s9" sC+s3 s1+s8' .. .. sA: s6: s4: s2: [i+1]
'''

g_mul_6 = '''
                   | i >= 6
                   | s5 ^6+s0+s9" sC+s3 s1+s8' .. .. sA: s6: s4: s2: [i]
mulx sp[0], s7, sB | s5 ^6+s0+s9" sC+s3 s1+s8' .. .. sA: s6: s4+sB: s2+s7: [i]
adox rp[i+6], s0   | s5" s0+s9 sC+s3 s1+s8' .. .. sA: s6: s4+sB: s2+s7: [i]
adcx s8, s1        | s5" s0+s9 sC+s3' s1 .. .. sA: s6: s4+sB: s2+s7: [i]
movq $0, s8
adox s8, s5        | s5 s0+s9 sC+s3' s1 .. .. sA: s6: s4+sB: s2+s7:" [i]
movq s5, rp[i+6]   | ^6 s0+s9 sC+s3' s1 .. .. sA: s6: s4+sB: s2+s7:" [i]
mulx sp[4], s5, s8 | ^6 s0+s9 sC+s3' s1 s8: s5: sA: s6: s4+sB: s2+s7:" [i]
adcx s3, sC        | ^6 s0+s9' sC s1 s8: s5: sA: s6: s4+sB: s2+s7:" [i]
ado2 rp[i], s2     | ^6 s0+s9' sC s1 s8: s5: sA: s6: s4+sB:" s7: [i]
mulx sp[2], s2, s3 | ^6 s0+s9' sC s1 s8: s5: sA+s3: s6+s2: s4+sB:" s7: [i]
adcx s9, s0        | ^6' s0 sC s1 s8: s5: sA+s3: s6+s2: s4+sB:" s7: [i]
movq $0, s9
ado2 rp[i+1], s4   | ^6' s0 sC s1 s8: s5: sA+s3: s6+s2:" sB: s7: [i]
adc2 rp[i+6], s9   | ^6 s0 sC s1 s8: s5: sA+s3: s6+s2:" sB: s7:' [i]
mulx sp[6], s4, s9 | ^6 s0 sC+s9 s1+s4 s8: s5: sA+s3: s6+s2:" sB: s7:' [i]
ado2 rp[i+2], s6   | ^6 s0 sC+s9 s1+s4 s8: s5: sA+s3:" s2: sB: s7:' [i]
adc2 rp[i], s7     | ^6 s0 sC+s9 s1+s4 s8: s5: sA+s3:" s2: sB:' [i+1]
mulx sp[3], s6, s7 | ^6 s0 sC+s9 s1+s4 s8: s5+s7: sA+s3+s6:" s2: sB:' [i+1]
ado2 rp[i+3], sA   | ^6 s0 sC+s9 s1+s4 s8: s5+s7:" s3+s6: s2: sB:' [i+1]
adc2 rp[i+1], sB   | ^6 s0 sC+s9 s1+s4 s8: s5+s7:" s3+s6: s2:' [i+2]
mulx sp[5], sA, sB | ^6 s0 sC+s9 s1+s4+sB s8+sA: s5+s7:" s3+s6: s2:' [i+2]
ado2 rp[i+4], s5   | ^6 s0 sC+s9 s1+s4+sB s8+sA:" s7: s3+s6: s2:' [i+2]
adc2 rp[i+2], s2   | ^6 s0 sC+s9 s1+s4+sB s8+sA:" s7: s3+s6:' [i+3]
mulx sp[8], s2, s5 | ^6+s5 s0+s2 sC+s9 s1+s4+sB s8+sA:" s7: s3+s6:' [i+3]
ado2 rp[i+5], s8   | ^6+s5 s0+s2 sC+s9 s1+s4+sB" sA: s7: s3+s6:' [i+3]
s8:=v[i+1]         | ^6+s5 s0+s2 sC+s9 s1+s4+sB" sA: s7: s3+s6:' [i+3] s8
adc2 rp[i+3], s3   | ^6+s5 s0+s2 sC+s9 s1+s4+sB" sA: s7:' s6: [i+3] s8
adox s4, s1        | ^6+s5 s0+s2 sC+s9" s1+sB sA: s7:' s6: [i+3] s8
mulx sp[9], s3, s4 | s4 ^6+s5+s3 s0+s2 sC+s9" s1+sB sA: s7:' s6: [i+3] s8
adc2 rp[i+4], s7   | s4 ^6+s5+s3 s0+s2 sC+s9" s1+sB sA:' .. s6: [i+3] s8
adox s9, sC        | s4 ^6+s5+s3 s0+s2" sC s1+sB sA:' .. s6: [i+3] s8
mulx sp[7], s7, s9 | s4 ^6+s5+s3 s0+s2+s9" sC+s7 s1+sB sA:' .. s6: [i+3] s8
adc2 rp[i+5], sA   | s4 ^6+s5+s3 s0+s2+s9" sC+s7 s1+sB' .. .. s6: [i+3] s8
adox s2, s0        | s4 ^6+s5+s3" s0+s9 sC+s7 s1+sB' .. .. s6: [i+3] s8
mulx sp[1], s2, sA | s4 ^6+s5+s3" s0+s9 sC+s7 s1+sB' .. .. s6: sA: s2: [i+1] s8
movq s8, dd        | s4 ^6+s5+s3" s0+s9 sC+s7 s1+sB' .. .. s6: sA: s2: [i+1]
adcx sB, s1        | s4 ^6+s5+s3" s0+s9 sC+s7' s1 .. .. s6: sA: s2: [i+1]
'''

g_mul_7 = '''
                   | i >= 7
                   | s4 ^5+s5+s3" s0+s9 sC+s7' s1 .. .. s6: sA: s2: [i] dd=v[i]
mulx sp[0], s8, sB | s4 ^5+s5+s3" s0+s9 sC+s7' s1 .. .. s6: sA+sB: s2+s8: [i]
adox s3, s5        | s4" ^5+s5 s0+s9 sC+s7' s1 .. .. s6: sA+sB: s2+s8: [i]
movq s1, rp[i+6]   | s4" ^5+s5 s0+s9 sC+s7' ^6 .. .. s6: sA+sB: s2+s8: [i]
mulx sp[3], s1, s3 | s4" ^5+s5 s0+s9 sC+s7' ^6 s3: s1: s6: sA+sB: s2+s8: [i]
adcx s7, sC        | s4" ^5+s5 s0+s9' sC ^6 s3: s1: s6: sA+sB: s2+s8: [i]
movq $0, s7
adox s7, s4        | s4 ^5+s5 s0+s9' sC ^6 s3: s1: s6: sA+sB: s2+s8:" [i]
adcx s9, s0        | s4 ^5+s5' s0 sC ^6 s3: s1: s6: sA+sB: s2+s8:" [i]
mulx sp[2], s7, s9 | s4 ^5+s5' s0 sC ^6 s3: s1+s9: s6+s7: sA+sB: s2+s8:" [i]
ado2 rp[i], s2     | s4 ^5+s5' s0 sC ^6 s3: s1+s9: s6+s7: sA+sB:" s8: [i]
movq $0, s2
adcx rp[i+5], s5   | s4' s5 s0 sC ^6 s3: s1+s9: s6+s7: sA+sB:" s8: [i]
ado2 rp[i+1], sA   | s4' s5 s0 sC ^6 s3: s1+s9: s6+s7:" sB: s8: [i]
adcx s2, s4        | s4 s5 s0 sC ^6 s3: s1+s9: s6+s7:" sB: s8:' [i]
mulx sp[5], s2, sA | s4 s5 s0 sC+sA ^6+s2 s3: s1+s9: s6+s7:" sB: s8:' [i]
ado2 rp[i+2], s6   | s4 s5 s0 sC+sA ^6+s2 s3: s1+s9:" s7: sB: s8:' [i]
adc2 rp[i], s8     | s4 s5 s0 sC+sA ^6+s2 s3: s1+s9:" s7: sB:' [i+1]
mulx sp[4], s6, s8 | s4 s5 s0 sC+sA ^6+s2+s8 s3+s6: s1+s9:" s7: sB:' [i+1]
ado2 rp[i+3], s1   | s4 s5 s0 sC+sA ^6+s2+s8 s3+s6:" s9: s7: sB:' [i+1]
adc2 rp[i+1], sB   | s4 s5 s0 sC+sA ^6+s2+s8 s3+s6:" s9: s7:' [i+2]
mulx sp[7], s1, sB | s4 s5+sB s0+s1 sC+sA ^6+s2+s8 s3+s6:" s9: s7:' [i+2]
ado2 rp[i+4], s3   | s4 s5+sB s0+s1 sC+sA ^6+s2+s8" s6: s9: s7:' [i+2]
adc2 rp[i+2], s7   | s4 s5+sB s0+s1 sC+sA ^6+s2+s8" s6: s9:' [i+3]
mulx sp[6], s3, s7 | s4 s5+sB s0+s1+s7 sC+sA+s3 ^6+s2+s8" s6: s9:' [i+3]
adox rp[i+6], s2   | s4 s5+sB s0+s1+s7 sC+sA+s3" s2+s8 s6: s9:' [i+3]
movq s2, rp[i+5]   | s4 s5+sB s0+s1+s7 sC+sA+s3" s8: s6: s9:' [i+3]
s2:=v[i+1]         | s4 s5+sB s0+s1+s7 sC+sA+s3" s8: s6: s9:' [i+3] s2
adc2 rp[i+3], s9   | s4 s5+sB s0+s1+s7 sC+sA+s3" s8: s6:' [i+4] s2
movq s4, rp[i+6]   | ^6 s5+sB s0+s1+s7 sC+sA+s3" s8: s6:' [i+4] s2
mulx sp[9], s4, s9 | s9 ^6+s4 s5+sB s0+s1+s7 sC+sA+s3" s8: s6:' [i+4] s2
adox sA, sC        | s9 ^6+s4 s5+sB s0+s1+s7" sC+s3 s8: s6:' [i+4] s2
adc2 rp[i+4], s6   | s9 ^6+s4 s5+sB s0+s1+s7" sC+s3 s8:' [i+5] s2
mulx sp[8], s6, sA | s9 ^6+s4+sA s5+sB+s6 s0+s1+s7" sC+s3 s8:' [i+5] s2
adox s1, s0        | s9 ^6+s4+sA s5+sB+s6" s0+s7 sC+s3 s8:' [i+5] s2
adc2 rp[i+5], s8   | s9 ^6+s4+sA s5+sB+s6" s0+s7 sC+s3' [i+6] s2
mulx sp[1], s1, s8 | s9 ^6+s4+sA s5+sB+s6" s0+s7 sC+s3' {3} s8: s1: [i+1] s2
movq s2, dd        | s9 ^6+s4+sA s5+sB+s6" s0+s7 sC+s3' {3} s8: s1: [i+1]
adox sB, s5        | s9 ^6+s4+sA" s5+s6 s0+s7 sC+s3' {3} s8: s1: [i+1]
'''

g_mul_8 = '''
                   | i >= 8
                   | s9 ^5+s4+sA" s5+s6 s0+s7 sC+s3' .. .. .. s8: s1: [i] dd=v[i]
mulx sp[2], s2, sB | s9 ^5+s4+sA" s5+s6 s0+s7 sC+s3' .. sB: s2: s8: s1: [i]
adcx s3, sC        | s9 ^5+s4+sA" s5+s6 s0+s7' sC .. sB: s2: s8: s1: [i]
adox rp[i+5], s4   | s9" s4+sA s5+s6 s0+s7' sC .. sB: s2: s8: s1: [i]
movq sC, rp[i+5]   | s9" s4+sA s5+s6 s0+s7' .. .. sB: s2: s8: s1: [i]
mulx sp[0], s3, sC | s9" s4+sA s5+s6 s0+s7' .. .. sB: s2: s8+sC: s1+s3: [i]
adcx s7, s0        | s9" s4+sA s5+s6' s0 .. .. sB: s2: s8+sC: s1+s3: [i]
movq $0, s7
adox s7, s9        | s9 s4+sA s5+s6' s0 .. .. sB: s2: s8+sC: s1+s3:" [i]
adcx s6, s5        | s9 s4+sA' s5 s0 .. .. sB: s2: s8+sC: s1+s3:" [i]
mulx sp[4], s6, s7 | s9 s4+sA' s5 s0 s7: s6: sB: s2: s8+sC: s1+s3:" [i]
ado2 rp[i], s1     | s9 s4+sA' s5 s0 s7: s6: sB: s2: s8+sC:" s3: [i]
adcx sA, s4        | s9' s4 s5 s0 s7: s6: sB: s2: s8+sC:" s3: [i]
mulx sp[1], s1, sA | s9' s4 s5 s0 s7: s6: sB: s2+sA: s8+sC+s1:" s3: [i]
ado2 rp[i+1], s8   | s9' s4 s5 s0 s7: s6: sB: s2+sA:" sC+s1: s3: [i]
movq $0, s8
adcx s8, s9        | s9 s4 s5 s0 s7: s6: sB: s2+sA:" sC+s1: s3:' [i]
ado2 rp[i+2], s2   | s9 s4 s5 s0 s7: s6: sB:" sA: sC+s1: s3:' [i]
mulx sp[6], s2, s8 | s9 s4 s5+s8 s0+s2 s7: s6: sB:" sA: sC+s1: s3:' [i]
adc2 rp[i], s3     | s9 s4 s5+s8 s0+s2 s7: s6: sB:" sA: sC+s1:' [i+1]
ado2 rp[i+3], sB   | s9 s4 s5+s8 s0+s2 s7: s6:" .. sA: sC+s1:' [i+1]
mulx sp[3], s3, sB | s9 s4 s5+s8 s0+s2 s7: s6+sB:" s3: sA: sC+s1:' [i+1]
adc2 rp[i+1], sC   | s9 s4 s5+s8 s0+s2 s7: s6+sB:" s3: sA:' s1: [i+1]
ado2 rp[i+4], s6   | s9 s4 s5+s8 s0+s2 s7:" sB: s3: sA:' s1: [i+1]
mulx sp[5], s6, sC | s9 s4 s5+s8 s0+s2+sC s7+s6:" sB: s3: sA:' s1: [i+1]
adc2 rp[i+2], sA   | s9 s4 s5+s8 s0+s2+sC s7+s6:" sB: s3:' .. s1: [i+1]
sA:=v[i+1]         | s9 s4 s5+s8 s0+s2+sC s7+s6:" sB: s3:' .. s1: [i+1] sA
if tail_jump: jmp tail
if tail_here: tail:
ado2 rp[i+5], s7   | s9 s4 s5+s8 s0+s2+sC" s6: sB: s3:' .. s1: [i+1] sA
movq s4, rp[i+6]   | s9 ^6 s5+s8 s0+s2+sC" s6: sB: s3:' .. s1: [i+1] sA
mulx sp[8], s4, s7 | s9+s7 ^6+s4 s5+s8 s0+s2+sC" s6: sB: s3:' .. s1: [i+1] sA
adc2 rp[i+3], s3   | s9+s7 ^6+s4 s5+s8 s0+s2+sC" s6: sB:' .. .. s1: [i+1] sA
adox s2, s0        | s9+s7 ^6+s4 s5+s8" s0+sC s6: sB:' .. .. s1: [i+1] sA
mulx sp[7], s2, s3 | s9+s7 ^6+s4+s3 s5+s8+s2" s0+sC s6: sB:' .. .. s1: [i+1] sA
| sB not ready?
adox s8, s5        | s9+s7 ^6+s4+s3" s5+s2 s0+sC s6: sB:' .. .. s1: [i+1] sA
adc2 rp[i+4], sB   | s9+s7 ^6+s4+s3" s5+s2 s0+sC s6:' {3} s1: [i+1] sA
mulx sp[9], s8, sB | sB s9+s7+s8 ^6+s4+s3" s5+s2 s0+sC s6:' {3} s1: [i+1] sA
movq sA, dd        | sB s9+s7+s8 ^6+s4+s3" s5+s2 s0+sC s6:' {3} s1: [i+1]
adox rp[i+6], s4   | sB s9+s7+s8" s4+s3 s5+s2 s0+sC s6:' {3} s1: [i+1]
adc2 rp[i+5], s6   | sB s9+s7+s8" s4+s3 s5+s2 s0+sC' {4} s1: [i+1]
'''

g_mul_9 = '''
                   | i = 9
                   | sB s9+s7+s8" s4+s3 s5+s2 s0+sC' .. .. .. .. s1: [i] dd=v[i]
mulx sp[1], s6, sA | sB s9+s7+s8" s4+s3 s5+s2 s0+sC' .. .. sA: s6: s1: [i]
adox s7, s9        | sB" s9+s8 s4+s3 s5+s2 s0+sC' .. .. sA: s6: s1: [i]
movq $0, s7
adcx sC, s0        | sB" s9+s8 s4+s3 s5+s2' s0 .. .. sA: s6: s1: [i]
adox s7, sB        | sB s9+s8 s4+s3 s5+s2' s0 .. .. sA: s6: s1:" [i]
mulx sp[3], s7, sC | sB s9+s8 s4+s3 s5+s2' s0 sC: s7: sA: s6: s1:" [i]
adcx s2, s5        | sB s9+s8 s4+s3' s5 s0 sC: s7: sA: s6: s1:" [i]
ado2 rp[i], s1     | sB s9+s8 s4+s3' s5 s0 sC: s7: sA: s6:" [i+1]
mulx sp[0], s1, s2 | sB s9+s8 s4+s3' s5 s0 sC: s7: sA: s6+s2:" s1: [i]
adcx s3, s4        | sB s9+s8' s4 s5 s0 sC: s7: sA: s6+s2:" s1: [i]
movq s0, rp[i+5]   | sB s9+s8' s4 s5 .. sC: s7: sA: s6+s2:" s1: [i]
mulx sp[5], s0, s3 | sB s9+s8' s4 s5+s3 s0: sC: s7: sA: s6+s2:" s1: [i]
ado2 rp[i+1], s6   | sB s9+s8' s4 s5+s3 s0: sC: s7: sA:" s2: s1: [i]
adcx s8, s9        | sB' s9 s4 s5+s3 s0: sC: s7: sA:" s2: s1: [i]
mulx sp[2], s6, s8 | sB' s9 s4 s5+s3 s0: sC: s7+s8: sA+s6:" s2: s1: [i]
ado2 rp[i+2], sA   | sB' s9 s4 s5+s3 s0: sC: s7+s8:" s6: s2: s1: [i]
movq $0, sA
adcx sA, sB        | sB s9 s4 s5+s3 s0: sC: s7+s8:" s6: s2: s1:' [i]
ado2 rp[i+3], s7   | sB s9 s4 s5+s3 s0: sC:" s8: s6: s2: s1:' [i]
mulx sp[7], s7, sA | sB s9+sA s4+s7 s5+s3 s0: sC:" s8: s6: s2: s1:' [i]
adc2 rp[i], s1     | sB s9+sA s4+s7 s5+s3 s0: sC:" s8: s6: s2:' [i+1]
ado2 rp[i+4], sC   | sB s9+sA s4+s7 s5+s3 s0:" .. s8: s6: s2:' [i+1]
mulx sp[4], s1, sC | sB s9+sA s4+s7 s5+s3 s0+sC:" s1: s8: s6: s2:' [i+1]
adc2 rp[i+1], s2   | sB s9+sA s4+s7 s5+s3 s0+sC:" s1: s8: s6:' [i+2]
ado2 rp[i+5], s0   | sB s9+sA s4+s7 s5+s3" sC: s1: s8: s6:' [i+2]
mulx sp[9], s0, s2 | s2 sB+s0 s9+sA s4+s7 s5+s3" sC: s1: s8: s6:' [i+2]
adc2 rp[i+2], s6   | s2 sB+s0 s9+sA s4+s7 s5+s3" sC: s1: s8:' [i+3]
adox s3, s5        | s2 sB+s0 s9+sA s4+s7" s5 sC: s1: s8:' [i+3]
mulx sp[6], s3, s6 | s2 sB+s0 s9+sA s4+s7+s6" s5+s3 sC: s1: s8:' [i+3]
adc2 rp[i+3], s8   | s2 sB+s0 s9+sA s4+s7+s6" s5+s3 sC: s1:' [i+4]
mulx sp[8], s8, dd | s2 sB+s0+dd s9+sA+s8 s4+s7+s6" s5+s3 sC: s1:' [i+4]
adox s7, s4        | s2 sB+s0+dd s9+sA+s8" s4+s6 s5+s3 sC: s1:' [i+4]
adc2 rp[i+4], s1   | s2 sB+s0+dd s9+sA+s8" s4+s6 s5+s3 sC:' [i+5]
adox sA, s9        | s2 sB+s0+dd" s9+s8 s4+s6 s5+s3 sC:' [i+5]
adc2 rp[i+5], sC   | s2 sB+s0+dd" s9+s8 s4+s6 s5+s3' [i+6]
movq rp[i+6], sp
adox s0, sB        | s2" sB+dd s9+s8 s4+s6 s5+s3' [i+6]
movq $0, s0
adcx s3, s5        | s2" sB+dd s9+s8 s4+s6' s5 [i+6]
movq s5, rp[i+6]   | s2" sB+dd s9+s8 s4+s6' [i+7]
adox s0, s2        | s2 sB+dd s9+s8 s4+s6' [i+7]
adcx s6, s4
movq s4, rp[i+7]   | s2 sB+dd s9+s8' [i+8]
adcx s8, s9
movq s9, rp[i+8]   | s2 sB+dd' [i+9]
adcx sB, dd
movq dd, rp[i+9]
adcx s0, s2
movq s2, rp[i+10]
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P
import gen_mul7_t03 as A
import gen_mul8_aligned as E
import gen_mul11_ryzen as L

def extract_v(i, alignment, tgt):
    if (i < 2) or (i >= 10) or (alignment == None):
        return ''
    return L.extract_v(i, alignment, tgt)

def evaluate_row(s, i, alignment):
    m = E.g_if_patt.match(s)
    if m:
        d = \
                {\
                    'tail_jump' : (i == 8) and (alignment != 0),
                    'tail_here' : (i == 8) and (alignment == 0),
                }
        s = P.evaluate_if(s, d, m.group(1), m.group(2))

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

    m = L.g_ad2_patt.match(s)
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
                if k == 'jmp tail':
                    break

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
        code = chew_code(g_preamble, 0, None, None)
    else:
        code = chew_code(g_load_0, None, True, None)
    code += chew_code(g_mul_012, 0, alignment, None)
    p = list(range(0xC + 1))
    code += chew_code(g_mul_3, 3, alignment, p)
    code += chew_code(g_mul_4, 4, alignment, p)
    code += chew_code(g_mul_5, 5, alignment, p)
    code += chew_code(g_mul_6, 6, alignment, p)
    code += chew_code(g_mul_7, 7, alignment, p)
    code += chew_code(g_mul_8, 8, alignment, p)
    if not alignment:
        code += chew_code(g_mul_9, 9, alignment, p)
    return code

def do_it(o):
    code = alignment_code(8) + alignment_code(0)
    P.cook_asm(o, code, L.g_var_map, True)

if __name__ == '__main__':
    with open(sys.argv[1], 'wb') as g_out:
        do_it(g_out)
