'''
8x8 multiplication targeting Ryzen. 108 ticks 
'''

"""
      rdi -< rp
      rsi -< up
      rdx -< vp

rbp rbx r12 r13 r14 r15
wB  wA  w9  w8  w6  w5    -- saved

rax r8  r9  r10 r11 rcx rsi rdi rdx
w0  w1  w2  w3  w4  w7  up  rp  dd
"""

g_mul_01='''
vzeroupper                       | removing vzeroupper slows code down by 4 ticks
movq dd, w0
movq w0, vp
movq (dd), dd                    | ready v0
!save w5
movdqu 8(w0), t0                 | t0 = v[1..2]
mulx (up), w1, w2                | w2 w1
mulx 8(up), w3, w4               | w4 w2+w3 w1
!save w6
mulx 16(up), w5, w6              | w6 w4+w5 w2+w3 w1
!save w8
mulx 24(up), w7, w8              | w8 w6+w7 w4+w5 w2+w3 w1
!save w9
!save wA
mulx 32(up), w0, w9              | w9 w0+w8 w6+w7 w4+w5 w2+w3 w1
!save wB
mulx 40(up), wA, wB              | wB w9+wA w0+w8 w6+w7 w4+w5 w2+w3 w1
addq w3, w2                      | wB w9+wA w0+w8 w6+w7 w4+w5' w2 w1
movq w1, (rp)                    | wB w9+wA w0+w8 w6+w7 w4+w5' w2 --
movq w2, 8(rp)                   | wB w9+wA w0+w8 w6+w7 w4+w5' .. --
movq t0, w2                      | w2=v[1]
mulx 48(up), w1, w3              | w3 w1+wB w9+wA w0+w8 w6+w7 w4+w5' .. -- w2=v[1]
adcq w5, w4                      | w3 w1+wB w9+wA w0+w8 w6+w7' w4 .. -- w2=v[1]
mulx 56(up), dd, w5              | w5 dd+w3 w1+wB w9+wA w0+w8 w6+w7' w4 .. -- w2=v[1]
adcq w7, w6                      | w5 dd+w3 w1+wB w9+wA w0+w8' w6 w4 .. -- w2=v[1]
movq w4, 16(rp)                  | w5 dd+w3 w1+wB w9+wA w0+w8' w6 .. .. -- w2=v[1]
xchg w2, dd                      | w5 dd+w3 w1+wB w9+wA w0+w8' w6 .. .. --
mulx (up), w4, w7                | w5 w2+w3 w1+wB w9+wA w0+w8' w6 w7: w4: --
adcq w8, w0                      | w5 w2+w3 w1+wB w9+wA' w0 w6 w7: w4: --
adcq wA, w9                      | w5 w2+w3 w1+wB' w9 w0 w6 w7: w4: --
mulx 8(up), w8, wA               | w5 w2+w3 w1+wB' w9 w0 w6+wA w7+w8: w4: --
adcq wB, w1                      | w5 w2+w3' w1 w9 w0 w6+wA w7+w8: w4: --
adcq w3, w2                      | w5' w2 w1 w9 w0 w6+wA w7+w8: w4: --
mulx 16(up), w3, wB              | w5' w2 w1 w9 w0+wB w6+wA+w3 w7+w8: w4: --
adcq $0, w5                      | w5 w2 w1 w9 w0+wB w6+wA+w3 w7+w8: w4: --
adcx 8(rp), w4                   | w5 w2 w1 w9 w0+wB w6+wA+w3 w7+w8:' w4 --
movq w4, 8(rp)                   | w5 w2 w1 w9 w0+wB w6+wA+w3 w7+w8:' {2}
adox 16(rp), w7                  | w5 w2 w1 w9 w0+wB w6+wA+w3" w7+w8' {2}
adox wA, w6                      | w5 w2 w1 w9 w0+wB" w6+w3 w7+w8' {2}
adcx w8, w7                      | w5 w2 w1 w9 w0+wB" w6+w3' w7 {2}
movq w7, 16(rp)                  | w5 w2 w1 w9 w0+wB" w6+w3' .. {2}
mulx 24(up), w7, w8              | w5 w2 w1 w9+w8 w0+wB+w7" w6+w3' .. {2}
mulx 32(up), w4, wA              | w5 w2 w1+wA w9+w8+w4 w0+wB+w7" w6+w3' .. {2}
adox wB, w0                      | w5 w2 w1+wA w9+w8+w4" w0+w7 w6+w3' .. {2}
adcx w6, w3                      | w5 w2 w1+wA w9+w8+w4" w0+w7' w3 .. {2}
movq w3, 24(rp)                  | w5 w2 w1+wA w9+w8+w4" w0+w7' [2] {2}
pextrq $0x1, t0, w3
mulx 40(up), w6, wB            | w5 w2+wB w1+wA+w6 w9+w8+w4" w0+w7' [2] {2} w3=v[2]
adox w9, w8                    | w5 w2+wB w1+wA+w6" w8+w4 w0+w7' [2] {2} w3=v[2]
adcx w7, w0                    | w5 w2+wB w1+wA+w6" w8+w4' w0 [2] {2} w3=v[2]
mulx 48(up), w7, w9            | w5+w9 w2+wB+w7 w1+wA+w6" w8+w4' w0 [2] {2} w3=v[2]
adox wA, w1                    | w5+w9 w2+wB+w7" w1+w6 w8+w4' w0 [2] {2} w3=v[2]
mulx 56(up), wA, dd            | dd w5+w9+wA w2+wB+w7" w1+w6 w8+w4' w0 [2] {2} w3=v[2]
xchg dd, w3                    | w3 w5+w9+wA w2+wB+w7" w1+w6 w8+w4' w0 [2] {2}
adcx w4, w8                    | w3 w5+w9+wA w2+wB+w7" w1+w6' w8 w0 [2] {2}
adox wB, w2
'''

"""
i>=2
multiplied by v[0], .. v[i-1]
data lies like that: s3 s5+s9+sA" s2+s7 s1+s6' s8 s0 [2] {i} dd=v[i]
"""

