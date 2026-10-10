"""앞뒤 노드를 직접 연결하는 이중 연결 리스트 자료구조."""

from typing import Any, Optional


class Node:
    """리스트에 저장할 데이터와 앞뒤 노드의 연결 정보를 보관한다."""

    def __init__(self, data: Any) -> None:
        self.prev: Optional["Node"] = None
        self.next: Optional["Node"] = None
        self.data = data
        self._owner: Optional["DoublyLinkedList"] = None


class DoublyLinkedList:
    """양 끝과 이미 알고 있는 노드를 O(1)에 삽입·삭제·이동한다."""

    def __init__(self) -> None:
        self.head: Optional[Node] = None
        self.tail: Optional[Node] = None
        self._length = 0

    def __len__(self) -> int:
        return self._length

    def insert_front(self, data: Any) -> Node:
        """데이터를 맨 앞에 추가하고 생성한 노드를 반환한다."""
        node = Node(data)
        node.next = self.head
        node._owner = self

        if self.head is None:
            self.tail = node
        else:
            self.head.prev = node

        self.head = node
        self._length += 1
        return node

    def insert_back(self, data: Any) -> Node:
        """데이터를 맨 뒤에 추가하고 생성한 노드를 반환한다."""
        node = Node(data)
        node.prev = self.tail
        node._owner = self

        if self.tail is None:
            self.head = node
        else:
            self.tail.next = node

        self.tail = node
        self._length += 1
        return node

    def remove_front(self) -> Optional[Any]:
        """맨 앞 데이터를 제거해 반환하고, 비어 있으면 None을 반환한다."""
        if self.head is None:
            return None
        return self.remove_node(self.head)

    def remove_back(self) -> Optional[Any]:
        """맨 뒤 데이터를 제거해 반환하고, 비어 있으면 None을 반환한다."""
        if self.tail is None:
            return None
        return self.remove_node(self.tail)

    def remove_node(self, node: Node) -> Any:
        """이 리스트에 속한 노드를 제거하고 그 데이터를 반환한다."""
        self._ensure_owned(node)

        if node.prev is None:
            self.head = node.next
        else:
            node.prev.next = node.next

        if node.next is None:
            self.tail = node.prev
        else:
            node.next.prev = node.prev

        data = node.data
        node.prev = None
        node.next = None
        node._owner = None
        self._length -= 1
        return data

    def move_to_front(self, node: Node) -> None:
        """이 리스트에 속한 노드를 새로 만들지 않고 맨 앞으로 옮긴다."""
        self._ensure_owned(node)

        if node is self.head:
            return

        previous = node.prev
        following = node.next

        previous.next = following
        if following is None:
            self.tail = previous
        else:
            following.prev = previous

        node.prev = None
        node.next = self.head
        self.head.prev = node
        self.head = node

    def _ensure_owned(self, node: Node) -> None:
        """노드가 현재 리스트 소속인지 순회 없이 확인한다."""
        if not isinstance(node, Node) or node._owner is not self:
            raise ValueError("node does not belong to this list")
