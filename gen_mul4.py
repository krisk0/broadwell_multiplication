"""
mulx p1 p6 p23
vmovq xmm0, rbx               p0
vmovq mem, xmm0               p23
vmovq rbx, xmm0               p5
pinsrq $1, rbx, xmm0          p23 p5
vpextrq $0x1,%%xmm0,tgt       p0 p5
push rbx                      p237 p4
pop rbx                       p23
movq mem, rbx                 p23
movq rbx, mem                 p237 p4
psrldq p5
vperm2i128 $imm,ymm0,ymm0,ymm0 p5
xorq p0156
vperm2i128 p5
add!sub                       p0156 p23
adc!sbb                       p06 p23
adox ?p06
adcx ?p06
vmovdqu mem, ymm0             p23
vmovdqu ymm0, mem             p237 p4
vpxor xmm0, xmm0              p015

parameters: rdi, rsi, rdx, rcx, r8, r9
general purpose registers: rax, rbx, rcx, rdx, rbp, rsi, rdi, rsp and r8-r15
scratch registers: rax, rcx, rdx, rsi, rdi, r8-r11, ymm0-ymm15

a rax
b rbx
c rcx
d rdx
S rsi
D rdi
"""

#TODO: vmovdqu should not be the first command, load v0 directly
g_code = '''
vmovdqu (dd), vC
||save w8
vmovq 128_vC, dd               |                                        dd:=v[0]
mulx (up), w1, w2              |          w2 w1
xorq w8, w8                    |                                        cf:=0  of:=0
mulx 8(up), w3, w4             |          w4 w2+w3 w1
movq w1, (rp)                  |          w4 w2+w3
vpextrq $0x1,128_vC,w1         |                                        w1:=v[1]
mulx 16(up), w5, w6            |          w6 w4+w5 w2+w3
||save w7
adcx w3, w2                    |          w6 w4+w5' w2
mulx 24(up), w7, w8            |          w8 w6+w7 w4+w5' w2
movq w1, dd                    |                          dd:=v[1]
adcx w5, w4                    |          w8 w7+w6' w4 w2

mulx (up), w1, w3              |          w8 w7+w6' w3+w4 w1+w2
vperm2i128 $0x81,vC,vC,vC      |                                        ready v[3] v[2]
adcx w7, w6                    |          w8' w6 w3+w4 w1+w2
adox w2, w1                    |          w8' w6 w3+w4" w1
mulx 16(up), w2, w7            |          w7+w8' w2+w6 w3+w4" w1
vpxor vZ, vZ, vZ
adox w4, w3                    |          w7+w8' w2+w6" w3 w1
movq w1, 8(rp)                 |          w7+w8' w2+w6" w3
mulx 24(up), w1, w4            |          w4 w1+w7+w8' w2+w6" w3
vmovq vZ, w5                   |                                        w5:=0
adcx w8, w7                    |          w4' w1+w7 w2+w6" w3
adox w6, w2                    |          w4' w1+w7" w2 w3
mulx 8(up), w6, w8             |          w4' w1+w7" w2+w8 w3+w6
adcx w5, w4                    |          w4 w1+w7" w2+w8 w3+w6         cf==0
adox w7, w1                    |          w4" w1 w2+w8 w3+w6
vmovq 128_vC, dd               |                                        dd:=v[2]
adcx w6, w3                    |          w4" w1 w2+w8' w3
adox w5, w4                    |          w4 w1 w2+w8' w3               of==0

mulx (up), w5, w6              |          w4 w1 w2+w6+w8' w3+w5
adcx w8, w2                    |          w4 w1' w2+w6 w3+w5
adox w5, w3                    |          w4 w1' w2+w6" w3
mulx 16(up), w5, w8            |          w4+w8 w1+w5' w2+w6" w3
movq w3, 16(rp)                |          w4+w8 w1+w5' w2+w6"
adox w6, w2                    |          w4+w8 w1+w5'" w2
adcx w5, w1                    |          w4+w8' w1" w2
mulx 8(up), w3, w5             |          w4+w8' w1+w5" w2+w3
adcx w8, w4                    |          ' w4 w1+w5" w2+w3
mulx 24(up), w6, w8            |          w8' w4+w6 w1+w5" w2+w3
vmovq vZ, w7                   |                                        w7:=0
adox w5, w1                    |          w8' w4+w6" w1 w2+w3
vpextrq $0x1,128_vC,dd         |                                        dd:=v[3]
adcx w7, w8                    |          w8 w4+w6" w1 w2+w3            cf==0
adox w6, w4                    |          w8" w4 w1 w2+w3
adcx w3, w2                    |          w8" w4 w1' w2

mulx (up), w3, w5              |          w8" w4 w1+w5' w2+w3
adox w7, w8                    |          w8 w4 w1+w5' w2+w3
mulx 16(up), w6, w7            |          w7+w8 w4+w6 w1+w5' w2+w3
adox w3, w2                    |          w7+w8 w4+w6 w1+w5'" w2
adcx w5, w1                    |          w7+w8 w4+w6' w1" w2
mulx 8(up), w3, w5             |          w7+w8 w4+w6+w5' w1+w3" w2
movq w2, 24(rp)                |          w7+w8 w4+w6+w5' w1+w3"
adcx w6, w4                    |          w7+w8' w4+w5 w1+w3"
adox w3, w1                    |          w7+w8' w4+w5" w1
vmovq vZ, w2                   |                                        w2:=0
mulx 24(up), w3, w6            |          w6 w3+w7+w8' w4+w5" w1
adcx w8, w7                    |          w6' w3+w7 w4+w5" w1
adox w5, w4                    |          w6' w3+w7" w4 w1
movq w1, 32(rp)                |          w6' w3+w7" w4
adcx w2, w6                    |          w6 w3+w7" w4
adox w7, w3                    |          w6" w3 w4
movq w4, 40(rp)                |          w6" w3
||restore w7
adox w2, w6                    |          w6 w3
movq w3, 48(rp)                |          w6
||restore w8
movq w6, 56(rp)                |
'''

