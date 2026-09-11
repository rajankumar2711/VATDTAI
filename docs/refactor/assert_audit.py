"""Phase 4 audit: list @then step functions that contain no assert/raise/fail
(potential weak assertions), per step-def module."""
import ast
from pathlib import Path

SD = Path(__file__).resolve().parent.parent.parent / "tests" / "step_defs"


def decos(fn):
    names = []
    for d in fn.decorator_list:
        node = d.func if isinstance(d, ast.Call) else d
        if isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, ast.Attribute):
            names.append(node.attr)
    return names


def has_check(fn):
    for n in ast.walk(fn):
        if isinstance(n, ast.Assert):
            return True
        if isinstance(n, ast.Raise):
            return True
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Attribute) and f.attr in ("fail", "skip", "xfail"):
                return True
            # Playwright web-first assertion: expect(locator).to_be_*()
            if isinstance(f, ast.Attribute) and str(f.attr).startswith("to_"):
                return True
            if isinstance(f, ast.Name) and f.id == "expect":
                return True
    return False


for path in sorted(SD.glob("test_*.py")):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    weak = []
    total_then = 0
    for fn in tree.body:
        if not isinstance(fn, ast.FunctionDef):
            continue
        d = decos(fn)
        if "then" in d:
            total_then += 1
            if not has_check(fn):
                weak.append((fn.lineno, fn.name))
    print(f"\n=== {path.name}: {len(weak)}/{total_then} @then steps have NO assert/raise/fail ===")
    for ln, name in weak:
        print(f"  L{ln}: {name}")