g_muladd_2 = '''
                         | s3 s5+s9+sA" s2+s7 s1+s6' s8 s0 [2] {i}
mulx (up), s4, sB        | s3 s5+s9+sA" s2+s7 s1+s6' s8 s0 sB: s4: {i}
adcx s6, s1              | s3 s5+s9+sA" s2+s7' s1 s8 s0 sB: s4: {i}
adox s9, s5              | s3" s5+sA s2+s7' s1 s8 s0 sB: s4: {i}
mulx 8(up), s6, s9       | s3" s5+sA s2+s7' s1 s8 s0+s9 sB+s6: s4: {i}
adcx s7,s2               | s3" s5+sA' s2 s1 s8 s0+s9 sB+s6: s4: {i}
movq $0, s7
adox s7, s3              | s3 s5+sA' s2 s1 s8 s0+s9 sB+s6: s4: {i} s7=0
adcx sA, s5              | s3' s5 s2 s1 s8 s0+s9 sB+s6: s4: {i} s7=0
movq s5, t0              | s3' t0 s2 s1 s8 s0+s9 sB+s6: s4: {i} s7=0
mulx 16(up), s5, sA      | s3' t0 s2 s1 s8+sA s0+s9+s5 sB+s6: s4: {i} s7=0
adox i(rp), s4           | s3' t0 s2 s1 s8+sA s0+s9+s5 sB+s6:" s4 {i} s7=0
movq s4, i(rp)           | s3' t0 s2 s1 s8+sA s0+s9+s5 sB+s6:" {i+1} s7=0
adcx s7, s3              | s3 t0 s2 s1 s8+sA s0+s9+s5 sB+s6:" {i+1} s7=0
mulx 24(up), s4, s7      | s3 t0 s2 s1+s7 s8+sA+s4 s0+s9+s5 sB+s6:" {i+1}
adox sB, s6              | s3 t0 s2 s1+s7 s8+sA+s4 s0+s9+s5" s6: {i+1}
adox s9, s0              | s3 t0 s2 s1+s7 s8+sA+s4" s0+s5 s6: {i+1}
movq vp, s9
adcx i+1(rp), s6     | s3 t0 s2 s1+s7 s8+sA+s4" s0+s5' s6 {i+1} s9=vp
movq s6, i+1(rp)     | s3 t0 s2 s1+s7 s8+sA+s4" s0+s5' .. {i+1} s9=vp
mulx 32(up), s6, sB  | s3 t0 s2+sB s1+s7+s6 s8+sA+s4" s0+s5' .. {i+1} s9=vp
adox sA, s8          | s3 t0 s2+sB s1+s7+s6" s8+s4 s0+s5' .. {i+1} s9=vp
movq t0, sA          | s3 sA s2+sB s1+s7+s6" s8+s4 s0+s5' .. {i+1} s9=vp
adcx s5, s0          | s3 sA s2+sB s1+s7+s6" s8+s4' s0 .. {i+1} s9=vp
movq s0, i+2(rp)     | s3 sA s2+sB s1+s7+s6" s8+s4' [2] {i+1} s9=vp
mulx 40(up), s0, s5  | s3 sA+s5 s2+sB+s0 s1+s7+s6" s8+s4' [2] {i+1} s9=vp
adox s7, s1          | s3 sA+s5 s2+sB+s0" s1+s6 s8+s4' [2] {i+1} s9=vp
movdqu i+1(s9), t0   | t0=v[i+1..i+2], latency 4
mulx 48(up), s7, s9  | s3+s9 sA+s5+s7 s2+sB+s0" s1+s6 s8+s4' [2] {i+1}
adcx s8, s4          | s3+s9 sA+s5+s7 s2+sB+s0" s1+s6' s4 [2] {i+1}
movq s4, i+3(rp)     | s3+s9 sA+s5+s7 s2+sB+s0" s1+s6' [3] {i+1}
mulx 56(up), s4, s8  | s8 s3+s9+s4 sA+s5+s7 s2+sB+s0" s1+s6' [3] {i+1}
adox sB, s2          | s8 s3+s9+s4 sA+s5+s7" s2+s0 s1+s6' [3] {i+1}
adcx s6, s1          | s8 s3+s9+s4 sA+s5+s7" s2+s0' s1 [3] {i+1}
adox sA, s5          | s8 s3+s9+s4" s5+s7 s2+s0' s1 [3] {i+1}
adcx s2, s0          | s8 s3+s9+s4" s5+s7' s0 s1 [3] {i+1}
movq t0, dd          | latency 3
adox s9, s3          | s8" s3+s4 s5+s7' s0 s1 [3] {i+1}
adcx s7, s5          | s8" s3+s4' s5 s0 s1 [3] {i+1}
movq $0, s2          | s8" s3+s4' s5 s0 s1 [3] {i+1} dd=v[i+1] s2=0
adox s2, s8          | s8 s3+s4' s5 s0 s1 [3] {i+1} dd=v[i+1] s2=0
adcx s4, s3          | s8' s3 s5 s0 s1 [3] {i+1} dd=v[i+1] s2=0
'''

'''
i >= 3
multiplied by v[0], .. v[i-1]
data lies like that: s8' s3 s5 s0 s1 [3] {i} dd=v[i+1]  s2=0  t0=v[i..i+1]
'''

