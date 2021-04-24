'''
Copy some gen_*.py scripts to two directories.

Rename files so foo.s.py makes foo.s, foo.h.py makes foo.h .

Patch mul4.s.py so subroutine name is __g prepended to old name.

Multiplication subroutines should be called __gmpn_mul_N (for instance
 __gmpn_mul_11).

Non-trivial makefile rules go to all.rule. Example:
$(o)/toom22_interpolate_16.s: $(o)/toom22_interpolate_16_raw.s $(o)/mpn_add_2_4arg.s
    cat $^ > $@

Put into the two directories
 * python scripts
 * piece of makefile make.rules
'''

import os, re, shutil, sys

g_ignored_dependency = ['addmul_1_adox.o', 'cstdint_gmp.h', 'mul7_t03.o']

g_tgt_dir = sys.argv[1] + '/'
g_output_dir = [g_tgt_dir + 'x86_64/coreibwl', g_tgt_dir + 'x86_64/zen']
g_ninja = os.path.realpath(os.path.dirname(sys.argv[0]) + '/../build.ninja')
g_src_dir = os.path.dirname(g_ninja)

def is_banned(f):
    f = os.path.basename(f)
    return f in g_ignored_dependency

'''
Extract rule from ninja file. Return everything after :, including extra line if it
 is there
'''
def extract_ninja_rule(i, p):
    while True:
        j = i.readline()
        if not j:
            die('rule for not found')
        if p.match(j):
            break
    p = j.find(':')
    res = j[p + 1:].lstrip()
    # maybe add next line
    j = i.readline()
    i.seek(0)
    if (j == '') or (j[0] != ' '):
        return res.rstrip()
    return res + j.strip()        # extra line delimetered by '\n'

'''
List dependencies that start with $o, omit directory. Skip blacklisted files or those
 whose name contains 'test'.
'''
def extract_dep_0(rule):
    res = []
    for r in rule.split(' '):
        if (r[:3] == '$o/'):
            s = r[3:]
            if (s.find('test') == -1) and (not is_banned(s)):
                res.append(s)
    return res

'''
Last line of list ss might contain '\n' + addition where addition is either
 'extra = smth' or 'extra = $extra smth'

Separate ss from addition. Return tuple cleaned_ss,smth
'''
def takeout_extra(ss):
    j = ' '.join(ss)
    p = j.find('\n')
    if p == -1:
        return ss,''
    extra = j[1 + p:].split(' ')[-1]
    j = j[:p]
    return j.split(' '),extra

'''
Find ninja rules that create $o/d and its dependencies. Store trivial rules in the
 form (script,target) into pp. Store non-trivial rules into rr in Makefile style.

Omit compilation rules .s -> .o .
'''
def ninja_to_make(pp, rr, inp, d):
    while True:
        p = re.compile(r'build \$o/%s:' % d)
        r = extract_ninja_rule(inp, p).split(' ')
        if r[0] != 'compile_c_code':
            break
        d = r[1]
        if d[:3] != '$o/':
            return                 # happens for addmul_1_adox.o
        d = d[3:]
    if r[0] == 'catenate':
        r = r[1:]
        r = [x for x in r if not is_banned(x)]
        x = ('$(o)/%s: ' % d) + ' '.join(r)
        x = x.replace('$o/', '$(o)/')
        rr.append(x)
        rr.append('\tcat $^ > $@')
        for x in r:
            if x[:3] == '$o/':
                ninja_to_make(pp, rr, inp, x[3:])
    elif r[0] == 'create_c_code':
        s,extra = takeout_extra(r[1:])
        assert ' '.join(s).find('\n') == -1
        rr.append(('$(o)/%s: ' % d) + ' '.join(s))
        a = ('\t$(PYTHON2) %s %s' % (s[0], extra)).rstrip() + ' $@'
        rr.append(a)
    elif r[0] == 'unroll_c_code':
        s,extra = takeout_extra(r[1:])
        if extra:
            rr.append(('$(o)/%s: ' % d) + ' '.join(s))
            rr.append('\t$(PYTHON2) %s %s $@' % (s[0], extra))
        else:
            pp.append((r[1], d))

