# Data Model

## 스키마 설계 원칙

### 테이블/컬럼 네이밍
- **스네이크 케이스** (`user_preferences`, `created_at`)
- **복수형 테이블명** (`users`, `orders`)
- **외래 키**: `{단수명}_id` (`user_id`, `order_id`)
- **조인 테이블**: 알파벳 순 (`user_roles`, `order_items`)

### 관계 설계
- **1:N**: 외래 키를 "다" 쪽에 배치
- **N:M**: 조인 테이블 사용, 복합 유니크 키
- **1:1**: 동일한 테이블에 통합하거나 외래 키 + 유니크 제약

### 마이그레이션
- 마이그레이션은 **단방향** — 롤백 가능하게 설계
- **데이터 손실 마이그레이션**은 별도 스크립트로 분리
- 프로덕션 마이그레이션은 **백업 후 실행**
- 컬럼 추가는 항상 **nullable** 또는 **기본값**으로

### 인덱스
- 외래 키 컬럼에 인덱스 추가 (JOIN 성능)
- WHERE 절에서 자주 쓰이는 컬럼에 인덱스
- **과도한 인덱스 금지** — 쓰기 성능 저하
- 복합 인덱스는 가장 discriminatory한 컬럼 먼저

### 타입 선택
| 데이터 | 권장 타입 | 피해야 할 타입 |
|--------|-----------|----------------|
| 날짜/시간 | `TIMESTAMP WITH TIME ZONE` | `VARCHAR` |
| 금액 | `DECIMAL` 또는 `NUMERIC` | `FLOAT` |
| UUID | `UUID` | `VARCHAR(36)` |
| JSON | `JSONB` | `TEXT` (파싱 오버헤드) |
| 불리언 | `BOOLEAN` | `TINYINT` |

### 프로젝트 스택별 ORM 선택
프로젝트 스택에 맞는 ORM/라이브러리를 선택하라. `claude/examples/` 디렉토리의 프레임워크별 예시를 참조하라.

## [CUSTOMIZE] 프로젝트별 데이터 모델

- 사용하는 ORM/쿼리 빌더 (Prisma, TypeORM, SQLAlchemy, etc.)
- 데이터베이스 종류 (PostgreSQL, MySQL, SQLite, MongoDB)
- 마이그레이션 도구 및 프로세스
- 소프트 삭제 정책
- 감사 테이블 (created_at, updated_at) 적용 여부