# mul4_broadwell_macro() wants registers not expressions
g_wr_code = '''
#define mul4_broadwell_macro_wr(r, u, v)
    {
        auto mul4_broadwell_macro_wr_r = r;
        auto mul4_broadwell_macro_wr_u = u;
        auto mul4_broadwell_macro_wr_v = v;
        mul4_broadwell_macro(mul4_broadwell_macro_wr_r,
                mul4_broadwell_macro_wr_u, mul4_broadwell_macro_wr_v);
'''

g_autogenerated_patt = '// This file auto-generated from %s \n\n'

import os, re, sys

def extract_int_vars_name(vv):
    return [v.split(' ')[0] for v in vv]

def extract_ext_vars_name(vv):
    return [v.split(' ')[-1] for v in vv]

def do_it(tgt, code):
    scratch = ['vC x v256', 'vZ x v_z']                   # ymm0, xmm1
    for i in range(1, 9):
        scratch.append('w%s t%s' % (i, i))                # 7 scratch vars w1...w7
    # gcc refuses to allow v_p to change when declared as uint64_t* const. Bug?
    subr_parameters = '@ r_p, @ u_p, @ v_p'.replace('@', 'uint64_t*')
    data = {
            'scratch': scratch,
            'input': ['up u_p', 'rp r_p'],
            'input_output': ['dd +d v_p'],
            'clobber': 'memory cc',
            'macro_name': 'mul4_broadwell_macro',
            'macro_parameters': 'r_p u_p v_p',
            'subroutine_parameters': subr_parameters,
            'headers': 'stdint.h immintrin.h',
            'source': os.path.basename(sys.argv[0]),
            'default_type': 'uint64_t',
            'code_language': 'asm',
            }
    code = code.strip()
    all_vars = extract_int_vars_name(scratch) + extract_int_vars_name(data['input']) + \
            extract_int_vars_name(data['input_output'])
    # type: uint64_t or __m256i
    vars_type = extract_ext_vars_name(scratch)
    # Don't define v_p. Empty string instead of uint64_t
    vars_type = dict((v, '') for v in vars_type)
    vars_type['v256'] = '__m256i'
    vars_type['v_z'] = '__m128i'
    data['vars_type'] = vars_type
    # mulx (up),... -> mulx (%[up]),...
    for v in all_vars:
        code = re.sub(r'\b%s\b' % v, '%%[%s]' % v, code)
    # 128_vC -> %x[vC]
    code = re.sub(r'\b128_vC\b', '%x[vC]', code)
    write_cpp_code(tgt, code, data)
    tgt.write('\n')
    for i in g_wr_code.strip().split('\n'):
        tgt.write(append_backslash(i, 77))
    tgt.write('    }\n')
    tgt.write('\nextern "C" {\nvoid mul4_broadwell(mp_ptr, mp_srcptr, mp_srcptr);\n}')

