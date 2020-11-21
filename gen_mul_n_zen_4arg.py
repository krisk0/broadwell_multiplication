'''
GMP subroutine mul_basecase specialized for case un=vn
'''

g_code='''
|rdi  rsi  rdx  rcx      r8  r15      r14     rbp
|rp   up   un   u_index  w0  v_index  neg_un  vp
    cmp $2, %rdx
    ja  .Lgen
    mov (%rcx), %rdx
    .byte   0xc4,98,251,0xf6,14
    je  .Ls2x

.Ls11:
    mov %rax, (%rdi)                 | size = 1
    mov %r9, 8(%rdi)

    ret

.Ls2x:
    .byte 0x0F,0x1F,0x40,0x00        | NOP of size 4 instead of cmp $2, %r8
    .byte 0xc4,98,187,0xf6,86,8
    .byte 0x66,0x90                  | NOP of size 2 instead of je
    add %r8, %r9
    adc $0, %r10
    mov 8(%rcx), %rdx
    mov %rax, (%rdi)
    .byte   0xc4,98,187,0xf6,30
    .byte   0xc4,226,251,0xf6,86,8
    add %r11, %rax
    adc $0, %rdx
    add %r8, %r9
    adc %rax, %r10
    adc $0, %rdx
    mov %r9, 8(%rdi)
    mov %r10, 16(%rdi)
    mov %rdx, 24(%rdi)

    ret

    add %r8, %r9                        | unreachable code of length 19
    adc $0, %r10                        | TODO: shorten the unreachable code
    mov %rax, (%rdi)
    mov %r9, 8(%rdi)
    mov %r10, 16(%rdi)

    ret


.Lgen:
    push    %r15
    push    %r14
    push    %r13
    push    %r12
    push    %rbp
    push    %rbx

    mov %rdx, %r14
    mov %rcx, %rbp
    mov %rdx, %r15

    mov (%rsi), %r9
    mov (%rbp), %rdx

    lea (%rsi,%r14,8), %rsi
    lea -32(%rdi,%r14,8), %rdi

    neg %r14
    mov %r14, %rcx
    test    $1, %r14b
    jz  .Lmx0
.Lmx1:  test    $2, %r14b
    jz  .Lmb3

.Lmb1:  .byte   0xc4,194,227,0xf6,193
    inc %rcx
    .byte   0xc4,0x22,0xb3,0xf6,0x44,0xf6,0x08
    .byte   0xc4,0x22,0xa3,0xf6,0x54,0xf6,0x10
    jmp .Lmlo1

.Lmb3:  .byte   0xc4,66,163,0xf6,209
    .byte   0xc4,0x22,0x93,0xf6,0x64,0xf6,0x08
    .byte   0xc4,0xa2,0xe3,0xf6,0x44,0xf6,0x10
    sub $-3, %rcx
    jz  .Lmwd3
    test    %edx, %edx
    jmp .Lmlo3

.Lmx0:  test    $2, %r14b
    jz  .Lmb0

.Lmb2:  .byte   0xc4,66,147,0xf6,225
    .byte   0xc4,0xa2,0xe3,0xf6,0x44,0xf6,0x08
    lea 2(%rcx), %rcx
    .byte   0xc4,0x22,0xb3,0xf6,0x44,0xf6,0x10
    jmp .Lmlo2

.Lmb0:  .byte   0xc4,66,179,0xf6,193
    .byte   0xc4,0x22,0xa3,0xf6,0x54,0xf6,0x08
    .byte   0xc4,0x22,0x93,0xf6,0x64,0xf6,0x10
    jmp .Lmlo0

    .align  16, 0x90
.Lmtop:jrcxz    .Lmend
    adc %r8, %r11
    mov %r9, (%rdi,%rcx,8)
.Lmlo3:.byte    0xc4,0x62,0xb3,0xf6,0x04,0xce
    adc %r10, %r13
    mov %r11, 8(%rdi,%rcx,8)
.Lmlo2:.byte    0xc4,0x62,0xa3,0xf6,0x54,0xce,0x08
    adc %r12, %rbx
    mov %r13, 16(%rdi,%rcx,8)
.Lmlo1:.byte    0xc4,0x62,0x93,0xf6,0x64,0xce,0x10
    adc %rax, %r9
    mov %rbx, 24(%rdi,%rcx,8)
.Lmlo0:.byte    0xc4,0xe2,0xe3,0xf6,0x44,0xce,0x18
    lea 4(%rcx), %rcx
    jmp .Lmtop

.Lmend:mov  %r9, (%rdi)
    adc %r8, %r11
.Lmwd3:mov  %r11, 8(%rdi)
    adc %r10, %r13
    mov %r13, 16(%rdi)
    adc %r12, %rbx
    adc $0, %rax
    mov %rbx, 24(%rdi)
    mov %rax, 32(%rdi)
    add $8, %rbp
    dec %r15
    jz  .Lend


    test    $1, %r14b
    jnz .L0x1

.L0x0:  test    $2, %r14b
    jnz .Loloop2_entry

.Loloop0_entry:

    mov (%rbp), %rdx
    add $8, %rbp
    mov %r14, %rcx
    add $8, %rdi
    .byte   0xc4,0x22,0xb3,0xf6,0x04,0xf6
    .byte   0xc4,0x22,0xa3,0xf6,0x54,0xf6,0x08
    .byte   0xc4,0x22,0x93,0xf6,0x64,0xf6,0x10
    .byte   0xc4,0xa2,0xe3,0xf6,0x44,0xf6,0x18
    add %r8, %r11
    jmp .Llo0

.Loloop0:

    mov (%rbp), %rdx
    add $8, %rbp
    add %r9, (%rdi)
    .byte   0xc4,0x22,0xb3,0xf6,0x04,0xf6
    adc %r11, 8(%rdi)
    .byte   0xc4,0x22,0xa3,0xf6,0x54,0xf6,0x08
    adc %r13, 16(%rdi)
    .byte   0xc4,0x22,0x93,0xf6,0x64,0xf6,0x10
    adc %rbx, 24(%rdi)
    mov %r14, %rcx
    adc $0, %rax
    mov %rax, 32(%rdi)
    add $8, %rdi
    .byte   0xc4,0xa2,0xe3,0xf6,0x44,0xf6,0x18
    add %r8, %r11
    jmp .Llo0

    .align  16, 0x90
.Ltp0:  add %r9, (%rdi,%rcx,8)
    .byte   0xc4,0x62,0xb3,0xf6,0x04,0xce
    adc %r11, 8(%rdi,%rcx,8)
    .byte   0xc4,0x62,0xa3,0xf6,0x54,0xce,0x08
    adc %r13, 16(%rdi,%rcx,8)
    .byte   0xc4,0x62,0x93,0xf6,0x64,0xce,0x10
    adc %rbx, 24(%rdi,%rcx,8)
    adc %rax, %r9
    .byte   0xc4,0xe2,0xe3,0xf6,0x44,0xce,0x18
    adc %r8, %r11
.Llo0:  adc %r10, %r13
    adc %r12, %rbx
    adc $0, %rax
    add $4, %rcx
    jnz .Ltp0

    dec %r15
    jne .Loloop0

    jmp .Lfinal_wind_down

.Loloop2_entry:
    mov (%rbp), %rdx
    add $8, %rbp
    lea 2(%r14), %rcx
    add $8, %rdi
    .byte   0xc4,0x22,0x93,0xf6,0x24,0xf6
    .byte   0xc4,0xa2,0xe3,0xf6,0x44,0xf6,0x08
    add %r12, %rbx
    adc $0, %rax
    .byte   0xc4,0x22,0xb3,0xf6,0x44,0xf6,0x10
    .byte   0xc4,0x62,0xa3,0xf6,0x54,0xce,0x08
    add %r13, 16(%rdi,%rcx,8)
    jmp .Llo2

.Loloop2:
    mov (%rbp), %rdx
    add $8, %rbp
    add %r9, (%rdi)
    adc %r11, 8(%rdi)
    adc %r13, 16(%rdi)
    .byte   0xc4,0x22,0x93,0xf6,0x24,0xf6
    adc %rbx, 24(%rdi)
    adc $0, %rax
    mov %rax, 32(%rdi)
    .byte   0xc4,0xa2,0xe3,0xf6,0x44,0xf6,0x08
    lea 2(%r14), %rcx
    add $8, %rdi
    .byte   0xc4,0x22,0xb3,0xf6,0x44,0xf6,0x10
    add %r12, %rbx
    adc $0, %rax
    .byte   0xc4,0x22,0xa3,0xf6,0x54,0xf6,0x18
    add %r13, 16(%rdi,%rcx,8)
    jmp .Llo2

    .align  16, 0x90
.Ltp2:  add %r9, (%rdi,%rcx,8)
    .byte   0xc4,0x62,0xb3,0xf6,0x04,0xce
    adc %r11, 8(%rdi,%rcx,8)
    .byte   0xc4,0x62,0xa3,0xf6,0x54,0xce,0x08
    adc %r13, 16(%rdi,%rcx,8)
.Llo2:  .byte   0xc4,0x62,0x93,0xf6,0x64,0xce,0x10
    adc %rbx, 24(%rdi,%rcx,8)
    adc %rax, %r9
    .byte   0xc4,0xe2,0xe3,0xf6,0x44,0xce,0x18
    adc %r8, %r11
    adc %r10, %r13
    adc %r12, %rbx
    adc $0, %rax
    add $4, %rcx
    jnz .Ltp2

    dec %r15
    jne .Loloop2

    jmp .Lfinal_wind_down

.L0x1:  test    $2, %r14b
    jz  .Loloop3_entry

.Loloop1_entry:
    mov (%rbp), %rdx
    add $8, %rbp
    lea 1(%r14), %rcx
    add $8, %rdi
    .byte   0xc4,0xa2,0xe3,0xf6,0x04,0xf6
    .byte   0xc4,0x22,0xb3,0xf6,0x44,0xf6,0x08
    .byte   0xc4,0x22,0xa3,0xf6,0x54,0xf6,0x10
    .byte   0xc4,0x62,0x93,0xf6,0x64,0xce,0x10
    add %rbx, 24(%rdi,%rcx,8)
    jmp .Llo1

.Loloop1:
    mov (%rbp), %rdx
    add $8, %rbp
    add %r9, (%rdi)
    .byte   0xc4,0x22,0xb3,0xf6,0x44,0xf6,0x08
    adc %r11, 8(%rdi)
    .byte   0xc4,0x22,0xa3,0xf6,0x54,0xf6,0x10
    adc %r13, 16(%rdi)
    .byte   0xc4,0x22,0x93,0xf6,0x64,0xf6,0x18
    adc %rbx, 24(%rdi)
    adc $0, %rax
    mov %rax, 32(%rdi)
    .byte   0xc4,0xa2,0xe3,0xf6,0x04,0xf6
    lea 1(%r14), %rcx
    add $8, %rdi
    add %rbx, 24(%rdi,%rcx,8)
    jmp .Llo1

    .align  16, 0x90
.Ltp1:  add %r9, (%rdi,%rcx,8)
    .byte   0xc4,0x62,0xb3,0xf6,0x04,0xce
    adc %r11, 8(%rdi,%rcx,8)
    .byte   0xc4,0x62,0xa3,0xf6,0x54,0xce,0x08
    adc %r13, 16(%rdi,%rcx,8)
    .byte   0xc4,0x62,0x93,0xf6,0x64,0xce,0x10
    adc %rbx, 24(%rdi,%rcx,8)
.Llo1:  adc %rax, %r9
    .byte   0xc4,0xe2,0xe3,0xf6,0x44,0xce,0x18
    adc %r8, %r11
    adc %r10, %r13
    adc %r12, %rbx
    adc $0, %rax
    add $4, %rcx
    jnz .Ltp1

    dec %r15
    jne .Loloop1

    jmp .Lfinal_wind_down

.Loloop3_entry:
    mov (%rbp), %rdx
    add $8, %rbp
    lea 3(%r14), %rcx
    add $8, %rdi
    .byte   0xc4,0x22,0xa3,0xf6,0x14,0xf6
    .byte   0xc4,0x22,0x93,0xf6,0x64,0xf6,0x08
    .byte   0xc4,0xa2,0xe3,0xf6,0x44,0xf6,0x10
    add %r10, %r13
    adc %r12, %rbx
    adc $0, %rax
    test    %rcx, %rcx
    jz  .Lwd3
    .byte   0xc4,0x62,0xb3,0xf6,0x04,0xce
    add %r11, 8(%rdi,%rcx,8)
    jmp .Llo3

.Loloop3:
    mov (%rbp), %rdx
    add $8, %rbp
    add %r9, (%rdi)
    adc %r11, 8(%rdi)
    .byte   0xc4,0x22,0xa3,0xf6,0x14,0xf6
    adc %r13, 16(%rdi)
    .byte   0xc4,0x22,0x93,0xf6,0x64,0xf6,0x08
    adc %rbx, 24(%rdi)
    adc $0, %rax
    mov %rax, 32(%rdi)
    .byte   0xc4,0xa2,0xe3,0xf6,0x44,0xf6,0x10
    lea 3(%r14), %rcx
    add $8, %rdi
    add %r10, %r13
    .byte   0xc4,0x62,0xb3,0xf6,0x04,0xce
    adc %r12, %rbx
    adc $0, %rax
    add %r11, 8(%rdi,%rcx,8)
    jmp .Llo3

    .align  16, 0x90
.Ltp3:  add %r9, (%rdi,%rcx,8)
    .byte   0xc4,0x62,0xb3,0xf6,0x04,0xce
    adc %r11, 8(%rdi,%rcx,8)
.Llo3:  .byte   0xc4,0x62,0xa3,0xf6,0x54,0xce,0x08
    adc %r13, 16(%rdi,%rcx,8)
    .byte   0xc4,0x62,0x93,0xf6,0x64,0xce,0x10
    adc %rbx, 24(%rdi,%rcx,8)
    adc %rax, %r9
    .byte   0xc4,0xe2,0xe3,0xf6,0x44,0xce,0x18
    adc %r8, %r11
    adc %r10, %r13
    adc %r12, %rbx
    adc $0, %rax
    add $4, %rcx
    jnz .Ltp3

    dec %r15
    jne .Loloop3

.Lfinal_wind_down:
    add %r9, (%rdi)
    adc %r11, 8(%rdi)
    adc %r13, 16(%rdi)
    adc %rbx, 24(%rdi)
    adc $0, %rax
    mov %rax, 32(%rdi)

.Lend:  pop %rbx
    pop %rbp
    pop %r12
    pop %r13
    pop %r14
    pop %r15

    ret

.L3:    mov (%rbp), %rdx
    add $8, %rbp
    add $8, %rdi
    .byte   0xc4,0x22,0xa3,0xf6,0x14,0xf6
    .byte   0xc4,0x22,0x93,0xf6,0x64,0xf6,0x08
    .byte   0xc4,0xa2,0xe3,0xf6,0x44,0xf6,0x10
    add %r10, %r13
    adc %r12, %rbx
    adc $0, %rax
.Lwd3:  adc %r11, 8(%rdi)
    adc %r13, 16(%rdi)
    adc %rbx, 24(%rdi)
    adc $0, %rax
    mov %rax, 32(%rdi)
    dec %r15
    jne .L3
    jmp .Lend
'''

g_vars_map='rdi,rp rsi,up rdx,un rcx,u_index r8,w0 r15,v_index r14,neg_un ' + \
    'rbp,vp rdx,dd'

import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

g_subroutine = 'mul_n_zen_4arg'

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

def do_4arg(o):
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
    do_4arg(g_o)
