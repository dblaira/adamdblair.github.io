#!/bin/bash
# Behavioural tests for every shipped hook.
#
# These exist so the claim "the hooks work" has an artifact you can run, not a
# sentence you have to trust. Each test fires the real hook with the real stdin
# shape Claude Code sends, and asserts on the exit code and the message.
#
#   bash tests/run-tests.sh
#
# Requires: bash, jq, git, python3.

set -uo pipefail

HOOKS="$(cd "$(dirname "${BASH_SOURCE[0]}")/../hooks" && pwd)"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

PASS=0
FAIL=0

# ---------------------------------------------------------------- assertions

# fire HOOK JSON [VAR=VAL...] -> sets OUT (stdout+stderr) and CODE.
# Runs in TEST_CWD if set. Must not be called in a subshell — OUT and CODE
# would not survive it, and the next assertion would silently read stale values.
fire() {
  local hook="$1" json="$2" prev="$PWD"
  shift 2
  [ -n "${TEST_CWD:-}" ] && cd "$TEST_CWD"
  set +e
  OUT=$(printf '%s' "$json" | env "$@" bash "$HOOKS/$hook" 2>&1)
  CODE=$?
  set -e
  cd "$prev"
}

check() {
  local name="$1" want_code="$2" want_text="${3:-}"
  if [ "$CODE" != "$want_code" ]; then
    printf 'FAIL  %s\n      expected exit %s, got %s\n      output: %s\n' \
      "$name" "$want_code" "$CODE" "$OUT"
    FAIL=$((FAIL + 1))
    return
  fi
  if [ -n "$want_text" ] && ! printf '%s' "$OUT" | grep -q "$want_text"; then
    printf 'FAIL  %s\n      expected output matching %s\n      output: %s\n' \
      "$name" "$want_text" "$OUT"
    FAIL=$((FAIL + 1))
    return
  fi
  printf 'pass  %s\n' "$name"
  PASS=$((PASS + 1))
}

edit_json() { printf '{"tool_input":{"file_path":"%s"}}' "$1"; }
bash_json() { printf '{"tool_input":{"command":"%s"},"cwd":"%s"}' "$1" "$2"; }

# ------------------------------------------------------------------ fixtures

REPO="$WORK/repo"
mkdir -p "$REPO"
git -C "$REPO" init -q -b main
git -C "$REPO" config user.email t@t.t
git -C "$REPO" config user.name t
echo x >"$REPO/f.txt"
git -C "$REPO" add -A
git -C "$REPO" commit -qm init

python3 - "$WORK" <<'PY'
import sys
w = sys.argv[1]

with open(f"{w}/short.py", "w") as fh:
    fh.write("def add(a, b):\n    return a + b\n")

with open(f"{w}/long.txt", "w") as fh:
    fh.writelines("line\n" for _ in range(500))

with open(f"{w}/package-lock.json", "w") as fh:
    fh.writelines("line\n" for _ in range(500))

# 12 sequential branches -> cyclomatic 13
body = "".join(f"    if x == {i}:\n        return {i}\n" for i in range(12))
with open(f"{w}/complex.py", "w") as fh:
    fh.write(f"def route(x):\n{body}    return None\n")

# same 10-line block twice, with different names around it
block = "".join(f"    total += value_{i}\n" for i in range(10))
with open(f"{w}/dup.py", "w") as fh:
    fh.write(f"def one(total):\n{block}    return total\n")
    fh.write(f"def two(total):\n{block}    return total\n")

with open(f"{w}/unique.py", "w") as fh:
    fh.write("".join(f"def f{i}(x):\n    return x * {i}\n" for i in range(12)))

with open(f"{w}/broken.py", "w") as fh:
    fh.write("def nope(:\n")
PY

# copy half of dup.py's block into a second repo file, for DUP_SCOPE=repo
mkdir -p "$REPO/pkg"
python3 - "$REPO" <<'PY'
import sys
r = sys.argv[1]
block = "".join(f"    total += value_{i}\n" for i in range(10))
with open(f"{r}/pkg/a.py", "w") as fh:
    fh.write(f"def alpha(total):\n{block}    return total\n")
with open(f"{r}/pkg/b.py", "w") as fh:
    fh.write(f"def beta(total):\n{block}    return total\n")
PY
git -C "$REPO" add -A
git -C "$REPO" commit -qm files

# ------------------------------------------------------------ protect-main.sh

fire protect-main.sh "$(bash_json 'git commit -m x' "$REPO")" PROTECTED_BRANCHES=main
check "protect-main: denies commit on protected branch" 0 '"deny"'

