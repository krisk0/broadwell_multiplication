'''
8x8 multiplication targeting Ryzen. Uses rsp to free rsi.

112 ticks on Ryzen, 133 ticks on Broadwell
'''

"""
xmm usage:
0-3 v[]
"""

g_preamble = '''
vzeroupper
movq sp, rp[11]
movq wC, sp
movq dd, w5
and $0xF, dd
movq w5[0], dd
movq w5[1], w6
jz align0
movq w5[2], x0
movdqa w5[3], x1
movdqa w5[5], x2
movq w5[7], x3
'''

g_load_0 = '''
align0:
movdqa w5[2], x0
movdqa w5[4], x1
movdqa w5[6], x2
'''

def extract_v(i, alignment, tgt):
    if (i < 2) or (i > 7) or (alignment == None):
        return '# bad :=v[]'
    i -= 2
    if i == 0:
        return 'movq x0, ' + tgt
    if alignment:
        i -= 1
        j = i / 2 + 1
    else:
        j = i / 2
    if i & 1:
        return 'pextrq $0x1, x%s, %s' % (j, tgt)
    else:
        return 'movq x%s, %s' % (j, tgt)

g_mul_01 = '''
mulx sp[0], w0, w1    | w1 w0 == w6=v[1]
mulx sp[1], w2, w3    | w3 w1+w2 w0 == w6=v[1]
xchg dd, w6           | w3 w1+w2 w0 == dd=v[1] w6=v[0]
mulx sp[0], w4, w7    | w3+w7 w1+w2+w4 w0 == dd=v[1] w6=v[0]
rp[6]:=v[2]
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
xchg dd, w8         | wB wA+w9 w4+w6+w3" wC+w7 w2+w5' [4] == dd=v[1]
mulx sp[6], w1, w8  | wB+w8 wA+w9+w1 w4+w6+w3" wC+w7 w2+w5' [4] == dd=v[1]
adcx w5, w2         | wB+w8 wA+w9+w1 w4+w6+w3" wC+w7' w2 [4] == dd=v[1]
movq w2, rp[4]      | wB+w8 wA+w9+w1 w4+w6+w3" wC+w7' [5] == dd=v[1]
mulx sp[7], w2, w5  | w5 wB+w8+w2 wA+w9+w1 w4+w6+w3" wC+w7' [5] == dd=v[1]
adox w6, w4         | w5 wB+w8+w2 wA+w9+w1" w4+w3 wC+w7' [5] == dd=v[1]
adcx w7, wC         | w5 wB+w8+w2 wA+w9+w1" w4+w3' wC [5] == dd=v[1]
movq wC, rp[5]      | w5 wB+w8+w2 wA+w9+w1" w4+w3' [6] == dd=v[1]
mulx sp[1], w6, w0  | w5 wB+w8+w2 wA+w9+w1" w4+w3' .. .. w0: w6: [2] == dd=v[1]
adox w9, wA         | w5 wB+w8+w2" wA+w1 w4+w3' .. .. w0: w6: [2] == dd=v[1]
adcx w3, w4         | w5 wB+w8+w2" wA+w1' w4 .. .. w0: w6: [2] == dd=v[1]
mulx sp[3], w7, w9  | w5 wB+w8+w2" wA+w1' w4 w9: w7: w0: w6: [2] == dd=v[1]
mulx sp[5], w3, wC  | w5 wB+w8+w2" wA+w1+wC' w4+w3 w9: w7: w0: w6: [2] == dd=v[1]
movq rp[6], dd
adox w8, wB         | w5" wB+w2 wA+w1+wC' w4+w3 w9: w7: w0: w6: [2] == dd=v[2]
movq $0, w8
adcx w1, wA         | w5" wB+w2' wA+wC w4+w3 w9: w7: w0: w6: [2] == dd=v[2]
adox w8, w5         | w5 wB+w2' wA+wC w4+w3 w9: w7: w0: w6: [2] == dd=v[2]
'''

