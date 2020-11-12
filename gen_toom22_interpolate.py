import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

g_n = int(sys.argv[1])
g_tgt = sys.argv[2]

"""
a := number at p_a ... p_a+@-1
b := number at p_a+@ ... p_a+2*@-1
c := number at p_c ... p_c+@-1
g := a + b - (-1)**sign * c
0 <= g <= 2**(64*@ + 2)
use zero or more bytes of scratch memory at p_c + @
add @+1 words of g to number at address p_a+@/2 ... p_a+@+@/2-1

b7 b6 b5 b4 b3 b2 b1 b0 a7 a6 a5 a4 a3 a2 a1 a0
         g8 g7 g6 g5 g4 g3 g2 g1 g0

bF bE bD bC bB bA b9 b8 b7 b6 b5 b4 b3 b2 b1 b0 aF aE aD aC aB aA a9 a8 a7 a6 a5 a4 a3 a2 a1 a0
                        gF gE gD gC gB gA g9 g8 g7 g6 g5 g4 g3 g2 g1 g0
"""

g_subroutine = 'toom22_interpolate_'

g_code = '''
void
@s_@(mp_ptr p_a, mp_srcptr p_c, uint64_t sign) {
    if(sign) {
        toom22_add_add_@(p_a, p_c);
    } else {
        toom22_add_sub_@(p_a, p_c);
    }
}
'''.replace('@s', g_subroutine).replace('@', '%s' % g_n)

g_spread_carry='''
adcq @r, +24(rp)
jnc @done
@again:
addq $1, +25(rp)
lea +1(rp), rp
jc @again
@done:
'''

