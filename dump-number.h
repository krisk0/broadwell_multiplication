#pragma once

#include <cstdint>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include <gmp.h>

#include "random-number.h"

#ifndef PRINTF_FORMAT
    #define PRINTF_FORMAT "%016lX"
#endif

#ifndef INT
    #define INT uint64_t
#endif

unsigned
senior_zeroes(const INT* p, unsigned n) {
    unsigned i;
    for(i = n; i--;) {
        if(p[i]) {
            return n - 1 - i;
        }
    }
    return n - 1;
}

void
dump_number(const INT* p, unsigned n) {
    n -= senior_zeroes(p, n);
    for(unsigned i = n; i--;) {
        printf("%X:" PRINTF_FORMAT " ", i, p[i]);
    }
    printf("\n");
}

#define BITS_PER_LIMB (sizeof(INT) * 8)

void
deg2(INT* t, unsigned size, unsigned x) {
    // set one bit
    auto i = x / BITS_PER_LIMB;
    x -= i * BITS_PER_LIMB;
    memset(t, 0, sizeof(INT) * size);
    t[i] = (INT(1)) << x;
}

void
one_word(INT* t, unsigned size, unsigned x) {
    // one word -1
    memset(t, 0, sizeof(INT) * size);
    t[x] = (INT)-1;
}