g_muladd_3 = '''
                     | s8' s3 s5 s0 s1 [3] {i} dd=v[i+1]  s2=0  t0=v[i..i+1]
mulx (up), s4, s6    | s8' s3 s5 s0 s1 .. s6: s4: {i} s2=0  t0=v[i..i+1]
adcx s2, s8          | s8 s3 s5 s0 s1 .. s6: s4: {i} s2=0  t0=v[i..i+1]
mulx 8(up), s2, s7   | s8 s3 s5 s0 s1 s7: s6+s2: s4: {i} t0=v[i..i+1]
mulx 16(up), s9, sA  | s8 s3 s5 s0 s1+sA s7+s9: s6+s2: s4: {i} t0=v[i..i+1]
movq s8, t1          | t1 s3 s5 s0 s1+sA s7+s9: s6+s2: s4: {i} t0=v[i..i+1]
mulx 24(up), s8, sB  | t1 s3 s5 s0+sB s1+sA+s8 s7+s9: s6+s2: s4: {i} t0=v[i..i+1]
adox i(rp), s4       | t1 s3 s5 s0+sB s1+sA+s8 s7+s9: s6+s2:" s4 {i} t0=v[i..i+1]
movq s4, i(rp)       | t1 s3 s5 s0+sB s1+sA+s8 s7+s9: s6+s2:" {i+1} t0=v[i..i+1]
adox s6, s2          | t1 s3 s5 s0+sB s1+sA+s8 s7+s9:" s2: {i+1} t0=v[i..i+1]
mulx 32(up), s4, s6  | t1 s3 s5+s6 s0+sB+s4 s1+sA+s8 s7+s9:" s2: {i+1} t0=v[i..i+1]
adcx i+1(rp), s2     | t1 s3 s5+s6 s0+sB+s4 s1+sA+s8 s7+s9:"' s2 {i+1} t0=v[i..i+1]
movq s2, i+1(rp)     | t1 s3 s5+s6 s0+sB+s4 s1+sA+s8 s7+s9:"' .. {i+1} t0=v[i..i+1]
adox s9, s7          | t1 s3 s5+s6 s0+sB+s4 s1+sA+s8" s7:' .. {i+1} t0=v[i..i+1]
mulx 40(up), s2, s9  | t1 s3+s9 s5+s6+s2 s0+sB+s4 s1+sA+s8" s7:' .. {i+1} t0=v[i..i+1]
adcx i+2(rp), s7     | t1 s3+s9 s5+s6+s2 s0+sB+s4 s1+sA+s8"' s7 .. {i+1} t0=v[i..i+1]
movq s7, i+2(rp)     | t1 s3+s9 s5+s6+s2 s0+sB+s4 s1+sA+s8"' [2] {i+1} t0=v[i..i+1]
adox sA, s1          | t1 s3+s9 s5+s6+s2 s0+sB+s4" s1+s8' [2] {i+1} t0=v[i..i+1]
mulx 48(up), s7, sA  | t1+sA s3+s9+s7 s5+s6+s2 s0+sB+s4" s1+s8' [2] {i+1} t0=v[i..i+1]
adcx s8, s1          | t1+sA s3+s9+s7 s5+s6+s2 s0+sB+s4"' s1 [2] {i+1} t0=v[i..i+1]
movq t1, s8          | sA+s8 s3+s9+s7 s5+s6+s2 s0+sB+s4"' s1 [2] {i+1} t0=v[i..i+1]
movq s1, i+3(rp)     | sA+s8 s3+s9+s7 s5+s6+s2 s0+sB+s4"' [3] {i+1} t0=v[i..i+1]
adox sB, s0          | sA+s8 s3+s9+s7 s5+s6+s2" s0+s4' [3] {i+1} t0=v[i..i+1]
mulx 56(up), s1, sB  | sB sA+s8+s1 s3+s9+s7 s5+s6+s2" s0+s4' [3] {i+1} t0=v[i..i+1]
pextrq $0x1, t0, dd  | dd=v[i+1], latency 3
adcx s4, s0          | sB sA+s8+s1 s3+s9+s7 s5+s6+s2"' s0 [3] {i+1} t0=v[i..i+1]
adox s6, s5          | sB sA+s8+s1 s3+s9+s7" s5+s2' s0 [3] {i+1} t0=v[i..i+1]
movq $0, s4          | sB sA+s8+s1 s3+s9+s7" s5+s2' s0 [3] {i+1} t0=v[i..i+1]  s4=0
adcx s5, s2          | sB sA+s8+s1 s3+s9+s7"' s2 s0 [3] {i+1} t0=v[i..i+1]  s4=0
adox s9, s3          | sB sA+s8+s1" s3+s7' s2 s0 [3] {i+1} t0=v[i..i+1]  s4=0
adcx s7, s3          | sB sA+s8+s1"' s3 s2 s0 [3] {i+1} t0=v[i..i+1]  s4=0
adox sA, s8          | sB" s8+s1' s3 s2 s0 [3] {i+1} t0=v[i..i+1]  s4=0
adcx s8, s1          | sB"' s1 s3 s2 s0 [3] {i+1} t0=v[i..i+1]  s4=0
'''

'''
i >= 4
multiplied by v[0], .. v[i-1]
data lies like that: sB"' s1 s3 s2 s0 [3] {i} dd=v[i]  s4=0
'''

g_muladd_4 = '''
                     | sB"' s1 s3 s2 s0 [3] {i} dd=v[i]  s4=0
movq vp, s5          | sB"' s1 s3 s2 s0 [3] {i} s4=0  s5=vp
mulx (up), s6, s7    | sB"' s1 s3 s2 s0 .. s7: s6: {i} s4=0  s5=vp
adox s4, sB          | sB' s1 s3 s2 s0 .. s7: s6: {i} s4=0  s5=vp
mulx 8(up), s8, s9   | sB' s1 s3 s2 s0 s9: s7+s8: s6: {i} s4=0  s5=vp
adcx s4, sB          | sB s1 s3 s2 s0 s9: s7+s8: s6: {i} s4=0  s5=vp
mulx 16(up), s4, sA  | sB s1 s3 s2 s0+sA s9+s4: s7+s8: s6: {i} s5=vp
| 300 tacts slow-down vmovdqu i(s5), t0l   | t0l=v[i..i+3], latency 4
movdqu i+1(s5), t0   | t0=v[i+1..i+2]
adox i(rp), s6       | sB s1 s3 s2 s0+sA s9+s4: s7+s8:" s6 {i} s5=vp
movq s6, i(rp)       | sB s1 s3 s2 s0+sA s9+s4: s7+s8:" {i+1} s5=vp
vmovdqu i+2(s5), t2  | t2=v[i+2..i+3]
mulx 24(up), s5, s6  | sB s1 s3 s2+s6 s0+sA+s5 s9+s4: s7+s8:" {i+1}
adox s8, s7          | sB s1 s3 s2+s6 s0+sA+s5 s9+s4:" s7: {i+1}
movq sB, t1          | t1 s1 s3 s2+s6 s0+sA+s5 s9+s4:" s7: {i+1}
mulx 32(up), s8, sB  | t1 s1 s3+sB s2+s6+s8 s0+sA+s5 s9+s4:" s7: {i+1}
adcx i+1(rp), s7     | t1 s1 s3+sB s2+s6+s8 s0+sA+s5 s9+s4:"' s7 {i+1}
movq s7, i+1(rp)     | t1 s1 s3+sB s2+s6+s8 s0+sA+s5 s9+s4:"' .. {i+1}
adox s9, s4          | t1 s1 s3+sB s2+s6+s8 s0+sA+s5" s4:' .. {i+1}
mulx 40(up), s7, s9  | t1 s1+s9 s3+sB+s7 s2+s6+s8 s0+sA+s5" s4:' .. {i+1}
adcx i+2(rp), s4     | t1 s1+s9 s3+sB+s7 s2+s6+s8 s0+sA+s5"' s4 .. {i+1}
movq s4, i+2(rp)     | t1 s1+s9 s3+sB+s7 s2+s6+s8 s0+sA+s5"' [2] {i+1}
movq t1, s4          | s4 s1+s9 s3+sB+s7 s2+s6+s8" s0+sA+s5"' [2] {i+1}
adox sA, s0          | s4 s1+s9 s3+sB+s7 s2+s6+s8" s0+s5' [2] {i+1}
adox s6, s2          | s4 s1+s9 s3+sB+s7" s2+s8 s0+s5' [2] {i+1}
mulx 48(up), s6, sA  | s4+sA s1+s9+s6 s3+sB+s7" s2+s8 s0+s5' [2] {i+1}
adcx s5, s0          | s4+sA s1+s9+s6 s3+sB+s7" s2+s8' s0 [2] {i+1}
movq t0, s5          | s4+sA s1+s9+s6 s3+sB+s7" s2+s8' s0 [2] {i+1} s5=v[i+1]
adox sB, s3          | s4+sA s1+s9+s6" s3+s7 s2+s8' s0 [2] {i+1} s5=v[i+1]
mulx 56(up), sB, dd  | dd s4+sA+sB s1+s9+s6" s3+s7 s2+s8' s0 [2] {i+1} s5=v[i+1]
adcx s8, s2          | dd s4+sA+sB s1+s9+s6" s3+s7' s2 s0 [2] {i+1} s5=v[i+1]
adox s9, s1          | dd s4+sA+sB" s1+s6 s3+s7' s2 s0 [2] {i+1} s5=v[i+1]
adcx s7, s3          | dd s4+sA+sB" s1+s6' s3 s2 s0 [2] {i+1} s5=v[i+1]
movq $0, s7          | dd s4+sA+sB" s1+s6' s3 s2 s0 [2] {i+1} s5=v[i+1]  s7=0
                     | possibly lost 1 tick on sA
adox sA, s4          | dd" s4+sB s1+s6' s3 s2 s0 [2] {i+1} s5=v[i+1]  s7=0
adcx s6, s1          | dd" s4+sB' s1 s3 s2 s0 [2] {i+1} s5=v[i+1]  s7=0
adox s7, dd          | dd s4+sB' s1 s3 s2 s0 [2] {i+1} s5=v[i+1]  s7=0
xchg dd, s5          | s5 s4+sB' s1 s3 s2 s0 [2] {i+1} s7=0
'''

