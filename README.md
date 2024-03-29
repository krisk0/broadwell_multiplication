Low-level big-integer arithmetic subroutines in C/C++/asm for modern Intel or AMD CPU.

`mul8_zen()` multiplies 512-bit (8-limb) numbers faster than `GMP` subroutine `gmpn_mul(,, 8, , 8)` (both on Skylake and Ryzen). Such hand-optimized assembler subroutines exist for sizes 4…11.

Templated subroutine `toom22_broadwell_t<N>` multiplies N-limb numbers faster than `gmpn_mul(,, N, , N)`, for small values of N.

# Status

Work-in-progress. Code needs cleaning. Some subroutines might not work as expected. However, if there is a benchmark published for a procedure, then this procedure is thoroughly tested and expected to be bug-free.

Currently my code outperforms GMP for at least the following limb sizes: 4…20, 22, 24, 32, 48, 64, 72, 127. I am using Skylake and Ryzen desktops to run benchmarks (CPUs: Core i7-6700 @3.40GHz and Ryzen 7 3800X 8-Core).

# Quick start

```
python2 configure.py
ninja
automagic/test4.exe
automagic/benchm8_official.exe 0
ninja more_benchmarks
automagic/benchm8_basecase.exe 0
automagic/benchm8_toom22_t.exe 0
```
, where 0 is a randomness generator seed.

# Benchmarks

subroutine | tacts
:---: | ---:
mpn_mul_n 8 | 143
gmpn_mul_basecase 8 | 133
mul8_aligned | 104
mpn_mul_n 16 | 489
gmpn_mul_basecase 16 | 478
toom22_xx_broadwell 16 | 402
toom22_broadwell_t 16 | 392
mpn_mul_n 24 | 1086
toom22_broadwell_t 24 | 967
mpn_mul_n 32 | 1678
toom22_deg2_broadwell 32 | 1344

Left column contains subroutine name and size indicator. For instance,
`gmpn_mul_basecase 16` indicates that `gmpn_mul_basecase(target, operand_a, 16, operand_b, 16)` was called.

Right column contains count of CPU tacts (ticks), as returned by `__rdtsc()`.

GMP benchmarks (`..._basecase`, `mpn_mul_n`) are for GMP version 6.1.2, GCC version 9.3.0.

For stable result, don't forget to turn off turbo boost and fix CPU frequency when benchmarking.

# Requirements

1. To generate and compile code, `Python2` interpreter, `ninja` utility, `GCC` C/C++ compiler on X86_64 Linux or compatible OS.

2. To benchmark code, Intel Broadwell or AMD Ryzen or better CPU (capable to `adcx`/`adox`).

# License

For code, [GNU Lesser General Public License version 3](https://www.gnu.org/licenses/lgpl-3.0.en.html).

# Questions and answers

*Q0*. I want to link against `GMP` library hand-installed at `/opt/gmp`.

A0. Supposing `gmp` static library is at `/opt/gmp/lib64/libgmp.a`, call `configure.py` like this:

```
c_compiler=/opt/bin/gcc-9.9 \
cpp_compiler=/opt/bin/g++-9.9 \
flags='-O9 -march=broadwell -static' \
gmp_location=/opt/gmp/lib64/libgmp.a \
/usr/bin/python2 \
configure.py
```

where `/usr/bin/python2` is full path to your `Python2` interpreter, `flags` are `C` and `C++` compiler flags.

*Q1*. Can I use other compiler than `GCC`?

*A1*. Maybe, if it fully supports GCC-style inline `asm`. Oops, `clang` rejects to compile due to [if constexpr problem](https://stackoverflow.com/questions/54899466/constexpr-if-with-a-non-bool-condition).

*Q2*. I found a bug in your code.

*A2*. File bugreport. Include value of input parameters, received output and expected output. Prefererably in a form of compilable C or C++ program.

*Q3*. Can I use your code under OS other than Linux?

*A3*. If this OS uses the same calling convention (System V ABI for 64-bit Unix systems), then probably yes. If not, then some subroutines are unusable.

*Q4*. My benchmark of `GMP` code shows bigger tact numbers than found above in this README.

*A4*. Did you install `GMP` via packet manager? Probably it is not optimized for your Broadwell or Ryzen. Symptom: no `mulx` and/or `adox` instruction in disassembled code.

*Q5*. How do I know that installed `GMP` library is optimized for Broadwell or better CPU?

*A5*. Disassemble it, unpack source code

```
cd /tmp
objdump -d /usr/lib64/libgmp.a > gmp.asm
tar xf /distfiles/gmp-6.2.1.tar.xz
```
, open `gmp.asm`, look at `__gmpn_mul_basecase` subroutine. The code should be similar to source found in
`/tmp/portage/dev-libs/gmp-6.2.1/work/gmp-6.2.1/mpn/x86_64/coreibwl/mul_basecase.asm`. If optimized for Zen2, then source code is in `.../mpn/x86_64/zen1/` directory.

*Q6*. My packet manager installed crippled (not microarch-optimized) GMP. How do I build `GMP` optimized for my CPU?

*A6*. Under Gentoo Linux, use [my ebuild script](https://github.com/krisk0/razin/blob/master/ebuild/gmp-6.2.1-r99.ebuild). If you are not using `portage` packet manager, follow official [build instructions](https://gmplib.org/manual/Installing-GMP.html).

*Q7*. Why do you generate C/assembler code instead of writing it directly?

*A7*. Because it is a lot easier to write and read
```
mulx 8(up), w3, w4
```
than
```
" mulx 8(%[up]), %[w3], %[w4]\n"   \
```
. Note that GMP developers use a loop-optimizing software and `m4` macro processor.

*Q8*. Why do you generate `ninja.build` instead of writing it directly?

*A8*. Because `ninja` is about speed, not user convenience. `ninja.build` is redundant and unreadable, compared to `Makefile`. It is hard and unpleasant to manually edit `ninja.build`.

*Q9*. How do I remove all generated code to start from scratch?

*A9*. `python2 configure.py clean` .
