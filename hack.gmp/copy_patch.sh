src=/home/mE/i/gmp-6.2.1.original
tgt=/tmp/e/gmp

rm -rf $tgt
cp -a $src $tgt

cd $tgt
find . -iname Makefile.in -delete
for m in `find . -name Makefile.am` ; do
    sed  -i '1i PYTHON2 ?= /usr/bin/python2' $m
done
rm configure
sed -i \
    -e 's|enable C++ support [default=no]|enable C++ support [default=yes]|' \
    -e 's|enable_cxx=no|enable_cxx=yes|' \
    -e 's:asm S s c:asm S s c cpp:' \
    configure.ac
p='PREPROCESS_FLAGS = $(DEFS) $(DEFAULT_INCLUDES) $(INCLUDES) $(AM_CPPFLAGS)'
sed -i \
    -e 's:$(CPPFLAGS)::' \
    -e "s:$p.*:$p:" \
    mpn/Makeasm.am
# TODO: patch mpn/README

autoconf
aclocal
automake

export CFLAGS="-O2 -march=native -fno-stack-protector"
export CPPFLAGS="$CFLAGS"

./configure --prefix=/tmp/e/gmp.inst > /tmp/configure-make.log \
    || exit
time make -j7
