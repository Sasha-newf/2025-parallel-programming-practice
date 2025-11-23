import subprocess
import random
import time
import logging
import os
import json
from typing import List, Optional, Tuple, Iterator

import pytest

logger: logging.Logger = logging.getLogger(__name__)


def test_factorization_correctness(
    number: int,
    expected_factors: List[int],
    timout_seconds: Optional[float],
) -> None:
    logger.info(f"{expected_factors=}")
    _prepare_solution()

    actual_factors: List[int] = _call_solution(number, timout_seconds)

    assert actual_factors == expected_factors, (
        f"Expected factors {expected_factors} didn't match actual factors "
        f"{actual_factors}"
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if metafunc.function.__name__ != "test_factorization_correctness":
        return

    random.seed(42)

    # Simple small use cases to check correctness
    simple_test_data = [
        (num, _simple_factorize(num), None)
        for num in [random.randint(1000, 10000) for _ in range(10)]
    ]

    # Larger test cases that require parallelism to successfully pass
    larger_test_data = [
        (num, factorization, 2) for (num, factorization) in _read_test_data()
    ]

    metafunc.parametrize(
        "number,expected_factors,timout_seconds", simple_test_data + larger_test_data
    )


def _read_test_data() -> Iterator[Tuple[int, List[int]]]:
    test_data_path: str = os.path.join(os.path.dirname(__file__), "test_data")
    for filename in os.listdir(test_data_path):
        with open(os.path.join(test_data_path, filename), "rt") as f:
            data = json.load(f)
            yield (data["num"], data["expected_factors"])


def _simple_factorize(num: int) -> List[int]:
    factors: List[int] = []
    i = 2
    while i * i <= num:
        while num % i == 0:
            factors.append(i)
            num //= i
        i += 1
    if num > 1:
        factors.append(num)
    return sorted(factors)


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


def _call_solution(input_number: int, timout_seconds: Optional[float]) -> List[int]:
    """
    This function calls the solution that was prepared earlier.
    """
    try:
        start_time: float = time.perf_counter()
        result: subprocess.CompletedProcess[str] = subprocess.run(
            ["make", "run"],
            input=str(input_number),
            text=True,
            stdout=subprocess.PIPE,
            check=True,
            timeout=timout_seconds,
        )
        end_time: float = time.perf_counter()
        logger.info(
            f"Solution successfully executed in {end_time - start_time:.6f} seconds"
        )
        return sorted([int(num.strip()) for num in result.stdout.strip().split()])
    except Exception as e:
        pytest.fail(f"Execution failed with error: {e}")