g_mul_2 = '''
                    | i=2
                    | s5 sB+s2' sA+sC s4+s3 s9: s7: s0: s6: [i] dd=v[i]
rp[i+4]:=v[i+1]
mulx sp[0], s1, s8  | s5 sB+s2' sA+sC s4+s3 s9: s7: s0+s8: s6+s1: [i]
adcx s2, sB         | s5' sB sA+sC s4+s3 s9: s7: s0+s8: s6+s1: [i]
| TODO: use memory instead of x4, x5?
movq sB, x5         | s5' ^5 sA+sC s4+s3 s9: s7: s0+s8: s6+s1: [i]
movq $0, s2
ado2 rp[i], s6      | s5' ^5 sA+sC s4+s3 s9: s7: s0+s8:" s1: [i]
adcx s2, s5         | s5 ^5 sA+sC s4+s3 s9: s7: s0+s8:" s1: [i]
movq s5, x4         | ^4 ^5 sA+sC s4+s3 s9: s7: s0+s8:" s1: [i]
mulx sp[2], s2, s6  | ^4 ^5 sA+sC s4+s3 s9+s6: s7+s2: s0+s8:" s1: [i]
ado2 rp[i+1], s0    | ^4 ^5 sA+sC s4+s3 s9+s6: s7+s2:" s8: s1: [i]
mulx sp[4], s0, s5  | ^4 ^5 sA+sC+s5 s4+s3+s0 s9+s6: s7+s2:" s8: s1: [i]
ado2 rp[i+2], s7    | ^4 ^5 sA+sC+s5 s4+s3+s0 s9+s6:" s2: s8: s1: [i]
mulx sp[6], s7, sB  | ^4+sB ^5+s7 sA+sC+s5 s4+s3+s0 s9+s6:" s2: s8: s1: [i]
adc2 rp[i], s1      | ^4+sB ^5+s7 sA+sC+s5 s4+s3+s0 s9+s6:" s2: s8:' [i+1]
movq x5, s1         | ^4+sB s1+s7 sA+sC+s5 s4+s3+s0 s9+s6:" s2: s8:' [i+1]
ado2 rp[i+3], s9    | ^4+sB s1+s7 sA+sC+s5 s4+s3+s0" s6: s2: s8:' [i+1]
adc2 rp[i+1], s8    | ^4+sB s1+s7 sA+sC+s5 s4+s3+s0" s6: s2:' [i+2]
mulx sp[7], s8, s9  | s9 ^4+sB+s8 s1+s7 sA+sC+s5 s4+s3+s0" s6: s2:' [i+2]
adox s3, s4         | s9 ^4+sB+s8 s1+s7 sA+sC+s5" s4+s0 s6: s2:' [i+2]
movq x4, s3         | s9 s3+sB+s8 s1+s7 sA+sC+s5" s4+s0 s6: s2:' [i+2]
adc2 rp[i+2], s2    | s9 s3+sB+s8 s1+s7 sA+sC+s5" s4+s0 s6:' [i+3]
adox sC, sA         | s9 s3+sB+s8 s1+s7" sA+s5 s4+s0 s6:' [i+3]
mulx sp[1], s2, sC  | s9 s3+sB+s8 s1+s7" sA+s5 s4+s0 s6:' sC: s2: [i+1]
adc2 rp[i+3], s6    | s9 s3+sB+s8 s1+s7" sA+s5 s4+s0' .. sC: s2: [i+1]
adox s7, s1         | s9 s3+sB+s8" s1 sA+s5 s4+s0' .. sC: s2: [i+1]
mulx sp[3], s6, s7  | s9 s3+sB+s8" s1 sA+s5 s4+s0+s7' s6: sC: s2: [i+1]
adcx s0, s4         | s9 s3+sB+s8" s1 sA+s5' s4+s7 s6: sC: s2: [i+1]
adox sB, s3         | s9" s3+s8 s1 sA+s5' s4+s7 s6: sC: s2: [i+1]
mulx sp[5], s0, sB  | s9" s3+s8 s1+sB sA+s5+s0' s4+s7 s6: sC: s2: [i+1]
movq rp[i+4], dd
movq s4, rp[i+4]    | s9" s3+s8 s1+sB sA+s5+s0' s7: s6: sC: s2: [i+1]
adcx s5, sA         | s9" s3+s8 s1+sB' sA+s0 s7: s6: sC: s2: [i+1]
'''

