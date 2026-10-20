"""Reproducible bottom-up merge/insertion-sort experiment (standard library only)."""

from __future__ import annotations

import argparse
import json
import math
import platform
import random
import statistics
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from time import perf_counter, perf_counter_ns
from typing import MutableSequence, TypeVar


T = TypeVar("T")
SEED = 20260921
DEFAULT_SIZES = (1000, 10000, 50000)
DEFAULT_KS = (1, 4, 8, 16, 32, 64, 128)
DATA_TYPES = ("random", "sorted", "reversed", "few_unique")


def hybrid_sort(values: MutableSequence[T], k: int = 16) -> None:
    """Stable in-place result, O(n) auxiliary storage; k=1 is merge sort.

    Sort consecutive blocks using insertion sort, then merge adjacent runs.
    There is no 'already ordered' merge shortcut. All copying uses loops.
    """
    if not isinstance(k, int) or isinstance(k, bool) or k < 1:
        raise ValueError("k must be a positive integer")
    n = len(values)
    buffer = [None] * n
    for start in range(0, n, k):
        end = min(start + k, n)
        for j in range(start + 1, end):
            item = values[j]
            i = j - 1
            while i >= start and values[i] > item:
                values[i + 1] = values[i]
                i -= 1
            values[i + 1] = item

    width = k
    while width < n:
        for left in range(0, n, 2 * width):
            mid = min(left + width, n)
            right = min(left + 2 * width, n)
            i, j, pos = left, mid, left
            while i < mid and j < right:
                if values[i] <= values[j]:
                    buffer[pos] = values[i]
                    i += 1
                else:
                    buffer[pos] = values[j]
                    j += 1
                pos += 1
            while i < mid:
                buffer[pos] = values[i]
                i += 1
                pos += 1
            while j < right:
                buffer[pos] = values[j]
                j += 1
                pos += 1
            for pos in range(left, right):
                values[pos] = buffer[pos]
        width *= 2


class Tagged:
    """Comparison ignores tag so tag order can verify algorithm stability."""

    def __init__(self, key: int, tag: int):
        self.key = key
        self.tag = tag

    def __gt__(self, other: Tagged) -> bool:
        return self.key > other.key

    def __le__(self, other: Tagged) -> bool:
        return self.key <= other.key


def check_correctness() -> dict:
    count = 0
    edge_cases = [[], [7], [3, -1, 3, 0, -1], [2, 1], list(range(17, -1, -1))]
    for original in edge_cases:
        for k in (1, 2, 3, 4, 8, 16, 128):
            actual = original.copy()
            hybrid_sort(actual, k)
            assert actual == sorted(original), (original, k, actual)
            count += 1

    rng = random.Random(SEED)
    random_cases = 0
    for _ in range(250):
        n = rng.randrange(0, 401)
        original = [rng.randrange(-50, 51) for _ in range(n)]
        k = rng.choice((1, 2, 3, 5, 8, 16, 31, 64, 128, n + 1))
        actual = original.copy()
        hybrid_sort(actual, k)
        assert actual == sorted(original), (n, k)
        random_cases += 1
        count += 1

    invalid_cases = 0
    for k in (0, -1, -20, 1.5, "4", None, True):
        try:
            hybrid_sort([2, 1], k)
        except ValueError:
            invalid_cases += 1
            count += 1
        else:
            raise AssertionError(f"invalid k was accepted: {k!r}")

    stability_cases = 0
    for n in (0, 1, 17, 101):
        keys = [rng.randrange(-3, 4) for _ in range(n)]
        original = [Tagged(key, tag) for tag, key in enumerate(keys)]
        expected = sorted(original, key=lambda value: value.key)
        expected_pairs = [(value.key, value.tag) for value in expected]
        for k in (1, 3, 8, 16, 128):
            actual = original.copy()
            hybrid_sort(actual, k)
            assert [(value.key, value.tag) for value in actual] == expected_pairs
            stability_cases += 1
            count += 1
    return {
        "passed": True,
        "total_cases": count,
        "edge_cases": len(edge_cases) * 7,
        "random_cases": random_cases,
        "invalid_k_cases": invalid_cases,
        "stability_cases": stability_cases,
        "coverage": [
            "empty", "single element", "negative values", "duplicates",
            "k > n (pure insertion sort)", "n not divisible by k", "invalid k",
            "randomized sorted() oracle", "tagged-object stability",
        ],
    }


def make_input(n: int, kind: str, seed: int) -> list[int]:
    rng = random.Random(seed)
    if kind == "few_unique":
        return [rng.randrange(16) for _ in range(n)]
    values = [rng.randrange(-n, n + 1) for _ in range(n)]
    if kind == "sorted":
        values.sort()
    elif kind == "reversed":
        values.sort(reverse=True)
    elif kind != "random":
        raise ValueError(kind)
    return values


def cpu_model() -> str:
    if platform.system() == "Windows":
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance Win32_Processor | Select-Object -First 1).Name"],
                capture_output=True, text=True, timeout=15, check=True,
            )
            return result.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
    return platform.processor() or "unavailable"


def metadata() -> dict:
    return {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "python_version": sys.version,
        "platform": platform.platform(),
        "cpu_model": cpu_model(),
        "timer": "time.perf_counter_ns",
        "units": "milliseconds",
    }


