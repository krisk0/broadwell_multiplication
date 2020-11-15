'''
GMP subroutine mul_basecase specialized for size divisable by 4. Time on
 AMD Ryzen 7 3800X: same as mul_basecase
'''

g_code='''
|rdi  rsi  rdx  rcx      r8  r15      r14     rbp
|rp   up   un   u_index  w0  v_index  neg_un  vp
    !save neg_un
    mov dd, neg_un
    !save vp
    mov u_index, vp
    !save v_index
    mov w0, v_index

    mov (up), %r9                 | r9 = u0
    mov (vp), dd                  | rdx = v0

    lea (up,neg_un,8), up           | now up points to 1 past tail of u: up += un
    lea -32(rp,neg_un,8), rp        | rp points to &r_p[un-4]

    neg neg_un                      | r14 = -un, -8 = ff...f8
    mov neg_un, u_index             | u_index = -un
    test $1, %r14b
    !save %r12
    mulx %r9,%r9,%r8
    !save %r13
    mulx 0x8(%rsi,neg_un,8),%r11,%r10
    !save %rbx
    mulx 0x10(%rsi,neg_un,8),%r13,%r12
    jmp .Lmlo0

	.align	16, 0x90
.v0_loop:
    jrcxz .Lmend
    adc w0, %r11
    mov %r9, (rp,u_index,8)
.Lmlo3:
    mulx (%rsi,%rcx,8), %r9, %r8
    adc %r10, %r13
    mov %r11, 8(rp,u_index,8)
.Lmlo2:
    mulx 8(%rsi,%rcx,8),%r11,%r10
    adc %r12, %rbx
    mov %r13, 16(rp,u_index,8)
.Lmlo1:
    mulx 16(%rsi,%rcx,8), %r13, %r12
    adc %rax, %r9
    mov %rbx, 24(rp,u_index,8)
.Lmlo0:
    mulx 24(%rsi,%rcx,8), %rbx, %rax
    lea 4(u_index), u_index
    jmp .v0_loop

.Lmend:
    mov %r9, (rp)
    adc w0, %r11
.Lmwd3:
    mov %r11, 8(rp)
    adc %r10, %r13
    mov %r13, 16(rp)
    adc %r12, %rbx
    adc $0, %rax
    mov %rbx, 24(rp)
    mov %rax, 32(rp)
    add $8, vp                   | vp points to next limb
    dec v_index

    mov (vp), dd                 | rdx = next v limb
    add $8, vp
    mov neg_un, u_index             | initialize index of inner loop
    add $8, rp                         | increase result pointer
    mulx (%rsi,neg_un,8), %r9, %r8
    mulx 0x8(%rsi,neg_un,8), %r11, %r10
    mulx 0x10(%rsi,neg_un,8), %r13, %r12
    mulx 0x18(%rsi,neg_un,8), %rbx, %rax
    add w0, %r11
    jmp .Llo0

.Loloop0:
    mov (vp), dd
    add $8, vp
    add %r9, (rp)
    mulx (%rsi,neg_un,8),%r9,%r8
    adc %r11, 8(rp)
    mulx 0x8(%rsi,neg_un,8),%r11,%r10
    adc %r13, 16(rp)
    mulx 0x10(%rsi,neg_un,8),%r13,%r12
    adc %rbx, 24(rp)
    mov neg_un, u_index
    adc $0, %rax
    mov %rax, 32(rp)
    add $8, rp
    mulx 0x18(%rsi,neg_un,8), %rbx, %rax
    add w0, %r11
    jmp .Llo0

    .align  16, 0x90
.Ltp0:                                     | mul-add loop
    add %r9, (rp,u_index,8)
    mulx (%rsi,%rcx,8), %r9, %r8
    adc %r11, 8(rp,u_index,8)
    mulx 8(%rsi,%rcx,8), %r11, %r10
    adc %r13, 16(rp,u_index,8)
    mulx 16(%rsi,%rcx,8),%r13,%r12
    adc %rbx, 24(rp,u_index,8)
    adc %rax, %r9
    mulx 0x18(%rsi,%rcx,8), %rbx, %rax
    adc w0, %r11
.Llo0:
    adc %r10, %r13
    adc %r12, %rbx
    adc $0, %rax
    add $4, u_index
    jnz .Ltp0

    dec v_index
    jne .Loloop0

    jmp .Lfinal_wind_down

.Loloop2:
    mov (vp), dd
    add $8, vp
    add %r9, (rp)
    adc %r11, 8(rp)
    adc %r13, 16(rp)
    mulx (%rsi,neg_un,8), %r13, %r12
    adc %rbx, 24(rp)
    adc $0, %rax
    mov %rax, 32(rp)
    mulx 0x8(%rsi,neg_un,8),%rbx,%rax
    lea 2(neg_un), u_index
    add $8, rp
    mulx 0x10(%rsi,neg_un,8), %r9, %r8
    add %r12, %rbx
    adc $0, %rax
    mulx 0x18(%rsi,neg_un,8),%r11,%r10
    add %r13, 16(rp,u_index,8)
    jmp .Llo2

    .align  16, 0x90
.Ltp2:
    add %r9, (rp,u_index,8)
    mulx   (%rsi,%rcx,8),%r9,%r8
    adc %r11, 8(rp,u_index,8)
    mulx   0x8(%rsi,%rcx,8),%r11,%r10
    adc %r13, 16(rp,u_index,8)
.Llo2:
    mulx   0x10(%rsi,%rcx,8),%r13,%r12
    adc %rbx, 24(rp,u_index,8)
    adc %rax, %r9
    mulx   0x18(%rsi,%rcx,8),%rbx,%rax
    adc w0, %r11
    adc %r10, %r13
    adc %r12, %rbx
    adc $0, %rax
    add $4, u_index
    jnz .Ltp2

    dec v_index
    jne .Loloop2

    jmp .Lfinal_wind_down

.Loloop1:
    mov (vp), dd
    add $8, vp
    add %r9, (rp)
    mulx 0x8(%rsi,neg_un,8),%r9,%r8
    adc %r11, 8(rp)
    mulx 0x10(%rsi,neg_un,8),%r11,%r10
    adc %r13, 16(rp)
    mulx 0x18(%rsi,neg_un,8),%r13,%r12
    adc %rbx, 24(rp)
    adc $0, %rax
    mov %rax, 32(rp)
    mulx   (%rsi,neg_un,8),%rbx,%rax
    lea 1(neg_un), u_index
    add $8, rp
    add %rbx, 24(rp,u_index,8)
    jmp .Llo1

    .align  16, 0x90
.Ltp1:
    add %r9, (rp,u_index,8)
    mulx (%rsi,%rcx,8), %r9, %r8
    adc %r11, 8(rp,u_index,8)
    mulx 0x8(%rsi,%rcx,8), %r11, %r10
    adc %r13, 16(rp,u_index,8)
    mulx 0x10(%rsi,%rcx,8), %r13, %r12
    adc %rbx, 24(rp,u_index,8)
.Llo1:
    adc %rax, %r9
    mulx   0x18(%rsi,%rcx,8),%rbx,%rax
    adc w0, %r11
    adc %r10, %r13
    adc %r12, %rbx
    adc $0, %rax
    add $4, u_index
    jnz .Ltp1

    dec v_index
    jne .Loloop1

    jmp .Lfinal_wind_down

.Loloop3:
    mov (vp), dd
    add $8, vp
    add %r9, (rp)
    adc %r11, 8(rp)
    mulx (%rsi,neg_un,8), %r11, %r10
    adc %r13, 16(rp)
    mulx 0x8(%rsi,neg_un,8),%r13,%r12
    adc %rbx, 24(rp)
    adc $0, %rax
    mov %rax, 32(rp)
    mulx 0x10(%rsi,neg_un,8),%rbx,%rax
    lea 3(neg_un), u_index
    add $8, rp
    add %r10, %r13
    mulx (%rsi,%rcx,8),%r9,%r8
    adc %r12, %rbx
    adc $0, %rax
    add %r11, 8(rp,u_index,8)
    jmp .Llo3

    .align  16, 0x90
.Ltp3:
    add %r9, (rp,u_index,8)
    mulx (%rsi,%rcx,8), %r9, %r8
    adc %r11, 8(rp,u_index,8)
.Llo3:
    mulx 0x8(%rsi,%rcx,8), %r11, %r10
    adc %r13, 16(rp,u_index,8)
    mulx 0x10(%rsi,%rcx,8), %r13,%r12
    adc %rbx, 24(rp,u_index,8)
    adc %rax, %r9
    mulx 0x18(%rsi,%rcx,8), %rbx,%rax
    adc w0, %r11
    adc %r10, %r13
    adc %r12, %rbx
    adc $0, %rax
    add $4, u_index
    jnz .Ltp3

    dec v_index
    jne .Loloop3

.Lfinal_wind_down:
    !restore %r12
    add %r9, (rp)
    !restore neg_un
    adc %r11, 8(rp)
    !restore v_index
    adc %r13, 16(rp)
    !restore %r13
    adc %rbx, 24(rp)
    !restore %rbx
    adc $0, %rax
    !restore vp
    mov %rax, 32(rp)
    ret
'''