"""
rax rcx rdx r8 r9 r10 r11 -> w0 w1 w6 w2 w3 w4 w5
rbx rbp r12 r13 r14 r15 -> w7 w8 w9 wA wB wC
13: w0 .. w12, rdx = w6
"""
g_code_16 = '''
!save w8
movq +16(rp), w0                       | w0 := b0
movq +17(rp), w1                       | w1 := b1
cmp $0, %dl
!save w9
jne three_additions
movq w0, w8                            | w8 := b0
movq w1, w9                            | w9 := b1
!save wA
movq +18(rp), w2                       | w2 := b2
movq +19(rp), w3                       | w3 := b3
!save wB
movq w2, wA                            | wA := b2
movq w3, wB                            | wB := b3
vmovq w6, VZ                           | VZ := 0
addq +8(rp), w0                        | w0 := b0 + a8
adcq +9(rp), w1                        | w1' := b1 + a9
!save w7
movq +20(rp), w4                       | w4 := b4
movq +21(rp), w5                       | w5 := b5
vmovq w1, 128_V0                       | V0 := b1 + a9
adcq +10(rp), w2                       | w2' := b2 + aA
adcq +11(rp), w3                       | w3' := b3 + aB
movq +22(rp), w6                       | w6 := b6
movq +23(rp), w7                       | w7 := b7
adcq +12(rp), w4                       | w4' := b4 + aC
adcq +13(rp), w5                       | w5' := b5 + aD
@save wC
adcq +14(rp), w6                       | w6' := b6 + aE
adcq +15(rp), w7                       | w7' := b7 + aF
adcq +24(rp), w8                       | w8' := b0 + b8
adcq +25(rp), w9                       | w9' := b1 + b9
adcq +26(rp), wA                       | wA' := b2 + bA
adcq +27(rp), wB                       | wB' := b3 + bB
movq +28(rp), wC                       | wC := bC
movq +29(rp), w1                       | w1 := bD
movq w8, +16(rp)                       | update b0
movq w9, +17(rp)                       | update b1
movq +30(rp), w8                       | w8 := bE
movq +31(rp), w9                       | w9 := bF
movq wA, +18(rp)                       | update b2
movq wB, +19(rp)                       | update b3
adcq +20(rp), wC                       | wC := b4 + bC
adcq +21(rp), w1                       | w1 := b5 + bD
adcq +22(rp), w8                       | w8 := b6 + bE
adcq +23(rp), w9                       | w9 := b7 + bF
movq wC, +20(rp)                       | update b4
movq w1, +21(rp)                       | update b5
vmovq VZ, wC
movq w8, +22(rp)                       | update b6
movq w9, +23(rp)                       | update b7
vmovq 128_V0, w1                       | w1 := b1 + a9
adcq $0, wC                            | wC := carry
| bF .. b0 added to b7 .. b0 aF a8, result in w0 .. w7 +16(rp) .. +23(rp) wC
| call it s
addq (rp), w0                          | w0 := s0 + a0
adcq +1(rp), w1                        | w1' := s1 + a1
adcq +2(rp), w2                        | w2' := s2 + a2
adcq +3(rp), w3                        | w3' := s3 + a3
movq +16(rp), w8                       | w8 := s8
movq +17(rp), w9                       | w9 := s9
adcq +4(rp), w4                        | w4' := s4 + a4
adcq +5(rp), w5                        | w5' := s5 + a5
movq +18(rp), wA                       | wA := sA
movq +19(rp), wB                       | wB := sB
| e := s + a
adcq +6(rp), w6                        | w6' := s6 + a6 = e6
adcq +7(rp), w7                        | w7' := e7
adcq +8(rp), w8                        | w8' := e8
adcq +9(rp), w9                        | w9' := e9
adcq +10(rp), wA                       | wA' := eA
adcq +11(rp), wB                       | wB' := eB
movq w8, +16(rp)                       | b0 := e8
movq w9, +17(rp)                       | b1 := e9
movq +20(rp), w8                       | w8 := sC
movq +21(rp), w9                       | w9 := sD
movq wA, +18(rp)                       | b2 := eA
movq wB, +19(rp)                       | b3 := eB
movq +22(rp), wA                       | wA := sE
movq +23(rp), wB                       | wB := sF
adcq +12(rp), w8                       | w8 := eC
adcq +13(rp), w9                       | w9 := eD
adcq +14(rp), wA                       | wA := eE
adcq +15(rp), wB                       | wB := eF
movq w8, +20(rp)                       | b4 := eC
movq w9, +21(rp)                       | b5 := eD
!restore w8
adcq $0, wC                            | wC := e(16) <= 2
movq wA, +22(rp)                       | b6 := eE
movq wB, +23(rp)                       | b7 := eF
| e = s + a calculated, stored in w0 .. w7 +16(rp) .. +23(rp) wC
subq (gp), w0
sbbq +1(gp), w1
!restore w9
sbbq +2(gp), w2
sbbq +3(gp), w3
!restore wA
movq w0, +8(rp)                        | a8 updated
movq w1, +9(rp)                        | a9 updated
!restore wB
sbbq +4(gp), w4
sbbq +5(gp), w5
movq +16(rp), w0                       | w0 := e8
movq +17(rp), w1                       | w1 := e9
movq w2, +10(rp)                       | aA updated
movq w3, +11(rp)                       | aB updated
sbbq +6(gp), w6
| m := e - g
sbbq +7(gp), w7                        | w7 := m7
movq +18(rp), w2                       | w2 := eA
movq +19(rp), w3                       | w3 := eB
movq w4, +12(rp)                       | aC updated
movq w5, +13(rp)                       | aD updated
sbbq +8(gp), w0                        | w0 := m8
sbbq +9(gp), w1                        | w1 := m9
movq +20(rp), w4                       | w4 := eC
movq +21(rp), w5                       | w5 := eD
movq w6, +14(rp)                       | aE updated
movq w7, +15(rp)                       | aF updated
sbbq +10(gp), w2                       | w2 := mA
sbbq +11(gp), w3                       | w3 := mB
!restore w7
movq w0, +16(rp)                       | b0 updated
movq w1, +17(rp)                       | b1 updated
sbbq +12(gp), w4                       | w4 := mC
sbbq +13(gp), w5                       | w5 := mD
movq +22(rp), w0                       | w0 := eE
movq +23(rp), w1                       | w1 := eF
movq w2, +18(rp)                       | b2 updated
movq w3, +19(rp)                       | b3 updated
movq wC, w2
@restore wC
movq w4, +20(rp)                       | b4 updated
movq w5, +21(rp)                       | b5 updated
sbbq +14(gp), w0                       | w0 := mE
sbbq +15(gp), w1                       | w1 := mF
sbbq $0, w2                            | w2 := carry, in range 0 .. 2
--spread_carry(w2 0)
movq w0, +22(rp)                       | b6 updated
movq w1, +23(rp)                       | b7 updated
retq
three_additions:
| w0=b0    w1=b1    rdx=1     w8, w9 saved
sub $1, %dl                            | rdx = 0, CF=OF=0
!save w7
adcx (gp), w0                          | w0 = b0 + g0
movq +18(rp), w2                       | w2 = b2
movq +19(rp), w3                       | w3 = b3
vmovq w6, VZ
!save wA
| f := b + g + a
adox (rp), w0                          | w0 = f0
adcx +1(gp), w1                        | w1 = b1 + g1
movq +20(rp), w4                       | w4 = b4
movq +21(rp), w5                       | w5 = b5
adox +1(rp), w1                        | w1 = f1
adcx +2(gp), w2                        | w2 = b2 + g2
!save wB
movq +22(rp), w6                       | w6 = b6
movq +23(rp), w7                       | w7 = b7
adox +2(rp), w2                        | w2 = f2
adcx +3(gp), w3                        | w3 = b3 + g3
movq +24(rp), w8                       | w8 = b8
movq +25(rp), w9                       | w9 = b9
@save wC
adox +3(rp), w3                        | w3 = f3
adcx +4(gp), w4                        | w4 = b4 + g4
movq +26(rp), wA                       | wA = bA
movq +27(rp), wB                       | wB = bB
vmovq w1, 128_V0                       | V0 = f1
| vacant 64-bit registers: w1 wC
adox +4(rp), w4                        | w4 = f4
adcx +5(gp), w5                        | w5 = b5 + g5
movq +28(rp), wC                       | wC = bC
movq +29(rp), w1                       | w1 = bD
adox +5(rp), w5                        | w5 = f5
adcx +6(gp), w6                        | w6 = b6 + g6
vmovdqu +30(rp), 128_V1                | V1 = 0 0 bF bE
adox +6(rp), w6                        | w6 = f6
adcx +7(gp), w7
movq w5, +5(gp)                        | g5 = f5
movq w6, +6(gp)                        | g6 = f6
adox +7(rp), w7                        | w7 = f7
adcx +8(gp), w8                        | w8 = b8 + g8
vmovq 128_V1, w5                       | w5 = bE
adcx +9(gp), w9                        | w9 = b9 + g9
adox +8(rp), w8                        | w8 = f8
adcx +10(gp), wA                       | wA = bA + gA
movq w7, +7(gp)                        | g7 = f7
movq w8, +8(gp)                        | g8 = f8
adox +9(rp), w9                        | w9 = f9
adcx +11(gp), wB                       | wB = bB + aB
adox +10(rp), wA                       | wA = fA
adcx +12(gp), wC                       | wC = bC + gC
vpextrq $1, 128_V1, w6                 | w6 = bF
movq w9, +9(gp)                        | g9 = f9
movq wA, +10(gp)                       | gA = fA
adox +11(rp), wB                       | wB = fB
adcx +13(gp), w1                       | w1 = bD + gD
adox +12(rp), wC                       | wC = fC
vmovq VZ, w7                           | w7 = 0
adcx +14(gp), w5                       | w5 = bE + gE
adox +13(rp), w1                       | w1 = fD
movq w7, w8                            | w8 = 0
movq wB, +11(gp)                       | gB = fB
movq wC, +12(gp)                       | gC = fC
adcx +15(gp), w6                       | w8 = bF + gF
adox +14(rp), w5                       | w5 = fE
!restore wB
adcx w8, w7                            | w7 = carry, in range 0 .. 1
adox +15(rp), w6                       | w6 = fF
movq w1, +13(gp)                       | gD = fD
movq w5, +14(gp)                       | gE = fE
vmovq 128_V0, w1
adox w8, w7                            | w7 = carry, in range 0 .. 2
| f calculated, stored in w7 w6 +14(gp) .. +5(gp) w4 w3 w2 V0 w0, carry cleared
addq +8(rp), w0                        | w0 = a8 + f0
!restore w8
adcq +9(rp), w1                        | w1 = a9 + f1
adcq +10(rp), w2                       | w2 = aA + f2
movq +5(gp), w5                        | w5 = f5
movq +6(gp), wC                        | wC = f6
adcq +11(rp), w3                       | w3 = aB + f3
!restore w9
adcq +12(rp), w4                       | w4 = aC + f4
movq w0, +8(rp)                        | a8 updated
movq w1, +9(rp)                        | a9 updated
adcq +13(rp), w5                       | w5 = aD + f5
adcq +14(rp), wC                       | wC = aE + f6
movq +7(gp), w0                        | w0 = f7
movq +8(gp), w1                        | w1 = f8
movq w2, +10(rp)                       | aA updated
movq w3, +11(rp)                       | aB updated
movq +9(gp), w2                        | w2 = f9
movq +10(gp), w3                       | w3 = fA
adcq +15(rp), w0                       | w0 = aF + f7
adcq +16(rp), w1                       | w1 = b0 + f8
movq w4, +12(rp)                       | aC updated
movq w5, +13(rp)                       | aD updated
adcq +17(rp), w2                       | w2 = b1 + f9
adcq +18(rp), w3                       | w3 = b2 + fA
movq +11(gp), w4                       | w4 = fB
movq +12(gp), w5                       | w5 = fC
movq wC, +14(rp)                       | aE updated
movq w0, +15(rp)                       | aF updated
movq +13(gp), wC                       | wC = fD
movq +14(gp), w0                       | w0 = fE
adcq +19(rp), w4                       | w4 = b3 + fB
adcq +20(rp), w5                       | w5 = b4 + fC
movq w1, +16(rp)                       | b0 updated
movq w2, +17(rp)                       | b1 updated
adcq +21(rp), wC                       | wC = b5 + fD
adcq +22(rp), w0                       | w0 = b6 + fE
movq w3, +18(rp)                       | b2 updated
movq w4, +19(rp)                       | b3 updated
adcq +23(rp), w6                       | w6 = b7 + fF
movq w5, +20(rp)                       | b4 updated
movq wC, +21(rp)                       | b5 updated
@restore wC
movq w0, +22(rp)                       | b6 updated
movq w6, +23(rp)                       | b7 updated
adcq $0, w7                            | w7 = carry, in range 0 .. 3
!restore wA
--spread_carry(w7 1)
!restore w7
retq
'''