g_mul_3 = '''
                    | i >= 3
                    | s9" s3+s8 s1+sB' sA+s0 s7: s6: sC: s2: [i] dd=v[i]
                    | s2 should be ready after one mulx
rp[i+4]:=v[i+1]
movq $0, s4
adox s4, s9         | s9 s3+s8 s1+sB' sA+s0 s7: s6: sC: s2: [i]
mulx sp[0], s4, s5  | s9 s3+s8 s1+sB' sA+s0 s7: s6: sC+s5: s2+s4: [i]
adcx sB, s1         | s9 s3+s8' s1 sA+s0 s7: s6: sC+s5: s2+s4: [i]
ado2 rp[i], s2      | s9 s3+s8' s1 sA+s0 s7: s6: sC+s5:" s4: [i]
mulx sp[2], s2, sB  | s9 s3+s8' s1 sA+s0 s7+sB: s6+s2: sC+s5:" s4: [i]
adcx s8, s3         | s9' s3 s1 sA+s0 s7+sB: s6+s2: sC+s5:" s4: [i]
movq s3, x4         | s9' ^4 s1 sA+s0 s7+sB: s6+s2: sC+s5:" s4: [i]
ado2 rp[i+1], sC    | s9' ^4 s1 sA+s0 s7+sB: s6+s2:" s5: s4: [i]
movq $0, sC
mulx sp[4], s3, s8  | s9' ^4 s1+s8 sA+s0+s3 s7+sB: s6+s2:" s5: s4: [i]
adcx sC, s9         | s9 ^4 s1+s8 sA+s0+s3 s7+sB: s6+s2:" s5: s4: [i]
ado2 rp[i+2], s6    | s9 ^4 s1+s8 sA+s0+s3 s7+sB:" s2: s5: s4: [i]
mulx sp[6], s6, sC  | s9+sC ^4+s6 s1+s8 sA+s0+s3 s7+sB:" s2: s5: s4: [i]
adc2 rp[i], s4      | s9+sC ^4+s6 s1+s8 sA+s0+s3 s7+sB:" s2: s5:' [i+1]
movq x4, s4         | s9+sC s4+s6 s1+s8 sA+s0+s3 s7+sB:" s2: s5:' [i+1]
ado2 rp[i+3], s7    | s9+sC s4+s6 s1+s8 sA+s0+s3" sB: s2: s5:' [i+1]
adc2 rp[i+1], s5    | s9+sC s4+s6 s1+s8 sA+s0+s3" sB: s2:' [i+2]
mulx sp[7], s5, s7  | s7 s9+sC+s5 s4+s6 s1+s8 sA+s0+s3" sB: s2:' [i+2]
adox s0, sA         | s7 s9+sC+s5 s4+s6 s1+s8" sA+s3 sB: s2:' [i+2]
adc2 rp[i+2], s2    | s7 s9+sC+s5 s4+s6 s1+s8" sA+s3 sB:' [i+3]
mulx sp[5], s0, s2  | s7 s9+sC+s5 s4+s6+s2 s1+s8+s0" sA+s3 sB:' [i+3]
| delay 1 tick?
adox s8, s1         | s7 s9+sC+s5 s4+s6+s2" s1+s0 sA+s3 sB:' [i+3]
adc2 rp[i+3], sB    | s7 s9+sC+s5 s4+s6+s2" s1+s0 sA+s3' [i+4]
mulx sp[1], s8, sB  | s7 s9+sC+s5 s4+s6+s2" s1+s0 sA+s3' .. sB: s8: [i+1]
adox s6, s4         | s7 s9+sC+s5" s4+s2 s1+s0 sA+s3' .. sB: s8: [i+1]
adcx s3, sA         | s7 s9+sC+s5" s4+s2 s1+s0' sA .. sB: s8: [i+1]
mulx sp[3], s3, s6  | s7 s9+sC+s5" s4+s2 s1+s0' sA+s6 s3: sB: s8: [i+1]
movq rp[i+4], dd
adox sC, s9         | s7" s9+s5 s4+s2 s1+s0' sA+s6 s3: sB: s8: [i+1]
movq s9, rp[i+4]    | s7" ^4+s5 s4+s2 s1+s0' sA+s6 s3: sB: s8: [i+1]
'''

