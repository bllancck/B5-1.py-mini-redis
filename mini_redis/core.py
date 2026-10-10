"""Mini Redis의 저장 명령과 자료구조 상태를 조정하는 모듈."""

from time import time
from typing import Callable, Optional

from .hash_map import HashMap
from .linked_list import DoublyLinkedList
from .min_heap import MinHeap


class MiniRedis:
    """해시맵을 이용해 Redis 스타일의 기본 저장 명령을 처리한다."""

    INTEGER_ERROR = "(error) ERR value is not an integer or out of range"
    OOM_ERROR = "(error) OOM command not allowed when used_memory > 'maxmemory'"

    def __init__(self, clock: Callable[[], float] = time) -> None:
        self._store = HashMap()
        self._lru = DoublyLinkedList()
        self._lru_nodes = HashMap()
        self._expiry_heap = MinHeap()
        self._expires = HashMap()
        self._clock = clock
        self._used_memory = 0
        self._maxmemory = 0
        self._evicted_keys = 0

    def set(self, key: str, value: str) -> str:
        """Key에 문자열 값을 저장하고 OK를 반환한다."""
        self._purge_expired()
        new_size = self._entry_size(key, value)
        if self._maxmemory > 0 and new_size > self._maxmemory:
            return self.OOM_ERROR

        old_value = self._store.get(key)
        self._store.put(key, value)

        if old_value is None:
            self._used_memory += new_size
        else:
            self._used_memory += new_size - self._entry_size(key, old_value)

        self._mark_as_recently_used(key)
        self._expires.remove(key)
        self._evict_if_needed()
        return "OK"

    def get(self, key: str) -> str:
        """Key의 값을 따옴표로 감싸 반환하고, 없으면 (nil)을 반환한다."""
        self._purge_expired()
        value = self._store.get(key)
        if value is None:
            return "(nil)"
        self._mark_as_recently_used(key)
        return '"{}"'.format(value)

    def delete(self, key: str) -> str:
        """Key를 삭제하고 삭제 여부를 Redis 정수 형식으로 반환한다."""
        self._purge_expired()
        if self._remove_key(key) is None:
            return "(integer) 0"
        return "(integer) 1"

    def exists(self, key: str) -> str:
        """Key의 존재 여부를 Redis 정수 형식으로 반환한다."""
        self._purge_expired()
        result = 1 if self._store.contains(key) else 0
        return "(integer) {}".format(result)

    def dbsize(self) -> str:
        """현재 저장된 Key 개수를 Redis 정수 형식으로 반환한다."""
        self._purge_expired()
        return "(integer) {}".format(self._store.size())

    def keys(self) -> str:
        """현재 저장된 모든 Key를 Redis 배열과 비슷한 형식으로 반환한다."""
        self._purge_expired()
        keys = self._store.keys()
        if not keys:
            return "(empty array)"

        lines = []
        for index, key in enumerate(keys, start=1):
            lines.append('{}. "{}"'.format(index, key))
        return "\n".join(lines)

    def config_set_maxmemory(self, bytes_value: object) -> str:
        """최대 메모리를 바이트 단위로 설정하며 0은 무제한으로 처리한다."""
        parsed_value = self._parse_integer(bytes_value)
        if parsed_value is None or parsed_value < 0:
            return self.INTEGER_ERROR

        self._purge_expired()
        self._maxmemory = parsed_value
        return "OK"

    def info_memory(self) -> str:
        """현재 사용량, 제한, 자동 제거 횟수를 Redis INFO 형식으로 반환한다."""
        self._purge_expired()
        return "\n".join(
            [
                "used_memory:{}".format(self._used_memory),
                "maxmemory:{}".format(self._maxmemory),
                "evicted_keys:{}".format(self._evicted_keys),
            ]
        )

    def expire(self, key: str, seconds: object) -> str:
        """Key의 만료 시간을 초 단위로 설정한다."""
        parsed_seconds = self._parse_integer(seconds)
        if parsed_seconds is None:
            return self.INTEGER_ERROR

        self._purge_expired()
        if not self._store.contains(key):
            return "(integer) 0"

        if parsed_seconds <= 0:
            self._remove_key(key)
            return "(integer) 1"

        expire_at = self._clock() + parsed_seconds
        self._expires.put(key, expire_at)
        self._expiry_heap.push((expire_at, key))
        return "(integer) 1"

    def ttl(self, key: str) -> str:
        """Key의 남은 만료 시간을 Redis 정수 형식으로 반환한다."""
        now = self._clock()
        self._purge_expired(now)

        if not self._store.contains(key):
            return "(integer) -2"

        expire_at = self._expires.get(key)
        if expire_at is None:
            return "(integer) -1"

        return "(integer) {}".format(int(expire_at - now))

    def _mark_as_recently_used(self, key: str) -> None:
        """Key의 LRU 노드를 O(1)에 가장 최근 사용 위치로 옮긴다."""
        lru_node = self._lru_nodes.get(key)
        if lru_node is None:
            lru_node = self._lru.insert_front(key)
            self._lru_nodes.put(key, lru_node)
            return

        self._lru.move_to_front(lru_node)

    def _remove_key(self, key: str) -> Optional[str]:
        """저장소, LRU, TTL, 메모리 사용량에서 Key를 함께 제거한다."""
        value = self._store.remove(key)
        if value is None:
            self._expires.remove(key)
            return None

        self._used_memory -= self._entry_size(key, value)
        lru_node = self._lru_nodes.remove(key)
        if lru_node is not None:
            self._lru.remove_node(lru_node)
        self._expires.remove(key)
        return value

    def _evict_if_needed(self) -> None:
        """사용량이 한도 이내가 될 때까지 가장 오래된 Key부터 제거한다."""
        while self._maxmemory > 0 and self._used_memory > self._maxmemory:
            oldest_node = self._lru.tail
            if oldest_node is None:
                return

            if self._remove_key(oldest_node.data) is None:
                return
            self._evicted_keys += 1

    def _purge_expired(self, now: Optional[float] = None) -> None:
        """힙의 루트부터 현재 시각이 지난 유효한 만료 기록을 처리한다."""
        if now is None:
            now = self._clock()

        while True:
            next_expiry = self._expiry_heap.peek()
            if next_expiry is None or next_expiry[0] > now:
                return

            expire_at, key = self._expiry_heap.pop()
            current_expire_at = self._expires.get(key)
            if current_expire_at != expire_at:
                continue

            self._remove_key(key)

    @staticmethod
    def _entry_size(key: str, value: str) -> int:
        """Key와 Value의 UTF-8 바이트 길이 합을 계산한다."""
        return len(key.encode("utf-8")) + len(value.encode("utf-8"))

    @staticmethod
    def _parse_integer(value: object) -> Optional[int]:
        """정수 또는 정수 문자열을 정수로 변환한다."""
        if isinstance(value, bool):
            return None

        if isinstance(value, int):
            parsed_value = value
        elif isinstance(value, str):
            try:
                parsed_value = int(value)
            except ValueError:
                return None
        else:
            return None
        return parsed_value
