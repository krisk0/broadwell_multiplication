import os, re, sys
sys.dont_write_bytecode = 1

import gen_mul4 as P

"""
g_code = '''
movq 0(up), w0
movq 8(up), w1
sub 0(vp), w0
sbb 8(vp), w1
movq 16(up), w2
movq 24(up), w3
movq w0, 0(rp)
movq w1, 8(rp)
sbb 16(vp), w2
sbb 24(vp), w3
--
movq w2, 16(rp)
movq w3, 24(rp)
'''.strip()

g_ofs_patt = re.compile(r'(.+) ([0-9]+)(\(\S+\))(.*)')
def increase_offset(src, ofs):
    m = g_ofs_patt.match(src)
    if not m:
        return src
    i = int(m.group(2)) + ofs
    return m.group(1) + (' %s%s%s' % (i, m.group(3), m.group(4)))

def form_code_slave(tgt, ss, offset, last):
    for s in ss:
        if s == '--':
            if last:
                # don't need to load two numbers
                continue
            tgt.append('movq %s(up), w0' % (32 + offset))
            tgt.append('movq %s(up), w1' % (40 + offset))
            continue
        t = increase_offset(s, offset)
        tgt.append(t)

g_head_pattern = re.compile(r'.*movq 8\(up\), w1')
def form_code(source, pieces):
    code = []
    src = source.split('\n')
    ofs = 0
    for i in range(pieces):
        if i == 1:
            # replace sub with sbb, omit two instructions at start
            src = source.replace('sub', 'sbb').split('\n')[2:]
        form_code_slave(code, src, ofs, i + 1 == pieces)
        ofs += 32
    return code

def do_it(tgt):
    # TODO: call mpn_sub_n() for big n
    assert g_n % 4 == 0
    scratch = ['w%s w_%s' % (i, i) for i in range(4)]
    data = {
            'macro_name': 'mpn_sub%s' % g_n,
            'input': ['rp r_p', 'up u_p', 'vp v_p'],
            'scratch': scratch,
            'clobber': 'cc memory',
            'default_type': 'uint64_t',
            'macro_parameters': 'r_p u_p v_p',
            'source': os.path.basename(sys.argv[0]),
            'code_language': 'asm',
            'default_type': 'uint64_t',
            }
    code = form_code(g_code, g_n // 4)
    code = '\n'.join(code)
    code = code.replace(' 0(', ' (')

    all_vars = P.extract_int_vars_name(data['scratch']) + \
            P.extract_int_vars_name(data['input'])
    for v in all_vars:
        code = re.sub(r'\b%s\b' % v, '%%[%s]' % v, code)

    vars_type = dict((v, '') for v in P.extract_ext_vars_name(scratch))
    data['vars_type'] = vars_type

    P.write_cpp_code(tgt, code, data)
"""

g_code_0 = '''
movq (up), w0
movq 8(up), w1
movq 16(up), w2
movq 24(up), w3
subq (vp), w0
sbbq 8(vp), w1                       | (w3) (w2) w1 w0
'''

g_code_m = '''
sbbq +16(vp), w2
sbbq +24(vp), w3
movq w0, +0(rp)
movq w1, +8(rp)                      | w3 w2
movq +32(up), w0
movq +40(up), w1                     | (w1) (w0) w3 w2
movq w2, +16(rp)
movq w3, +24(rp)                     | (w1) (w0)
movq +48(up), w2
movq +56(up), w3                     | (w3) (w2) (w1) (w0)
sbbq +32(vp), w0
sbbq +40(vp), w1                     | (w3) (w2) w1 w0
'''

g_code_e = '''
sbbq +16(vp), w2
sbbq +24(vp), w3                     | w3 w2 w1 w0
movq w0, +0(rp)
movq w1, +8(rp)
movq w2, +16(rp)
movq w3, +24(rp)
'''

g_tail_6 = '''
sbbq 16(vp), w2
sbbq 24(vp), w3                      | w3 w2 w1 w0
movq w0, (rp)
movq w1, 8(rp)                       | w3 w2
movq 32(up), w0
movq 40(up), w1                      | (w1) (w0) w3 w2
movq w2, 16(rp)
movq w3, 24(rp)                      | (w1) (w0)
sbbq 32(vp), w0
sbbq 40(vp), w1
movq w0, 32(rp)
movq w1, 40(rp)
'''

g_ofs_patt = re.compile(r' \+([0-9]+)(\(.+\))')
def update_ofs_slave(src, offset):
    while 1:
        m = re.search(g_ofs_patt, src)
        if not m:
            return src
        k = int(m.group(1))
        src = src.replace(m.group(0), (' %s' % (offset + k)) + m.group(2))

def update_ofs(src, offset):
    tgt = []
    for l in src.split('\n'):
        tgt.append(update_ofs_slave(l, offset))
    return '\n'.join(tgt)

def do_it_6(tgt, data):
    code = (g_code_0 + g_tail_6).strip()
    all_vars = P.extract_int_vars_name(data['scratch']) + \
            P.extract_int_vars_name(data['input'])
    for v in all_vars:
        code = re.sub(r'\b%s\b' % v, '%%[%s]' % v, code)

    vars_type = dict((v, '') for v in P.extract_ext_vars_name(data['scratch']))
    data['vars_type'] = vars_type

    P.write_cpp_code(tgt, code, data)

def do_it(tgt):
    data = {
            'macro_name': 'mpn_sub%s' % g_n,
            'input': ['rp r_p', 'up u_p', 'vp v_p'],
            'scratch': ['w%s w_%s' % (i, i) for i in range(4)],
            'clobber': 'cc memory',
            'default_type': 'uint64_t',
            'macro_parameters': 'r_p u_p v_p',
            'source': os.path.basename(sys.argv[0]),
            'code_language': 'asm',
            'default_type': 'uint64_t',
            }
    if g_n == 6:
        do_it_6(tgt, data)
        return
    # TODO: call mpn_sub_n() for big n
    assert g_n % 4 == 0
    loop_count = g_n / 4 - 1
    code = g_code_0.strip()
    ofs = 0
    for i in range(loop_count):
        code += '\n' + update_ofs(g_code_m, ofs)
        ofs += 32
    code += '\n' + update_ofs(g_code_e, ofs)
    code = code.replace(' 0(', ' (')
    all_vars = P.extract_int_vars_name(data['scratch']) + \
            P.extract_int_vars_name(data['input'])
    for v in all_vars:
        code = re.sub(r'\b%s\b' % v, '%%[%s]' % v, code)

    vars_type = dict((v, '') for v in P.extract_ext_vars_name(data['scratch']))
    data['vars_type'] = vars_type

    P.write_cpp_code(tgt, code, data)

if __name__ == '__main__':
    g_n = int(sys.argv[1])
    g_tgt = sys.argv[2]
    
    try:
        os.makedirs(os.path.dirname(g_tgt))
    except:
        pass
    
    with open(g_tgt, 'wb') as g_o:
        do_it(g_o)