def write_asm_procedure_header(o, n):
    o.write(' .text\n .globl |\n .type |, @function\n|:\n'.replace('|', n))

def write_asm_inside(tgt, code):
    for i in code.split('\n'):
        j = strip_off_comment(i)
        if not j:
            continue
        if j[-1] != ':':
            tgt.write(' ')
        tgt.write(j + '\n')

def replace_symbolic_vars_name(src, m):
    if isinstance(src, list):
        for i in range(len(src)):
            for k,v in m.items():
                src[i] = re.sub(r'\b%s\b' % k, v, src[i])
        return src
    for k,v in m.items():
        src = re.sub(r'\b%s\b' % k, v, src)
    return src

def do_asm_subroutine(tgt, code):
    code = (code + '\nretq').replace('\n||save ', '\n pushq ').\
            replace('\n||restore ', '\n popq ')
    write_asm_procedure_header(tgt, 'mul4_broadwell')
    change_map = ['vC ymm9', '128_vC xmm9', 'vZ xmm8', 'rp rdi', 'up rsi', 'dd rdx',
            'w8 r12', 'w7 rbx', 'w1 rax', 'w2 rcx', 'w3 r8', 'w4 r9', 'w5 r10', 'w6 r11']
    for i in change_map:
        j = i.split(' ')
        s = r'\b%s\b' % j[0]
        t = '%' + j[1]
        code = re.sub(s, t, code)
    write_asm_inside(tgt, code)

def append_backslash(x, length):
    if isinstance(x, list):
        x = ''.join(x)
    if x.find(r':\n') != -1:
        # delete space before label
        x = x.replace('" ', '"')
    l = len(x)
    if l < length - 1:
        x += ' ' * (length - 1 - l)
    return x + '\\\n'

def strip_off_comment(i):
    p = i.find('|')
    if p != -1:
        i = i[:p]
    return i.strip()

def cutoff_comments(s):
    result = [strip_off_comment(x) for x in s.split('\n')]
    return [x for x in result if x]

def define_asm_vars(i):
    try:
        d = i['vars_type']
    except:
        return []
    default,result = [],[]
    for k,v in d.items():
        if v:
            result.append('  %s %s;' % (v, k))
        else:
            default.append(k)
    if not default:
        return result
    default.sort()
    result.append('  %s %s;' % (i['default_type'], ', '.join(default)))
    return result

def dress_asm_lines(xx):
    '''
    Cuts off comment after | .

    Prepends apostrophe" and space. Appends \n and apostrophe
    '''
    result = []
    for x in xx:
        y = strip_off_comment(x)
        if y:
            result.append(r'   " %s\n"' % y)
    return result

def split_cpp_line_slave(line, delimeters, head_space, total_length):
    '''
    Breaks line respecting delimeters
    '''
    result = []
    while 1:
        if len(line) <= total_length:
            return result + [line]
        start = line[:total_length]
        p = -1
        for d in delimeters:
            p = start.rfind(d)
            if p > 0:
                break
        if p == -1:
            # failed to break line
            return result + [line]
        p += 1
        result.append(line[:p])
        line = (' ' * head_space) + line[p:]

def split_cpp_line(ii, delimeters, head_space, overhang, total_length):
    result = []
    for i in ii:
        j = (' ' * head_space) + i
        result += split_cpp_line_slave(j, delimeters, head_space + overhang, total_length)
    return result

def asm_epilog_scratch_slave(data, extra):
    '''
    returns [internal]"=&register"(external)
    '''
    data = data.split(' ')
    if len(data) == 2:
        data = [data[0], 'r', data[1]]
    if data[2] == '-':
        return '[%s]"%s%s"' % (data[0], extra, data[1])
    p = '[%s]"@%s"(%s)'.replace('@', extra)
    return p % tuple(data)

