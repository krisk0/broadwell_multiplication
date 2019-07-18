Low-level big-integer arithmetic subroutines in C/C++/asm, including `mul8_broadwell_store_once()` and `toom22_mul16_broadwell()`.

`mul8_broadwell_store_once()` multiplies 512-bit (8-word) numbers faster than `GMP` subroutine `gmpn_mul(,, 8, , 8)`.

`toom22_mul16_broadwell()` multiplies 16-word numbers faster than `gmpn_mul(,, 16, , 16)`.

`toom22_deg2_broadwell()` multiplies k-word numbers faster than `gmpn_toom22_mul()`, where k is a degree of 2, in range 32...65536.

# Quick start

```
python2 configure.py
ninja
automagic/test4.exe
automagic/benchm8_custom.exe 0
```
, where 0 is randomness generator seed.

# Benchmarks

subroutine | tacts 
:---: | ---:
gmpn_mul 8 | 131
gmpn_mul_basecase 8 | 114
mul8_broadwell_store_once | 98
gmpn_mul 16 | 427
gmpn_mul_basecase 16 | 408
toom22_mul16_broadwell | 350
mpn_mul 32 | 1395
gmpn_toom22_mul 32 | 1404
toom22_deg2_broadwell 32 | 1217
mpn_mul 64 | 4512
gmpn_toom22_mul 64 | 4482
toom22_deg2_broadwell 64 | 3941

Left column contains subroutine name and size indicator. For instance, 
`gmpn_mul_basecase 16` indicates that `gmpn_mul_basecase(target, operand_a, 16, operand_b, 16)` was called.

Right column contains count of CPU tacts (ticks), as returned by `__rdtsc()`.

For stable result, don't forget to turn off turbo boost when benchmarking.

# Requirements

1. To generate and compile code, `Python2` interpreter, `ninja` utility, `GCC` C/C++ compiler on X86_64 Linux or compatible OS.

2. To benchmark code, Intel Broadwell or better CPU (capable to `adcx`/`adox`).

# License

For code, [GNU Lesser General Public License version 3](https://www.gnu.org/licenses/lgpl-3.0.en.html).

# Questions and answers

*Q0*. I want to link against `GMP` library hand-installed at `/opt/gmp`.

A0. Supposing `gmp` static library is at `/opt/gmp/lib64/libgmp.a`, call `configure.py` like this:

```
c_compiler=/opt/bin/gcc-9.9 \
cpp_compiler=/opt/bin/g++-9.9 \
flags='-O9 -march=broadwell -static' \
gmp_location=/opt/gmp/lib64/libgmp.a
/usr/bin/python2 \
configure.py
```

where `/usr/bin/python2` is full path to your `Python2` interpreter, `flags` are `C` and `C++` compiler flags.

*Q1*. Can I use other compiler than `GCC`?

*A1*. Maybe, if it fully supports GCC-style inline `asm`.

*Q2*. I found a bug in your code.

*A2*. File bugreport. Include value of input parameters, received output and expected output. Prefererably in a form of compilable C or C++ program.

*Q3*. Can I use your code under OS other than Linux?

*A3*. If this OS uses the same calling convention (System V ABI for 64-bit Unix systems), then probably yes. If not, then some subroutines are unusable.

*Q4*. Benchmark of `GMP` code shows bigger tact numbers than found above in this README.

*A4*. Did you install `GMP` via packet manager? Probably it is not optimized for Broadwell.

*Q5*. How do I know that installed `GMP` library is optimized for Broadwell or better CPU?

*A5*. Disassemble it, unpack source code

```
cd /tmp
objdump -d /usr/lib64/libgmp.a > gmp.asm
tar xf /distfiles/gmp-6.1.2.tar.xz 
```
, open `gmp.asm`, look at `__gmpn_mul_basecase` subroutine. The code should be similar to source found in `/tmp/gmp-6.1.2/mpn/x86_64/coreibwl/mul_basecase.asm`.

*Q6*. My packet manager installed crippled (not microarch-optimized) GMP. How do I build `GMP` optimized for my CPU?

*A6*. Under Gentoo Linux, use [my ebuild script](https://github.com/krisk0/razin/blob/master/ebuild/gmp-6.1.2-r99.ebuild). If you are not using `portage` packet manager, follow official [build instructions](https://gmplib.org/manual/Installing-GMP.html).

*Q7*. Why do you generate C/assembler code instead of writing it directly?

*A7*. Because it is a lot easier to write and examine
```
mulx 8(up), w3, w4
```
than
```
" mulx 8(%[up]), %[w3], %[w4]\n"   \
```
. Note that GMP developers use a loop-optimizing software and `m4` macro processor.

*Q8*. Why do you generate `ninja.build` instead of writing it directly?

*A8*. Because `ninja` is about speed, not user convenience. `ninja.build` is redundant and unreadable, compared to `Makefile`.

*Q9*. How do I remove all generated code to start from scratch?

*A9*. `python2 configure.py clean` .
