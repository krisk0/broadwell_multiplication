'''
n: not a multiple of 4, >4
mpn_sub_inplace(tgt, src, n)

subtract r := src - tgt. Place r at tgt. Put borrow (0 or 1) into n.

On exit, tgt is increased to original tgt + original n
'''

g_code = '''
movq (sp), w0
movq nn, w3
subq (tp), w0
and $3, nn
shr $2, w3
.align 32
loop_short:
lea 8(sp), sp
movq w0, (tp)
lea 8(tp), tp
dec nn
movq (sp), w0
jz done_short
sbbq (tp), w0
jmp loop_short
| m = n & 3 subtractions done, w0 = tgt[m]
done_short:
movq 8(sp), w1
movq w3, nn
.align 32
loop_long:
| nn = count of subtractions left / 4; 2 words of src loaded to w0 w1
movq 16(sp), w2
movq 24(sp), w3            | 4 words of sp loaded
sbbq (tp), w0
sbbq 8(tp), w1
lea 32(sp), 32
sbbq 16(tp), w2
sbbq 24(tp), w3
lea 32(tp), tp
movq w0, -32(sp)
movq w1, -24(sp)
dec nn
movq w2, -16(sp)
movq w3, -8(sp)
jz done_long
movq (sp), w0
movq 8(sp), w1
jmp loop_long
done_long:
adc $0, nn
'''
