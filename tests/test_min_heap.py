"""최소 힙의 필수 연산과 힙 순서 유지를 검증한다."""

import unittest

from mini_redis.min_heap import MinHeap


class MinHeapTest(unittest.TestCase):
    def test_empty_heap(self) -> None:
        heap = MinHeap()

        self.assertEqual(heap.size(), 0)
        self.assertIsNone(heap.peek())
        self.assertIsNone(heap.pop())

    def test_single_item(self) -> None:
        heap = MinHeap()
        item = (10.0, "name")

        heap.push(item)

        self.assertEqual(heap.peek(), item)
        self.assertEqual(heap.size(), 1)
        self.assertEqual(heap.pop(), item)
        self.assertEqual(heap.size(), 0)
        self.assertIsNone(heap.peek())

    def test_peek_returns_earliest_without_removing(self) -> None:
        heap = MinHeap()
        heap.push((30.0, "third"))
        heap.push((10.0, "first"))
        heap.push((20.0, "second"))

        self.assertEqual(heap.peek(), (10.0, "first"))
        self.assertEqual(heap.peek(), (10.0, "first"))
        self.assertEqual(heap.size(), 3)

    def test_repeated_pop_returns_expiration_order(self) -> None:
        heap = MinHeap()
        items = [
            (50.0, "fifth"),
            (10.0, "first"),
            (40.0, "fourth"),
            (20.0, "second"),
            (30.0, "third"),
        ]

        for item in items:
            heap.push(item)

        popped = []
        while heap.size() > 0:
            popped.append(heap.pop())

        self.assertEqual(popped, sorted(items))

    def test_heap_order_survives_pushes_and_pops(self) -> None:
        heap = MinHeap()
        items = [
            (7.0, "seven"),
            (3.0, "three"),
            (9.0, "nine"),
            (1.0, "one"),
            (5.0, "five"),
            (2.0, "two"),
        ]

        for item in items:
            heap.push(item)
            self._assert_heap_order(heap)

        while heap.size() > 0:
            heap.pop()
            self._assert_heap_order(heap)

    def test_equal_expiration_times_keep_both_keys(self) -> None:
        heap = MinHeap()
        heap.push((10.0, "beta"))
        heap.push((10.0, "alpha"))

        self.assertEqual(heap.pop(), (10.0, "alpha"))
        self.assertEqual(heap.pop(), (10.0, "beta"))

    def _assert_heap_order(self, heap: MinHeap) -> None:
        for index, item in enumerate(heap._items):
            left_index = index * 2 + 1
            right_index = index * 2 + 2

            if left_index < heap.size():
                self.assertLessEqual(item, heap._items[left_index])
            if right_index < heap.size():
                self.assertLessEqual(item, heap._items[right_index])


if __name__ == "__main__":
    unittest.main()
