"""이중 연결 리스트의 필수 연산을 검증한다."""

import unittest

from mini_redis.linked_list import DoublyLinkedList, Node


class DoublyLinkedListTest(unittest.TestCase):
    def test_empty_list(self) -> None:
        linked_list = DoublyLinkedList()

        self.assertIsNone(linked_list.head)
        self.assertIsNone(linked_list.tail)
        self.assertEqual(len(linked_list), 0)
        self.assertIsNone(linked_list.remove_front())
        self.assertIsNone(linked_list.remove_back())

    def test_insert_front_and_back_connect_nodes(self) -> None:
        linked_list = DoublyLinkedList()

        middle = linked_list.insert_front("middle")
        front = linked_list.insert_front("front")
        back = linked_list.insert_back("back")

        self.assertIs(linked_list.head, front)
        self.assertIs(linked_list.tail, back)
        self.assertIsNone(front.prev)
        self.assertIs(front.next, middle)
        self.assertIs(middle.prev, front)
        self.assertIs(middle.next, back)
        self.assertIs(back.prev, middle)
        self.assertIsNone(back.next)
        self.assertEqual(len(linked_list), 3)

    def test_remove_front_and_back_until_empty(self) -> None:
        linked_list = DoublyLinkedList()
        linked_list.insert_back("first")
        remaining = linked_list.insert_back("second")
        linked_list.insert_back("third")

        self.assertEqual(linked_list.remove_front(), "first")
        self.assertIs(linked_list.head, remaining)
        self.assertIsNone(remaining.prev)
        self.assertEqual(linked_list.remove_back(), "third")
        self.assertIs(linked_list.head, remaining)
        self.assertIs(linked_list.tail, remaining)
        self.assertEqual(linked_list.remove_back(), "second")
        self.assertIsNone(linked_list.head)
        self.assertIsNone(linked_list.tail)
        self.assertEqual(len(linked_list), 0)

    def test_remove_middle_node_reconnects_neighbors(self) -> None:
        linked_list = DoublyLinkedList()
        front = linked_list.insert_back("front")
        middle = linked_list.insert_back("middle")
        back = linked_list.insert_back("back")

        self.assertEqual(linked_list.remove_node(middle), "middle")

        self.assertIs(front.next, back)
        self.assertIs(back.prev, front)
        self.assertIsNone(middle.prev)
        self.assertIsNone(middle.next)
        self.assertEqual(len(linked_list), 2)

    def test_move_middle_and_tail_to_front(self) -> None:
        linked_list = DoublyLinkedList()
        first = linked_list.insert_back("first")
        second = linked_list.insert_back("second")
        third = linked_list.insert_back("third")

        linked_list.move_to_front(second)
        self.assertIs(linked_list.head, second)
        self.assertIs(second.next, first)
        self.assertIs(first.next, third)
        self.assertIs(linked_list.tail, third)

        linked_list.move_to_front(third)
        self.assertIs(linked_list.head, third)
        self.assertIs(third.next, second)
        self.assertIs(second.next, first)
        self.assertIs(linked_list.tail, first)
        self.assertEqual(len(linked_list), 3)

        linked_list.move_to_front(third)
        self.assertIs(linked_list.head, third)
        self.assertEqual(len(linked_list), 3)

    def test_rejects_node_from_another_list(self) -> None:
        linked_list = DoublyLinkedList()
        other_node = Node("other")

        with self.assertRaises(ValueError):
            linked_list.remove_node(other_node)
        with self.assertRaises(ValueError):
            linked_list.move_to_front(other_node)


if __name__ == "__main__":
    unittest.main()