def find_s_and_h(ninja):
    '''
    Analyze test_toom22_broadwell_t.exe rule, only paying attention at $o/*.h and
     $o/*.s. Extract rules generating those .h and .s.

    If rule is trivial (python2 script.py result.h), remember pair (script,result).

    Else remember pair (None,result) and remember rule (in Makefile style).

    Return tuple: list of pairs and list of rules. Rules are jammed in one list, \n
     delimits one rule from another: [rule1_0,rule1_1+'\n',rule2_0,rule2_1+'\n',...]
    '''
    res0,res1 = [],['o = automagic\n']
    sea = re.compile(r'build \$o/test_toom22_broadwell_t\.exe')
    inp = open(ninja, 'rb')
    rule_0 = extract_ninja_rule(inp, sea)
    dep_0 = extract_dep_0(rule_0)
    for d in dep_0:
        s0,s1 = len(res0),len(res1)
        ninja_to_make(res0, res1, inp, d)
        if (s0,s1) == (len(res0),len(res1)):
            die('nothing found for ' + d)
    return res0,res1

'''
Find microarch-specific subroutines by analyzing '#if AMD_ZEN' directive.

Find microarch-agnostic subroutines by browsing body of mul_basecase_t<>()
Return result as tuple: [Intel subroutines,AMD subroutines],agnostic subroutines
'''
def find_asm_subroutines(toom22_h):
    i,phase = open(toom22_h, 'rb'),0
    '''
    0 before #if
    1 AMD stuff
    2 Intel stuff
    3 before mul_basecase_t
    4 inside mul_basecase_t
    '''
    p = re.compile('#if AMD_ZEN')
    v = re.compile(r'\s+void (\S+)\(')
    u = re.compile('mul_basecase_t')
    a = re.compile(r' +\b(mul\S+)\(rp, ap, bp\);')
    spe,agn = [[], []],[]
    for j in i:
        if (phase == 0) and (p.match(j)):
            phase = 1
        elif phase == 1:
            m = v.match(j)
            if m:
                spe[1].append(m.group(1))
            elif j[:5] == '#else':
                phase = 2
        elif phase == 2:
            m = v.match(j)
            if m:
                spe[0].append(m.group(1))
            elif j[:6] == '#endif':
                phase = 3
        elif phase == 3:
            m = u.match(j)
            if m:
                phase = 4
        elif phase == 4:
            m = a.match(j)
            if m:
                s = m.group(1)
                if not s + '.o' in g_ignored_dependency:
                    agn.append(s)
            elif j[0] == '}':
                break
    return spe,agn

def filter_file_list(ff, n):
    i = [i for i in range(len(ff)) if ff[i][1] == n]
    if not i:
        return False
    del ff[i[0]]
    return True

def filter_rule_list(rr, n):
    p = re.compile(r'\$\(o\)/' + n + ':')
    ii = [i for i in range(len(rr)) if p.match(rr[i])]
    if not ii:
        return False
    k = len(ii)
    for j in range(k - 1, -1, -1):
        del rr[1 + ii[j]]
        del rr[ii[j]]
    return True

def die(x):
    print x
    assert 0

def filter_subr(fl, ru, ban):
    ban += '.s'
    found = filter_file_list(fl, ban)
    found |= filter_rule_list(ru, ban)
    if not found:
        print 'fl =', fl
        print 'ru =', ru
        die('filter_subr(): failed to find subroutine ' + ban)

def filter_files_and_rules(fl_arg, ru_arg, ban):
    fl,ru = list(set(fl_arg)),ru_arg[:]
    for i in ban:
        filter_subr(fl, ru, i)
    return fl,ru