def asm_epilog_scratch(data, field):
    result = []
    if field == 'scratch':
        early_clobber = '=&'
    else:
        early_clobber = ''
    try:
        ii = data[field]
    except:
        ii = []
    jj = []
    if field == 'scratch':
        try:
            jj = data['input_output']
        except:
            pass
    for j in jj:
        result.append(asm_epilog_scratch_slave(j, ''))
    for i in ii:
        result.append(asm_epilog_scratch_slave(i, early_clobber))
    return ' : ' + ', '.join(result)

def asm_epilog_clobber(data):
    try:
        clobber = data['clobber'].split(' ')
    except:
        clobber = []
    # TODO: sort ymm by numbers so that ymm9 < ymm10 < ymm11
    clobber.sort(reverse=True)
    return ' : ' + ', '.join(['"%s"' % c for c in clobber]) + ');'

def asm_epilog(i):
    result = [asm_epilog_scratch(i, 'scratch'), asm_epilog_scratch(i, 'input'),
            asm_epilog_clobber(i)]
    return split_cpp_line(result, ',', 2, 2, i['macro_line_length'] - 2)

def dress_asm_stmt(stmt, info):
    stmt = [' {'] + \
            define_asm_vars(info) + \
            ['  __asm__ __volatile__ ('] + \
            dress_asm_lines(stmt.split('\n'))
    return stmt + asm_epilog(info) + [' }']

def get_macro_parameters(i):
    try:
        pp = i['macro_parameters'].split(' ')
    except:
        return ''
    return ', '.join(pp)

def write_macro_code(o, macro_body, info):
    if not info.has_key('macro_line_length'):
        info['macro_line_length'] = 77
    l = ['#define %s(' % info['macro_name']]
    pp = get_macro_parameters(info)
    if pp:
        l.append(pp)
    l = append_backslash(l + [')'], info['macro_line_length'])
    o.write(l)
    try:
        l = info['code_language']
    except:
        l = None
    if l == 'asm':
        macro_body = dress_asm_stmt(macro_body, info)
    if not isinstance(macro_body, list):
        macro_body = macro_body.split('\n')
    # don't write backslash after last line
    last = macro_body[-1]
    macro_body = macro_body[:-1]
    for l in macro_body:
        if not l:
            continue
        o.write(append_backslash(l, info['macro_line_length']))
    o.write(last + '\n')

def write_subroutine(f, data):
    f.write('\nvoid\n%s(' % data['subroutine_name'])
    try:
        f.write(data['subroutine_parameters'])
    except:
        pass
    f.write(') {\n')
    f.write('    %s(%s);\n' % (data['macro_name'], get_macro_parameters(data)))
    f.write('}\n')

def write_cpp_code(o, macro_body, info):
    try:
        o.write(g_autogenerated_patt % info['source'])
    except:
        pass
    try:
        hh = info['headers'].split(' ')
        for h in hh:
            o.write('#include <%s>\n' % h)
        o.write('\n')
    except:
        pass
    if info.has_key('macro_name'):
        write_macro_code(o, macro_body, info)
    if info.has_key('subroutine_name'):
        write_subroutine(o, info)

g_amp_save_pattern = re.compile(r'@save (\S+)\b')
def replace_amp_save(src):
    while 1:
        m = re.search(g_amp_save_pattern, src)
        if not m:
            return src
        src = src.replace(m.group(0), 'movq %s, -8(%%rsp)' % m.group(1))

g_amp_restore_pattern = re.compile(r'@restore (\S+)\b')
def replace_amp_restore(src):
    while 1:
        m = re.search(g_amp_restore_pattern, src)
        if not m:
            return src
        src = src.replace(m.group(0), 'movq -8(%rsp), ' + m.group(1))

g_positive_ofs_pattern = re.compile(r' \+([0-9]+)\(')
def replace_positive_offsets(code):
    '''
    replace +x( by 8*x(
    '''
    while 1:
        m = re.search(g_positive_ofs_pattern, code)
        if not m:
            return code
        n = int(m.group(1)) * 8
        code = code.replace(m.group(0), ' %s(' % n)

