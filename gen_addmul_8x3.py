'''
void addmul_8x3(mp_ptr rp, mp_srcptr up, mp_srcptr vp);

Multiplies 8-limb number u by 3-limb number v; adds result to 14-limb number r;
 puts result in-place onto rp. Summation is done modulo 2**(14*64).

r' := r + u * v

Take 0: not caching u.
'''

"""
g_code_take1 uses 6 limbs of red zone: sc[x] = rsp[x-6]. mul_11() using this code
 spends 242 ticks on Broadwell and 228 on Ryzen.
"""

g_sc_shift = 6

g_code = '''
movq dd[1], t0
movq dd[2], t1
movq dd[0], dd
xor w0, w0
movq rp, t2
mulx up[0], w0, w1         | w1 w0
mulx up[1], w2, w3         | w3 w1+w2 w0
mulx up[2], w4, w5         | w5 w3+w4 w1+w2 w0
mulx up[3], w6, w7         | w7 w5+w6 w3+w4 w1+w2 w0
movq w0, sc[0]             | w7 w5+w6 w3+w4 w1+w2 [1]
mulx up[4], w0, w8         | w8 w7+w0 w5+w6 w3+w4 w1+w2 [1]
movq t0, w9                | w8 w7+w0 w5+w6 w3+w4 w1+w2 [1] w9=v[1]
adcx w2, w1                | w8 w7+w0 w5+w6 w3+w4' w1 [1] w9=v[1]
movq w1, sc[1]             | w8 w7+w0 w5+w6 w3+w4' [2] w9=v[1]
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

"""
Take 1: caching u. Take 1 is slower than take0 by 2 ticks on Ryzen.

code below uses 12 limbs of scratch
g_sc_shift = 12
"""

g_code_take1 = '''
xor w0, w0
!save w6
movq dd[1], t0
movq dd[2], t1
!save w7
movq dd[0], dd
movq rp, t2
movq up[0], rp
movq rp, sc[0]             | cache u[0]
!save w8
mulx rp, w0, w1            | w1 w0
movq up[1], rp
!save w9
movq rp, sc[1]             | cache u[1]
mulx rp, w2, w3            | w3 w1+w2 w0
!save wA
movq up[2], rp
movq rp, sc[2]             | cache u[2]
!save wB
movq t0, wB                | wB=v[1]
mulx rp, w4, w5            | w5 w3+w4 w1+w2 w0
movq up[3], rp
movq rp, sc[3]             | cache u[3]
mulx rp, w6, w7            | w7 w5+w6 w3+w4 w1+w2 w0
movq up[4], rp
movq rp, sc[4]             | cache u[4]
mulx rp, w8, w9            | w9 w7+w8 w5+w6 w3+w4 w1+w2 w0
adcx w2, w1                | w9 w7+w8 w5+w6 w3+w4' w1 w0
movq up[5], rp
movq rp, sc[5]             | cache u[5]
mulx rp, w2, wA            | wA w9+w2 w7+w8 w5+w6 w3+w4' w1 w0
adcx w4, w3                | wA w9+w2 w7+w8 w5+w6' w3 w1 w0
movq up[6], rp
movq rp, sc[6]             | cache u[6]
mulx rp, w4, rp            | rp wA+w4 w9+w2 w7+w8 w5+w6' w3 w1 w0
adcx w6, w5                | rp wA+w4 w9+w2 w7+w8' w5 w3 w1 w0
movq up[7], w6
movq w6, sc[7]             | cache u[7]
mulx w6, w6, up            | up rp+w6 wA+w4 w9+w2 w7+w8' w5 w3 w1 w0
movq wB, dd                | dd=v[1]
movq w0, sc[8]             | up rp+w6 wA+w4 w9+w2 w7+w8' w5 w3 w1 [1]
mulx sc[0], w0, wB         | up rp+w6 wA+w4 w9+w2 w7+w8' w5 w3+wB w1+w0 [1]
adcx w8, w7                | up rp+w6 wA+w4 w9+w2' w7 w5 w3+wB w1+w0 [1]
movq w3, sc[9]             | up rp+w6 wA+w4 w9+w2' w7 w5 {9}+wB w1+w0 [1]
mulx sc[1], w3, w8         | up rp+w6 wA+w4 w9+w2' w7 w5+w8 {9}+wB+w3 w1+w0 [1]
adcx w9, w2                | up rp+w6 wA+w4' w2 w7 w5+w8 {9}+wB+w3 w1+w0 [1]
movq w5, sc[10]            | up rp+w6 wA+w4' w2 w7 {A}+w8 {9}+wB+w3 w1+w0 [1]
mulx sc[2], w5, w9         | up rp+w6 wA+w4' w2 w7+w9 {A}+w8+w5 {9}+wB+w3 w1+w0 [1]
adcx wA, w4                | up rp+w6' w4 w2 w7+w9 {A}+w8+w5 {9}+wB+w3 w1+w0 [1]
movq w7, sc[11]            | up rp+w6' w4 w2 {B}+w9 {A}+w8+w5 {9}+wB+w3 w1+w0 [1]
mulx sc[3], w7, wA     | up rp+w6' w4 w2+wA {B}+w9+w7 {A}+w8+w5 {9}+wB+w3 w1+w0 [1]
adox w1, w0            | up rp+w6' w4 w2+wA {B}+w9+w7 {A}+w8+w5 {9}+wB+w3" w0 [1]
movq sc[9], w1         | up rp+w6' w4 w2+wA {B}+w9+w7 {A}+w8+w5 w1+wB+w3" w0 [1]
movq w0, sc[9]         | up rp+w6' w4 w2+wA {B}+w9+w7 {A}+w8+w5 w1+wB+w3" [2]
adcx w6, rp            | up' rp w4 w2+wA {B}+w9+w7 {A}+w8+w5 w1+wB+w3" [2]
mulx sc[4], w0, w6     | up' rp w4+w6 w2+wA+w0 {B}+w9+w7 {A}+w8+w5 w1+wB+w3" [2]
adox wB, w1            | up' rp w4+w6 w2+wA+w0 {B}+w9+w7 {A}+w8+w5" w1+w3 [2]
movq $0, wB
adcx wB, up            | up rp w4+w6 w2+wA+w0 {B}+w9+w7 {A}+w8+w5" w1+w3 [2]
movq sc[10], wB        | up rp w4+w6 w2+wA+w0 {B}+w9+w7 wB+w8+w5" w1+w3 [2]
adox wB, w8            | up rp w4+w6 w2+wA+w0 {B}+w9+w7" w8+w5 w1+w3 [2]
movq t1, wB            | up rp w4+w6 w2+wA+w0 {B}+w9+w7" w8+w5 w1+w3 [2] wB=d[2]
adcx w3, w1            | up rp w4+w6 w2+wA+w0 {B}+w9+w7" w8+w5' w1 [2] wB=d[2]
movq sc[11], w3        | up rp w4+w6 w2+wA+w0 w3+w9+w7" w8+w5' w1 [2] wB=d[2]
adox w9, w3            | up rp w4+w6 w2+wA+w0" w3+w7 w8+w5' w1 [2] wB=d[2]
movq w1, sc[10]        | up rp w4+w6 w2+wA+w0" w3+w7 w8+w5' [3] wB=d[2]
mulx sc[5], w1, w9     | up rp+w9 w4+w6+w1 w2+wA+w0" w3+w7 w8+w5' [3] wB=d[2]
adcx w8, w5            | up rp+w9 w4+w6+w1 w2+wA+w0" w3+w7' w5 [3] wB=d[2]
adox wA, w2            | up rp+w9 w4+w6+w1" w2+w0 w3+w7' w5 [3] wB=d[2]
mulx sc[6], w8, wA     | up+wA rp+w9+w8 w4+w6+w1" w2+w0 w3+w7' w5 [3] wB=d[2]
adcx w7, w3            | up+wA rp+w9+w8 w4+w6+w1" w2+w0' w3 w5 [3] wB=d[2]
adox w6, w4            | up+wA rp+w9+w8" w4+w1 w2+w0' w3 w5 [3] wB=d[2]
mulx sc[7], w6, w7     | w7 up+wA+w6 rp+w9+w8" w4+w1 w2+w0' w3 w5 [3] wB=d[2]
movq wB, dd
adcx w2, w0            | w7 up+wA+w6 rp+w9+w8" w4+w1' w0 w3 w5 [3]
mulx sc[0], w2, wB     | w7 up+wA+w6 rp+w9+w8" w4+w1' w0 w3 w5+wB w2| [2]
adox w9, rp            | w7 up+wA+w6" rp+w8 w4+w1' w0 w3 w5+wB w2| [2]
adcx w4, w1            | w7 up+wA+w6" rp+w8' w1 w0 w3 w5+wB w2| [2]
mulx sc[1], w4, w9     | w7 up+wA+w6" rp+w8' w1 w0 w3+w9 w5+wB+w4 w2| [2]
adox wA, up            | w7" up+w6 rp+w8' w1 w0 w3+w9 w5+wB+w4 w2| [2]
adcx w8, rp            | w7" up+w6' rp w1 w0 w3+w9 w5+wB+w4 w2| [2]
mulx sc[2], w8, wA     | w7" up+w6' rp w1 w0+wA w3+w9+w8 w5+wB+w4 w2| [2]
movq w5, sc[11]        | w7" up+w6' rp w1 w0+wA w3+w9+w8 wB+w4| w2| [2]
movq $0, w5
adox w5, w7            | w7 up+w6' rp w1 w0+wA w3+w9+w8 wB+w4| w2| [2]
adcx w6, up            | w7' up rp w1 w0+wA w3+w9+w8 wB+w4| w2| [2]
ado3(sc[10], w2, w5)   | w7' up rp w1 w0+wA w3+w9+w8 wB+w4|" [3]
mulx sc[3], w2, w5     | w7' up rp w1+w5 w0+wA+w2 w3+w9+w8 wB+w4|" [3]
movq $0, w6
adcx w6, w7            | w7 up rp w1+w5 w0+wA+w2 w3+w9+w8 wB+w4|" [3]
ado3(sc[11], wB, w6)   | w7 up rp w1+w5 w0+wA+w2 w3+w9+w8" w4| [3]
mulx sc[4], w6, wB     | w7 up rp+wB w1+w5+w6 w0+wA+w2 w3+w9+w8" w4| [3]
movq w7, t0            | t0 up rp+wB w1+w5+w6 w0+wA+w2 w3+w9+w8" w4| [3]
movq sc[11], w7        | t0 up rp+wB w1+w5+w6 w0+wA+w2 w3+w9+w8" w4+w7 [3]
adcx w7, w4            | t0 up rp+wB w1+w5+w6 w0+wA+w2 w3+w9+w8"' w4 [3]
movq w4, sc[11]        | t0 up rp+wB w1+w5+w6 w0+wA+w2 w3+w9+w8"' [4]
movq t2, w4
adox w9, w3            | t0 up rp+wB w1+w5+w6 w0+wA+w2" w3+w8' [4]
mulx sc[5], w7, w9     | t0 up+w9 rp+wB+w7 w1+w5+w6 w0+wA+w2" w3+w8' [4]
adcx w8, w3            | t0 up+w9 rp+wB+w7 w1+w5+w6 w0+wA+w2"' w3 [4]
adox wA, w0            | t0 up+w9 rp+wB+w7 w1+w5+w6" w0+w2' w3 [4]
mulx sc[6], w8, wA     | t0+wA up+w9+w8 rp+wB+w7" w1+w6 w0+w2' w3 [4]
adox w5, w1
movq t0, w5            | wA+w5 up+w9+w8 rp+wB+w7" w1+w6 w0+w2' w3 [4]
adcx w2, w0            | wA+w5 up+w9+w8 rp+wB+w7" w1+w6' w0 w3 [4]
mulx sc[7], w2, dd     | dd wA+w5+w2 up+w9+w8 rp+wB+w7" w1+w6' w0 w3 [4]
adox wB, rp            | dd wA+w5+w2 up+w9+w8" rp+w7 w1+w6' w0 w3 [4] w4=rp
adcx w6, w1            | dd wA+w5+w2 up+w9+w8" rp+w7' w1 w0 w3 [4] w4=rp
movq w1, t1            | dd wA+w5+w2 up+w9+w8" rp+w7' t1 t2 w3 [4] w4=rp
movq sc[8], w1
movq sc[9], w6
movq sc[10], wB
movq w0, t2            | dd wA+w5+w2 up+w9+w8" rp+w7' t1 t2 w3 .. wB w6 w1  w4=rp
movq sc[11], w0        | dd wA+w5+w2 up+w9+w8" rp+w7' t1 t2 w3 w0 wB w6 w1  w4=rp
movq w4[0], t0         | prefetch r[0]
adox w9, up            | dd wA+w5+w2" up+w8 rp+w7' t1 t2 w3 w0 wB w6 w1  w4=rp
adcx w7, rp            | dd wA+w5+w2" up+w8' rp t1 t2 w3 w0 wB w6 w1  w4=rp
                       | possible delay 1 tick
