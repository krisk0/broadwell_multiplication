'''
Copy some gen_*.py scripts to two directories.

Rename files so foo.s.py makes foo.s, foo.h.py makes foo.h .

Patch mul4.s.py so subroutine name is __g prepended to old name.

Multiplication subroutines should be called __gmpn_mul_N (for instance
 __gmpn_mul_11).

Non-trivial makefile rules go to all.rule. Example:
$(o)/toom22_interpolate_16.s: $(o)/toom22_interpolate_16_raw.s $(o)/mpn_add_2_4arg.s
    cat $^ > $@

TODO: omit some subroutines (such as addmul_8x3)
'''

import os, re, sys

g_ignored_dependency = ['addmul_1_adox.o']

g_tgt_dir = sys.argv[1] + '/'
g_output_dir = [g_tgt_dir + 'x86_64/coreibwl', g_tgt_dir + 'x86_64/zen']
g_ninja = os.path.realpath(os.path.dirname(sys.argv[0]) + '/../build.ninja')
g_src_dir = os.path.dirname(g_ninja)

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
            if (s.find('test') == -1) and (not s in g_ignored_dependency):
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
Return result as two lists.
'''
def find_microarch_asm_subroutines(toom22_h):
    i,phase = open(toom22_h, 'rb'),0
    p = re.compile('#if AMD_ZEN')
    v = re.compile(r'\s+void (\S+)\(')
    res = [[], []]
    for j in i:
        if (phase == 0) and (p.match(j)):
            phase = 1
        elif phase == 1:
            m = v.match(j)
            if m:
                res[1].append(m.group(1))
            elif j[:5] == '#else':
                phase = 2
        elif phase == 2:
            m = v.match(j)
            if m:
                res[0].append(m.group(1))
            elif j[:5] == '#endif':
                break
    return res

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

def extract_script_names(rr):
    res = []
    for r in rr:
        p = r.find(':')
        if p == -1:
            continue
        q = r[1 + p].split(' ')
        res += [t for t in q if t[-3:] == '.py']
    return res

def rename_and_store(tgt, ff, rr):
    ss = set([i[0] for i in ff] + extract_script_names(rr))
    # TODO: renaming should occur here
    ss = sorted(list(ss))
    with open(tgt + '/.scripts', 'wb') as s:
        s.write('\n'.join(ss) + '\n')
    with open(tgt + '/all.rules', 'wb') as r:
        for x in rr:
            r.write(x + '\n')
            if x and (x[0] == '\t'):
                r.write('\n')

def store_result(tgt_dir, all_sh, all_rules, forbidden):
    all_sh,all_rules = filter_files_and_rules(all_sh, all_rules, forbidden)
    rename_and_store(tgt_dir, all_sh, all_rules)

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

g_all_sh,g_rules = find_s_and_h(g_ninja)
# TODO: remove duplicate rules?
g_all_sh = add_python_dependencies(g_all_sh, g_rules)
g_readonly_header = os.path.dirname(g_ninja) + '/toom22_generic.h'
g_specific_asm_subroutines = find_microarch_asm_subroutines(g_readonly_header)
store_result(g_output_dir[0], g_all_sh, g_rules, g_specific_asm_subroutines[1])
store_result(g_output_dir[1], g_all_sh, g_rules, g_specific_asm_subroutines[0])
