#!/usr/bin/env python3
"""Calibration tests for the degradation instrument.

An instrument that has never been pointed at a known answer is not an
instrument. These build series whose ground truth we control — one that
degrades by construction, one that does not — and check that the metrics
separate them with the right sign.

    python3 RESEARCH/tools/test_degrade_metrics.py

Exit 0 = calibrated. Any failure prints what it expected and what it got.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from degrade_metrics import (  # noqa: E402
    TRACKED,
    dir_checkpoints,
    fit_series,
    ols,
    permutation_p,
)

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
        "REVENUE",
        "DELIVERABLE",
        "hooks",
        "lib",
    ),
)
from pystruct import gini  # noqa: E402

PASSED = 0
FAILED = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"pass  {name}")
    else:
        FAILED += 1
        print(f"FAIL  {name}\n      {detail}")


# --------------------------------------------------------------- synthetic series


def _clean_module(index: int, size: int) -> str:
    """Small, distinct, single-branch functions. Adding these should not degrade."""
    return "".join(
        f"def op_{index}_{i}(value):\n"
        f"    if value > {i}:\n"
        f"        return value - {i}\n"
        f"    return value\n\n"
        for i in range(size)
    )


def _slop_module(index: int, size: int) -> str:
    """One growing god-function plus a pasted block. Degrades by construction."""
    branches = "".join(
        f"    if value == {i}:\n        return {i}\n" for i in range(4 + index * 3)
    )
    pasted = "".join(f"    total += weight_{i}\n" for i in range(10))
    body = f"def god_{index}(value):\n{branches}    return None\n\n"
    for i in range(size):
        body += f"def helper_{index}_{i}(total):\n{pasted}    return total\n\n"
    return body


def _build(root: str, checkpoints: int, module) -> list[str]:
    """Write a cumulative series: each checkpoint keeps everything before it."""
    dirs = []
    for step in range(checkpoints):
        path = os.path.join(root, f"cp{step:02d}")
        os.makedirs(path, exist_ok=True)
        for earlier in range(step + 1):
            with open(os.path.join(path, f"mod{earlier}.py"), "w") as fh:
                fh.write(module(earlier, 3))
        dirs.append(path)
    return dirs


def test_synthetic_separation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        stable = fit_series(dir_checkpoints(_build(f"{tmp}/a", 8, _clean_module), ".py"))
        slop = fit_series(dir_checkpoints(_build(f"{tmp}/b", 8, _slop_module), ".py"))

    for metric in ("erosion_gini", "mean_complexity", "duplication_ratio"):
        s, d = stable[metric]["slope"], slop[metric]["slope"]
        check(
            f"degrading series has a rising {metric}",
            d > 0,
            f"slope was {d}",
        )
        check(
            f"stable series does not rise on {metric} the way the degrading one does",
            d > s,
            f"stable {s} vs degrading {d}",
        )

    check(
        "growth alone is not read as degradation",
        abs(stable["erosion_gini"]["slope"]) < 0.01,
        f"clean series erosion slope was {stable['erosion_gini']['slope']}",
    )
    check(
        "both series do grow in size (the control is not empty)",
        stable["logical_lines"]["slope"] > 0 and slop["logical_lines"]["slope"] > 0,
        f"{stable['logical_lines']['slope']} / {slop['logical_lines']['slope']}",
    )


# ------------------------------------------------------------------- unit checks


def test_ols_recovers_a_known_line() -> None:
    xs = list(range(10))
    fit = ols([float(x) for x in xs], [3.0 + 2.5 * x for x in xs])
    check("ols recovers a known slope", abs(fit["slope"] - 2.5) < 1e-9, str(fit))
    check("ols recovers a known intercept", abs(fit["intercept"] - 3.0) < 1e-9, str(fit))
    check("ols reports r2 = 1 on an exact line", abs(fit["r2"] - 1.0) < 1e-9, str(fit))

    flat = ols([float(x) for x in xs], [7.0] * 10)
    check("ols reports zero slope on a flat series", flat["slope"] == 0.0, str(flat))

    short = ols([0.0, 1.0], [0.0, 5.0])
    check("ols refuses to fit fewer than 3 points", short["slope"] == 0.0, str(short))


def test_gini_endpoints() -> None:
    check("gini of an even distribution is 0", gini([5, 5, 5, 5]) == 0.0)
    check("gini of a single value is 0", gini([9]) == 0.0)
    check("gini rises with concentration", gini([1, 1, 1, 40]) > gini([1, 1, 1, 4]))
    check("gini stays below 1", gini([0, 0, 0, 1000]) < 1.0)


def test_permutation_behaviour() -> None:
    same = permutation_p([1.0, 1.1, 0.9], [1.0, 1.05, 0.95], 5000, 1)
    apart = permutation_p([0.0, 0.1, -0.1], [9.0, 9.1, 8.9], 5000, 1)
    check("identical arms give a large p", same > 0.2, f"p={same}")
    check("well-separated arms give a small p", apart < 0.15, f"p={apart}")
    check("p is never zero (the +1 correction holds)", apart > 0)


def test_tracked_metrics_are_all_fitted() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        fits = fit_series(dir_checkpoints(_build(f"{tmp}/c", 5, _clean_module), ".py"))
    missing = [m for m in TRACKED if m not in fits]
    check("every tracked metric gets a fit", not missing, f"missing: {missing}")


def main() -> int:
    test_ols_recovers_a_known_line()
    test_gini_endpoints()
    test_permutation_behaviour()
    test_tracked_metrics_are_all_fitted()
    test_synthetic_separation()
    print(f"\n{PASSED} passed, {FAILED} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
