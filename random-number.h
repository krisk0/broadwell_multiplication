#pragma once

#include <unistd.h>

template <typename T>
T
random_limb() {
    T result{};
    for(unsigned i = 0; i < sizeof(T); i++) {
        result = (result << 8) ^ (((unsigned)rand()) & 0xFF);
    }
    return result;
}

template <typename T>
void
random_number(T* p, unsigned n) {
    for(unsigned i = 0; i < n; i++) {
        p[i] = random_limb<T>();
    }
}