'''
i = 5
multiplied by v[0], .. v[i-1]
data lies like that: s5 s4+sB' s1 s3 s2 s0 [2] {i} s7=0  t0=v[i..i+1]
                     t2=v[i+1..i+2]
'''

g_muladd_5 = '''
                 | s5 s4+sB' s1 s3 s2 s0 [2] {i} s7=0  t0=v[i+1..i+2]  t2=v[i+2..i+3]
mulx (up), s6, s8    | s5 s4+sB' s1 s3 s2 s0 s8: s6: {i} s7=0
adcx sB, s4          | s5' s4 s1 s3 s2 s0 s8: s6: {i} s7=0
mulx 8(up), s9, sA   | s5' s4 s1 s3 s2 s0+sA s8+s9: s6: {i} s7=0
adcx s7, s5          | s5 s4 s1 s3 s2 s0+sA s8+s9: s6: {i} s7=0
mulx 16(up), s7, sB  | s5 s4 s1 s3 s2+sB s0+sA+s7 s8+s9: s6: {i}
adox i(rp), s6       | s5 s4 s1 s3 s2+sB s0+sA+s7 s8+s9:" s6 {i}
movq s5, t1          | t1 s4 s1 s3 s2+sB s0+sA+s7 s8+s9:" s6 {i}
movq s6, i(rp)       | t1 s4 s1 s3 s2+sB s0+sA+s7 s8+s9:" {i+1}
mulx 24(up), s5, s6  | t1 s4 s1 s3+s6 s2+sB+s5 s0+sA+s7 s8+s9:" {i+1}
adox i+1(rp), s8     | t1 s4 s1 s3+s6 s2+sB+s5 s0+sA+s7" s8+s9 {i+1}
adox sA, s0          | t1 s4 s1 s3+s6 s2+sB+s5" s0+s7 s8+s9 {i+1}
adcx s9, s8          | t1 s4 s1 s3+s6 s2+sB+s5" s0+s7' s8 {i+1}
movq s8, i+1(rp)     | t1 s4 s1 s3+s6 s2+sB+s5" s0+s7' .. {i+1}
mulx 32(up), s9, sA  | t1 s4 s1+sA s3+s6+s9 s2+sB+s5" s0+s7' .. {i+1}
adox sB, s2          | t1 s4 s1+sA s3+s6+s9" s2+s5 s0+s7' .. {i+1}
movq t1, sB          | sB s4 s1+sA s3+s6+s9" s2+s5 s0+s7' .. {i+1}
adcx s7, s0          | sB s4 s1+sA s3+s6+s9" s2+s5' s0 .. {i+1}
movq s0, i+2(rp)     | sB s4 s1+sA s3+s6+s9" s2+s5' [2] {i+1}
movq t2, s0          | sB s4 s1+sA s3+s6+s9" s2+s5' [2] {i+1} s0=v[i+1]
mulx 40(up), s7, s8  | sB s4+s8 s1+sA+s7 s3+s6+s9" s2+s5' [2] {i+1} s0=v[i+1]
adox s6, s3          | sB s4+s8 s1+sA+s7" s3+s9 s2+s5' [2] {i+1} s0=v[i+1]
adcx s5, s2          | sB s4+s8 s1+sA+s7" s3+s9' s2 [2] {i+1} s0=v[i+1]
mulx 48(up), s5, s6  | sB+s6 s4+s8+s5 s1+sA+s7" s3+s9' s2 [2] {i+1} s0=v[i+1]
adox sA, s1          | sB+s6 s4+s8+s5" s1+s7 s3+s9' s2 [2] {i+1} s0=v[i+1]
mulx 56(up), sA, dd  | dd sB+s6+sA s4+s8+s5" s1+s7 s3+s9' s2 [2] {i+1} s0=v[i+1]
adcx s9, s3          | dd sB+s6+sA s4+s8+s5" s1+s7' s3 s2 [2] {i+1} s0=v[i+1]
xchg s0, dd          | s0 sB+s6+sA s4+s8+s5" s1+s7' s3 s2 [2] {i+1}
adox s8, s4          | s0 sB+s6+sA" s4+s5 s1+s7' s3 s2 [2] {i+1}
'''

'''
i = 6
multiplied by v[0], .. v[i-1]
data lies like that: s0 sB+s6+sA" s4+s5 s1+s7' s3 s2 [2] {i} t2=[.. v[7]]
'''

