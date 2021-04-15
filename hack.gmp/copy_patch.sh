set -e

src=/home/mE/i/gmp-6.2.1.original
tgt=/tmp/e/gmp

mkdir -p `dirname $tgt`
rm -rf $tgt
cp -a $src $tgt
here=`realpath $0|xargs dirname`

cd $tgt
find . -iname Makefile.in -delete
for m in `find . -name Makefile.am` ; do
    sed -i '1i PYTHON2 ?= python2' $m
done
rm configure
sed -i \
    -e 's|enable C++ support [default=no]|enable C++ support [default=yes]|' \
    -e 's|enable_cxx=no|enable_cxx=yes|' \
    -e 's:asm S s c:\0 cpp:' \
    configure.ac
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

autoconf
aclocal
automake

export CFLAGS="-O2 -march=native -fno-stack-protector"
export CPPFLAGS="$CFLAGS"

# No more dummy files, copy .cpp rules into mpn/Makefile
python2 $here/copy_makefile_rule.py .cpp.o,.cpp.lo Makefile.in mpn/Makefile.in
# ... and make .cpp suffix known
sed -i 's:.asm .c .lo:.asm .c .cpp .lo:' mpn/Makefile.in
# ... and copy ...CXX... vars
sed -n '/^CXXCOMPILE/,/^am__v_CXXLD_1/p' Makefile.in >> mpn/Makefile.in

time ./configure --prefix=${tgt}.inst > /tmp/configure-make.log
time make -j7 >> /tmp/configure-make.log
