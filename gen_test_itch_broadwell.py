import sys

with open(sys.argv[1], 'wb') as o:
    for b in 12, 28:
        for n in range(1, 129):
            o.write('do_test<%s, %s>();\n' % (n, b))
