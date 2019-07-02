#!/bin/bash

set -ex

L_FLAG='-lgmp'
L_FLAG='/usr/libexec/gmp-6.1.2.gcc82/broadwell/libgmp.a'

CPP_FLAGS="-O3 -march=broadwell -fomit-frame-pointer -static"

g++ $CPP_FLAGS -DSUBR=BASECASE benchmark8.cpp $L_FLAG \
    -oautomagic/test8_basecase.exe
g++ $CPP_FLAGS -DSUBR=MUL8 benchmark8.cpp $L_FLAG \
    -oautomagic/test8_official.exe
g++ $CPP_FLAGS -DSUBR=CUSTOM benchmark8.cpp -lgmp -oautomagic/test8_custom.exe

#broadwell-emu automagic/test8_tested.exe 20190611
