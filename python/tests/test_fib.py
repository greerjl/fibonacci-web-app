import pytest

# Unit tests for the pure Fibonacci generator to lock in its contract.
from python.main import fibonacci_first_n


def test_fibonacci_n1():
  assert fibonacci_first_n(1) == [0]


def test_fibonacci_n2():
  assert fibonacci_first_n(2) == [0, 1]


def test_fibonacci_n6():
  assert fibonacci_first_n(6) == [0, 1, 1, 2, 3, 5]


def test_fibonacci_rejects_non_positive():
  with pytest.raises(ValueError):
    fibonacci_first_n(0)
  with pytest.raises(ValueError):
    fibonacci_first_n(-1)
