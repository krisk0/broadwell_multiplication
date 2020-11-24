import sys

with open(sys.argv[1], 'wb') as o:
    for i in range(1, 129):
        o.write('do_test<%s>();\n' % i)
