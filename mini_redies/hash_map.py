"""직접 만든 해시 함수와 체이닝을 사용하는 해시맵 자료구조."""

from typing import Any, List, Optional

from .linked_list import DoublyLinkedList, Node


class HashEntry:
    """해시맵에 저장할 하나의 Key-Value 쌍."""

    def __init__(self, key: str, value: Any) -> None:
        self.key = key
        self.value = value


class HashMap:
    """충돌을 이중 연결 리스트 체이닝으로 해결하는 해시맵."""

    MAX_LOAD_FACTOR = 0.75

    def __init__(self, initial_capacity: int = 8) -> None:
        if not isinstance(initial_capacity, int) or initial_capacity <= 0:
            raise ValueError("initial_capacity must be a positive integer")

        self._capacity = initial_capacity
        self._buckets: List[Optional[DoublyLinkedList]] = [
            None
        ] * initial_capacity
        self._size = 0

    @property
    def capacity(self) -> int:
        """현재 버킷 수를 반환한다."""
        return self._capacity

    def put(self, key: str, value: Any) -> Optional[Any]:
        """Key-Value를 저장하고, 덮어썼다면 이전 값을 반환한다."""
        bucket_index = self._bucket_index(key)
        bucket = self._buckets[bucket_index]
        node = self._find_node(bucket, key)

        if node is not None:
            old_value = node.data.value
            node.data.value = value
            return old_value

        if bucket is None:
            bucket = DoublyLinkedList()
            self._buckets[bucket_index] = bucket

        bucket.insert_back(HashEntry(key, value))
        self._size += 1

        if self._size / self._capacity > self.MAX_LOAD_FACTOR:
            self._resize(self._capacity * 2)

        return None

    def get(self, key: str) -> Optional[Any]:
        """Key의 값을 반환하고, Key가 없으면 None을 반환한다."""
        bucket = self._buckets[self._bucket_index(key)]
        node = self._find_node(bucket, key)
        if node is None:
            return None
        return node.data.value

    def remove(self, key: str) -> Optional[Any]:
        """Key를 제거해 값을 반환하고, Key가 없으면 None을 반환한다."""
        bucket_index = self._bucket_index(key)
        bucket = self._buckets[bucket_index]
        node = self._find_node(bucket, key)

        if node is None:
            return None

        entry = bucket.remove_node(node)
        self._size -= 1

        if len(bucket) == 0:
            self._buckets[bucket_index] = None

        return entry.value

    def contains(self, key: str) -> bool:
        """Key가 저장되어 있는지 반환한다."""
        bucket = self._buckets[self._bucket_index(key)]
        return self._find_node(bucket, key) is not None

    def keys(self) -> List[str]:
        """저장된 모든 Key를 버킷 순서대로 반환한다."""
        result = []

        for bucket in self._buckets:
            if bucket is None:
                continue

            current = bucket.head
            while current is not None:
                result.append(current.data.key)
                current = current.next

        return result

    def size(self) -> int:
        """저장된 Key의 개수를 반환한다."""
        return self._size

    def _hash(self, key: str) -> int:
        """문자열의 UTF-8 바이트를 FNV-1a 방식으로 혼합한다."""
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        hash_value = 2166136261
        for byte in key.encode("utf-8"):
            hash_value ^= byte
            hash_value = (hash_value * 16777619) & 0xFFFFFFFF
        return hash_value

    def _bucket_index(self, key: str) -> int:
        """해시값을 현재 버킷 범위의 인덱스로 바꾼다."""
        return self._hash(key) % self._capacity

    def _find_node(
        self, bucket: Optional[DoublyLinkedList], key: str
    ) -> Optional[Node]:
        """한 버킷의 체인을 따라가며 Key가 같은 노드를 찾는다."""
        if bucket is None:
            return None

        current = bucket.head
        while current is not None:
            if current.data.key == key:
                return current
            current = current.next
        return None

    def _resize(self, new_capacity: int) -> None:
        """버킷을 늘리고 모든 항목을 새 인덱스로 다시 배치한다."""
        old_buckets = self._buckets
        self._capacity = new_capacity
        self._buckets = [None] * new_capacity

        for bucket in old_buckets:
            if bucket is None:
                continue

            current = bucket.head
            while current is not None:
                entry = current.data
                bucket_index = self._bucket_index(entry.key)
                new_bucket = self._buckets[bucket_index]

                if new_bucket is None:
                    new_bucket = DoublyLinkedList()
                    self._buckets[bucket_index] = new_bucket

                new_bucket.insert_back(entry)
                current = current.next
