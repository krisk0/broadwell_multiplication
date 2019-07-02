#!/bin/bash

set -ex

CPP_FLAGS="-O3 -march=broadwell -fomit-frame-pointer -static"

./gen_mul4.py automagic/mul4_broadwell.h
./gen_toom22.py 8 automagic/toom22_mul.h
./gen_mpn_le.py 4 automagic/mpn_le_4.h
./gen_mpn_sub.py 4 automagic/mpn_sub_4.h
./gen_subtract_lesser_from_bigger.py 4 automagic/subtract_lesser_from_bigger_4.h
./gen_toom22_sum_subtract.py 8 automagic/sum_subtract_8.h
./gen_add_sub.py 8 automagic/add_sub_8.h
./gen_mul8_store1.py automagic/mul8_store_once.h

cd automagic 
gcc -c mul4_broadwell.s
g++ $CPP_FLAGS ../test4.cpp mul4_broadwell.o -lgmp -otest4.exe
g++ $CPP_FLAGS ../test8.cpp mul4_broadwell.o -lgmp -otest8.exe
g++ $CPP_FLAGS ../test8_once.cpp -lgmp -otest8_once.exe

broadwell-emu ./test4.exe
broadwell-emu ./test8.exe
broadwell-emu ./test8_once.exe
