"""Mini Redis 명령 파싱, 오류 출력, REPL 반복을 검증한다."""

import unittest

from mini_redies.cli import CommandProcessor, run_cli
from mini_redies.core import MiniRedis


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class CommandProcessorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FakeClock()
        self.processor = CommandProcessor(MiniRedis(clock=self.clock))

    def test_basic_commands_and_quoted_value(self) -> None:
        self.assertEqual(self._execute('SET name "Alice Smith"'), "OK")
        self.assertEqual(self._execute("GET name"), '"Alice Smith"')
        self.assertEqual(self._execute("EXISTS name"), "(integer) 1")
        self.assertEqual(self._execute("DBSIZE"), "(integer) 1")
        self.assertEqual(self._execute("KEYS"), '1. "name"')
        self.assertEqual(self._execute("DEL name"), "(integer) 1")
        self.assertEqual(self._execute("GET name"), "(nil)")

    def test_memory_commands_and_oom(self) -> None:
        self.assertEqual(self._execute("CONFIG SET maxmemory 5"), "OK")
        self.assertEqual(
            self._execute("INFO memory"),
            "used_memory:0\nmaxmemory:5\nevicted_keys:0",
        )
        self.assertEqual(
            self._execute("SET long xx"), self.processor.redis.OOM_ERROR
        )

    def test_ttl_commands(self) -> None:
        self._execute("SET name Alice")

        self.assertEqual(self._execute("EXPIRE name 3"), "(integer) 1")
        self.assertEqual(self._execute("TTL name"), "(integer) 3")

        self.clock.advance(3)
        self.assertEqual(self._execute("GET name"), "(nil)")
        self.assertEqual(self._execute("TTL name"), "(integer) -2")

    def test_commands_and_subcommands_are_case_insensitive(self) -> None:
        self.assertEqual(self._execute("config set MAXMEMORY 10"), "OK")
        self.assertEqual(self._execute("set name Alice"), "OK")
        self.assertEqual(self._execute("get name"), '"Alice"')
        self.assertIn("maxmemory:10", self._execute("info MEMORY"))

    def test_unknown_wrong_argument_and_syntax_errors(self) -> None:
        self.assertEqual(
            self._execute("HELLO"), "(error) ERR unknown command 'HELLO'"
        )

        wrong_commands = [
            ("SET key", "SET"),
            ("GET", "GET"),
            ("DEL", "DEL"),
            ("EXISTS", "EXISTS"),
            ("DBSIZE extra", "DBSIZE"),
            ("KEYS *", "KEYS"),
            ("CONFIG SET maxmemory", "CONFIG"),
            ("INFO", "INFO"),
            ("EXPIRE key", "EXPIRE"),
            ("TTL", "TTL"),
        ]
        for line, command in wrong_commands:
            with self.subTest(line=line):
                self.assertEqual(
                    self._execute(line),
                    "(error) ERR wrong number of arguments for '{}' command".format(
                        command
                    ),
                )

        self.assertEqual(
            self._execute('SET name "Alice'), self.processor.SYNTAX_ERROR
        )
        self.assertEqual(
            self._execute("CONFIG GET maxmemory 10"), self.processor.SYNTAX_ERROR
        )
        self.assertEqual(self._execute("INFO stats"), self.processor.SYNTAX_ERROR)

    def test_integer_errors(self) -> None:
        self.assertEqual(
            self._execute("CONFIG SET maxmemory abc"),
            self.processor.redis.INTEGER_ERROR,
        )
        self._execute("SET name Alice")
        self.assertEqual(
            self._execute("EXPIRE name abc"), self.processor.redis.INTEGER_ERROR
        )

    def test_blank_exit_and_quit(self) -> None:
        self.assertEqual(self.processor.execute("   "), (False, None))
        self.assertEqual(self.processor.execute("exit"), (True, None))
        self.assertEqual(self.processor.execute("QUIT"), (True, None))
        self.assertEqual(
            self._execute("exit now"),
            "(error) ERR wrong number of arguments for 'EXIT' command",
        )

    def _execute(self, line: str) -> str:
        should_exit, result = self.processor.execute(line)
        self.assertFalse(should_exit)
        self.assertIsNotNone(result)
        return result


class ReplTest(unittest.TestCase):
    def test_repl_prompts_prints_results_and_quits(self) -> None:
        commands = iter(["SET name Alice", "GET name", "quit"])
        prompts = []
        outputs = []

        def fake_input(prompt: str) -> str:
            prompts.append(prompt)
            return next(commands)

        run_cli(input_function=fake_input, output_function=outputs.append)

        self.assertEqual(prompts, ["mini-redis> "] * 3)
        self.assertEqual(outputs, ["OK", '"Alice"'])


if __name__ == "__main__":
    unittest.main()
