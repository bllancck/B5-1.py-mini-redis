"""Mini Redis의 기본 저장 명령 6개와 출력 형식을 검증한다."""

import unittest

from mini_redis.core import MiniRedis


class MiniRedisTest(unittest.TestCase):
    def setUp(self) -> None:
        self.redis = MiniRedis()

    def test_empty_store_responses(self) -> None:
        self.assertEqual(self.redis.get("missing"), "(nil)")
        self.assertEqual(self.redis.delete("missing"), "(integer) 0")
        self.assertEqual(self.redis.exists("missing"), "(integer) 0")
        self.assertEqual(self.redis.dbsize(), "(integer) 0")
        self.assertEqual(self.redis.keys(), "(empty array)")

    def test_set_get_and_exists(self) -> None:
        self.assertEqual(self.redis.set("name", "Alice"), "OK")
        self.assertEqual(self.redis.get("name"), '"Alice"')
        self.assertEqual(self.redis.exists("name"), "(integer) 1")
        self.assertEqual(self.redis.dbsize(), "(integer) 1")

    def test_set_existing_key_overwrites_without_growing(self) -> None:
        self.redis.set("name", "Alice")

        self.assertEqual(self.redis.set("name", "Bob"), "OK")
        self.assertEqual(self.redis.get("name"), '"Bob"')
        self.assertEqual(self.redis.dbsize(), "(integer) 1")

    def test_delete_existing_key(self) -> None:
        self.redis.set("name", "Alice")

        self.assertEqual(self.redis.delete("name"), "(integer) 1")
        self.assertEqual(self.redis.get("name"), "(nil)")
        self.assertEqual(self.redis.exists("name"), "(integer) 0")
        self.assertEqual(self.redis.dbsize(), "(integer) 0")

    def test_keys_lists_all_keys_without_requiring_order(self) -> None:
        self.redis.set("name", "Alice")
        self.redis.set("city", "Seoul")

        lines = self.redis.keys().splitlines()
        displayed_keys = sorted(line.split(". ", 1)[1] for line in lines)

        self.assertEqual(len(lines), 2)
        self.assertEqual(displayed_keys, ['"city"', '"name"'])
        self.assertEqual(self.redis.dbsize(), "(integer) 2")

    def test_value_may_contain_spaces(self) -> None:
        self.assertEqual(self.redis.set("message", "hello world"), "OK")
        self.assertEqual(self.redis.get("message"), '"hello world"')


if __name__ == "__main__":
    unittest.main()
