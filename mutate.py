import os, sys

def _8_to_6(i, o):
    c = r'\b8\b:6:g mul8_store_once:mul6: mul8_broadwell_store_once_wr:mul6_broadwell_wr:'
    c = ' '.join("-e 's:%s'" % i for i in c.split(' '))
    os.system("sed %s %s > %s" % (c, i, o))

if sys.argv[1] == '8_to_6':
    _8_to_6('test8_once.cpp', sys.argv[2])
    sys.exit(0)

assert 0
