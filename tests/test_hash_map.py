"""해시맵의 필수 연산, 충돌 처리, 버킷 확장을 검증한다."""

import unittest

from mini_redis.hash_map import HashMap


class AlwaysCollidingHashMap(HashMap):
    """충돌 처리 테스트를 위해 모든 Key에 같은 해시값을 반환한다."""

    def _hash(self, key: str) -> int:
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        return 0


class HashMapTest(unittest.TestCase):
    def test_put_get_and_size(self) -> None:
        hash_map = HashMap()

        self.assertIsNone(hash_map.put("name", "Alice"))
        self.assertEqual(hash_map.get("name"), "Alice")
        self.assertEqual(hash_map.size(), 1)

    def test_put_existing_key_updates_without_growing(self) -> None:
        hash_map = HashMap(initial_capacity=4)
        hash_map.put("name", "Alice")

        self.assertEqual(hash_map.put("name", "Bob"), "Alice")
        self.assertEqual(hash_map.get("name"), "Bob")
        self.assertEqual(hash_map.size(), 1)
        self.assertEqual(hash_map.capacity, 4)

    def test_missing_key(self) -> None:
        hash_map = HashMap()

        self.assertIsNone(hash_map.get("missing"))
        self.assertFalse(hash_map.contains("missing"))
        self.assertIsNone(hash_map.remove("missing"))
        self.assertEqual(hash_map.size(), 0)

    def test_contains_remove_and_keys(self) -> None:
        hash_map = HashMap()
        hash_map.put("name", "Alice")
        hash_map.put("city", "Seoul")

        self.assertTrue(hash_map.contains("name"))
        self.assertEqual(sorted(hash_map.keys()), ["city", "name"])
        self.assertEqual(hash_map.remove("name"), "Alice")
        self.assertFalse(hash_map.contains("name"))
        self.assertEqual(hash_map.keys(), ["city"])
        self.assertEqual(hash_map.size(), 1)

    def test_colliding_keys_remain_independent(self) -> None:
        hash_map = AlwaysCollidingHashMap(initial_capacity=8)
        hash_map.put("first", "one")
        hash_map.put("second", "two")
        hash_map.put("third", "three")

        self.assertEqual(hash_map.get("first"), "one")
        self.assertEqual(hash_map.get("second"), "two")
        self.assertEqual(hash_map.get("third"), "three")
        self.assertEqual(hash_map.remove("second"), "two")
        self.assertEqual(hash_map.get("first"), "one")
        self.assertEqual(hash_map.get("third"), "three")

    def test_resize_only_after_load_factor_exceeds_threshold(self) -> None:
        hash_map = HashMap(initial_capacity=4)
        hash_map.put("one", 1)
        hash_map.put("two", 2)
        hash_map.put("three", 3)

        self.assertEqual(hash_map.capacity, 4)

        hash_map.put("four", 4)

        self.assertEqual(hash_map.capacity, 8)
        self.assertEqual(hash_map.size(), 4)
        self.assertEqual(hash_map.get("one"), 1)
        self.assertEqual(hash_map.get("two"), 2)
        self.assertEqual(hash_map.get("three"), 3)
        self.assertEqual(hash_map.get("four"), 4)

    def test_unicode_key_and_invalid_key_type(self) -> None:
        hash_map = HashMap()
        hash_map.put("사용자", "홍길동")

        self.assertEqual(hash_map.get("사용자"), "홍길동")
        with self.assertRaises(TypeError):
            hash_map.put(123, "invalid")


if __name__ == "__main__":
    unittest.main()