g_muladd_6 = '''
                     | s0 sB+s6+sA" s4+s5 s1+s7' s3 s2 [2] {i} t2=[.. v[7]]
mulx (up), s8, s9    | s0 sB+s6+sA" s4+s5 s1+s7' s3 s2 s9: s8: {i} t2=[.. v[7]]
adcx s7, s1          | s0 sB+s6+sA" s4+s5' s1 s3 s2 s9: s8: {i} t2=[.. v[7]]
adox sB, s6          | s0" s6+sA s4+s5' s1 s3 s2 s9: s8: {i} t2=[.. v[7]]
mulx 8(up), s7, sB   | s0" s6+sA s4+s5' s1 s3 s2+sB s9+s7: s8: {i} t2=[.. v[7]]
adcx s5, s4          | s0" s6+sA' s4 s1 s3 s2+sB s9+s7: s8: {i} t2=[.. v[7]]
movq $0, s5          | s0" s6+sA' s4 s1 s3 s2+sB s9+s7: s8: {i} t2=[.. v[7]] s5=0
adox s5, s0          | s0 s6+sA' s4 s1 s3 s2+sB s9+s7: s8: {i} t2=[.. v[7]] s5=0
adcx sA, s6          | s0' s6 s4 s1 s3 s2+sB s9+s7: s8: {i} t2=[.. v[7]] s5=0
mulx 16(up), s5, sA  | s0' s6 s4 s1 s3+sA s2+sB+s5 s9+s7: s8: {i} t2=[.. v[7]]
adox i(rp), s8       | s0' s6 s4 s1 s3+sA s2+sB+s5 s9+s7:" s8 {i} t2=[.. v[7]]
movq s8, i(rp)       | s0' s6 s4 s1 s3+sA s2+sB+s5 s9+s7:" {i+1} t2=[.. v[7]]
movq $0, s8          | s0' s6 s4 s1 s3+sA s2+sB+s5 s9+s7:" {i+1} t2=[.. v[7]]
adcx s8, s0          | s0 s6 s4 s1 s3+sA s2+sB+s5 s9+s7:" {i+1} t2=[.. v[7]]
adox s9, s7          | s0 s6 s4 s1 s3+sA s2+sB+s5" s7: {i+1} t2=[.. v[7]]
mulx 24(up), s8, s9  | s0 s6 s4 s1+s9 s3+sA+s8 s2+sB+s5" s7: {i+1} t2=[.. v[7]]
adox sB, s2          | s0 s6 s4 s1+s9 s3+sA+s8" s2+s5 s7: {i+1} t2=[.. v[7]]
adcx i+1(rp), s7
movq s7, i+1(rp)     | s0 s6 s4 s1+s9 s3+sA+s8" s2+s5' .. {i+1} t2=[.. v[7]]
mulx 32(up), s7, sB  | s0 s6 s4+sB s1+s9+s7 s3+sA+s8" s2+s5' .. {i+1} t2=[.. v[7]]
adox sA, s3          | s0 s6 s4+sB s1+s9+s7" s3+s8 s2+s5' .. {i+1} t2=[.. v[7]]
pextrq $0x1, t2, sA  | s0 s6 s4+sB s1+s9+s7" s3+s8 s2+s5' .. {i+1} sA=v[7]
adcx s5, s2          | s0 s6 s4+sB s1+s9+s7" s3+s8' s2 .. {i+1} sA=v[7]
movq s2, i+2(rp)     | s0 s6 s4+sB s1+s9+s7" s3+s8' [2] {i+1} sA=v[7]
mulx 40(up), s2, s5  | s0 s6+s5 s4+sB+s2 s1+s9+s7" s3+s8' [2] {i+1} sA=v[7]
adox s9, s1          | s0 s6+s5 s4+sB+s2" s1+s7 s3+s8' [2] {i+1} sA=v[7]
adcx s8, s3          | s0 s6+s5 s4+sB+s2" s1+s7' s3 [2] {i+1} sA=v[7]
mulx 48(up), s8, s9  | s0+s9 s6+s5+s8 s4+sB+s2" s1+s7' s3 [2] {i+1} sA=v[7]
adox sB, s4          | s0+s9 s6+s5+s8" s4+s2 s1+s7' s3 [2] {i+1} sA=v[7]
mulx 56(up), sB, dd  | dd s0+s9+sB s6+s5+s8" s4+s2 s1+s7' s3 [2] {i+1} sA=v[7]
adcx s7, s1          | dd s0+s9+sB s6+s5+s8" s4+s2' s1 s3 [2] {i+1} sA=v[7]
adox s6, s5          | dd s0+s9+sB" s5+s8 s4+s2' s1 s3 [2] {i+1} sA=v[7]
xchg dd, sA          | sA s0+s9+sB" s5+s8 s4+s2' s1 s3 [2] {i+1}
'''

'''
i = 7
multiplied by v[0], .. v[i-1]
data lies like that: sA s0+s9+sB" s5+s8 s4+s2' s1 s3 [2] {i}
'''