def benchmark(sizes: tuple[int, ...], ks: tuple[int, ...], repeats: int) -> dict:
    rows = []
    execution_orders = []
    start_time = perf_counter()
    order_rng = random.Random(SEED + 100000)
    for n in sizes:
        for kind in DATA_TYPES:
            # One untimed warm-up for each k on a separate fixed-seed input.
            warm_input = make_input(n, kind, SEED + 10000)
            warm_expected = sorted(warm_input)
            warm_order = list(ks)
            order_rng.shuffle(warm_order)
            for k in warm_order:
                actual = warm_input.copy()
                hybrid_sort(actual, k)
                assert actual == warm_expected

            samples = {k: [] for k in ks}
            for repeat in range(repeats):
                # The input is identical for all k within the same repeat.
                original = make_input(n, kind, SEED + repeat)
                expected = sorted(original)
                order = list(ks)
                order_rng.shuffle(order)
                execution_orders.append({
                    "n": n, "data_type": kind, "repeat": repeat + 1, "ks": order,
                })
                for k in order:
                    actual = original.copy()  # Excluded from measured time.
                    before = perf_counter_ns()
                    hybrid_sort(actual, k)  # Includes the O(n) buffer allocation.
                    elapsed_ns = perf_counter_ns() - before
                    assert actual == expected  # Excluded from measured time.
                    samples[k].append(elapsed_ns / 1_000_000)
            for k in ks:
                rows.append({
                    "n": n, "data_type": kind, "k": k,
                    "samples_ms": samples[k],
                    "median_ms": statistics.median(samples[k]),
                    "min_ms": min(samples[k]), "max_ms": max(samples[k]),
                })
            print(f"Completed n={n}, data_type={kind}", flush=True)

    target_n = max(sizes)
    medians = {(row["data_type"], row["k"]): row["median_ms"]
               for row in rows if row["n"] == target_n}
    summaries = []
    for k in ks:
        times = [medians[(kind, k)] for kind in DATA_TYPES]
        ratios = [medians[(kind, k)] / medians[(kind, 1)] for kind in DATA_TYPES]
        geometric_ratio = math.exp(statistics.mean(math.log(ratio) for ratio in ratios))
        summaries.append({
            "k": k,
            "arithmetic_mean_ms": statistics.mean(times),
            "geometric_mean_ms": math.exp(statistics.mean(math.log(t) for t in times)),
            "geometric_mean_time_ratio_vs_k1": geometric_ratio,
            "geometric_mean_speedup_vs_k1": 1 / geometric_ratio,
        })
    best = min(summaries, key=lambda row: row["geometric_mean_time_ratio_vs_k1"])
    best_by_type = {
        kind: min(ks, key=lambda k: medians[(kind, k)]) for kind in DATA_TYPES
    }
    return {
        "config": {
            "sizes": sizes, "ks": ks, "data_types": DATA_TYPES,
            "repeats": repeats, "warmups_per_configuration": 1,
            "base_seed": SEED,
            "repeat_seed_rule": "20260921 + zero_based_repeat",
            "warmup_seed": SEED + 10000,
            "order_seed": SEED + 100000,
            "input_random": "uniform integers in [-n, n]",
            "input_sorted": "ascending version of random input",
            "input_reversed": "descending version of random input",
            "input_few_unique": "uniform integers in [0, 15]",
            "timed": "hybrid_sort only, including auxiliary buffer allocation",
            "excluded": "input generation, input copying, sorted() oracle, validation",
            "baseline": "same bottom-up implementation with k=1",
            "merge_order_shortcut": False,
        },
        "rows": rows,
        "execution_orders": execution_orders,
        "summary": {
            "n": target_n,
            "aggregation": "equal weight across four data types; ratios use median times",
            "by_k": summaries,
            "best_sampled_k_by_geometric_mean": best["k"],
            "best_sampled_k_by_data_type": best_by_type,
            "interpretation": "Candidate from this implementation, machine, inputs and sampled k values; not a universal optimum.",
        },
        "validated_timed_runs": len(sizes) * len(DATA_TYPES) * len(ks) * repeats,
        "validated_warmup_runs": len(sizes) * len(DATA_TYPES) * len(ks),
        "elapsed_seconds_including_warmup_and_validation": perf_counter() - start_time,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("check", "demo", "benchmark", "all"), default="all")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("experiment_results.json"))
    parser.add_argument("--sizes", type=int, nargs="+", default=DEFAULT_SIZES)
    parser.add_argument("--ks", type=int, nargs="+", default=DEFAULT_KS)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    if args.repeats < 1 or any(n < 1 for n in args.sizes):
        parser.error("repeats and sizes must be positive")
    if any(k < 1 for k in args.ks) or 1 not in args.ks or len(set(args.ks)) != len(args.ks):
        parser.error("ks must contain distinct positive integers including baseline k=1")
    start = perf_counter()
    if args.mode in ("demo", "all"):
        values = [9, -2, 7, 3, 7, 0, 5, 1, -2, 8]
        original = values.copy()
        hybrid_sort(values, k=4)
        print("Demo k=4:", original, "->", values)
    if args.mode == "demo":
        return
    result = {"metadata": metadata(), "correctness": check_correctness()}
    print("Correctness:", json.dumps(result["correctness"], ensure_ascii=False))
    if args.mode in ("benchmark", "all"):
        result["benchmark"] = benchmark(tuple(args.sizes), tuple(args.ks), args.repeats)
    result["total_elapsed_seconds"] = perf_counter() - start
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Saved:", args.output.name)
    print("Elapsed seconds:", round(result["total_elapsed_seconds"], 3))
    if "benchmark" in result:
        print("Summary:", json.dumps(result["benchmark"]["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
