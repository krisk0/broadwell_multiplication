#pragma once

#include <alloca.h>
#include <gmp.h>
#include <unistd.h>
#include <x86intrin.h>

#define bordeless_alloc_prepare(mask, unmask) \
    {                                          \
        mask = sysconf(_SC_PAGE_SIZE) - 1;     \
        unmask = ~mask;                        \
    }

#define BORDELESS_ALLOC(T, tgt, size, mask, unmask)                                      \
    {                                                                                    \
        auto bordeless_alloc_temp_ = (mp_limb_t)tgt;                                     \
        if (((bordeless_alloc_temp_ + size) & unmask) != (bordeless_alloc_temp_ & unmask)) { \
            bordeless_alloc_temp_ = (bordeless_alloc_temp_ + mask) & mask;               \
            tgt = (T*)bordeless_alloc_temp_;                                             \
        }                                                                                \
    }

// arrange for a bordeless memory of size size in stack, it will free automatically
#define bordeless_alloc(T, tgt, size, mask, unmask)          \
    auto tgt = (T*)alloca(2 * (size));                       \
    BORDELESS_ALLOC(T, tgt, size, mask, unmask)

#define bordeless_alloc_nodefine(T, tgt, size, mask, unmask) \
    tgt = (T*)alloca(2 * (size));                            \
    BORDELESS_ALLOC(T, tgt, size, mask, unmask)