g_muladd_7 = '''
                     | sA s0+s9+sB" s5+s8 s4+s2' s1 s3 [2] {i}
mulx (up), s6, s7    | sA s0+s9+sB" s5+s8 s4+s2' s1 s3 s7: s6: {i}
adcx s4, s2          | sA s0+s9+sB" s5+s8' s2 s1 s3 s7: s6: {i}
adox s9, s0          | sA" s0+sB s5+s8' s2 s1 s3 s7: s6: {i}
mulx 8(up), s4, s9   | sA" s0+sB s5+s8' s2 s1 s3+s9 s7+s4: s6: {i}
adcx s8, s5          | sA" s0+sB' s5 s2 s1 s3+s9 s7+s4: s6: {i}
movq $0, s8          | sA" s0+sB' s5 s2 s1 s3+s9 s7+s4: s6: {i}
adox s8, sA          | sA s0+sB' s5 s2 s1 s3+s9 s7+s4: s6: {i}
adcx sB, s0          | sA' s0 s5 s2 s1 s3+s9 s7+s4: s6: {i}
mulx 16(up), s8, sB  | sA' s0 s5 s2 s1+sB s3+s9+s8 s7+s4: s6: {i}
adox i(rp), s6       | sA' s0 s5 s2 s1+sB s3+s9+s8 s7+s4:" s6 {i}
movq s6, i(rp)       | sA' s0 s5 s2 s1+sB s3+s9+s8 s7+s4:" {i+1}
movq $0, s6
adcx s6, sA          | sA s0 s5 s2 s1+sB s3+s9+s8 s7+s4:" {i+1}
adox i+1(rp), s7     | sA s0 s5 s2 s1+sB s3+s9+s8" s7+s4 {i+1}
adox s9, s3          | sA s0 s5 s2 s1+sB" s3+s8 s7+s4 {i+1}
mulx 24(up), s6, s9  | sA s0 s5 s2+s9 s1+sB+s6" s3+s8 s7+s4 {i+1}
adcx s7, s4          | sA s0 s5 s2+s9 s1+sB+s6" s3+s8' s7 {i+1}
movq s4, i+1(rp)     | sA s0 s5 s2+s9 s1+sB+s6" s3+s8' {i+2}
mulx 32(up), s4, s7  | sA s0 s5+s7 s2+s9+s4 s1+sB+s6" s3+s8' {i+2}
adox sB, s1          | sA s0 s5+s7 s2+s9+s4" s1+s6 s3+s8' {i+2}
adcx s8, s3          | sA s0 s5+s7 s2+s9+s4" s1+s6' s3 {i+2}
movq s3, i+2(rp)     | sA s0 s5+s7 s2+s9+s4" s1+s6' {i+3}
mulx 40(up), s3, s8  | sA s0+s8 s5+s7+s3 s2+s9+s4" s1+s6' {i+3}
adox s9, s2          | sA s0+s8 s5+s7+s3" s2+s4 s1+s6' {i+3}
mulx 48(up), s9, sB  | sA+sB s0+s8+s9 s5+s7+s3" s2+s4 s1+s6' {i+3}
adcx s6, s1          | sA+sB s0+s8+s9 s5+s7+s3" s2+s4' s1 {i+3}
mulx 56(up), s6, dd  | dd sA+sB+s6 s0+s8+s9 s5+s7+s3" s2+s4' s1 {i+3}
adox s7, s5          | dd sA+sB+s6 s0+s8+s9" s5+s3 s2+s4' s1 {i+3}
movq s1, i+3(rp)     | dd sA+sB+s6 s0+s8+s9" s5+s3 s2+s4' {i+4}
adcx s4, s2          | dd sA+sB+s6 s0+s8+s9" s5+s3' s2 {i+4}
adox s8, s0          | dd sA+sB+s6" s0+s9 s5+s3' s2 {i+4}
movq s2, i+4(rp)     | dd sA+sB+s6" s0+s9 s5+s3' {i+5}
movq sA, s2          | dd s2+sB+s6" s0+s9 s5+s3' {i+5}
adcx s5, s3          | dd s2+sB+s6" s0+s9' s3 {i+5}
movq s3, i+5(rp)     | dd s2+sB+s6" s0+s9' {i+6}
movq $0, s3
adox sB, s2          | dd" s2+s6 s0+s9' {i+6}
adcx s9, s0          | dd" s2+s6' s0 {i+6}
adox s3, dd          | dd s2+s6' s0 {i+6}
movq s0, i+6(rp)     | dd s2+s6' {i+7}
adcx s6, s2          | dd' s2 {i+7}
movq s2, i+7(rp)     | dd' {i+8}
adcx s3, dd
movq dd, i+8(rp)
'''

g_muladd_3_unused='''
                              | s7' s3+s9 s5+sA" s0 s1 s4+s8 .. .. {i} s2=0
mulx (up), s6, sB             | s7' s3+s9 s5+sA" s0 s1 s4+s8 sB: s6: {i} s2=0
adox sA, s5                   | s7' s3+s9" s5 s0 s1 s4+s8 sB: s6: {i} s2=0
adcx s2, s7                   | s7 s3+s9" s5 s0 s1 s4+s8 sB: s6: {i} s2=0
adox s9, s3                   | s7" s3 s5 s0 s1 s4+s8 sB: s6: {i} s2=0
mulx 8(up), s9, sA            | s7" s3 s5 s0 s1 s4+s8+sA sB+s9: s6: {i} s2=0
adox s2, s7                   | s7 s3 s5 s0 s1 s4+s8+sA sB+s9: s6: {i} s2=0
adcx s8, s4                   | s7 s3 s5 s0 s1' s4+sA sB+s9: s6: {i} s2=0
mulx 16(up), s2, s8           | s7 s3 s5 s0 s1+s8' s4+sA+s2 sB+s9: s6: {i}
movq s7, t0                   | t0 s3 s5 s0 s1+s8' s4+sA+s2 sB+s9: s6: {i}
movq i(rp), s7                | t0 s3 s5 s0 s1+s8' s4+sA+s2 sB+s9: s6+s7 {i}
adox s7, s6                   | t0 s3 s5 s0 s1+s8' s4+sA+s2 sB+s9": s6 {i}
movq i+1(rp), s7              | t0 s3 s5 s0 s1+s8' s4+sA+s2 sB+s7+s9" s6 {i}
adox sB, s7                   | t0 s3 s5 s0 s1+s8' s4+sA+s2" s7+s9 s6 {i}
movq s6, i(rp)                | t0 s3 s5 s0 s1+s8' s4+sA+s2" s7+s9 {i+1}
movq $0, sB                   | t0 s3 s5 s0 s1+s8' s4+sA+s2" s7+s9 {i+1} sB=0
movq s3, t1                   | t0 t1 s5 s0 s1+s8' s4+sA+s2" s7+s9 {i+1} sB=0
mulx 24(up), s3, s6           | t0 t1 s5 s0+s6 s1+s8+s3' s4+sA+s2" s7+s9 {i+1} sB=0
adox sA, s4                   | t0 t1 s5 s0+s6 s1+s8+s3'" s4+s2 s7+s9 {i+1} sB=0
adcx s8, s1                   | t0 t1 s5 s0+s6' s1+s3" s4+s2 s7+s9 {i+1} sB=0
mulx 32(up), s8, sA           | t0 t1 s5+sA s0+s6+s8' s1+s3" s4+s2 s7+s9 {i+1} sB=0
adcx sB, sB                   | t0 t1 s5+sA s0+s6+s8+sB s1+s3" s4+s2 s7+s9 {i+1} sB=0
adcx s9, s7                   | t0 t1 s5+sA s0+s6+s8+sB s1+s3" s4+s2' s7 {i+1}
movq s7, i+1(rp)              | t0 t1 s5+sA s0+s6+s8+sB s1+s3" s4+s2' .. {i+1}
mulx 40(up), s7, s9           | t0 t1+s9 s5+sA+s7 s0+s6+s8+sB s1+s3" s4+s2' .. {i+1}
adcx s4, s2                   | t0 t1+s9 s5+sA+s7 s0+s6+s8+sB s1+s3"' s2 .. {i+1}
movq s2, i+2(rp)              | t0 t1+s9 s5+sA+s7 s0+s6+s8+sB s1+s3"' [2] {i+1}
movq $0, s2                   | t0 t1+s9 s5+sA+s7 s0+s6+s8+sB s1+s3"' [2] {i+1} s2=0
adox s3, s1                   | t0 t1+s9 s5+sA+s7 s0+s6+s8+sB" s1' [2] {i+1} s2=0
adox s6, s0                   | t0 t1+s9 s5+sA+s7" s0+s8+sB s1' [2] {i+1} s2=0
ulx 48(up), s3, s6           | t0+s6 t1+s9+s3 s5+sA+s7" s0+s8+sB s1' [2] {i+1} s2=0
adcx s2, s1                   | t0+s6 t1+s9+s3 s5+sA+s7" s0+s8+sB' s1 [2] {i+1} s2=0
mulx 56(up), s2, s4           | s4 t0+s6+s2 t1+s9+s3 s5+sA+s7" s0+s8+sB' s1 [2] {i+1}
movq rz, dd
movq s1, i+3(rp)              | s4 t0+s6+s2 t1+s9+s3 s5+sA+s7" s0+s8+sB' [3] {i+1}
movq $0, s1
adcx s8, s0                   | s4 t0+s6+s2 t1+s9+s3 s5+sA+s7"' s0+sB [3] {i+1} s1=0
movq t1, s8                   | s4 t0+s6+s2 s9+s3+s8 s5+sA+s7"' s0+sB [3] {i+1} s1=0
adox sA, s5                   | s4 t0+s6+s2 s9+s3+s8" s5+s7' s0+sB [3] {i+1} s1=0
movq t0, sA                   | s4 s6+s2+sA s9+s3+s8" s5+s7' s0+sB [3] {i+1} s1=0
movq i+1(dd), dd
adcx s7, s5                   | s4 s6+s2+sA s9+s3+s8"' s5 s0+sB [3] {i+1} s1=0
adox s9, s3                   | s4 s6+s2+sA" s3+s8' s5 s0+sB [3] {i+1} s1=0
adox s6, s2                   | s4" s2+sA s3+s8' s5 s0+sB [3] {i+1} s1=0
adcx s8, s3                   | s4" s2+sA' s3 s5 s0+sB [3] {i+1} s1=0
adox s1, s4                   | s4 s2+sA' s3 s5 s0+sB [3] {i+1} s1=0
adcx sA, s2                   | s4' s2 s3 s5 s0+sB [3] {i+1} s1=0
'''

