"""Mini Redis의 LRU 사용 순서 갱신과 삭제를 검증한다."""

import unittest

from mini_redies.core import MiniRedis


class LruTest(unittest.TestCase):
    def setUp(self) -> None:
        self.redis = MiniRedis()

    def test_set_records_keys_from_oldest_to_most_recent(self) -> None:
        self.redis.set("A", "one")
        self.redis.set("B", "two")
        self.redis.set("C", "three")

        self.assertEqual(self._oldest_first(), ["A", "B", "C"])
        self.assertEqual(len(self.redis._lru), 3)

    def test_successful_get_moves_key_to_most_recent(self) -> None:
        self.redis.set("A", "one")
        self.redis.set("B", "two")
        self.redis.set("C", "three")

        self.assertEqual(self.redis.get("A"), '"one"')

        self.assertEqual(self._oldest_first(), ["B", "C", "A"])

    def test_set_existing_key_moves_node_without_duplicating_it(self) -> None:
        self.redis.set("A", "one")
        self.redis.set("B", "two")
        self.redis.set("C", "three")

        self.assertEqual(self.redis.set("A", "updated"), "OK")

        self.assertEqual(self._oldest_first(), ["B", "C", "A"])
        self.assertEqual(len(self.redis._lru), 3)
        self.assertEqual(self.redis.get("A"), '"updated"')

    def test_missing_get_does_not_change_order(self) -> None:
        self.redis.set("A", "one")
        self.redis.set("B", "two")

        self.assertEqual(self.redis.get("missing"), "(nil)")

        self.assertEqual(self._oldest_first(), ["A", "B"])

    def test_delete_removes_lru_node_and_lookup(self) -> None:
        self.redis.set("A", "one")
        self.redis.set("B", "two")
        self.redis.set("C", "three")

        self.assertEqual(self.redis.delete("B"), "(integer) 1")

        self.assertEqual(self._oldest_first(), ["A", "C"])
        self.assertFalse(self.redis._lru_nodes.contains("B"))
        self.assertEqual(len(self.redis._lru), 2)

    def test_non_access_commands_do_not_change_order(self) -> None:
        self.redis.set("A", "one")
        self.redis.set("B", "two")
        original_order = self._oldest_first()

        self.redis.exists("A")
        self.redis.dbsize()
        self.redis.keys()

        self.assertEqual(self._oldest_first(), original_order)

    def _oldest_first(self):
        keys = []
        current = self.redis._lru.tail

        while current is not None:
            keys.append(current.data)
            current = current.prev

        return keys


if __name__ == "__main__":
    unittest.main()