adox wA, w5            | dd" w5+w2 up+w8' rp t1 t2 w3 w0 wB w6 w1  w4=rp
adcx w8, up            | dd" w5+w2' up rp t1 t2 w3 w0 wB w6 w1  w4=rp
movq $0, w8            | dd" w5+w2' up rp t1 t2 w3 w0 wB w6 w1  w4=rp w8=0
adox w8, dd            | dd w5+w2' up rp t1 t2 w3 w0 wB w6 w1  w4=rp w8=0
ado3(w4[0], w1, w7)    | dd w5+w2' up rp t1 t2 w3 w0 wB w6 [1]  w4=rp w8=0
adcx w5, w2            | dd' w2 up rp t1 t2 w3 w0 wB w6" [1]  w4=rp w8=0
ado3(w4[1], w6, w5)    | dd' w2 up rp t1 t2 w3 w0 wB" [2]  w4=rp w8=0
movq t2, w6            | dd' w2 up rp t1 w6 w3 w0 wB" [2]  w4=rp w8=0
adcx w8, dd            | dd w2 up rp t1 w6 w3 w0 wB" [2]  w4=rp w8=0
movq t1, w5            | w8 w8 w8 dd w2 up rp w5 w6 w3 w0 wB" [2]  w4=rp
ado3(w4[2], wB, w7)    | w8 w8 w8 dd w2 up rp w5 w6 w3 w0" [3]  w4=rp
ado3(w4[3], w0, w7)    | w8 w8 w8 dd w2 up rp w5 w6 w3" [4]  w4=rp
ado3(w4[4], w3, w0)    | w8 w8 w8 dd w2 up rp w5 w6" [5]  w4=rp
ado3(w4[5], w6, w0)    | w8 w8 w8 dd w2 up rp w5" [6]  w4=rp
ado3(w4[6], w5, w0)    | w8 w8 w8 dd w2 up rp" [7]  w4=rp
movq $0, w5            | w5 w5 w5 dd w2 up rp" [7]  w4=rp
ado3(w4[7], rp, w0)    | w5 w5 w5 dd w2 up" [8]  w4=rp
ado3(w4[8], up, w0)    | w5 w5 w5 dd w2" [9]  w4=rp
ado3(w4[9], w2, w0)    | w5 w5 w5 dd" [10]  w4=rp
ado3(w4[10], dd, w0)   | w5 w5 w5" [11]  w4=rp
ado3(w4[11], w5, w0)
ado3(w4[12], w5, w0)
ado3(w4[13], w5, w0)
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
        return [
                evaluate_row('movq %s, %s' % (m.group(1), m.group(3)))[0],
                'adox %s, %s' % (m.group(2), m.group(3)),
                evaluate_row('movq %s, %s' % (m.group(3), m.group(1)))[0]
               ]
    
    m = g_sc_patt.search(s)
    if m:
        s = s.replace(m.group(), ('st[%s]' % (int(m.group(1)) - g_sc_shift)))

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
    P.cook_asm(o, r, var_map, True)

if __name__ == '__main__':
    with open(sys.argv[1], 'wb') as g_o:
        do_it(g_o, g_code, E.g_var_map + ' st,rsp')
