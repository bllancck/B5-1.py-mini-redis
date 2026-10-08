"""TTL 만료 순서를 관리하는 최소 힙 자료구조."""

from typing import List, Optional, Tuple


HeapItem = Tuple[float, str]


class MinHeap:
    """가장 이른 만료 시각을 루트에 유지하는 최소 힙."""

    def __init__(self) -> None:
        self._items: List[HeapItem] = []

    def push(self, item: HeapItem) -> None:
        """항목을 마지막에 추가한 뒤 올바른 위치까지 위로 이동한다."""
        self._items.append(item)
        self._heapify_up(len(self._items) - 1)

    def pop(self) -> Optional[HeapItem]:
        """가장 이른 항목을 제거해 반환하고, 비어 있으면 None을 반환한다."""
        if not self._items:
            return None

        root = self._items[0]
        last = self._items.pop()

        if self._items:
            self._items[0] = last
            self._heapify_down(0)

        return root

    def peek(self) -> Optional[HeapItem]:
        """가장 이른 항목을 제거하지 않고 반환한다."""
        if not self._items:
            return None
        return self._items[0]

    def size(self) -> int:
        """힙에 저장된 항목 수를 반환한다."""
        return len(self._items)

    def _heapify_up(self, index: int) -> None:
        """부모보다 작은 항목을 위로 이동시켜 힙 순서를 복원한다."""
        while index > 0:
            parent_index = (index - 1) // 2
            if self._items[parent_index] <= self._items[index]:
                break

            self._swap(parent_index, index)
            index = parent_index

    def _heapify_down(self, index: int) -> None:
        """자식보다 큰 항목을 아래로 이동시켜 힙 순서를 복원한다."""
        item_count = len(self._items)

        while True:
            left_index = index * 2 + 1
            right_index = index * 2 + 2
            smallest_index = index

            if (
                left_index < item_count
                and self._items[left_index] < self._items[smallest_index]
            ):
                smallest_index = left_index

            if (
                right_index < item_count
                and self._items[right_index] < self._items[smallest_index]
            ):
                smallest_index = right_index

            if smallest_index == index:
                return

            self._swap(index, smallest_index)
            index = smallest_index

    def _swap(self, first_index: int, second_index: int) -> None:
        """두 인덱스에 저장된 항목의 위치를 맞바꾼다."""
        self._items[first_index], self._items[second_index] = (
            self._items[second_index],
            self._items[first_index],
        )
