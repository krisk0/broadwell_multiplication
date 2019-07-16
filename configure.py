import os, sys, re

if (len(sys.argv) == 2) and (sys.argv[1] == 'clean'):
    os.system('rm -rf build.ninja automagic .ninja*')
    sys.exit(0)

g_opt = {
        'flags': '-O3 -march=broadwell -fomit-frame-pointer -static -fmax-errors=3 -std=gnu++17',
        'c_compiler': 'gcc',
        'cpp_compiler': 'g++',
        'gmp_location': '-lgmp',
        'python': sys.executable,
        }

g_always_used_script = 'gen_mul4.py'

g_asm_source_pattern = re.compile(r'.+ (\S+)\.s\b')
def s_to_o(src):
    '''
    replace smth.s with $o/smth.o
    
    arrange for appending rule for $o/smth.o
    '''
    global g_s_to_o
    src += ' '
    while 1:
        m = re.search(g_asm_source_pattern, src)
        if not m:
            return src.rstrip()
        m = m.group(1)
        g_s_to_o.add(m)
        src = src.replace(m + '.s', '$o/' + m + '.o')

def append_gen_mul4(x):
    '''
    append g_always_used_script to x, if necessary
    '''
    y = x.split(' ')
    if y[-1] == g_always_used_script:
        return x
    return x + ' ' + g_always_used_script

g_expand_0_pattern = re.compile(r'(\S+): \b(\S+)\b$')
g_expand_1_pattern = re.compile(r'(\S+): \b(\S+)\b \[(.+)\]')
g_expand_2_pattern = re.compile(r'(\S+): (.+)')
def expand_ampersand(src):
    src = src.rstrip().replace('@int_h0_plain', g_int_h0_plain)
    src = src.rstrip().replace('@int_h0', g_int_h0)
    src = src.replace('@int_h', g_int_h)
    if src.find(': create_exe ') != -1:
        return [s_to_o(src)]
    '''
    turn
        tgt.h: script
    into
        build $o/tgt.h: create_c_code gen_script.py
    
    turn
        smth_@.s: script [x y]
    into
        build $o/smth_x.s: create_c_code gen_script.py
            extra = x
        build $o/smth_y.s: create_c_code gen_script.py
            extra = y
            
    turn
        target.h: srcA.h srcB.h ...
    into
        build $o/target.h: catenate $o/srcA.h $o/srcB.h ...
    '''
    m = g_expand_0_pattern.match(src)
    if m:
        return [append_gen_mul4('build $o/%s: create_c_code gen_%s.py' % m.groups())]
    m = g_expand_1_pattern.match(src)
    if m:
        tgt = []
        for x in m.group(3).split(' '):
            r = m.group(1).replace('@', x)
            tgt += [append_gen_mul4('build $o/%s: create_c_code gen_%s.py' % \
                    (r, m.group(2))), '    extra = %s' % x]
        return tgt
    m = g_expand_2_pattern.match(src)
    if m:
        ss = ['$o/' + i for i in m.group(2).split(' ')]
        return [('build $o/%s: catenate ' % m.group(1)) + ' '.join(ss)]
    return [src]

g_exe_rule_pattern = re.compile(r'(\S+)\.exe: (.+)')
def exe_rule(src):
    '''
    turn
        some.exe: src0 src1 ...
    into
        build $o/some.exe: create_exe src0 src1 ...
    '''
    m = re.match(g_exe_rule_pattern, src)
    if not m:
        return src
    return 'build $o/%s.exe: create_exe %s' % m.groups()

g_option_in_brackets_pattern = re.compile(r'(.+) \[\+(\S+) (.+)\]$')
def option_in_brackets(src):
    '''
    turn
        smth [+var add]
    into
        smth
            var = $var add
    '''
    m = g_option_in_brackets_pattern.match(src)
    if not m:
        return src
    result = '%s = $%s %s' % (m.group(2), m.group(2), m.group(3))
    return m.group(1) + '\n    ' + result + '\n'

def expand_line(src):
    tgt = exe_rule(src.rstrip())
    tgt = option_in_brackets(tgt)
    if tgt.find('\n') != -1:
        # expand 1st line, send 2nd line as is
        tgt = tgt.split('\n')
        e0 = '\n'.join(expand_ampersand(tgt[0]))
        tgt = e0 + '\n' + tgt[1]
    else:
        tgt = '\n'.join(expand_ampersand(tgt))
    if (not tgt) or (tgt[-1] != '\n'):
        tgt += '\n'
    return tgt

def do_it(o, i):
    for k,v in g_opt.items():
        o.write('%s = %s\n' % (k, v))
    o.write('\n')

    prev = None
    for j in i:
        if len(j) < 2:
            o.write(j)
            continue
        if j[-2] == '$':
            now = j[:-2]
            if prev is None:
                prev = now
            else:
                # ignore leading spaces in continuation
                prev += now.lstrip()
            continue
        if prev:
            # ignore leading spaces in continuation
            k = expand_line(prev + j.lstrip())
            prev = None
        else:
            k = expand_line(j)
        o.write(k)
    
    if g_s_to_o:
        o.write('\n')
        for i in g_s_to_o:
            o.write('build $o/@.o: compile_c_code $o/@.s\n\n'.replace('@', i))

g_space_smth_pattern = re.compile(' .*')
def escape_dot(i):
    return re.sub(g_space_smth_pattern, '', i).replace('.', r'\.')

# respect user choice
g_vv = g_opt.keys()
for v in g_vv:
    if v == 'python':
        continue
    u = os.getenv(v)
    if u:
        g_opt[v] = u

# magic headers
g_int_h_pattern = re.compile(r'.+\-.+\.h')
g_int_h = sorted([v for v in os.listdir('.') if g_int_h_pattern.match(v)])
g_int_h = ' '.join(g_int_h)
g_int_h0 = escape_dot(g_int_h)
g_int_h0_plain = g_int_h0.replace('\\', '')

g_s_to_o = set()
with open('build.ninja.in', 'rb') as g_i, open('build.ninja', 'wb') as g_o:
    do_it(g_o, g_i)