g_vars_map='rdi,rp rsi,up rdx,un rcx,u_index r8,w0 r15,v_index r14,neg_un ' + \
    'rbp,vp rdx,dd'

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

g_subroutine = 'mul_4x_zen_5arg'

g_xmm_save_pattern = re.compile('!save (.+)')
def save_registers_in_xmm(cc, s0):
    result = dict()
    for i in range(len(cc)):
        c = cc[i]
        m = g_xmm_save_pattern.match(c)
        if not m:
            continue
        m = m.group(1)
        t = '%%xmm%s' % s0
        s0 -= 1
        cc[i] = 'movq %s, %s' % (m, t)
        result[m] = t
    return result

def do_5arg(o):
    comment = P.g_autogenerated_patt % os.path.basename(sys.argv[0])
    o.write(comment.replace('//', '#'))
    P.write_asm_procedure_header(o, g_subroutine)
    code = P.cutoff_comments(g_code)
    xmm_save = save_registers_in_xmm(code, 15)
    code = '\n'.join(code)
    symb = dict()
    for v_k in g_vars_map.split(' '):
        v,k = v_k.split(',')
        symb[k] = '%' + v
    for k,v in xmm_save.items():
        code = code.replace('!restore ' + k, 'movq %s, %s' % (v, k))
    code = P.replace_symbolic_vars_name(code, symb)
    P.write_asm_inside(o, code)

with open(sys.argv[1], 'wb') as g_o:
    do_5arg(g_o)