g_mul_4 = '''
                    | i >= 4
                    | s7" ^3+s5 s4+s2 s1+s0' sA+s6 s3: sB: s8: [i] dd=v[i]
rp[i+5]:=v[i+1]
mulx sp[0], s9, sC  | s7" ^3+s5 s4+s2 s1+s0' sA+s6 s3: sB+sC: s8+s9: [i]
adcx s0, s1         | s7" ^3+s5 s4+s2' s1 sA+s6 s3: sB+sC: s8+s9: [i]
movq $0, s0
adox s0, s7         | s7 ^3+s5 s4+s2' s1 sA+s6 s3: sB+sC: s8+s9: [i]
adcx s2, s4         | s7 ^3+s5' s4 s1 sA+s6 s3: sB+sC: s8+s9: [i]
mulx sp[2], s0, s2  | s7 ^3+s5' s4 s1 sA+s6+s2 s3+s0: sB+sC: s8+s9: [i]
ado2 rp[i], s8      | s7 ^3+s5' s4 s1 sA+s6+s2 s3+s0: sB+sC:" s9: [i]
movq $0, s8
adcx rp[i+3], s5    | s7' s5 s4 s1 sA+s6+s2 s3+s0: sB+sC:" s9: [i]
ado2 rp[i+1], sB    | s7' s5 s4 s1 sA+s6+s2 s3+s0:" sC: s9: [i]
adcx s8, s7         | s7 s5 s4 s1 sA+s6+s2 s3+s0:" sC: s9: [i]
mulx sp[4], s8, sB  | s7 s5 s4+sB s1+s8 sA+s6+s2 s3+s0:" sC: s9: [i]
ado2 rp[i+2], s3    | s7 s5 s4+sB s1+s8 sA+s6+s2" s0: sC: s9: [i]
adc2 rp[i], s9      | s7 s5 s4+sB s1+s8 sA+s6+s2" s0: sC:' [i+1]
mulx sp[3], s3, s9  | s7 s5 s4+sB s1+s8+s9 sA+s6+s2+s3" s0: sC:' [i+1]
adox s6, sA         | s7 s5 s4+sB s1+s8+s9" sA+s2+s3 s0: sC:' [i+1]
adc2 rp[i+1], sC    | s7 s5 s4+sB s1+s8+s9" sA+s2+s3 s0:' [i+2]
mulx sp[6], s6, sC  | s7+sC s5+s6 s4+sB s1+s8+s9" sA+s2+s3 s0:' [i+2]
adc2 rp[i+2], s0    | s7+sC s5+s6 s4+sB s1+s8+s9" sA+s2+s3' [i+3]
movq s1, rp[i+3]    | s7+sC s5+s6 s4+sB ^3+s8+s9" sA+s2+s3' [i+3]
mulx sp[5], s0, s1  | s7+sC s5+s6+s1 s4+sB+s0 ^3+s8+s9" sA+s2+s3' [i+3]
adox rp[i+3], s8    | s7+sC s5+s6+s1 s4+sB+s0" s8+s9 sA+s2+s3' [i+3]
adcx s2, sA         | s7+sC s5+s6+s1 s4+sB+s0" s8+s9' sA+s3 [i+3]
movq sA, rp[i+3]    | s7+sC s5+s6+s1 s4+sB+s0" s8+s9' s3: [i+3]
mulx sp[7], s2, sA  | sA s7+sC+s2 s5+s6+s1 s4+sB+s0" s8+s9' s3: [i+3]
adox sB, s4         | sA s7+sC+s2 s5+s6+s1" s4+s0 s8+s9' s3: [i+3]
movq s8, rp[i+4]    | sA s7+sC+s2 s5+s6+s1" s4+s0 s9:' s3: [i+3]
mulx sp[1], s8, sB  | sA s7+sC+s2 s5+s6+s1" s4+s0 s9:' s3: sB: s8: [i+1]
| TODO: add s8+s9 directly
adc2 rp[i+4], s9    | sA s7+sC+s2 s5+s6+s1" s4+s0' .. s3: sB: s8: [i+1]
movq rp[i+5], dd
adox s6, s5         | sA s7+sC+s2" s5+s1 s4+s0' .. s3: sB: s8: [i+1]
'''

