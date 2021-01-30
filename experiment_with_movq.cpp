#if 0
Test if it is harmful to write
 movq %xmm0, %rax
 movq %xmm1, %rbx
in case rbx is not immediately needed

Result: slight harm on Skylake (.3 ticks lost), no difference on Ryzen.

1st column in table below is index of instruction 'movq %[i1], %[s2]' (0-based).

   bwl  zen
1 10.4  12.0
3 10.1  12.0
5 10.1  12.0
#endif


#include <iostream>
#include <iomanip>
#include <cstdint>
#include <xmmintrin.h>
#include <x86intrin.h>


#define do_it(i0, i1, rez)                                                  \
    uint64_t scr0, scr1, scr2, dx;                                           \
    __asm__ __volatile__(                                                    \
        " movq %[i0], %[rr]\n"                                               \
        " movq %[i1], %[s2]\n"                                               \
        " movq $3, %[dx]\n"                                                  \
        " mulx %[rr], %[s0], %[rr]\n"                                        \
        " movq $99, %[s0]\n"                                                 \
        " xorq %[s0], %[rr]\n"                                               \
        " movq $88, %[s0]\n"                                                 \
        " subq %[s0], %[rr]\n"                                               \
        " movq $5, %[dx]\n"                                                  \
        " mulx %[s2], %[s1], %[s2]\n"                                        \
        " addq %[s2], %[rr]\n"                                               \
        : [rr]"=&r"(rez), [s0]"=&r"(scr0), [s1]"=&r"(scr1), [s2]"=&r"(scr2), \
          [dx]"=&d"(dx)                                                      \
        : [i0]"x"(i0), [i1]"x"(i1)                                           \
    );

int
main() {
    __m128i i0, i1;

    __asm__ __volatile__(
        " vzeroupper\n"
        " movq $1, %%rdx\n"
        " movq %%rdx, %0\n"
        " movq $2, %%rdx\n"
        " pinsrq $1, %%rdx, %0\n"
        " movq $3, %%rdx\n"
        " movq %%rdx, %1\n"
        " movq $4, %%rdx\n"
        " pinsrq $1, %%rdx, %1\n"
        :"+x"(i0), "+x"(i1)
        ::"rdx");

    auto t = __rdtsc();
    constexpr int VOLUME = 10000;
    for(int i = 0; i < VOLUME; i++) {
        uint64_t r;
        do_it(i0, i1, r);
        i0 = i1;
        __m128i scratch;
        __asm__ __volatile__(
            " movq %2, %1\n"
            " psubq %1, %0\n"
            :"+x"(i1), "=&x"(scratch), "=r" (r)
        );
    }
    t = __rdtsc() - t;
    std::cout << std::setprecision(5) << (t * 1.0 / VOLUME) << '\n';
}
