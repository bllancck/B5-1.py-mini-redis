"""Mini Redis의 메모리 계산, 제한, LRU 자동 제거를 검증한다."""

import unittest

from mini_redis.core import MiniRedis


class MemoryManagementTest(unittest.TestCase):
    def setUp(self) -> None:
        self.redis = MiniRedis()

    def test_config_and_initial_memory_info(self) -> None:
        self.assertEqual(
            self.redis.info_memory(),
            "used_memory:0\nmaxmemory:0\nevicted_keys:0",
        )
        self.assertEqual(self.redis.config_set_maxmemory("10"), "OK")
        self.assertEqual(
            self.redis.info_memory(),
            "used_memory:0\nmaxmemory:10\nevicted_keys:0",
        )

        self.assertEqual(
            self.redis.config_set_maxmemory("invalid"), self.redis.INTEGER_ERROR
        )
        self.assertEqual(self.redis.config_set_maxmemory(-1), self.redis.INTEGER_ERROR)
        self.assertEqual(
            self.redis.info_memory(),
            "used_memory:0\nmaxmemory:10\nevicted_keys:0",
        )

    def test_used_memory_counts_utf8_bytes(self) -> None:
        self.redis.set("한", "글")
        self.redis.set("a", "é")

        self.assertEqual(
            self.redis.info_memory(),
            "used_memory:9\nmaxmemory:0\nevicted_keys:0",
        )

    def test_overwrite_and_delete_update_used_memory(self) -> None:
        self.redis.set("key", "a")
        self.assertIn("used_memory:4", self.redis.info_memory())

        self.redis.set("key", "abcd")
        self.assertIn("used_memory:7", self.redis.info_memory())

        self.redis.delete("key")
        self.assertEqual(
            self.redis.info_memory(),
            "used_memory:0\nmaxmemory:0\nevicted_keys:0",
        )

    def test_zero_maxmemory_is_unlimited(self) -> None:
        self.assertEqual(self.redis.config_set_maxmemory(0), "OK")
        self.assertEqual(self.redis.set("large", "x" * 1000), "OK")

        self.assertEqual(self.redis.exists("large"), "(integer) 1")
        self.assertIn("evicted_keys:0", self.redis.info_memory())

    def test_set_evicts_oldest_keys_until_within_limit(self) -> None:
        self.redis.set("A", "111")
        self.redis.set("B", "222")
        self.redis.set("C", "333")
        self.redis.get("A")

        self.assertEqual(self.redis.config_set_maxmemory(8), "OK")
        self.assertEqual(self.redis.dbsize(), "(integer) 3")
        self.assertIn("used_memory:12", self.redis.info_memory())

        self.assertEqual(self.redis.set("D", "444"), "OK")

        self.assertEqual(self.redis.exists("A"), "(integer) 1")
        self.assertEqual(self.redis.exists("B"), "(integer) 0")
        self.assertEqual(self.redis.exists("C"), "(integer) 0")
        self.assertEqual(self.redis.exists("D"), "(integer) 1")
        self.assertEqual(self.redis.dbsize(), "(integer) 2")
        self.assertEqual(
            self.redis.info_memory(),
            "used_memory:8\nmaxmemory:8\nevicted_keys:2",
        )

    def test_single_oversized_entry_returns_oom_without_storing(self) -> None:
        self.redis.config_set_maxmemory(5)

        self.assertEqual(self.redis.set("long", "xx"), self.redis.OOM_ERROR)

        self.assertEqual(self.redis.dbsize(), "(integer) 0")
        self.assertEqual(
            self.redis.info_memory(),
            "used_memory:0\nmaxmemory:5\nevicted_keys:0",
        )

    def test_oversized_overwrite_preserves_existing_entry(self) -> None:
        self.redis.config_set_maxmemory(5)
        self.redis.set("a", "1")

        self.assertEqual(self.redis.set("a", "12345"), self.redis.OOM_ERROR)

        self.assertEqual(self.redis.get("a"), '"1"')
        self.assertEqual(self.redis.dbsize(), "(integer) 1")
        self.assertEqual(
            self.redis.info_memory(),
            "used_memory:2\nmaxmemory:5\nevicted_keys:0",
        )


if __name__ == "__main__":
    unittest.main()
