set -e

src=/home/mE/i/gmp-6.2.1.original
tgt=/tmp/e/gmp
here=`realpath $0|xargs dirname`

[ -d $tgt ] && { cd $tgt; rm -rf * ; }
mkdir -p $tgt/mpn/automagic
cp -a $src/* $tgt

cd $tgt
find . -iname Makefile.in -delete
for m in `find . -name Makefile.am` ; do
    sed -i '1i PYTHON2 ?= python2' $m
done
sed -i '1i MPN_PATH = @MPN_PATH@' Makefile.am

rm configure
sed -i \
    -e 's|enable C++ support [default=no]|enable C++ support [default=yes]|' \
    -e 's|enable_cxx=no|enable_cxx=yes|' \
    -e 's:asm S s c:\0 cpp:' \
    -e '/^CL_AS_NOEXECSTACK/i MPN_PATH="$path"' \
    configure.ac

echo 'AC_SUBST(MPN_PATH)' >> configure.ac
# For cpp suffix to be known, need dummy .cpp along with dummy .cc
cp cxx/dummy.cc cxx/dummyy.cpp
sed -i 's:cxx/dummy.cc$:\0 cxx/dummyy.cpp:' Makefile.am
p='PREPROCESS_FLAGS = $(DEFS) $(DEFAULT_INCLUDES) $(INCLUDES) $(AM_CPPFLAGS)'
sed -i \
    -e 's:$(CPPFLAGS)::' \
    -e "s:$p.*:$p:" \
    mpn/Makeasm.am
# TODO: patch mpn/README
# TODO: copyright?
cp $here/mul_n.cpp mpn/x86_64/coreibwl/
# TODO: use 2 parameters MUL_TOOM33_SYMM and MUL_TOOM33_ASYMM instead of
#  MUL_TOOM33_THRESHOLD. Change gen_mpn_mul_n_switch.py, too.
sed 's:e AMD_ZEN 0:e AMD_ZEN 1:' mpn/x86_64/coreibwl/mul_n.cpp > \
    mpn/x86_64/zen/mul_n.cpp
cp $here/{gen_mpn_mul_n_switch,initiate_unroll}.py mpn/
t=mpn/automagic/toom22.hh
grep -v bordeless-alloc.h $here/../toom22_generic.h > $t
sed -i                            \
    -e '/^#if __znver2__/,/^$/d'   \
    -e '/^#if AMD_ZEN/,/^#endif$/d' \
    $t
sed -i "2i // This file modified by `basename $0`" $t
cat $here/mpn.makefile >> mpn/Makefile.am
cat $here/root.makefile >> Makefile.am

rm -f /tmp/copy_magic.cout
python2 $here/copy_magic.py $tgt/mpn | tee /tmp/copy_magic.cout
exit

autoconf
aclocal
automake

# No more dummy files, copy .cpp rules into mpn/Makefile
python2 $here/copy_makefile_rule.py .cpp.o,.cpp.lo Makefile.in mpn/Makefile.in
# , and make .cpp suffix known
sed -i 's:.asm .c .lo:.asm .c .cpp .lo:' mpn/Makefile.in
# , and copy ...CXX... vars
sed -n '/^CXXCOMPILE/,/^am__v_CXXLD_1/p' Makefile.in >> mpn/Makefile.in

# GNU automake inserts both CFLAGS and CPPFLAGS into COMPILE variable, then uses
#  the variable to compile C code. Is this bug or feature?

export CFLAGS="-O2 -march=native -fno-stack-protector"
export CPPFLAGS="$CFLAGS"

time ./configure --prefix=${tgt}.inst > /tmp/configure-make.log
time make -j7 >> /tmp/configure-make.log
