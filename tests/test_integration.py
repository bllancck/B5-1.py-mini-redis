"""CLI부터 저장소 상태까지 필수 기능의 통합 흐름을 검증한다."""

import unittest

from mini_redis.cli import CommandProcessor
from mini_redis.core import MiniRedis


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class MiniRedisIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FakeClock()
        self.processor = CommandProcessor(MiniRedis(clock=self.clock))

    def test_basic_storage_scenario_through_cli(self) -> None:
        self.assertEqual(self._execute('SET user:1 "Alice Smith"'), "OK")
        self.assertEqual(self._execute("GET user:1"), '"Alice Smith"')
        self.assertEqual(self._execute("EXISTS user:1"), "(integer) 1")
        self.assertEqual(self._execute("DBSIZE"), "(integer) 1")
        self.assertEqual(self._execute("KEYS"), '1. "user:1"')
        self.assertEqual(self._execute("DEL user:1"), "(integer) 1")
        self.assertEqual(self._execute("GET user:1"), "(nil)")

    def test_lru_eviction_scenario_through_cli(self) -> None:
        self._execute("SET A 111")
        self._execute("SET B 222")
        self._execute("SET C 333")
        self._execute("GET A")
        self._execute("CONFIG SET maxmemory 8")

        self.assertEqual(self._execute("SET D 444"), "OK")

        self.assertEqual(self._execute("EXISTS A"), "(integer) 1")
        self.assertEqual(self._execute("EXISTS B"), "(integer) 0")
        self.assertEqual(self._execute("EXISTS C"), "(integer) 0")
        self.assertEqual(self._execute("EXISTS D"), "(integer) 1")
        self.assertEqual(
            self._execute("INFO memory"),
            "used_memory:8\nmaxmemory:8\nevicted_keys:2",
        )

    def test_memory_accounting_and_oom_scenario_through_cli(self) -> None:
        self.assertEqual(self._execute("SET 한 글"), "OK")
        self.assertIn("used_memory:6", self._execute("INFO memory"))

        self.assertEqual(self._execute("SET 한 ab"), "OK")
        self.assertIn("used_memory:5", self._execute("INFO memory"))

        self.assertEqual(self._execute("DEL 한"), "(integer) 1")
        self.assertIn("used_memory:0", self._execute("INFO memory"))

        self._execute("CONFIG SET maxmemory 5")
        self.assertEqual(
            self._execute("SET long xx"), self.processor.redis.OOM_ERROR
        )
        self.assertEqual(self._execute("DBSIZE"), "(integer) 0")

    def test_ttl_overwrite_and_expiration_scenario_through_cli(self) -> None:
        self._execute("SET session old")
        self.assertEqual(self._execute("EXPIRE session 3"), "(integer) 1")

        self.clock.advance(1)
        self.assertEqual(self._execute("TTL session"), "(integer) 2")

        self._execute("SET session new")
        self.clock.advance(2)
        self.assertEqual(self._execute("TTL session"), "(integer) -1")
        self.assertEqual(self._execute("GET session"), '"new"')

        self._execute("EXPIRE session 1")
        self.clock.advance(1)
        self.assertEqual(self._execute("GET session"), "(nil)")
        self.assertEqual(self._execute("TTL session"), "(integer) -2")
        self.assertIn("used_memory:0", self._execute("INFO memory"))

    def test_error_and_exit_scenario(self) -> None:
        self.assertEqual(
            self._execute("HELLO"), "(error) ERR unknown command 'HELLO'"
        )
        self.assertEqual(
            self._execute("GET"),
            "(error) ERR wrong number of arguments for 'GET' command",
        )
        self.assertEqual(
            self._execute("CONFIG SET maxmemory abc"),
            self.processor.redis.INTEGER_ERROR,
        )
        self.assertEqual(self.processor.execute("quit"), (True, None))

    def _execute(self, line: str) -> str:
        should_exit, result = self.processor.execute(line)
        self.assertFalse(should_exit)
        self.assertIsNotNone(result)
        return result


if __name__ == "__main__":
    unittest.main()
