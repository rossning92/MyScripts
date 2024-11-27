import logging
import unittest

from usetool import use_tool

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


def add(a: int, b: int) -> int:
    return a + b


def multiply(a: int, b: int) -> int:
    return a * b


def power(a: int, b: int) -> int:
    n = 1
    for _ in range(b):
        n *= a
    return n


class TestUseToolFunction(unittest.TestCase):
    def test_use_tool_power(self):
        result = use_tool("Calculate 2 to the power of 8", tools=[add, multiply, power])
        self.assertIn("256", result)


if __name__ == "__main__":
    unittest.main()