g_mul_5 = '''
                    | i >= 5
                    | sA s7+sC+s2" s5+s1 s4+s0' .. s3: sB: s8: [i] dd=v[i]
                    | s0 should be ready after mulx
rp[i+4]:=v[i+1]
mulx sp[3], s6, s9  | sA s7+sC+s2" s5+s1 s4+s0+s9' s6: s3: sB: s8: [i]
adcx s0, s4         | sA s7+sC+s2" s5+s1' s4+s9 s6: s3: sB: s8: [i]
adox sC, s7         | sA" s7+s2 s5+s1' s4+s9 s6: s3: sB: s8: [i]
mulx sp[0], s0, sC  | sA" s7+s2 s5+s1' s4+s9 s6: s3: sB+sC: s8+s0: [i]
adcx s1, s5         | sA" s7+s2' s5 s4+s9 s6: s3: sB+sC: s8+s0: [i]
movq $0, s1
adox s1, sA         | sA s7+s2' s5 s4+s9 s6: s3: sB+sC: s8+s0: [i]
adcx s2, s7         | sA' s7 s5 s4+s9 s6: s3: sB+sC: s8+s0: [i]
mulx sp[2], s1, s2  | sA' s7 s5 s4+s9 s6+s2: s3+s1: sB+sC: s8+s0: [i]
ado2 rp[i], s8      | sA' s7 s5 s4+s9 s6+s2: s3+s1: sB+sC:" s0: [i]
movq $0, s8
adcx s8, sA         | sA s7 s5 s4+s9 s6+s2: s3+s1: sB+sC:" s0: [i]
ado2 rp[i+1], sB    | sA s7 s5 s4+s9 s6+s2: s3+s1:" sC: s0: [i]
mulx sp[5], s8, sB  | sA s7+sB s5+s8 s4+s9 s6+s2: s3+s1:" sC: s0: [i]
adc2 rp[i], s0      | sA s7+sB s5+s8 s4+s9 s6+s2: s3+s1:" sC:' [i+1]
ado2 rp[i+2], s3    | sA s7+sB s5+s8 s4+s9 s6+s2:" s1: sC:' [i+1]
mulx sp[4], s0, s3  | sA s7+sB s5+s8+s3 s4+s9+s0 s6+s2:" s1: sC:' [i+1]
adc2 rp[i+1], sC    | sA s7+sB s5+s8+s3 s4+s9+s0 s6+s2:" s1:' [i+2]
ado2 rp[i+3], s6    | sA s7+sB s5+s8+s3 s4+s9+s0" s2: s1:' [i+2]
mulx sp[7], s6, sC  | sC sA+s6 s7+sB s5+s8+s3 s4+s9+s0" s2: s1:' [i+2]
adc2 rp[i+2], s1    | sC sA+s6 s7+sB s5+s8+s3 s4+s9+s0" s2:' [i+3]
adox s9, s4         | sC sA+s6 s7+sB s5+s8+s3" s4+s0 s2:' [i+3]
mulx sp[6], s1, s9  | sC sA+s6+s9 s7+sB+s1 s5+s8+s3" s4+s0 s2:' [i+3]
adc2 rp[i+3], s2    | sC sA+s6+s9 s7+sB+s1 s5+s8+s3" s4+s0' [i+4]
adox s8, s5         | sC sA+s6+s9 s7+sB+s1" s5+s3 s4+s0' [i+4]
mulx sp[1], s2, s8  | sC sA+s6+s9 s7+sB+s1" s5+s3 s4+s0' .. s8: s2: [i+1]
movq rp[i+4], dd
adcx s0, s4         | sC sA+s6+s9 s7+sB+s1" s5+s3' s4 .. s8: s2: [i+1]
adox sB, s7         | sC sA+s6+s9" s7+s1 s5+s3' s4 .. s8: s2: [i+1]
'''

