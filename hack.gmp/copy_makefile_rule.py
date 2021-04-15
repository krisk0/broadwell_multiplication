import sys

def read_rules(i, rr):
    rr = [r + ':' for r in rr]
    copy,result = False,[]
    for j in i:
        k = j.rstrip()
        if k in rr:
            copy = True
            result.append(k)
            continue
        if copy:
            copy = False
            result += [k, '']
    return result

def write_rules(o, rr):
    o.write('\n')
    for r in rr:
        o.write(r + '\n')

with open(sys.argv[2], 'rb') as g_i:
    g_result = read_rules(g_i, sys.argv[1].split(','))

with open(sys.argv[3], 'ab') as g_o:
    write_rules(g_o, g_result)
