# GMP subroutine with no changes, other than name

	.text
	.align	16, 0x90
	.globl	__gmpn_addmul_1_adox
	.type	__gmpn_addmul_1_adox,@function
__gmpn_addmul_1_adox:

	mov	(%rsi), %r8

	push	%rbx
	push	%r12
	push	%r13

	lea	(%rsi,%rdx,8), %rsi
	lea	-16(%rdi,%rdx,8), %rdi
	mov	%edx, %eax
	xchg	%rcx, %rdx		

	neg	%rcx

	and	$3, %al
	jz	.Lb0
	cmp	$2, %al
	jl	.Lb1
	jz	.Lb2

.Lb3:	mulx	(%rsi,%rcx,8), %r11, %r10
	mulx	8(%rsi,%rcx,8), %r13, %r12
	mulx	16(%rsi,%rcx,8), %rbx, %rax
	dec	%rcx
	jmp	.Llo3

.Lb0:	mulx	(%rsi,%rcx,8), %r9, %r8
	mulx	8(%rsi,%rcx,8), %r11, %r10
	mulx	16(%rsi,%rcx,8), %r13, %r12
	jmp	.Llo0

.Lb2:	mulx	(%rsi,%rcx,8), %r13, %r12
	mulx	8(%rsi,%rcx,8), %rbx, %rax
	lea	2(%rcx), %rcx
	jrcxz	.Lwd2
.Lgt2:	mulx	(%rsi,%rcx,8), %r9, %r8
	jmp	.Llo2

.Lb1:	and	%al, %al
	mulx	(%rsi,%rcx,8), %rbx, %rax
	lea	1(%rcx), %rcx
	jrcxz	.Lwd1
	mulx	(%rsi,%rcx,8), %r9, %r8
	mulx	8(%rsi,%rcx,8), %r11, %r10
	jmp	.Llo1

.Lend:	adcx	%r10, %r13
	mov	%r11, -8(%rdi)
.Lwd2:	adox	(%rdi), %r13
	adcx	%r12, %rbx
	mov	%r13, (%rdi)
.Lwd1:	adox	8(%rdi), %rbx
	adcx	%rcx, %rax
	adox	%rcx, %rax
	mov	%rbx, 8(%rdi)
	pop	%r13
	pop	%r12
	pop	%rbx
	ret

.Ltop:	jrcxz	.Lend
	mulx	(%rsi,%rcx,8), %r9, %r8
	adcx	%r10, %r13
	mov	%r11, -8(%rdi,%rcx,8)
.Llo2:	adox	(%rdi,%rcx,8), %r13
	mulx	8(%rsi,%rcx,8), %r11, %r10
	adcx	%r12, %rbx
	mov	%r13, (%rdi,%rcx,8)
.Llo1:	adox	8(%rdi,%rcx,8), %rbx
	mulx	16(%rsi,%rcx,8), %r13, %r12
	adcx	%rax, %r9
	mov	%rbx, 8(%rdi,%rcx,8)
.Llo0:	adox	16(%rdi,%rcx,8), %r9
	mulx	24(%rsi,%rcx,8), %rbx, %rax
	adcx	%r8, %r11
	mov	%r9, 16(%rdi,%rcx,8)
.Llo3:	adox	24(%rdi,%rcx,8), %r11
	lea	4(%rcx), %rcx
	jmp	.Ltop
	.size	__gmpn_addmul_1_adox,.-__gmpn_addmul_1_adox