fire protect-main.sh "$(bash_json 'git commit -m x' "$REPO")" PROTECTED_BRANCHES=release
check "protect-main: silent on unprotected branch" 0 ""
[ -z "$OUT" ] || { echo "FAIL  protect-main should print nothing, got: $OUT"; FAIL=$((FAIL+1)); }

fire protect-main.sh "$(bash_json 'git commit --dry-run -m x' "$REPO")" PROTECTED_BRANCHES=main
check "protect-main: lets --dry-run through" 0 ""

fire protect-main.sh "$(bash_json 'ls -la' "$REPO")" PROTECTED_BRANCHES=main
check "protect-main: silent on non-commit command" 0 ""

# ---------------------------------------------------------- max-file-lines.sh

fire max-file-lines.sh "$(edit_json "$WORK/long.txt")" MAX_FILE_LINES=400
check "max-file-lines: fails over the limit" 2 "500 lines"

fire max-file-lines.sh "$(edit_json "$WORK/short.py")" MAX_FILE_LINES=400
check "max-file-lines: passes under the limit" 0 ""

fire max-file-lines.sh "$(edit_json "$WORK/package-lock.json")" MAX_FILE_LINES=400
check "max-file-lines: skips lockfiles" 0 ""

fire max-file-lines.sh "$(edit_json "$WORK/long.txt")" MAX_FILE_LINES=600
check "max-file-lines: honours the env override" 0 ""

fire max-file-lines.sh "$(edit_json "$WORK/gone.txt")" MAX_FILE_LINES=400
check "max-file-lines: silent on a missing file" 0 ""

# --------------------------------------------------------- max-complexity.sh

fire max-complexity.sh "$(edit_json "$WORK/complex.py")" MAX_COMPLEXITY=10
check "max-complexity: fails over the ceiling" 2 "complexity 13"

fire max-complexity.sh "$(edit_json "$WORK/complex.py")" MAX_COMPLEXITY=10
check "max-complexity: names the offending function" 2 "\`route\`"

fire max-complexity.sh "$(edit_json "$WORK/short.py")" MAX_COMPLEXITY=10
check "max-complexity: passes simple code" 0 ""

fire max-complexity.sh "$(edit_json "$WORK/complex.py")" MAX_COMPLEXITY=20
check "max-complexity: honours the env override" 0 ""

fire max-complexity.sh "$(edit_json "$WORK/long.txt")" MAX_COMPLEXITY=10
check "max-complexity: ignores non-Python files" 0 ""

fire max-complexity.sh "$(edit_json "$WORK/broken.py")" MAX_COMPLEXITY=10
check "max-complexity: silent on unparseable source" 0 ""

fire max-complexity.sh "$(edit_json "$WORK/gone.py")" MAX_COMPLEXITY=10
check "max-complexity: silent on a missing file" 0 ""

# ---------------------------------------------------------- no-duplication.sh

fire no-duplication.sh "$(edit_json "$WORK/dup.py")" DUP_MIN_LINES=8
check "no-duplication: fails on a repeated block" 2 "identical lines"

fire no-duplication.sh "$(edit_json "$WORK/dup.py")" DUP_MIN_LINES=8
check "no-duplication: names both line numbers" 2 "dup.py:.* and .*dup.py:"

fire no-duplication.sh "$(edit_json "$WORK/unique.py")" DUP_MIN_LINES=8
check "no-duplication: passes unique code" 0 ""

fire no-duplication.sh "$(edit_json "$WORK/dup.py")" DUP_MIN_LINES=40
check "no-duplication: honours the env override" 0 ""

fire no-duplication.sh "$(edit_json "$WORK/long.txt")" DUP_MIN_LINES=8
check "no-duplication: ignores non-Python files" 0 ""

# cross-file: each file alone is clean, together they are a paste
TEST_CWD="$REPO"
fire no-duplication.sh "$(edit_json "$REPO/pkg/a.py")" DUP_MIN_LINES=8 DUP_SCOPE=file
check "no-duplication: file scope misses a cross-file paste" 0 ""

fire no-duplication.sh "$(edit_json "$REPO/pkg/a.py")" DUP_MIN_LINES=8 DUP_SCOPE=repo
check "no-duplication: repo scope catches a cross-file paste" 2 "b.py"
TEST_CWD=""

# ------------------------------------------------- the deliverable's own code

for f in "$HOOKS"/lib/*.py; do
  fire max-complexity.sh "$(edit_json "$f")" MAX_COMPLEXITY=10
  check "dogfood: $(basename "$f") passes the complexity ceiling" 0 ""
  fire no-duplication.sh "$(edit_json "$f")" DUP_MIN_LINES=8
  check "dogfood: $(basename "$f") passes the duplication check" 0 ""
done

# ------------------------------------------------------------------- summary

echo
echo "$PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] || exit 1