"""
i >= 4
s2=0
dd=v[i]
multiplied by v[0], .. v[i-1]
data lies like that: s4' s2 s3 s5 s0+sB .. .. .. {i} s1=0
"""

g_muladd_4_unused = '''
mulx (up), s6, s7     | s4' s2 s3 s5 s0+sB .. s7: s6: {i} s1=0
adox sB, s0           | s4' s2 s3 s5" s0 .. s7: s6: {i} s1=0
adcx s1, s4           | s4 s2 s3 s5" s0 .. s7: s6: {i} s1=0
mulx 8(up), s8, sB    | s4 s2 s3 s5" s0 sB: s7+s8: s6: {i} s1=0
movq s4, i+3(rp)           | t0 s2 s3 s5" s0 sB: s7+s8: s6: {i} s1=0
movq i(rp), s4        | t0 s2 s3 s5" s0 sB: s7+s8: s4+s6 {i} s1=0
adcx s6, s4           | t0 s2 s3 s5" s0 sB: s7+s8': s4 {i} s1=0
adox s1, s1           | t0 s2 s3 s5+s1 s0 sB: s7+s8': s4 {i}
mulx 16(up), s6, s9   | t0 s2 s3 s5+s1 s0+s9 sB+s6: s7+s8': s4 {i}
movq i+1(rp), sA      | t0 s2 s3 s5+s1 s0+s9 sB+s6: s7+sA+s8' s4 {i}
adcx sA, s7           | t0 s2 s3 s5+s1 s0+s9 sB+s6': s7+s8 s4 {i}
movq s4, i(rp)        | t0 s2 s3 s5+s1 s0+s9 sB+s6': s7+s8 {i+1}
mulx 24(up), s4, sA   | t0 s2 s3 s5+s1+sA s0+s9+s4 sB+s6': s7+s8 {i+1}
adox s8, s7           | t0 s2 s3 s5+s1+sA s0+s9+s4 sB+s6'": s7 {i+1}
movq s7, i+1(rp)      | t0 s2 s3 s5+s1+sA s0+s9+s4 sB+s6'": .. {i+1}
movq i+2(rp), s7      | t0 s2 s3 s5+s1+sA s0+s9+s4 s7+sB+s6'" .. {i+1}
adcx sB, s7           | t0 s2 s3 s5+s1+sA s0+s9+s4' s7+s6" .. {i+1}
mulx 32(up), s8, sB   | t0 s2 s3+sB s5+s1+sA+s8 s0+s9+s4' s7+s6" .. {i+1}
adox s7, s6           | t0 s2 s3+sB s5+s1+sA+s8 s0+s9+s4'" s6 .. {i+1}
adcx s9, s0           | t0 s2 s3+sB s5+s1+sA+s8' s0+s4" s6 .. {i+1}
mulx 40(up), s7, s9   | t0 s2+s9 s3+sB+s7 s5+s1+sA+s8' s0+s4" s6 .. {i+1}
adox s4, s0           | t0 s2+s9 s3+sB+s7 s5+s1+sA+s8'" s0 s6 .. {i+1}
adcx s5, s1           | t0 s2+s9 s3+sB+s7' s1+sA+s8" s0 s6 .. {i+1}
mulx 48(up), s4, s5   | t0+s5 s2+s9+s4 s3+sB+s7' s1+sA+s8" s0 s6 .. {i+1}
movq s6, i+2(rp)      | t0+s5 s2+s9+s4 s3+sB+s7' s1+sA+s8" s0 [2] {i+1}
movq i+3(rp), s6      | s5+s6 s2+s9+s4 s3+sB+s7' s1+sA+s8" s0 [2] {i+1}
adox sA, s1           | s5+s6 s2+s9+s4 s3+sB+s7'" s1+s8 s0 [2] {i+1}
adcx sB, s3           | s5+s6 s2+s9+s4' s3+s7" s1+s8 s0 [2] {i+1}
mulx 56(up), sA, sB   | sB s5+s6+sA s2+s9+s4' s3+s7" s1+s8 s0 [2] {i+1}
movq rz, dd
movq s0, i+3(rp)      | sB s5+s6+sA s2+s9+s4' s3+s7" s1+s8 [3] {i+1}
movq $0, s0           | sB s5+s6+sA s2+s9+s4' s3+s7" s1+s8 [3] {i+1} s0=0
adox s7, s3           | sB s5+s6+sA s2+s9+s4'" s3 s1+s8 [3] {i+1} s0=0
adcx s9, s2           | sB s5+s6+sA' s2+s4" s3 s1+s8 [3] {i+1} s0=0
movq i+1(dd), dd
adox s4, s2           | sB s5+s6+sA'" s2 s3 s1+s8 [3] {i+1} s0=0
adcx s6, s5           | sB' s5+sA" s2 s3 s1+s8 [3] {i+1} s0=0
adox sA, s5           | sB'" s5 s2 s3 s1+s8 [3] {i+1} s0=0
adcx s0, sB           | sB" s5 s2 s3 s1+s8 [3] {i+1} s0=0
'''

