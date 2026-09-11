import base64
import json
import subprocess

GH = r"C:\Program Files\GitHub CLI\gh.exe"
REPO = "rajankumar2711/VATDTAI"
BASE_BRANCH = "Rajan_AI_VAT_automation"          # parent (already on remote)
NEW_BRANCH = "feature/inbound-invoice-tests"     # branch to create


def git(args, binary=False):
    r = subprocess.run(["git"] + args, capture_output=True, text=not binary)
    if r.returncode != 0:
        err = r.stderr if not binary else r.stderr.decode("utf-8", "replace")
        raise RuntimeError("git failed: %s\n%s" % (args, err))
    return r.stdout


def gh_api(method, path, body=None):
    cmd = [GH, "api", "-X", method, path]
    if body is not None:
        cmd += ["--input", "-"]
        r = subprocess.run(cmd, input=json.dumps(body), capture_output=True, text=True,
                           encoding="utf-8")
    else:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise RuntimeError("gh api failed: %s %s\n%s" % (method, path, r.stderr))
    return json.loads(r.stdout) if r.stdout.strip() else {}


def main():
    parent = git(["rev-parse", "origin/" + BASE_BRANCH]).strip()
    message = git(["log", "-1", "--format=%B", "HEAD"])
    parent_commit = gh_api("GET", "/repos/%s/git/commits/%s" % (REPO, parent))
    base_tree = parent_commit["tree"]["sha"]
    print("parent commit:", parent)
    print("base tree    :", base_tree)

    raw = git(["diff", "--raw", "--no-renames", "-z", parent, "HEAD"])
    tokens = [t for t in raw.split("\0") if t != ""]
    entries = []
    i = 0
    while i < len(tokens):
        meta = tokens[i]
        path = tokens[i + 1]
        i += 2
        parts = meta.lstrip(":").split()
        newmode, newsha, status = parts[1], parts[3], parts[4]
        entries.append((status, newmode, newsha, path))

    print("total changed paths:", len(entries))
    tree = []
    for n, (status, newmode, newsha, path) in enumerate(entries, 1):
        if status == "D":
            tree.append({"path": path, "mode": "100644", "type": "blob", "sha": None})
            print("[%d/%d] delete %s" % (n, len(entries), path))
            continue
        content = git(["cat-file", "blob", newsha], binary=True)
        b64 = base64.b64encode(content).decode("ascii")
        blob = gh_api("POST", "/repos/%s/git/blobs" % REPO,
                      {"content": b64, "encoding": "base64"})
        mode = newmode if newmode in ("100644", "100755", "120000", "160000") else "100644"
        tree.append({"path": path, "mode": mode, "type": "blob", "sha": blob["sha"]})
        print("[%d/%d] blob %s %s" % (n, len(entries), blob["sha"][:8], path))

    new_tree = gh_api("POST", "/repos/%s/git/trees" % REPO,
                      {"base_tree": base_tree, "tree": tree})
    print("new tree     :", new_tree["sha"])

    new_commit = gh_api("POST", "/repos/%s/git/commits" % REPO,
                        {"message": message, "tree": new_tree["sha"], "parents": [parent]})
    print("new commit   :", new_commit["sha"])

    ref = gh_api("POST", "/repos/%s/git/refs" % REPO,
                 {"ref": "refs/heads/%s" % NEW_BRANCH, "sha": new_commit["sha"]})
    print("ref created  :", ref["object"]["sha"])
    print("NEW_COMMIT_SHA=" + new_commit["sha"])
    print("DONE")


if __name__ == "__main__":
    main()
