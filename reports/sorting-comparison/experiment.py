"""四种经典排序算法及其可复现的性能实验。

默认实验对四种算法测试 512~8192 个随机整数；考虑到冒泡排序和
插入排序的 O(n^2) 开销，更大的规模只测试归并排序和快速排序。
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


SortFunction = Callable[[list[int]], None]


def bubble_sort(values: list[int]) -> None:
    """原地升序冒泡排序；已有序时可提前结束。"""
    end = len(values) - 1
    while end > 0:
        last_swap = 0
        for index in range(end):
            if values[index] > values[index + 1]:
                values[index], values[index + 1] = (
                    values[index + 1],
                    values[index],
                )
                last_swap = index
        end = last_swap


def insertion_sort(values: list[int]) -> None:
    """原地升序插入排序。"""
    for index in range(1, len(values)):
        current = values[index]
        position = index - 1
        while position >= 0 and values[position] > current:
            values[position + 1] = values[position]
            position -= 1
        values[position + 1] = current


def merge_sort(values: list[int]) -> None:
    """使用一个共享辅助数组完成稳定的归并排序。"""
    if len(values) < 2:
        return

    buffer = [0] * len(values)

    def sort_range(left: int, right: int) -> None:
        if right - left <= 1:
            return

        middle = (left + right) // 2
        sort_range(left, middle)
        sort_range(middle, right)

        left_index = left
        right_index = middle
        write_index = left

        while left_index < middle and right_index < right:
            # 相等时先取左半部分的元素，使算法保持稳定。
            if values[left_index] <= values[right_index]:
                buffer[write_index] = values[left_index]
                left_index += 1
            else:
                buffer[write_index] = values[right_index]
                right_index += 1
            write_index += 1

        while left_index < middle:
            buffer[write_index] = values[left_index]
            left_index += 1
            write_index += 1

        while right_index < right:
            buffer[write_index] = values[right_index]
            right_index += 1
            write_index += 1

        for write_index in range(left, right):
            values[write_index] = buffer[write_index]

    sort_range(0, len(values))


def _median_of_three(first: int, middle: int, last: int) -> int:
    """返回三个整数的中位数，不创建临时列表。"""
    if first < middle:
        if middle < last:
            return middle
        return last if first < last else first
    if first < last:
        return first
    return last if middle < last else middle


def quick_sort(values: list[int]) -> None:
    """三数取中、三路分区的原地快速排序。

    每次只递归处理较小分区，并用循环处理较大分区，从而把递归栈
    深度控制在 O(log n)；时间复杂度的最坏情况仍可能是 O(n^2)。
    """

    def sort_range(left: int, right: int) -> None:
        while left < right:
            middle = (left + right) // 2
            pivot = _median_of_three(
                values[left], values[middle], values[right]
            )

            less = left
            index = left
            greater = right
            while index <= greater:
                if values[index] < pivot:
                    values[less], values[index] = values[index], values[less]
                    less += 1
                    index += 1
                elif values[index] > pivot:
                    values[index], values[greater] = (
                        values[greater],
                        values[index],
                    )
                    greater -= 1
                else:
                    index += 1

            # 先递归较短区间，较长区间交给下一次循环。
            if less - left < right - greater:
                sort_range(left, less - 1)
                left = greater + 1
            else:
                sort_range(greater + 1, right)
                right = less - 1

    sort_range(0, len(values) - 1)


ALGORITHMS: dict[str, SortFunction] = {
    "Bubble": bubble_sort,
    "Insertion": insertion_sort,
    "Merge": merge_sort,
    "Quick": quick_sort,
}

CHINESE_NAMES = {
    "Bubble": "冒泡排序",
    "Insertion": "插入排序",
    "Merge": "归并排序",
    "Quick": "快速排序",
}

FAST_ALGORITHMS = {
    "Merge": merge_sort,
    "Quick": quick_sort,
}


@dataclass(frozen=True)
class Timing:
    size: int
    algorithm: str
    repetition: int
    elapsed_ns: int


def self_test() -> None:
    """用边界用例和随机小样本验证四种实现。"""
    cases = [
        [],
        [1],
        [1, 2, 3, 4, 5],
        [5, 4, 3, 2, 1],
        [7, 7, 7, 7],
        [3, -1, 2, -1, 0, 3],
        [9, 1, 8, 2, 7, 3, 6, 4, 5],
    ]
    test_rng = random.Random(314159)
    for length in range(20):
        cases.append([test_rng.randint(-20, 20) for _ in range(length)])

    for name, algorithm in ALGORITHMS.items():
        for original in cases:
            actual = original.copy()
            algorithm(actual)
            expected = sorted(original)
            if actual != expected:
                raise AssertionError(
                    f"{name} failed: input={original}, "
                    f"expected={expected}, actual={actual}"
                )


def warm_up() -> None:
    """在正式计时前运行所有算法，减少首次执行产生的偶然开销。"""
    rng = random.Random(271828)
    sample = [rng.randint(-1_000, 1_000) for _ in range(64)]
    for algorithm in ALGORITHMS.values():
        work = sample.copy()
        algorithm(work)


def benchmark_group(
    sizes: Iterable[int],
    algorithms: dict[str, SortFunction],
    repetitions: int,
    rng: random.Random,
) -> list[Timing]:
    """测试一组算法；复制、生成数据和校验均不计入排序时间。"""
    results: list[Timing] = []
    names = list(algorithms)

    for size_index, size in enumerate(sizes):
        for repetition in range(1, repetitions + 1):
            original = [rng.randint(-1_000_000_000, 1_000_000_000) for _ in range(size)]
            expected = sorted(original)

            # 每轮循环改变执行次序，降低固定测试顺序造成的系统偏差。
            shift = (size_index + repetition - 1) % len(names)
            execution_order = names[shift:] + names[:shift]

            for name in execution_order:
                work = original.copy()
                start_ns = time.perf_counter_ns()
                algorithms[name](work)
                elapsed_ns = time.perf_counter_ns() - start_ns

                if work != expected:
                    raise AssertionError(f"{name} produced an incorrect result at n={size}")

                results.append(
                    Timing(
                        size=size,
                        algorithm=name,
                        repetition=repetition,
                        elapsed_ns=elapsed_ns,
                    )
                )

    return results


def summarize(timings: list[Timing]) -> list[dict[str, int | float | str]]:
    grouped: dict[tuple[str, int], list[int]] = defaultdict(list)
    for timing in timings:
        grouped[(timing.algorithm, timing.size)].append(timing.elapsed_ns)

    rows: list[dict[str, int | float | str]] = []
    for algorithm in ALGORITHMS:
        previous_size: int | None = None
        previous_median: float | None = None
        sizes = sorted(size for name, size in grouped if name == algorithm)

        for size in sizes:
            samples = grouped[(algorithm, size)]
            median_ns = float(statistics.median(samples))
            if algorithm in {"Bubble", "Insertion"}:
                normalization = "T(n)/n^2"
                normalized_ns = median_ns / (size * size)
            else:
                normalization = "T(n)/(n*log2(n))"
                normalized_ns = median_ns / (size * math.log2(size))

            growth = (
                median_ns / previous_median
                if previous_median is not None and previous_median > 0
                else math.nan
            )
            rows.append(
                {
                    "size": size,
                    "algorithm": algorithm,
                    "repetitions": len(samples),
                    "median_ms": median_ns / 1_000_000,
                    "min_ms": min(samples) / 1_000_000,
                    "max_ms": max(samples) / 1_000_000,
                    "previous_size": previous_size if previous_size is not None else "",
                    "growth_ratio": growth,
                    "normalization": normalization,
                    "normalized_ns": normalized_ns,
                }
            )
            previous_size = size
            previous_median = median_ns

    return rows


def write_raw_csv(path: Path, timings: list[Timing]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["size", "algorithm", "repetition", "elapsed_ns", "elapsed_ms"])
        for timing in sorted(
            timings,
            key=lambda item: (
                item.size,
                list(ALGORITHMS).index(item.algorithm),
                item.repetition,
            ),
        ):
            writer.writerow(
                [
                    timing.size,
                    timing.algorithm,
                    timing.repetition,
                    timing.elapsed_ns,
                    f"{timing.elapsed_ns / 1_000_000:.6f}",
                ]
            )


def write_summary_csv(
    path: Path, rows: list[dict[str, int | float | str]]
) -> None:
    fieldnames = [
        "size",
        "algorithm",
        "repetitions",
        "median_ms",
        "min_ms",
        "max_ms",
        "previous_size",
        "growth_ratio",
        "normalization",
        "normalized_ns",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            output = dict(row)
            for field in ("median_ms", "min_ms", "max_ms", "normalized_ns"):
                output[field] = f"{float(row[field]):.6f}"
            growth = float(row["growth_ratio"])
            output["growth_ratio"] = "" if math.isnan(growth) else f"{growth:.4f}"
            writer.writerow(output)


def create_chart(
    path: Path, rows: list[dict[str, int | float | str]]
) -> bool:
    """生成运行时间和翻倍增长率图；缺少 matplotlib 时仅跳过图表。"""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False

    colors = {
        "Bubble": "#d62728",
        "Insertion": "#ff7f0e",
        "Merge": "#1f77b4",
        "Quick": "#2ca02c",
    }
    figure, (time_axis, growth_axis) = plt.subplots(1, 2, figsize=(13, 5.2))

    for algorithm in ALGORITHMS:
        algorithm_rows = [row for row in rows if row["algorithm"] == algorithm]
        sizes = [int(row["size"]) for row in algorithm_rows]
        medians = [float(row["median_ms"]) for row in algorithm_rows]
        growth_sizes = []
        growth_values = []
        for row in algorithm_rows:
            growth = float(row["growth_ratio"])
            if not math.isnan(growth):
                growth_sizes.append(int(row["size"]))
                growth_values.append(growth)

        time_axis.plot(
            sizes,
            medians,
            marker="o",
            linewidth=2,
            label=algorithm,
            color=colors[algorithm],
        )
        growth_axis.plot(
            growth_sizes,
            growth_values,
            marker="o",
            linewidth=2,
            label=algorithm,
            color=colors[algorithm],
        )

    time_axis.set_xscale("log", base=2)
    time_axis.set_yscale("log")
    time_axis.set_xlabel("Input size n (log2 scale)")
    time_axis.set_ylabel("Median execution time / ms (log scale)")
    time_axis.set_title("Execution Time")
    time_axis.grid(True, which="both", linestyle="--", alpha=0.35)
    time_axis.legend()

    # 参考值按实际相邻规模计算，因此自定义规模不必恰好翻倍。
    quadratic_rows = [
        row
        for row in rows
        if row["algorithm"] == "Bubble" and row["previous_size"] != ""
    ]
    n_log_n_rows = [
        row
        for row in rows
        if row["algorithm"] == "Merge" and row["previous_size"] != ""
    ]
    growth_axis.plot(
        [int(row["size"]) for row in quadratic_rows],
        [
            (int(row["size"]) / int(row["previous_size"])) ** 2
            for row in quadratic_rows
        ],
        color="#777777",
        linestyle="--",
        linewidth=1.2,
        label="c*n^2 reference",
    )
    growth_axis.plot(
        [int(row["size"]) for row in n_log_n_rows],
        [
            (
                int(row["size"]) * math.log2(int(row["size"]))
                / (
                    int(row["previous_size"])
                    * math.log2(int(row["previous_size"]))
                )
            )
            for row in n_log_n_rows
        ],
        color="#999999",
        linestyle=":",
        linewidth=1.2,
        label="c*n*log2(n) reference",
    )
    growth_axis.set_xscale("log", base=2)
    growth_axis.set_xlabel("Input size n (compared with previous tested size)")
    growth_axis.set_ylabel("T(n) / T(previous n)")
    growth_axis.set_title("Growth Relative to Previous Input Size")
    growth_axis.grid(True, linestyle="--", alpha=0.35)
    growth_axis.legend(fontsize=8, ncol=2)

    figure.suptitle("Sorting Algorithm Benchmark", fontsize=14)
    figure.tight_layout()
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)
    return True


def print_summary(rows: list[dict[str, int | float | str]]) -> None:
    sizes = sorted({int(row["size"]) for row in rows})
    lookup = {
        (int(row["size"]), str(row["algorithm"])): float(row["median_ms"])
        for row in rows
    }

    print("\nMedian execution time (ms)")
    print("| n | Bubble | Insertion | Merge | Quick |")
    print("|---:|---:|---:|---:|---:|")
    for size in sizes:
        cells = []
        for algorithm in ALGORITHMS:
            value = lookup.get((size, algorithm))
            cells.append("-" if value is None else f"{value:.3f}")
        print(f"| {size} | " + " | ".join(cells) + " |")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="实现并测试冒泡、插入、归并和快速排序。"
    )
    parser.add_argument(
        "--common-sizes",
        nargs="+",
        type=int,
        default=[512, 1024, 2048, 4096, 8192],
        help="四种算法共同测试的数据规模。",
    )
    parser.add_argument(
        "--extended-sizes",
        nargs="+",
        type=int,
        default=[16384, 32768, 65536, 131072],
        help="只测试归并和快速排序的扩展规模。",
    )
    parser.add_argument(
        "--common-repeats",
        type=int,
        default=5,
        help="共同规模的重复次数，默认 5。",
    )
    parser.add_argument(
        "--extended-repeats",
        type=int,
        default=5,
        help="扩展规模的重复次数，默认 5。",
    )
    parser.add_argument("--seed", type=int, default=20260919, help="随机种子。")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "results",
        help="CSV 和图表输出目录。",
    )
    parser.add_argument(
        "--self-test-only",
        action="store_true",
        help="只验证算法正确性，不运行性能实验。",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    all_sizes = args.common_sizes + args.extended_sizes
    if not all_sizes or any(size < 2 for size in all_sizes):
        raise ValueError("所有数据规模必须是大于等于 2 的整数。")
    if args.common_repeats < 1 or args.extended_repeats < 1:
        raise ValueError("重复次数必须大于等于 1。")


def main() -> None:
    args = parse_args()
    validate_args(args)
    self_test()
    print("Self-test passed for all four sorting algorithms.")
    if args.self_test_only:
        return

    warm_up()
    rng = random.Random(args.seed)
    common_sizes = sorted(set(args.common_sizes))
    common_size_set = set(common_sizes)
    extended_sizes = sorted(
        size for size in set(args.extended_sizes) if size not in common_size_set
    )

    timings = benchmark_group(
        common_sizes, ALGORITHMS, args.common_repeats, rng
    )
    if extended_sizes:
        timings.extend(
            benchmark_group(
                extended_sizes,
                FAST_ALGORITHMS,
                args.extended_repeats,
                rng,
            )
        )

    rows = summarize(timings)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_csv = args.output_dir / "raw_timings.csv"
    summary_csv = args.output_dir / "summary.csv"
    chart_path = args.output_dir / "sorting_benchmark.png"
    write_raw_csv(raw_csv, timings)
    write_summary_csv(summary_csv, rows)
    chart_created = create_chart(chart_path, rows)

    print_summary(rows)
    print(f"\nRaw timings: {raw_csv}")
    print(f"Summary: {summary_csv}")
    if chart_created:
        print(f"Chart: {chart_path}")
    else:
        print("Chart skipped because matplotlib is not installed.")


if __name__ == "__main__":
    main()
