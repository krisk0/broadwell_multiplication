import os, sys

def _8_to_6(i, o):
    c = r'\b8\b:6:g mul8_store_once:mul6: mul8_broadwell_store_once_wr:' + \
            'mul6_broadwell_wr:'
    c = ' '.join("-e 's:%s'" % i for i in c.split(' '))
    os.system("sed %s %s > %s" % (c, i, o))

def _8to6(i, o):
    d = r'extern \"C\" {void mul6_zen\(mp_ptr, mp_srcptr up, mp_srcptr\);}'
    c = r'\b8\b:6:g mul8_store_once:mul6: mul8_broadwell_store_once_wr:' + \
            'mul6_broadwell:'
    c = ' '.join("-e 's:%s'" % i for i in c.split(' '))
    c += r' -e "s:#include \"a.*:%s:"' % d
    os.system("sed %s %s > %s" % (c, i, o))

def sed_minus_i(r, o):
    os.system("sed -i s:%s:%s:g %s" % (r[0], r[1], o))

g_a = sys.argv[1:-1]
g_t = sys.argv[-1]

if '8_to_6' in g_a:
    _8_to_6('test8_once.cpp', g_t)

if '8to6' in g_a:
    _8to6('test8_once.cpp', g_t)

for g_p in g_a:
    if g_p.find('-') != -1:
        sed_minus_i(g_p.split('-'), g_t)
