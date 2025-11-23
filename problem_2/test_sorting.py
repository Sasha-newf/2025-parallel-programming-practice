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


@dataclass
class CompactArray:
    length: int
    a: int
    b: int
    p: int

    @cached_property
    def data(self) -> List[int]:
        result = [0] * self.length
        result[0] = self.a % self.p
        for i in range(1, self.length):
            result[i] = (result[i - 1] * self.a + self.b) % self.p
        return result

    def to_str(self) -> str:
        return f"{self.length} {self.a} {self.b} {self.p}"


def test_sorting(
    input_array: CompactArray,
    output_sampling: int,
    expected: List[int],
    timeout_seconds: Optional[float],
) -> None:
    _prepare_solution()

    actual: List[int] = _call_solution(input_array, output_sampling, timeout_seconds)

    assert expected == actual, "Output arrays don't match"


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if metafunc.function.__name__ != "test_sorting":
        return

    random.seed(42)

    # Simple small use cases to check correctness
    simple_test_data = [
        (input_array, 1, sorted(input_array.data), None)
        for input_array in [
            _generate_input_array(random.randint(10, 100)) for _ in range(10)
        ]
    ]

    # Larger test cases that require parallelism to successfully pass
    larger_test_data = [
        (input_array, output_sampling, expected, 3)
        for input_array, output_sampling, expected in _read_test_data()
    ]

    metafunc.parametrize(
        "input_array,output_sampling,expected,timeout_seconds",
        simple_test_data + larger_test_data,
    )


def _generate_input_array(length: int) -> CompactArray:
    return CompactArray(
        length=length,
        a=random.randint(1, int(1e9)),
        b=random.randint(1, int(1e9)),
        p=_generate_prime_number(9),
    )


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


def _read_test_data() -> Iterator[Tuple[CompactArray, int, List[int]]]:
    test_data_path: str = os.path.join(os.path.dirname(__file__), "test_data")
    for filename in os.listdir(test_data_path):
        with open(os.path.join(test_data_path, filename), "rt") as f:
            data = json.load(f)
            yield (
                CompactArray(**data["input_array"]),
                data["output_sampling"],
                data["expected"],
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
    input_array: CompactArray, output_sampling: int, timeout_seconds: Optional[float]
) -> List[int]:
    """
    This function calls the solution that was prepared earlier.
    """
    input_str = f"{input_array.to_str()}\n{output_sampling}"

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
        return [int(num.strip()) for num in result.stdout.strip().split()]
    except Exception as e:
        pytest.fail(f"Execution failed with error: {e}")