def do_rename(m, s):
    for k_v in m:
        s = re.sub(r'\b' + k_v[0] + r'\b', k_v[1], s)
    return s

def rename_simple(d, s_f):
    return [(do_rename(d, i[0]), do_rename(d, i[1])) for i in s_f]

def rename_general(d, rr):
    return [do_rename(d, r) for r in rr]

g_patt_rule_start = re.compile(r'.+/(\S+):\s*(.+)')
g_patt_python2_rule = re.compile(r'\s\$\(PYTHON2\) (.+)')
# Returns dict script -> target
def script_to_target(simple, general):
    res,i = dict(simple),0
    while True:
        i = next_rule_index(general, i)
        if not i:
            break
        m = g_patt_python2_rule.match(general[1 + i])
        if not m:
            continue
        scr = m.group(1).split(' ')[0]
        m = g_patt_rule_start.match(general[i])
        tgt = m.group(1)
        if scr == '$<':
            scr = m.group(2).split(' ')[0]
        res[scr] = tgt
    return res

def extract_scripts(tgt, mm):
    res = set(tgt)
    for m in mm:
        k = g_patt_rule_start.match(m)
        if k:
            for i in k.group(2).split(' '):
                if i[-3:] == '.py':
                    res.add(i)
    return res

g_patt_mul_digit = re.compile('(mul[0-9]+)(.*)')
'''
Returns dict old->new where old is src file name without directory, and list
 of all scripts to be copied under new name.
'''
def rename_map(simple, general, mul):
    st = script_to_target(simple, general)
    #ts = dict([(i[1], i[0]) for i in st.items()])
    re_map = dict()
    for s in mul:
        m = g_patt_mul_digit.match(s)
        if not m:
            die("Don't know how to rename " + s)
        n = m.group(1)
        if m.group(2):
            re_map[s + '.s'] = n + '.s'
            re_map[s + '.o'] = n + '.o'
    for s_t in st.items():
        n = s_t[1]
        try:
            n = re_map[n]
        except:
            pass
        if n[-2] != '.':
            die('Strange target %s -- no comma in place')
        re_map[s_t[0]] = n[:-1] + 'py'
    sc = st.keys()
    sc = extract_scripts(sc, general)
    for s in sc:
        if (not re_map.has_key(s)) and (s[:4] == 'gen_'):
            re_map[s] = s[4:]
    return re_map,sc

def subroutine_rename_map(dd, mul_subr):
    oo = dict()
    for k_v in dd.items():
        k = k_v[0]
        if k[-2:] != '.s':
            continue
        oo[k[:-2]] = '__gmpn_' + k_v[1][:-2]
    for s in mul_subr:
        if not oo.has_key(s):
            oo[s] = '__gmpn_' + s
    return oo

def rename_and_store(tgt, ff, rr, mul):
    re,sc = rename_map(ff, rr, mul)
    pp = re.items()
    ff_new = rename_simple(pp, ff)
    rr_new = rename_general(pp, rr)
    for s in sc:
        shutil.copy(g_src_dir + '/' + s, tgt + '/' + re[s])
    with open(tgt + '/make.rules', 'wb') as t:
        for r in rr_new:
            t.write(r + '\n')
            if r and (r[0] == '\t'):
                t.write('\n')
    ff_new.sort()
    with open(tgt + '/trivial.targets', 'wb') as s:
        tt = [i[1] for i in ff_new]
        s.write('\n'.join(tt) + '\n')
    return subroutine_rename_map(re, mul)

def store_result(tgt_dir, all_sh, all_rules, forbidden, mul_subr):
    all_sh,all_rules = filter_files_and_rules(all_sh, all_rules, forbidden)
    return rename_and_store(tgt_dir, all_sh, all_rules, mul_subr)