g_negative_ofs_pattern = re.compile(r' \-([0-9]+)\(')
def replace_negative_offsets(code):
    '''
    replace +x( by 8*x(
    '''
    minus_replacer = 'MiNuS'
    while 1:
        m = re.search(g_negative_ofs_pattern, code)
        if not m:
            return code.replace(minus_replacer, '-')
        n = int(m.group(1)) * 8
        code = code.replace(m.group(0), ' %s%s(' % (minus_replacer, n))

def handle_dec(dec, code):
    patt = re.compile(dec + r' \b(.+)\b')
    while 1:
        m = re.search(patt, code)
        if not m:
            return code
        code = code.replace(m.group(0), 'lea -1(@), @'.replace('@', m.group(1)))

g_save_pattern = re.compile('.save w(.)')
def save_registers(xx):
    # returns dictionary that lists saved registers
    n = len(xx)
    result = {}
    for i in range(n):
        x = xx[i]
        m = g_save_pattern.match(x)
        if not m:
            continue
        m = m.group(1)
        if x[0] == '@':
            xx[i] = 'push w' + m
            result['w' + m] = None
        else:
            xx[i] = 'movq w@, s@'.replace('@', m)
            result['w' + m] = 's' + m
    return result

g_xmm_save_pattern = re.compile('!save (.+)')
def save_registers_in_xmm(cc, s0):
    result = dict()
    for i in range(len(cc)):
        c = cc[i]
        m = g_xmm_save_pattern.match(c)
        if not m:
            continue
        m = m.group(1)
        try:
            t = result[m]
        except:
            t = '%%xmm%s' % s0
            s0 -= 1
            result[m] = t
        cc[i] = 'movq %s, %s' % (m, t)
    return result

def composition(a, b):
    r = a[:]
    for i in range(len(b)):
        r[i] = b[a[i]]
    return r

def invert_permutation(s):
    r = s[:]
    for i in range(len(s)):
        r[s[i]] = i
    return r

def insert_restore(cc, m):
    for k,v in m.items():
        '''
        k = name of register to restore
        v = name of xmm register
        must insert movq v, k if necessary
        '''
        insert_restore_3arg(cc, k, v)

def insert_restore_3arg(cc, r, x):
    p = re.compile(r'\b%s\b' % r)
    to_insert = 'movq %s, %s' % (x, r)
    for i in range(len(cc) - 1, -1, -1):
        j = cc[i]
        if p.search(j):
            if j != to_insert:
                # append or insert at index i+1
                cc.insert(i + 1, to_insert)
            return

def guess_subroutine_name(target_file_name):
    n = os.path.basename(target_file_name)
    p = n.find('.')
    if p != -1:
        n = n[:p]
    return n

def swap_adox_adcx(dd):
    rr = []
    for d in dd:
        x = d.replace('adox', 'ADCX').replace('adcx', 'adox').\
                replace('ADCX', 'adcx')
        rr.append(x)
    return rr

def replace_symbolic_names_wr(code, m):
    r = {}
    for x in m.split(' '):
        y = x.split(',')
        r[y[0]] = '%' + y[1]
    return replace_symbolic_vars_name(code, r)

def starting_from(cc, s):
    i = [i for i in range(len(cc)) if cc[i].find(s) != -1][0]
    return cc[i:]

def replace_in_string_array(cc, el, rr):
    return '\n'.join(cc).replace(el, rr).split('\n')

def save_in_xmm(code, f):
    for i in range(len(code)):
        m = g_xmm_save_pattern.match(code[i])
        if not m:
            continue
        m = m.group(1)
        code[i] = 'movq %s, %s' % (m, f[m])

if __name__ == '__main__':
    g_out = sys.argv[1]

    # create one of two files: .h or .s
    if g_out[-1] == 'h':
        with open(g_out, 'wb') as g_file:
            do_it(g_file, g_code)
        sys.exit(0)

    """
    GCC inserts extra lines:
     push %rbp
     vzeroupper
    (disrespecting -fomit-frame-pointer).

    So we write complete subroutine in assembler
    """
    with open(g_out, 'wb') as g_file:
        do_asm_subroutine(g_file, g_code)
