'''
Scans for .py scripts in $MPN_PATH and sym-links them into mpn directory.

Arranges it so they are run when necessary (by modifying mpn/Makefile)
'''

import os, sys

g_mpn = os.path.abspath(os.path.dirname(sys.argv[0]))
g_path = sys.argv[1:]

with open('/tmp/i.result', 'wb') as o:
    o.write('here = %s\n' % g_mpn)
    o.write('path = %s\n' % ','.join(g_path))

'''
g_run_us = scan_for_files(g_path)
modify_makefile(g_mpn + 'Makefile', g_run_us)
'''