def spread_carry_code(src, var_no):
    var,no = var_no.split(' ')
    return src.replace('@r', var).\
            replace('@done', 'done' + no).replace('@again', 'again' + no)

g_xmm_restore_pattern = re.compile(r'\!restore w(.)')
g_spread_carry_pattern = re.compile(r'--spread_carry\((.+)\)')
def do_16_s(o):
    comment = P.g_autogenerated_patt % os.path.basename(sys.argv[0])
    o.write(comment.replace('//', '#'))
    P.write_asm_procedure_header(o, g_subroutine + '%s' % g_n)
    code = g_code_16.strip()
    while 1:
        m = re.search(g_spread_carry_pattern, code)
        if not m:
            break
        code = code.replace(m.group(0), spread_carry_code(g_spread_carry, m.group(1)))
    register_map = {'VZ': 'xmm15',
            'V0': 'ymm14', '128_V0': 'xmm14',
            'V1': 'ymm13', '128_V1': 'xmm13',
            'rp': 'rdi', 'gp': 'rsi', 'w6': 'rdx'}
    for i in range(7, 0xB + 1):
        j = 1 + i
        register_map['S%X' % i] = 'ymm%s' % j
        register_map['s%X' % i] = 'xmm%s' % j
    scratch_regs = 'rax rcx r8 r9 r10 r11'.split(' ')
    for i in range(len(scratch_regs)):
        register_map['w%s' % i] = scratch_regs[i]
    protected_regs = 'rbx rbp r12 r13 r14 r15'.split(' ')
    for i in range(len(protected_regs)):
        register_map['w%X' % (7 + i)] = protected_regs[i]
    register_map = dict([(k,'%' + v) for k,v in register_map.items()])
    # fix offsets
    code = P.replace_positive_offsets(code)
    # replace '@save wY' by 'store below sp' instructon, '@restore' by ...
    code = P.replace_amp_save(code)
    code = P.replace_amp_restore(code)
    while 1:
        m = re.search(g_xmm_restore_pattern, code)
        if not m:
            break
        i = m.group(1)
        # !save wY means put wY into an xmm register
        code = code.replace('!restore w' + i, 'vmovq s@, w@'.replace('@', i))
        code = code.replace('!save w' + i, 'vmovq w@, s@'.replace('@', i))
    for k,v in register_map.items():
        code = re.sub(r'\b%s\b' % k, v, code)
    P.write_asm_inside(o, code)

g_extern_c='''
extern "C" {
void %s%s(mp_ptr, mp_srcptr, uint64_t);
}
'''

g_name_ext_pattern = re.compile(r'(\S+)\.(\S)')
def do_16(name):
    '''
    create one of two files: .s and .h, .h contains "extern C" forward declaration
    '''
    with open(name, 'wb') as o:
        if name[-1] == 's':
            do_16_s(o)
        else:
            o.write(P.g_autogenerated_patt % os.path.basename(sys.argv[0]))
            o.write(g_extern_c % (g_subroutine, g_n))

def do_it(tgt):
    tgt.write(P.g_autogenerated_patt % os.path.basename(sys.argv[0]))
    tgt.write(g_code.strip() + '\n')

try:
    os.makedirs(os.path.dirname(g_tgt))
except:
    pass

if g_n == 16:
    do_16(g_tgt)
else:
    with open(g_tgt, 'wb') as g_o:
        do_it(g_o)
