import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

g_n = int(sys.argv[1])
g_tgt = sys.argv[2]
assert g_n == 8                         # TODO: accept other values

g_code_8 = '''
vmovdqu 64(rp), bJ                                   | bJ := b3 b2 b1 b0       ! p23
movq (rp), w0                                        | w0 := a0                ! p0
vmovdqu 96(rp), bS                                   | bS := b7 b6 b5 b4       ! p23
vpextrq $0x1,bJ_128,w1                               | w1 := b1                ! p0 p5
addq 64(rp), w0                                      | ' w0                    ! p0156 p23
vperm2i128 $0x81,bJ,bJ,bJ                            | bJ := b3 b2             ! p5
adcq 8(rp), w1                                       | ' w1 w0                 ! p06 p23
vmovq bJ_128, w2                                     | w2 := b2                ! p0
push w6                                              |                         ! p237 p4
vpextrq $0x1,bJ_128,w3                               | w3 := b3                ! p0 p5
adcq 16(rp), w2                                      | ' w2 w1 w0              ! p06 p23
adcq 24(rp), w3                                      | ' w3 w2 w1 w0           ! p06 p23
vperm2i128 $0x81,bS,bS,bJ                            | bJ := b7 b6             ! p5
vmovq bS_128, w4                                     | w4 := b4                ! p0
push w7                                              |                         ! p237 p4
vpextrq $0x1,bS_128,w5                               | w5 := b5                ! p0 p5
adcq 32(rp), w4                                      | ' w4 w3 w2 w1 w0        ! p06
vpxor bS_128, bS_128, bS_128                         | bS := 0                 ! p015
vmovq bJ_128, w6                                     | w6 := b6                ! p0
adcq 40(rp), w5                                      | ' w5 w4 w3 w2 w1 w0     ! p06 p23
vpextrq $0x1,bJ_128,w7                               | w7 := b7                ! p0 p5
adcq 48(rp), w6                                      | ' w6 w5 w4 w3 w2 w1 w0  ! p06 p23
vmovq bS_128, w8                                     | w8 := 0                 ! p0
adcq 56(rp), w7                                      |  ' w7 w6 w5 w4 w3 w2 w1 w0! p06 p23
adcq $0, w8                                          | w8 w7 w6 w5 w4 w3 w2 w1 w0 ! p06

subq (cp), w0                              | w8 w7 w6 w5 w4 w3 w2 w1' w0
sbbq 8(cp), w1                             | w8 w7 w6 w5 w4 w3 w2' w1 w0
sbbq 16(cp), w2                            | w8 w7 w6 w5 w4 w3' w2 w1 w0
sbbq 24(cp), w3                            | w8 w7 w6 w5 w4' w3 w2 w1 w0
sbbq 32(cp), w4                            | w8 w7 w6 w5' w4 w3 w2 w1 w0
sbbq 40(cp), w5                            | w8 w7 w6' w5 w4 w3 w2 w1 w0
sbbq 48(cp), w6                            | w8 w7' w6 w5 w4 w3 w2 w1 w0
sbbq 56(cp), w7                            | w8' w7 w6 w5 w4 w3 w2 w1 w0
sbbq $0, w8                                | w8 w7 w6 w5 w4 w3 w2 w1 w0       cf==of==0

addq 32(rp), w0
adcq 40(rp), w1
adcq 48(rp), w2
adcq 56(rp), w3
movq w0, 32(rp)
movq w1, 40(rp)
movq w2, 48(rp)
movq w3, 56(rp)                            | w8 w7 w6 w5 w4'

vmovq bS_128, w0                           |                  w0 := 0
adcq 64(rp), w4
adcq 72(rp), w5
adcq 80(rp), w6
adcq 88(rp), w7                            | w8' w7 w6 w5 w4

lea 96(rp), w2                             |                  w2 := address of senior word

movq w4, 64(rp)
movq w5, 72(rp)
movq w6, 80(rp)
movq w7, 88(rp)

adcq $0, w8                                | w8
pop w7
addq w8, (w2)
jnc done
again:                                     | propagate carry
addq $1, 8(w2)
lea 8(w2), w2
jc again
done:
pop w6
'''

def do_it(tgt):
    assert g_n == 8
    scratch_tgt = 'rax rcx rdx r8 r9 r10 r11'.split(' ')
    scratch_tgt = ['%' + s for s in scratch_tgt]
    scratch_src = 'w0 w1 w2 w3 w4 w5 w8'.split(' ')
    data = {
            'macro_name': 'toom22_add_sub_%s' % g_n,
            'input': ['rp D r_p', 'cp S c_p'],
            'scratch': ['bJ x b_j', 'bS x b_s'],
            'source': os.path.basename(sys.argv[0]),
            'code_language': 'asm',
            'vars_type': {'b_j':'', 'b_s':''},
            'default_type': '__m256i',
            'macro_parameters': 'r_p c_p',
            'clobber': "cc memory " + ' '.join(scratch_tgt),
            }
    code = g_code_8
 
    for i in range(len(scratch_tgt)):
        code = re.sub(r'\b%s\b' % scratch_src[i], '%' + scratch_tgt[i], code)
    code = re.sub(r'\bw6\b', '%%rbx', code)
    code = re.sub(r'\bw7\b', '%%rbp', code)
    
    for i in ['rp', 'cp']:
        code = re.sub(r'\b%s\b' % i, '%%[%s]' % i, code)

    for i in ['J', 'S']:
         code = re.sub(r'\bb%s\b' % i, '%%[b%s]' % i, code)
         code = re.sub(r'\bb%s_128\b' % i, '%%x[b%s]' % i, code)
         
    for i in ['again', 'done']:
        code = re.sub(r'\b%s\b' % i, i + '%=', code)
        
    P.write_cpp_code(tgt, code, data)
    
    # TODO: is it faster to use both adcx and adox instead of adcq?
    
    tgt.write('\n')
    
    sub_to_add = {'subq': 'addq', 'sbbq': 'adcq'}
    for k,v in sub_to_add.items():
        code = re.sub(r'\b%s\b' % k, v, code)

    data['macro_name'] = 'toom22_add_add_%s' % g_n
    del data['source']

    P.write_cpp_code(tgt, code, data)

with open(g_tgt, 'wb') as g_o:
    do_it(g_o)
