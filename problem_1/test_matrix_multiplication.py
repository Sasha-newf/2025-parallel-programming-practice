import subprocess
import random
import os
import json
import time
import logging
from typing import List, Optional, Tuple, Iterator
from dataclasses import dataclass
from functools import cached_property

import pytest

logger: logging.Logger = logging.getLogger(__name__)


Matrix = List[List[float]]


@dataclass
class CompactMatrix:
    rows: int
    cols: int
    a: int
    b: int
    x: int
    y: int
    z: int
    p: int

    @cached_property
    def data(self) -> Matrix:
        intermediate = [[self.b % self.p] * self.cols for _ in range(self.rows)]
        intermediate[0][0] = self.a % self.p

        for i in range(self.rows):
            for j in range(self.cols):
                if i > 0 and j > 0:
                    intermediate[i][j] = (
                        intermediate[i][j] + intermediate[i - 1][j - 1] * self.x
                    ) % self.p
                if i > 0:
                    intermediate[i][j] = (
                        intermediate[i][j] + intermediate[i - 1][j] * self.y
                    ) % self.p
                if j > 0:
                    intermediate[i][j] = (
                        intermediate[i][j] + intermediate[i][j - 1] * self.z
                    ) % self.p

        max_value = max(max(row) for row in intermediate)

        return [
            [intermediate[i][j] / max_value for j in range(self.cols)]
            for i in range(self.rows)
        ]

    def to_str(self) -> str:
        return f"{self.rows} {self.cols}\n{self.a} {self.b} {self.x} {self.y} {self.z} {self.p}"


def test_matrix_multiplication(
    matrix_left: CompactMatrix,
    matrix_right: CompactMatrix,
    matrix_expected: Matrix,
    timeout_seconds: Optional[float],
) -> None:
    _prepare_solution()

    matrix_actual: Matrix = _call_solution(matrix_left, matrix_right, timeout_seconds)

    assert _all_close(matrix_expected, matrix_actual, tol=1e-7), "Matrices don't match"


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if metafunc.function.__name__ != "test_matrix_multiplication":
        return

    random.seed(42)

    # Simple small use cases to check correctness
    simple_test_data = [
        (matrix_left, matrix_right, _simple_multiply(matrix_left, matrix_right), None)
        for matrix_left, matrix_right in [
            _generate_matrix_pair(3, 4, 3) for _ in range(10)
        ]
    ]

    # Larger test cases that require parallelism to successfully pass
    larger_test_data = [
        (matrix_left, matrix_right, matrix_expected, 2.5)
        for matrix_left, matrix_right, matrix_expected in _read_test_data()
    ]

    metafunc.parametrize(
        "matrix_left,matrix_right,matrix_expected,timeout_seconds",
        simple_test_data + larger_test_data,
    )


def _all_close(left: Matrix, right: Matrix, tol: float) -> bool:
    return (
        max(
            abs(left_val - right_val)
            for left_val, right_val in zip(
                [el for row in left for el in row], [el for row in right for el in row]
            )
        )
        < tol
    )


def _simple_multiply(
    left_compact: CompactMatrix, right_compact: CompactMatrix
) -> Matrix:
    left = left_compact.data
    right = right_compact.data
    assert left and right and len(left[0]) == len(right), (
        f"Matrices ({len(left)} x {len(left[0]) if left else 0}) and "
        f"({len(right)} x {len(right[0]) if right else 0}) cannot be multiplied"
    )

    n = len(left)
    m = len(right[0])
    l = len(right)
    result: Matrix = [[0 for _ in range(m)] for _ in range(n)]
    for i in range(n):
        for j in range(m):
            for k in range(l):
                result[i][j] += left[i][k] * right[k][j]
    return result


def _generate_matrix_pair(
    left_rows: int, left_cols: int, right_cols: int
) -> Tuple[CompactMatrix, CompactMatrix]:
    left = CompactMatrix(
        rows=left_rows,
        cols=left_cols,
        a=random.randint(1, int(1e9)),
        b=random.randint(1, int(1e9)),
        x=random.randint(1, int(1e9)),
        y=random.randint(1, int(1e9)),
        z=random.randint(1, int(1e9)),
        p=_generate_prime_number(9),
    )
    right = CompactMatrix(
        rows=left_cols,
        cols=right_cols,
        a=random.randint(1, int(1e9)),
        b=random.randint(1, int(1e9)),
        x=random.randint(1, int(1e9)),
        y=random.randint(1, int(1e9)),
        z=random.randint(1, int(1e9)),
        p=_generate_prime_number(9),
    )

    return left, right


def _generate_prime_number(num_digits: int) -> int:
    lower_bound: int = 10 ** (num_digits - 1)
    upper_bound: int = (10**num_digits) - 1

    while True:
        candidate: int = random.randrange(lower_bound | 1, upper_bound, 2)
        if is_prime(candidate):
            return candidate


def is_prime(n: int) -> bool:
    if n <= 1:
        return False
    elif n <= 3:
        return True
    elif n % 2 == 0:
        return False

    # Write n - 1 as 2^s * d
    s = 0
    d = n - 1
    while d % 2 == 0:
        d //= 2
        s += 1

    # Predefined bases for deterministic testing
    bases = [2, 3, 5, 7, 11, 13, 17]

    for a in bases:
        if a >= n:
            continue  # Skip bases greater than or equal to n
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue  # Possibly prime
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break  # Possibly prime
        else:
            return False  # Composite number
    return True  # Probably prime


def _read_test_data() -> Iterator[Tuple[CompactMatrix, CompactMatrix, Matrix]]:
    test_data_path: str = os.path.join(os.path.dirname(__file__), "test_data")
    for filename in os.listdir(test_data_path):
        with open(os.path.join(test_data_path, filename), "rt") as f:
            data = json.load(f)
            yield (
                CompactMatrix(**data["matrix_left"]),
                CompactMatrix(**data["matrix_right"]),
                data["matrix_expected"],
            )


def _prepare_solution() -> None:
    """
    This function prepares the solution to be executed.

    E.g. for a solution written in C++ it might contain building the code. For
    a solution e.g. in Python this step might not do anything.
    """
    try:
        subprocess.run(["make", "prepare"], check=True)
    except Exception:
        pytest.fail(f"Prearing solution failed, see output for more information")


def _call_solution(
    left: CompactMatrix, right: CompactMatrix, timeout_seconds: Optional[float]
) -> Matrix:
    """
    This function calls the solution that was prepared earlier.
    """
    input_str = f"{left.to_str()}\n{right.to_str()}"

    try:
        start_time: float = time.perf_counter()
        result: subprocess.CompletedProcess[str] = subprocess.run(
            ["make", "run"],
            input=input_str,
            text=True,
            stdout=subprocess.PIPE,
            check=True,
            timeout=timeout_seconds,
        )
        end_time: float = time.perf_counter()
        logger.info(
            f"Solution successfully executed in {end_time - start_time:.6f} seconds"
        )
        lines = result.stdout.strip().split("\n")
        n, _ = [int(num) for num in lines[0].strip().split()]
        actual: Matrix = []
        for i in range(n):
            actual.append([float(num) for num in lines[i + 1].strip().split()])
        return actual
    except Exception as e:
        pytest.fail(f"Execution failed with error: {e}")
