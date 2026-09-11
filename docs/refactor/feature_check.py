import re
import glob
import os
from pytest_bdd.parser import parse_feature

allok = True
for path in sorted(glob.glob("tests/features/*.feature")):
    txt = open(path, encoding="utf-8").read()
    raw = len([l for l in txt.splitlines() if re.match(r"\s*(Given|When|Then|And|But)\b", l)])
    f = parse_feature("tests/features", os.path.basename(path))
    bg = len(f.background.steps) if f.background else 0
    parsed = bg + sum(len(sc.steps) - bg for sc in f.scenarios.values())
    ok = parsed == raw
    allok = allok and ok
    status = "OK" if ok else "*** MERGED ***"
    print("%-40s raw=%3d parsed=%3d scn=%2d %s" % (os.path.basename(path), raw, parsed, len(f.scenarios), status))
print("ALL CLEAN" if allok else "ISSUES REMAIN")
