"""Mini Redis CLI의 진입점."""

from cli import run_cli


def main() -> None:
    """Mini Redis REPL을 시작한다."""
    run_cli()


if __name__ == "__main__":
    main()