g_mul_6 = '''
                    | i = 6
                    | sC sA+s6+s9" s7+s1 s5+s3' s4 .. s8: s2: [i] dd=v[i]
rp[i+4]:=v[i+1]
if tail_jump: jmp tail
if tail_here: tail:
mulx sp[2], s0, sB  | sC sA+s6+s9" s7+s1 s5+s3' s4+sB s0: s8: s2: [i]
adcx s3, s5         | sC sA+s6+s9" s7+s1' s5 s4+sB s0: s8: s2: [i]
adox s6, sA         | sC" sA+s9 s7+s1' s5 s4+sB s0: s8: s2: [i]
mulx sp[0], s3, s6  | sC" sA+s9 s7+s1' s5 s4+sB s0: s8+s6: s2+s3: [i]
adcx s1, s7         | sC" sA+s9' s7 s5 s4+sB s0: s8+s6: s2+s3: [i]
movq s7, x4         | sC" sA+s9' x4 s5 s4+sB s0: s8+s6: s2+s3: [i]
movq $0, s1
adox s1, sC         | sC" sA+s9' x4 s5 s4+sB s0: s8+s6: s2+s3: [i]
mulx sp[1], s1, s7  | sC" sA+s9' x4 s5 s4+sB s0+s7: s8+s6+s1: s2+s3: [i]
adcx s9, sA         | sC"' sA x4 s5 s4+sB s0+s7: s8+s6+s1: s2+s3: [i]
movq sA, x5         | sC"' x5 x4 s5 s4+sB s0+s7: s8+s6+s1: s2+s3: [i]
movq $0, s9
adox s9, sC         | sC' x5 x4 s5 s4+sB s0+s7: s8+s6+s1: s2+s3: [i]
mulx sp[4], s9, sA  | sC' x5 x4+sA s5+s9 s4+sB s0+s7: s8+s6+s1: s2+s3: [i]
ado2 rp[i], s2      | sC' x5 x4+sA s5+s9 s4+sB s0+s7: s8+s6+s1:" s3: [i]
movq $0, s2
adcx s2, sC         | sC x5 x4+sA s5+s9 s4+sB s0+s7: s8+s6+s1:" s3: [i]
ado2 rp[i+1], s8    | sC x5 x4+sA s5+s9 s4+sB s0+s7:" s6+s1: s3: [i]
mulx sp[3], s2, s8  | sC x5 x4+sA s5+s9+s8 s4+sB+s2 s0+s7:" s6+s1: s3: [i]
adc2 rp[i], s3      | sC x5 x4+sA s5+s9+s8 s4+sB+s2 s0+s7:" s6+s1:' [i+1]
movq x4, s3         | sC x5 s3+sA s5+s9+s8 s4+sB+s2 s0+s7:" s6+s1:' [i+1]
ado2 rp[i+2], s0    | sC x5 s3+sA s5+s9+s8 s4+sB+s2" s7: s6+s1:' [i+1]
adcx s1, s6         | sC x5 s3+sA s5+s9+s8 s4+sB+s2" s7:' s6: [i+1]
movq s6, rp[i+3]    | sC x5 s3+sA s5+s9+s8 s4+sB+s2" s7:' ^3: [i+1]
mulx sp[5], s0, s1  | sC x5+s1 s3+sA+s0 s5+s9+s8 s4+sB+s2" s7:' ^3: [i+1]
adox sB, s4         | sC x5+s1 s3+sA+s0 s5+s9+s8" s4+s2 s7:' ^3: [i+1]
movq x5, sB         | sC sB+s1 s3+sA+s0 s5+s9+s8" s4+s2 s7:' ^3: [i+1]
adc2 rp[i+2], s7    | sC sB+s1 s3+sA+s0 s5+s9+s8" s4+s2' .. ^3: [i+1]
mulx sp[7], s6, s7  | s7 sC+s6 sB+s1 s3+sA+s0 s5+s9+s8" s4+s2' .. ^3: [i+1]
adox s9, s5         | s7 sC+s6 sB+s1 s3+sA+s0" s5+s8 s4+s2' .. ^3: [i+1]
| delay 1 tick?
adcx s2, s4         | s7 sC+s6 sB+s1 s3+sA+s0" s5+s8' s4 .. ^3: [i+1]
mulx sp[6], s2, s9  | s7 sC+s6+s9 sB+s1+s2 s3+sA+s0" s5+s8' s4 .. ^3: [i+1]
movq rp[i+4], dd
adox sA, s3         | s7 sC+s6+s9 sB+s1+s2" s3+s0 s5+s8' s4 .. ^3: [i+1]
adcx s8, s5         | s7 sC+s6+s9 sB+s1+s2" s3+s0' s5 s4 .. ^3: [i+1]
'''

