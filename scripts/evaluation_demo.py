"""주요 기능을 한 번에 보여주는 Mini Redis 데모 스크립트."""

import sys
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mini_redis.cli import CommandProcessor  # noqa: E402
from mini_redis.core import MiniRedis  # noqa: E402


class FakeClock:
    """기다리지 않고 TTL 경계 시각을 재현하는 데모용 시계."""

    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds
        print("[모의 시각을 {}초 진행]".format(seconds))


def print_section(title: str) -> None:
    """기능별 시연 제목을 출력한다."""
    print("\n{}\n{}".format(title, "=" * len(title)))


def execute(
    processor: CommandProcessor, command: str, expected: Optional[str]
) -> None:
    """CLI 명령과 결과를 출력하고 예상 결과와 같은지 확인한다."""
    print("mini-redis> {}".format(command))
    should_exit, result = processor.execute(command)

    if should_exit:
        raise AssertionError("데모 도중 예기치 않게 종료되었습니다: {}".format(command))
    if result is not None:
        print(result)
    if result != expected:
        raise AssertionError(
            "{}의 예상 결과는 {!r}이지만 실제 결과는 {!r}입니다.".format(
                command, expected, result
            )
        )


def complete_section() -> None:
    """현재 기능 시나리오가 예상대로 끝났음을 표시한다."""
    print("[PASS] 예상한 결과와 일치합니다.")


def demonstrate_basic_commands() -> None:
    print_section("기본 명령")
    processor = CommandProcessor()
    commands = [
        ('SET name "Alice Smith"', "OK"),
        ("GET name", '"Alice Smith"'),
        ("EXISTS name", "(integer) 1"),
        ("DBSIZE", "(integer) 1"),
        ("KEYS", '1. "name"'),
        ("SET name Bob", "OK"),
        ("DBSIZE", "(integer) 1"),
        ("DEL name", "(integer) 1"),
        ("DEL name", "(integer) 0"),
        ("GET name", "(nil)"),
        ("EXISTS name", "(integer) 0"),
        ("DBSIZE", "(integer) 0"),
        ("KEYS", "(empty array)"),
    ]
    for command, expected in commands:
        execute(processor, command, expected)
    complete_section()


def demonstrate_lru_eviction() -> None:
    print_section("LRU 자동 제거")
    processor = CommandProcessor()
    commands = [
        ("CONFIG SET maxmemory 8", "OK"),
        ("SET A 111", "OK"),
        ("SET B 222", "OK"),
        ("GET A", '"111"'),
        ("SET C 333", "OK"),
        ("EXISTS A", "(integer) 1"),
        ("EXISTS B", "(integer) 0"),
        ("EXISTS C", "(integer) 1"),
        (
            "INFO memory",
            "used_memory:8\nmaxmemory:8\nevicted_keys:1",
        ),
    ]
    for command, expected in commands:
        execute(processor, command, expected)
    complete_section()


def demonstrate_memory_accounting() -> None:
    print_section("메모리 정보")
    processor = CommandProcessor()
    commands = [
        ("SET 한 글", "OK"),
        ("INFO memory", "used_memory:6\nmaxmemory:0\nevicted_keys:0"),
        ("SET 한 ab", "OK"),
        ("INFO memory", "used_memory:5\nmaxmemory:0\nevicted_keys:0"),
        ("DEL 한", "(integer) 1"),
        ("INFO memory", "used_memory:0\nmaxmemory:0\nevicted_keys:0"),
    ]
    for command, expected in commands:
        execute(processor, command, expected)
    complete_section()


def demonstrate_ttl() -> None:
    print_section("TTL 관리")
    clock = FakeClock()
    processor = CommandProcessor(MiniRedis(clock=clock))

    commands = [
        ("EXPIRE missing 3", "(integer) 0"),
        ("TTL missing", "(integer) -2"),
        ("SET session old", "OK"),
        ("TTL session", "(integer) -1"),
        ("EXPIRE session 3", "(integer) 1"),
        ("TTL session", "(integer) 3"),
    ]
    for command, expected in commands:
        execute(processor, command, expected)

    clock.advance(3)
    execute(processor, "GET session", "(nil)")
    execute(processor, "TTL session", "(integer) -2")
    execute(
        processor,
        "INFO memory",
        "used_memory:0\nmaxmemory:0\nevicted_keys:0",
    )

    print("\n[SET 덮어쓰기 시 기존 TTL 초기화]")
    execute(processor, "SET session old", "OK")
    execute(processor, "EXPIRE session 3", "(integer) 1")
    clock.advance(1)
    execute(processor, "SET session new", "OK")
    clock.advance(3)
    execute(processor, "TTL session", "(integer) -1")
    execute(processor, "GET session", '"new"')
    complete_section()


def demonstrate_errors() -> None:
    print_section("에러 처리")
    processor = CommandProcessor()
    commands = [
        ("HELLO", "(error) ERR unknown command 'HELLO'"),
        (
            "GET",
            "(error) ERR wrong number of arguments for 'GET' command",
        ),
        (
            "CONFIG SET maxmemory abc",
            "(error) ERR value is not an integer or out of range",
        ),
        (
            "CONFIG SET maxmemory -1",
            "(error) ERR value is not an integer or out of range",
        ),
        (
            "EXPIRE missing abc",
            "(error) ERR value is not an integer or out of range",
        ),
        ("CONFIG SET maxmemory 5", "OK"),
        (
            "SET long xx",
            "(error) OOM command not allowed when used_memory > 'maxmemory'",
        ),
        ("DBSIZE", "(integer) 0"),
    ]
    for command, expected in commands:
        execute(processor, command, expected)
    complete_section()


def main() -> None:
    """모든 기능 시나리오를 순서대로 실행한다."""
    print("Mini Redis 기능 데모")
    demonstrate_basic_commands()
    demonstrate_lru_eviction()
    demonstrate_memory_accounting()
    demonstrate_ttl()
    demonstrate_errors()
    print("\n모든 데모가 정상적으로 완료되었습니다.")


if __name__ == "__main__":
    main()
