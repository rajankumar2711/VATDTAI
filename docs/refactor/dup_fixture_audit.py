"""Phase B+C audit:
 B) step phrasings defined in >1 step-def file (consolidation candidates), and
    any defined BOTH in a module file and in VAT_Common_Library.
 C) conftest.py fixtures that are never referenced as a parameter anywhere."""
import ast
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SD = ROOT / "tests" / "step_defs"
CONFTEST = ROOT / "conftest.py"
SEARCH_DIRS = [ROOT / "tests", ROOT / "pageobjects", CONFTEST]

STEP_DECOS = {"given", "when", "then"}


def deco_step_text(d):
    """Return step text for a given/when/then decorator, else None."""
    if not isinstance(d, ast.Call):
        return None
    fn = d.func
    name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", None)
    if name not in STEP_DECOS or not d.args:
        return None
    a = d.args[0]
    if isinstance(a, ast.Constant) and isinstance(a.value, str):
        return a.value
    if isinstance(a, ast.Call):  # parsers.parse("...") / cfparse / re
        if a.args and isinstance(a.args[0], ast.Constant):
            return "parse:" + str(a.args[0].value)
    return None


# ---- B: step duplication ----
step_defs = defaultdict(list)  # text -> [(file, func, lineno)]
for path in sorted(SD.glob("*.py")):
    if path.name == "__init__.py":
        continue
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    for fn in tree.body:
        if isinstance(fn, ast.FunctionDef):
            for d in fn.decorator_list:
                txt = deco_step_text(d)
                if txt:
                    step_defs[txt].append((path.name, fn.name, fn.lineno))

print("=" * 70)
print("B) STEP TEXTS DEFINED IN MULTIPLE FILES")
print("=" * 70)
dups = {t: locs for t, locs in step_defs.items()
        if len({l[0] for l in locs}) > 1}
if not dups:
    print("  none")
for t, locs in sorted(dups.items()):
    files = ", ".join(f"{f}:{ln}({fn})" for f, fn, ln in locs)
    print(f"  [{t}]\n      {files}")

# ---- C: conftest fixture usage ----
ct = ast.parse(CONFTEST.read_text(encoding="utf-8-sig"))
fixtures = []
for fn in ct.body:
    if isinstance(fn, ast.FunctionDef):
        is_fx = any(
            (isinstance(d, ast.Call) and getattr(d.func, "attr", None) == "fixture") or
            (isinstance(d, ast.Attribute) and d.attr == "fixture")
            for d in fn.decorator_list
        )
        if is_fx:
            fixtures.append(fn.name)

# Build corpus of all param usage across search dirs (exclude conftest def lines handled below)
corpus = []
for d in SEARCH_DIRS:
    if d.is_file():
        corpus.append((d.name, d.read_text(encoding="utf-8-sig")))
    else:
        for p in d.rglob("*.py"):
            corpus.append((str(p.relative_to(ROOT)), p.read_text(encoding="utf-8-sig")))

print("\n" + "=" * 70)
print("C) CONFTEST FIXTURE USAGE (references outside its own def)")
print("=" * 70)
for fx in fixtures:
    pat = re.compile(rf"\b{re.escape(fx)}\b")
    hits = 0
    hitfiles = set()
    for name, text in corpus:
        for i, line in enumerate(text.splitlines(), 1):
            if pat.search(line):
                # skip the fixture's own def line
                if name == "conftest.py" and re.match(rf"\s*def {re.escape(fx)}\s*\(", line):
                    continue
                hits += 1
                hitfiles.add(name)
    flag = "  <-- UNUSED?" if hits == 0 else ""
    print(f"  {fx}: {hits} ref(s) in {len(hitfiles)} file(s){flag}")
