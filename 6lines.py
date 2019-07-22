#!/usr/bin/pypy

'''
This script helps in debugging Toom-Cook multiplication.

take 6 lines from test_toom22_xx.exe stdout:

a=
b=
at -1:
at  0:
at  i:
a*b=

check if half-size multiplication, and final result was correct
'''

import sys

def read_line(f, c):
    result = f.readline()
    p = result.find(c)
    return result[1 + p:].strip()

def read_input(name):
    with open(name, 'rb') as i:
        a = read_line(i, '=')
        b = read_line(i, '=')
        qm = read_line(i, ':')
        q0 = read_line(i, ':')
        qi = read_line(i, ':')
        r = read_line(i, '=')
    globals()['size'] = 4 * len(a)
    globals()['a'] = int(a, 0x10)
    globals()['b'] = int(b, 0x10)
    globals()['qm'] = int(qm, 0x10)
    globals()['q0'] = int(q0, 0x10)
    globals()['qi'] = int(qi, 0x10)
    globals()['qr'] = int(r, 0x10)

read_input(sys.argv[1])
size_half = size / 2

a0 = a % 2**size_half
a1 = a >> size_half
b0 = b % 2**size_half
b1 = b >> size_half

fmt = '%0@X'.replace('@', '%s' % (size / 4))

gm = (a0 - a1) * (b0 - b1)
g0 = a0 * b0
gi = a1 * b1
gr = a * b

if gm != qm:
    print 'mismatch at -1'
    print 'good = %X' % gm
    print 'baad = %X' % qm

if g0 != q0:
    print 'mismatch at 0'
    print 'good = %X' % g0
    print 'baad = %X' % q0

if gi != qi:
    print 'mismatch at -1'
    print 'good = %X' % gi
    print 'baad = %X' % qi

if qr != gr:
    print 'final result mismatch'
    print 'good = %X' % gr
    print 'baad = %X' % qr
