# Mini Redis

Python의 기본 자료구조를 직접 구현하고 연결해 만드는 CLI 기반 인메모리
Key-Value 저장소입니다. 해시맵, 이중 연결 리스트, 최소 힙을 이용해 Redis의
기본 저장 기능과 LRU 메모리 관리, TTL 만료 처리를 학습하는 것이 목적입니다.

과제의 필수 결과물인 CLI 기반 Mini Redis 프로그램을 구현했으며, 필수 기능과
통합 동작을 테스트로 검증했습니다.

## 주요 기능

| 구분 | 지원 기능 |
|---|---|
| 기본 명령 | `SET`, `GET`, `DEL`, `EXISTS`, `DBSIZE`, `KEYS` |
| 메모리 관리 | `CONFIG SET maxmemory`, `INFO memory`, LRU 자동 제거 |
| 만료 관리 | `EXPIRE`, `TTL`, 최소 힙 기반 만료 처리 |
| CLI | `mini-redis>` REPL, 큰따옴표 값, Redis 스타일 결과와 오류 |
| 핵심 자료구조 | 직접 구현한 체이닝 해시맵, 이중 연결 리스트, 최소 힙 |

네트워크 통신, 데이터 영속성, 복합 Redis 자료형, 동시성 처리, `KEYS` 패턴
검색과 보너스 과제는 구현 범위에 포함하지 않습니다.

## 구조

Mini Redis는 다음과 같은 흐름으로 구성되어 있습니다.

```text
사용자 명령
    ↓
CLI 입력 해석 및 검증
    ↓
Mini Redis 명령 처리
    ├─ 해시맵: Key-Value 저장과 조회
    ├─ 이중 연결 리스트: LRU 사용 순서 관리
    ├─ 최소 힙: TTL 만료 순서 관리
    └─ 메모리 관리: 사용량 계산과 LRU 제거
    ↓
Redis 스타일 결과 출력
```

| 경로 | 역할 |
|---|---|
| `main.py` | 프로그램 진입점 |
| `cli.py` | 입력 파싱, 명령 검증, REPL 실행 |
| `mini_redis.py` | 저장 명령과 LRU·메모리·TTL 상태 조정 |
| `linked_list.py` | LRU와 해시 체이닝에 사용하는 이중 연결 리스트 |
| `hash_map.py` | 직접 설계한 해시 함수와 체이닝 기반 Key-Value 저장소 |
| `min_heap.py` | 가장 빠른 TTL 만료 시각 관리 |
| `tests/` | 자료구조·명령·통합 동작 테스트 |

## 요구 환경

- Python 3.8 이상

외부 패키지는 필요하지 않습니다. Python 3.12.3 환경에서 실행과 테스트를
검증했습니다.

## 실행 및 사용 방법

프로젝트 디렉터리에서 다음 명령으로 실행합니다.

```bash
python3 main.py
```

실행 후 `mini-redis>` 프롬프트에서 명령을 입력합니다. 명령은 대소문자를
구분하지 않으며, 공백이 포함된 값은 큰따옴표로 감쌀 수 있습니다.

```text
mini-redis> CONFIG SET maxmemory 100
OK
mini-redis> SET name "Alice Smith"
OK
mini-redis> GET name
"Alice Smith"
mini-redis> EXPIRE name 60
(integer) 1
mini-redis> TTL name
(integer) 59
mini-redis> INFO memory
used_memory:15
maxmemory:100
evicted_keys:0
mini-redis> quit
```

`exit` 또는 `quit`을 입력하면 종료합니다. `TTL` 결과는 명령 실행 시점에 따라
달라질 수 있습니다.

## 주요 동작과 제약

- `maxmemory`가 `0`이면 메모리 제한이 없습니다.
- 메모리 사용량은 Key와 Value의 UTF-8 바이트 길이 합으로 계산하며 자료구조
  자체의 오버헤드는 포함하지 않습니다.
- 설정 변경만으로 Key를 제거하지 않습니다. `SET` 후 한도를 초과하면 LRU
  순서로 자동 제거합니다.
- 단일 Key-Value 크기가 한도보다 크면 저장하지 않고 OOM 오류를 반환합니다.
- `SET`으로 기존 Key를 덮어쓰면 이전 TTL을 초기화합니다.
- 만료된 Key는 백그라운드 작업이 아니라 다음 명령에서 만료 힙을 확인할 때
  정리됩니다.
- `KEYS`는 패턴 검색과 정렬을 지원하지 않습니다.

## 검증

자동 테스트는 다음 명령으로 실행합니다.

```bash
python3 -B -m unittest discover -s tests -v
```

Python 3.12.3에서 전체 테스트 62개가 통과했습니다. 검증 범위는 다음과
같습니다.

- 세 자료구조의 필수 연산, 경계 조건, 해시 충돌과 버킷 확장
- 기본 명령과 Redis 스타일 출력
- LRU 순서, 메모리 계산, 자동 제거와 OOM
- TTL 설정·초기화·만료 및 관련 상태 정리
- CLI 파싱, 오류 메시지, 프롬프트와 종료
- 위 기능을 함께 사용하는 통합 시나리오

실제 `main.py` 실행에서도 프롬프트, 명령 처리, LRU 제거, 즉시 만료, 오류
출력과 종료를 확인했습니다.
