'''
Scans for .py scripts in $MPN_PATH and sym-links them into mpn directory.

Arranges it so they are run when necessary (by modifying mpn/Makefile)
'''

import os, shutil, sys

def read_rules(res, src):
    with open(src, 'rb') as i:
        res += [j for j in i]

def copy_py_files(res, tgt, src):
    for x in os.listdir(src):
        y = x[:-3]
        if y == '.py':
            res[0].append(y)
            shutil.copy(src + '/' + x, tgt)
        elif x[:-5] == '.rule':
            read_rules(res[1], src + '/' + x)

def scan_for_files(base, path):
    result = [[],[]]
    for i in path:
        copy_py_files(result, base, base + '/' + i)
    return result

'''
create makefile-style rules:
 python2 name.s.py name.s
 python2 name.h.py name.h
'''
def implicit_rules(ff):
    result = []
    for f in ff:
        g = f[:-2]
        if (g == '.s') or (g == '.h'):
            result.append('%s: %s.py\n' % (f, f))
            result.append('\t$(PYTHON2) $< $@\n\n')

def modify_makefile(tgt, src):
    with open(tgt, 'ab') as o:
        for i in src:
            o.write(i)

g_mpn = os.path.dirname(sys.argv[0])
g_path = sys.argv[1:]

g_run_us = scan_for_files(g_mpn, g_path)
# TODO: don't create implicit rule if rule to make the file already exists
g_run_us[1] += implicit_rules(g_run_us[0])
modify_makefile(g_mpn + 'Makefile', g_run_us[1])
