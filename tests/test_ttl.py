"""Mini Redis의 TTL 설정, 만료, 관련 상태 정리를 검증한다."""

import unittest

from mini_redis import MiniRedis


class FakeClock:
    def __init__(self, now: float = 100.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class TtlTest(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FakeClock()
        self.redis = MiniRedis(clock=self.clock)

    def test_missing_key_and_key_without_expiration(self) -> None:
        self.assertEqual(self.redis.expire("missing", 3), "(integer) 0")
        self.assertEqual(self.redis.ttl("missing"), "(integer) -2")

        self.redis.set("name", "Alice")
        self.assertEqual(self.redis.ttl("name"), "(integer) -1")

    def test_expire_sets_and_counts_down_ttl(self) -> None:
        self.redis.set("name", "Alice")

        self.assertEqual(self.redis.expire("name", "3"), "(integer) 1")
        self.assertEqual(self.redis.ttl("name"), "(integer) 3")

        self.clock.advance(1)
        self.assertEqual(self.redis.ttl("name"), "(integer) 2")

    def test_expired_get_removes_all_related_state(self) -> None:
        self.redis.set("name", "Alice")
        self.redis.expire("name", 3)

        self.clock.advance(3)

        self.assertEqual(self.redis.get("name"), "(nil)")
        self.assertEqual(self.redis.ttl("name"), "(integer) -2")
        self.assertEqual(self.redis.dbsize(), "(integer) 0")
        self.assertFalse(self.redis._lru_nodes.contains("name"))
        self.assertEqual(len(self.redis._lru), 0)
        self.assertIn("used_memory:0", self.redis.info_memory())

    def test_non_positive_expiration_removes_key_immediately(self) -> None:
        self.redis.set("zero", "value")
        self.assertEqual(self.redis.expire("zero", 0), "(integer) 1")
        self.assertEqual(self.redis.get("zero"), "(nil)")

        self.redis.set("negative", "value")
        self.assertEqual(self.redis.expire("negative", -1), "(integer) 1")
        self.assertEqual(self.redis.get("negative"), "(nil)")
        self.assertIn("used_memory:0", self.redis.info_memory())

    def test_set_overwrite_clears_existing_ttl(self) -> None:
        self.redis.set("name", "Alice")
        self.redis.expire("name", 3)

        self.redis.set("name", "Bob")
        self.clock.advance(3)

        self.assertEqual(self.redis.ttl("name"), "(integer) -1")
        self.assertEqual(self.redis.get("name"), '"Bob"')

    def test_delete_then_reuse_key_ignores_old_expiration(self) -> None:
        self.redis.set("name", "Alice")
        self.redis.expire("name", 3)
        self.redis.delete("name")
        self.redis.set("name", "Bob")

        self.clock.advance(3)

        self.assertEqual(self.redis.get("name"), '"Bob"')
        self.assertEqual(self.redis.ttl("name"), "(integer) -1")

    def test_eviction_then_reuse_key_ignores_old_expiration(self) -> None:
        self.redis.set("A", "111")
        self.redis.expire("A", 1)
        self.redis.config_set_maxmemory(4)

        self.redis.set("B", "222")
        self.assertEqual(self.redis.ttl("A"), "(integer) -2")

        self.redis.set("A", "new")
        self.clock.advance(1)

        self.assertEqual(self.redis.get("A"), '"new"')
        self.assertEqual(self.redis.ttl("A"), "(integer) -1")
        self.assertIn("evicted_keys:2", self.redis.info_memory())

    def test_reset_expiration_ignores_stale_heap_record(self) -> None:
        self.redis.set("name", "Alice")
        self.redis.expire("name", 3)

        self.clock.advance(1)
        self.redis.expire("name", 5)
        self.clock.advance(2)

        self.assertEqual(self.redis.get("name"), '"Alice"')
        self.assertEqual(self.redis.ttl("name"), "(integer) 3")

        self.clock.advance(3)
        self.assertEqual(self.redis.get("name"), "(nil)")

    def test_expired_key_is_removed_before_non_get_commands(self) -> None:
        self.redis.set("expired", "value")
        self.redis.set("alive", "value")
        self.redis.expire("expired", 1)
        self.clock.advance(1)

        self.assertEqual(self.redis.exists("expired"), "(integer) 0")
        self.assertEqual(self.redis.dbsize(), "(integer) 1")
        self.assertIn('"alive"', self.redis.keys())
        self.assertNotIn('"expired"', self.redis.keys())

    def test_expired_get_does_not_move_another_lru_entry(self) -> None:
        self.redis.set("A", "one")
        self.redis.set("B", "two")
        self.redis.expire("A", 1)
        self.clock.advance(1)

        self.assertEqual(self.redis.get("A"), "(nil)")
        self.assertIsNotNone(self.redis._lru.head)
        self.assertEqual(self.redis._lru.head.data, "B")
        self.assertEqual(self.redis._lru.tail.data, "B")

    def test_invalid_expiration_is_rejected(self) -> None:
        self.redis.set("name", "Alice")

        self.assertEqual(
            self.redis.expire("name", "invalid"), self.redis.INTEGER_ERROR
        )
        self.assertEqual(self.redis.ttl("name"), "(integer) -1")


if __name__ == "__main__":
    unittest.main()
