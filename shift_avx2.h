#if 0
vpsrlq imm, ymm0, ymm1        | shift right 64 bit numbers in ymm0, put result into ymm1
vpsllq imm, ymm0, ymm1        | shift left

vperm2i128 $0x81, w0, w0, w1; vpalignr $8, w0, w1, w1 | w1 = w0 shifted right one limb
#include <immintrin.h>
__m256i _mm256_srli_epi64(__m256i a, int imm8)        | shift bits right
__m256i _mm256_slli_epi64(__m256i a, int imm8)        | shift bits left
result = _mm256_alignr_epi8(
        _mm256_permute2x128_si256(src, src, _MM_SHUFFLE(2, 0, 0, 1)), src, bytes)
                                                      | shift right bytes, bytes < 16
#endif

#include "automagic/shr1_x_avx2.h"
