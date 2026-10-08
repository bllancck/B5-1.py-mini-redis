"""Mini Redis 명령을 파싱하고 REPL 입력·출력을 반복하는 모듈."""

import shlex
from typing import Callable, Optional, Tuple

from mini_redis import MiniRedis


class CommandProcessor:
    """한 줄의 사용자 입력을 검증하고 MiniRedis 메서드로 전달한다."""

    SYNTAX_ERROR = "(error) ERR syntax error"

    def __init__(self, redis: Optional[MiniRedis] = None) -> None:
        self.redis = redis if redis is not None else MiniRedis()

    def execute(self, line: str) -> Tuple[bool, Optional[str]]:
        """명령 한 줄을 실행하고 종료 여부와 출력할 결과를 반환한다."""
        try:
            tokens = shlex.split(line, comments=False, posix=True)
        except ValueError:
            return False, self.SYNTAX_ERROR

        if not tokens:
            return False, None

        raw_command = tokens[0]
        command = raw_command.upper()
        arguments = tokens[1:]

        if command in ("EXIT", "QUIT"):
            if arguments:
                return False, self._wrong_number(command)
            return True, None

        if command == "SET":
            if len(arguments) != 2:
                return False, self._wrong_number(command)
            return False, self.redis.set(arguments[0], arguments[1])

        if command == "GET":
            if len(arguments) != 1:
                return False, self._wrong_number(command)
            return False, self.redis.get(arguments[0])

        if command == "DEL":
            if len(arguments) != 1:
                return False, self._wrong_number(command)
            return False, self.redis.delete(arguments[0])

        if command == "EXISTS":
            if len(arguments) != 1:
                return False, self._wrong_number(command)
            return False, self.redis.exists(arguments[0])

        if command == "DBSIZE":
            if arguments:
                return False, self._wrong_number(command)
            return False, self.redis.dbsize()

        if command == "KEYS":
            if arguments:
                return False, self._wrong_number(command)
            return False, self.redis.keys()

        if command == "CONFIG":
            if len(arguments) != 3:
                return False, self._wrong_number(command)
            if arguments[0].upper() != "SET" or arguments[1].lower() != "maxmemory":
                return False, self.SYNTAX_ERROR
            return False, self.redis.config_set_maxmemory(arguments[2])

        if command == "INFO":
            if len(arguments) != 1:
                return False, self._wrong_number(command)
            if arguments[0].lower() != "memory":
                return False, self.SYNTAX_ERROR
            return False, self.redis.info_memory()

        if command == "EXPIRE":
            if len(arguments) != 2:
                return False, self._wrong_number(command)
            return False, self.redis.expire(arguments[0], arguments[1])

        if command == "TTL":
            if len(arguments) != 1:
                return False, self._wrong_number(command)
            return False, self.redis.ttl(arguments[0])

        return False, "(error) ERR unknown command '{}'".format(raw_command)

    @staticmethod
    def _wrong_number(command: str) -> str:
        """명령의 인자 개수가 잘못됐을 때 표준 오류를 만든다."""
        return "(error) ERR wrong number of arguments for '{}' command".format(
            command
        )


def run_cli(
    processor: Optional[CommandProcessor] = None,
    input_function: Callable[[str], str] = input,
    output_function: Callable[[str], None] = print,
) -> None:
    """프롬프트를 표시하고 종료 명령이나 입력 종료까지 REPL을 실행한다."""
    command_processor = processor if processor is not None else CommandProcessor()

    while True:
        try:
            line = input_function("mini-redis> ")
        except EOFError:
            return
        except KeyboardInterrupt:
            output_function("")
            return

        should_exit, result = command_processor.execute(line)
        if should_exit:
            return
        if result is not None:
            output_function(result)