g_mul_7 = '''
                    | i = 7
                    | s7 sC+s6+s9 sB+s1+s2" s3+s0' s5 s4 .. ^2: [i] dd=v[i]
mulx sp[1], s8, sA  | s7 sC+s6+s9 sB+s1+s2" s3+s0' s5 s4+sA s8: ^2: [i]
adox s1, sB         | s7 sC+s6+s9" sB+s2 s3+s0' s5 s4+sA s8: ^2: [i]
movq rp[i+2], s1    | s7 sC+s6+s9" sB+s2 s3+s0' s5 s4+sA s8: s1: [i]
adcx s0, s3         | s7 sC+s6+s9" sB+s2' s3 s5 s4+sA s8: s1: [i]
movq s4, rp[i+2]    | s7 sC+s6+s9" sB+s2' s3 s5 sA: s8: s1: [i]
mulx sp[0], s0, s4  | s7 sC+s6+s9" sB+s2' s3 s5 sA: s8+s4: s1+s0: [i]
adox s6, sC         | s7" sC+s9 sB+s2' s3 s5 sA: s8+s4: s1+s0: [i]
movq $0, s6
adcx s2, sB         | s7" sC+s9' sB s3 s5 sA: s8+s4: s1+s0: [i]
adox s6, s7         | s7 sC+s9' sB s3 s5 sA: s8+s4: s1+s0: [i]
mulx sp[3], s2, s6  | s7 sC+s9' sB s3+s6 s5+s2 sA: s8+s4: s1+s0: [i]
adcx s9, sC         | s7' sC sB s3+s6 s5+s2 sA: s8+s4: s1+s0: [i]
movq $0, s9
ado2 rp[i], s1      | s7' sC sB s3+s6 s5+s2 sA: s8+s4:" s0: [i]
adcx s9, s7         | s7 sC sB s3+s6 s5+s2 sA: s8+s4:" s0: [i]
mulx sp[2], s1, s9  | s7 sC sB s3+s6 s5+s2+s9 sA+s1: s8+s4:" s0: [i]
ado2 rp[i+1], s8    | s7 sC sB s3+s6 s5+s2+s9 sA+s1:" s4: s0: [i]
adc2 rp[i], s0      | s7 sC sB s3+s6 s5+s2+s9 sA+s1:" s4:' [i+1]
mulx sp[5], s0, s8  | s7 sC+s8 sB+s0 s3+s6 s5+s2+s9 sA+s1:" s4:' [i+1]
ado2 rp[i+2], sA    | s7 sC+s8 sB+s0 s3+s6 s5+s2+s9" s1: s4:' [i+1]
adc2 rp[i+1], s4    | s7 sC+s8 sB+s0 s3+s6 s5+s2+s9" s1:' [i+2]
mulx sp[4], s4, sA  | s7 sC+s8 sB+s0+sA s3+s6+s4 s5+s2+s9" s1:' [i+2]
adox s2, s5         | s7 sC+s8 sB+s0+sA s3+s6+s4" s5+s9 s1:' [i+2]
adc2 rp[i+2], s1    | s7 sC+s8 sB+s0+sA s3+s6+s4" s5+s9' [i+3]
mulx sp[7], s1, s2  | s2 s7+s1 sC+s8 sB+s0+sA s3+s6+s4" s5+s9' [i+3]
adox s6, s3         | s2 s7+s1 sC+s8 sB+s0+sA" s3+s4 s5+s9' [i+3]
adcx s9, s5         | s2 s7+s1 sC+s8 sB+s0+sA" s3+s4' s5 [i+3]
mulx sp[6], s6, s9  | s2 s7+s1+s9 sC+s8+s6 sB+s0+sA" s3+s4' s5 [i+3]
adox s0, sB         | s2 s7+s1+s9 sC+s8+s6" sB+sA s3+s4' s5 [i+3]
adcx s4, s3         | s2 s7+s1+s9 sC+s8+s6" sB+sA' s3 s5 [i+3]
movq s5, rp[i+3]    | s2 s7+s1+s9 sC+s8+s6" sB+sA' s3 [i+4]
movq rp[i+4], sp
adox s8, sC         | s2 s7+s1+s9" sC+s6 sB+sA' s3 [i+4]
movq s3, rp[i+4]    | s2 s7+s1+s9" sC+s6 sB+sA' [i+5]
adcx sA, sB         | s2 s7+s1+s9" sC+s6' sB [i+5]
adox s1, s7         | s2" s7+s9 sC+s6' sB [i+5]
movq $0, s1
adcx s6, sC         | s2" s7+s9' sC sB [i+5]
movq sB, rp[i+5]    | s2" s7+s9' sC [i+6]
adox s1, s2         | s2 s7+s9' sC [i+6]
adcx s9, s7
movq sC, rp[i+6]
movq s7, rp[i+7]    | s2' [i+8]
adcx s1, s2         | s2 [i+8]
movq s2, rp[i+8]
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P
import gen_mul7_t03 as A
import gen_mul8_aligned as E
import gen_mul11_ryzen as L

g_iplus_minus_patt = re.compile(r'\bi([\+\-])\b([0-9]+)\b')
def evaluate_row(s, i, alignment):
    m = E.g_if_patt.match(s)
    if m:
        d = \
                {\
                    'tail_jump' : (i == 6) and (alignment != 0),
                    'tail_here' : (i == 6) and (alignment == 0),
                }
        s = P.evaluate_if(s, d, m.group(1), m.group(2))

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
    code += chew_code(g_mul_2, 2, alignment, p)
    code += chew_code(g_mul_3, 3, alignment, p)
    code += chew_code(g_mul_4, 4, alignment, p)
    code += chew_code(g_mul_5, 5, alignment, p)
    if alignment:
        fresh = chew_code(g_mul_6, 6, alignment, p)
        code += L.remove_after_jmp(fresh)
    else:
        code += chew_code(g_mul_6, 6, alignment, p)
        code += chew_code(g_mul_7, 7, alignment, p)
    return code

def do_it(o):
    code = alignment_code(8) + alignment_code(0)
    P.cook_asm(o, code, L.g_var_map, True)

if __name__ == '__main__':
    with open(sys.argv[1], 'wb') as g_out:
        do_it(g_out)
