from collections import defaultdict, OrderedDict
from os import path
import re, sys, argparse

parser = argparse.ArgumentParser(description='Parse a .map file and print size information')
parser.add_argument('file_path', metavar='<path.map>', type=str,
                   help='path to .map file or $program yotta variable')
parser.add_argument('-v', '--verbose', help='verbose mode', default=False, action='store_true')
args = parser.parse_args()

p = args.file_path
if not p.endswith(".map"):
    fn = path.basename(p).split(".")[0] + ".map"
    p = path.join(path.dirname(p), fn)
if not path.exists(p):
    print "File not found!", p
    parser.print_usage()
    sys.exit(1)

with open(p, 'r') as fd:
    s = fd.read()

i = s.find("Linker script and memory map")
ptn = re.compile("\.(text|bss|rodata|data)\.(.*)\n *(0x[0-9a-f]*) *(0x[0-9a-f]*) (.*)\n", re.MULTILINE & re.DEBUG & re.DOTALL)

cnt_dep = defaultdict(lambda : defaultdict(int))
cnt_app = defaultdict(lambda : defaultdict(int))
cnt_ext = defaultdict(lambda : defaultdict(int))

for match in ptn.finditer(s[i:]):
    r = re.search("\(.*\)", match.group(5))
    if r != None:
        p = match.group(5)[0:r.start()]
    else:
        p = match.group(5)

    module_name = path.basename(p).split(".")[0]
    if p.startswith("source"):
        cnt = cnt_app
    elif p.startswith("ym"):
        cnt = cnt_dep
    else:
        cnt = cnt_ext

    cnt[module_name]["total"] += int(match.group(4), 16)
    cnt[module_name][match.group(1)] += int(match.group(4), 16)

keys = cnt_dep.keys()+cnt_app.keys()+cnt_ext.keys();
vals = cnt_dep.values()+cnt_app.values()+cnt_ext.values();
ljust = max([len(x) for x in keys])
rjust = max([len(str(x['total'])) for x in vals])

print "-"*(ljust+rjust+4)
for section, cnt in (("Application code", cnt_app), ("Dependencies", cnt_dep), ("External Libraries", cnt_ext)):
    print section
    for key, val in sorted(cnt.items()):
        print "  {:<{}} {:>{}}".format(key, ljust+1, val["total"], rjust)
        if args.verbose:
            for k, v in sorted(val.items()):
                if k != "total":
                    print "    {:<{}} {:>{}}".format(k, ljust-1, v, rjust)
    print "-"*(ljust+rjust+4)