"""
i >= 5
dd=v[i]
multiplied by v[0], .. v[i-1]
    old data:        s4' s2 s3 s5 s0+sB [3] {i} s1=0
data lies like that: sB" s5 s2 s3 s1+s8 [3] {i} s0=0
"""

#         0 1 2 3 4 5 6 7 8 9 A B
g_perm = '1 0 5 2 B 3 6 7 4 9 A 8'

g_tail = '''
                      | sB' s5 s2 s3 s1+s8 [3] {i+1} s0=0 i=7
movq s0, dd
adcx sB, s0           | s0 s5 s2 s3 s1+s8 [3] {i+1} dd=0
movq s5, s4           | s0 s4 s2 s3 s1+s8 [3] {i+1} dd=0
adox s8, s1           | s0 s4 s2 s3" s1 [3] {i+1} dd=0
movq s1, i+4(rp)      | s0 s4 s2 s3" [4] {i+1} dd=0
adox dd, s3           | s0 s4 s2" s3 [4] {i+1} dd=0
movq s3, i+5(rp)      | s0 s4 s2" [5] {i+1} dd=0
adox dd, s2           | s0 s4" s2 [5] {i+1} dd=0
movq s2, i+6(rp)      | s0 s4" [6] {i+1} dd=0
adox dd, s4           | s0" s4 [6] {i+1} dd=0
movq s4, i+7(rp)      | s0" [7] {i+1} dd=0
adox s0, dd           | dd [7] {i+1} dd=0
movq dd, i+8(rp)
'''

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

g_v1_ofs = 4            # valid range: 4 - 8

def extract_code(i):
    if (i >= 1) and (i <= 7):
        return 'movq %s(rp), dd' % ((i - 1 + g_v1_ofs) * 8)
    return ''

def mul1_code(i, jj, p):
    rr = ['# mul_add %s' % i]
    for j in jj:
        rr.append(j)

    # apply permutation p, replace i(rp)
    for y in range(len(rr)):
        src = rr[y]
        for x in range(12):
            a = '%X' % x
            b = '%X' % p[x]
            src = re.sub(r'\bs%s\b' % a, 'w' + b, src)
        src += ' '
        for x in range(1, 9):
            ' replace i+x with 8*(i+x) '
            src = src.replace('i+%s(' % x, '%s(' % (8 * (i + x)))
        ' replace i with 8*i '
        src = src.replace('i(', '%s(' % (8 * i)) + ' '
        rr[y] = src.rstrip()

    return rr

def cook_asm(o, code):
    xmm_save = P.save_registers_in_xmm(code, 9)

    P.insert_restore(code, xmm_save)
    code = '\n'.join(code)
    for k,v in xmm_save.items():
        code = code.replace('!restore ' + k, 'movq %s, %s' % (v, k))

    m = 'rp,rdi up,rsi w7,rcx wB,rbp wA,rbx w9,r12 w8,r13 w6,r14 w5,r15 '
    m += 'w0,rax w1,r8 w2,r9 w3,r10 w4,r11 dd,rdx vp,ymm15 t0,xmm14 t0l,ymm14 '
    m += 't1,ymm13 t2,xmm12 t3,ymm11 t4,ymm10'
    r = {}
    for x in m.split(' '):
        y = x.split(',')
        r[y[0]] = '%' + y[1]
    code = P.replace_symbolic_vars_name(code, r)

    # replace ymm with xmm in all movq
    code = '\n'.join([replace_ymm_by_xmm(x) for x in code.split('\n')])

    comment = P.g_autogenerated_patt % os.path.basename(sys.argv[0])
    o.write(comment.replace('//', '#'))
    P.write_asm_procedure_header(o, 'mul8_zen')
    P.write_asm_inside(o, code + '\nretq')

g_ymm_to_xmm_patt = re.compile(r'movq .*%ymm.*')
def replace_ymm_by_xmm(s):
    if g_ymm_to_xmm_patt.match(s):
        return s.replace('ymm', 'xmm')
    return s

def replace_rz(s):
    return re.sub(r'\brz\b', '-8(%rsp)', s)

g_extract_v_patt = re.compile(r'extract v\[(.)\]')
def mul0_code(cc):
    for i in range(len(cc)):
        cc[i] = replace_rz(cc[i])
    return cc

def do_it(o):
    meat = mul0_code(P.cutoff_comments(g_mul_01))
    p = list(range(12))
    meat += mul1_code(2, P.cutoff_comments(g_muladd_2), p)
    meat += mul1_code(3, P.cutoff_comments(g_muladd_3), p)
    meat += mul1_code(4, P.cutoff_comments(g_muladd_4), p)
    meat += mul1_code(5, P.cutoff_comments(g_muladd_5), p)
    meat += mul1_code(6, P.cutoff_comments(g_muladd_6), p)
    meat += mul1_code(7, P.cutoff_comments(g_muladd_7), p)

    cook_asm(o, meat)

def swap_adox_adcx(dd):
    rr = []
    for d in dd:
        x = d.replace('adox', 'ADCX').replace('adcx', 'adox').\
                replace('ADCX', 'adcx')
        rr.append(x)
    return rr

with open(sys.argv[1], 'wb') as g_out:
    do_it(g_out)