g_patt_import = re.compile(r'import (\S+) as \b\S+')
'''
s: file name without directory
'''
def find_python_dependencies_subr(s_arg):
    res = set()
    s = g_src_dir + '/' + s_arg
    if not os.path.isfile(s):
        return res
    with open(s, 'rb') as i:
        for j in i:
            m = g_patt_import.match(j)
            if m:
                n = m.group(1) + '.py'
                m = g_src_dir + '/' + n
                if os.path.isfile(m):
                    old_size = len(res)
                    res.add(n)
                    if old_size < len(res):
                        res.update(find_python_dependencies_subr(n))
    return res

'''
Return dependencies of files in ff excluding them.
'''
def find_python_dependencies(ff):
    ss = set(ff)
    dd = set()
    for s in ss:
        dd.update(find_python_dependencies_subr(s))
    dd.difference_update(ss)
    return dd

'''
Find unlisted Python dependencies, add them to list of dependencies
'''
def add_python_dependencies(simple, general):
    simple_ok,general_new = [],[]
    for s_t in simple:
        ff = find_python_dependencies([s_t[0]])
        if not ff:
            simple_ok.append(s_t)
        else:
            d = '$(o)/%s: %s ' % (s_t[1], s_t[0])
            d += ' '.join(ff)
            general_new.append(d)
            general_new.append('\t$(PYTHON2) %s $@' % s_t[0])
    for i in range(len(general)):
        r = general[i]
        if (not r) or (r[0] != '$'):
            continue
        p = r.find(':')
        if p == -1:
            continue
        q = r[1 + p:].lstrip().split(' ')
        q = [x for x in q if x[-3:] == '.py']
        ff = find_python_dependencies(q)
        if not ff:
            continue
        general[i] = r + ' ' + ' '.join(ff)
    general += general_new
    return simple_ok

def next_rule_index(rr, i):
    while True:
        i += 1
        if i >= len(rr):
            return
        if g_patt_rule_start.match(rr[i]):
            return i

'''
Use $< if possible.

If general rule is trivial, move it to simple
'''
def clean_rules(simple, general):
    i,to_delete = 0,[]
    while True:
        i = next_rule_index(general, i)
        if not i:
            break
        m = g_patt_rule_start.match(general[i])
        if m.group(2).find(' ') == -1:
            simple.append((m.group(2), m.group(1)))
            to_delete.append(i)
            continue
        s = r'\b%s\b' % (m.group(2).split(' ')[0])
        general[i + 1] = re.sub(s, '$<', general[i + 1])
    for i in range(len(to_delete) - 1, -1, -1):
        j = to_delete[i]
        del general[j + 1]
        del general[j]

g_patt_mul_capital = re.compile(r'MUL([0-9]+)_SUBR\(')
'''
Filter file tgt + 'h', renaming subroutines. Store result at tgt. dd is rename map.

Also change MULx_SUBR( to __gmpn_mulx( where x is a number
'''
def patch_header(tgt, dd):
    src = tgt + 'h'
    with open(tgt, 'wb') as o, open(src, 'rb') as i:
        for j in i:
            for d in dd.items():
                j = re.sub(r'\b%s\b' % d[0], d[1], j)
            m = g_patt_mul_capital.search(j)
            if m:
                j = j.replace(m.group(), '__gmpn_mul%s(' % m.group(1))
            o.write(j)
    os.remove(src)

g_all_sh,g_rules = find_s_and_h(g_ninja)
# TODO: remove duplicate rules? For now, there are none.
g_all_sh = add_python_dependencies(g_all_sh, g_rules)
clean_rules(g_all_sh, g_rules)
g_readonly_header = g_src_dir + '/toom22_generic.h'
g_specific_asm,g_general_mul = find_asm_subroutines(g_readonly_header)
for g_i in range(2):
    g_subr_rename = store_result(g_output_dir[g_i], g_all_sh, g_rules,
        g_specific_asm[(1 + g_i) % 2], g_general_mul + g_specific_asm[g_i])
    if g_i == 0:
        patch_header(g_tgt_dir + 'automagic/toom22.h', g_subr_rename)
