'''
count scratch size for Tomm-Cook-22 algorithm using recurrent formula

s(x) = 0, x < 12
s(2*h+1) = max(3*h+s(h), 2*h+s(h-1))
s(2*h) = 2*h + s(h)
'''

import os, sys

g_raw_output = os.getenv('out', 0)
g_raw_output = (g_raw_output == 'h')

if len(sys.argv) == 2:
    g_max = int(sys.argv[1])
else:
    g_max = 129

g_s = [0 for i in range(g_max)]

for i in range(12, g_max):
    h = i // 2
    if i & 1:
        g_s[i] = max(3 * h + g_s[h], 2 * h + g_s[h - 1])
        if g_raw_output and (2 * h + g_s[h - 1] > 3 * h + g_s[h]):
            print 'max() 2nd value greater, i =', i
    else:
        g_s[i] = i + g_s[h]

if g_raw_output:
    for i in range(12, g_max):
        print '%3s: %s' % (i, g_s[i])
else:
    print 'C-style output not implemented'
