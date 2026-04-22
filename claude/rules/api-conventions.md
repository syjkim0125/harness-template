# API Conventions

## REST API 설계 규칙

### 엔드포인트 네이밍
- **리소스는 명사**, 복수형 사용 (`/users`, `/orders`)
- **동사는 동사 서브리소스**에 한정 (`/users/123/verify`)
- **버전 관리는 URL 또는 헤더**에서 명시 (`/api/v1/users` 또는 `Accept: application/vnd.myapi.v1+json`)
- **스네이크 케이스**로 일관 (`/user_preferences` X → `/user-preferences`)

### HTTP 메소드 의미
| 메소드 | 의미 | 멱등성 | 안전 |
|--------|------|--------|------|
| GET | 리소스 조회 | O | O |
| POST | 리소스 생성 | X | X |
| PUT | 리소스 전체 교체 | O | X |
| PATCH | 리소스 일부 수정 | O | X |
| DELETE | 리소스 삭제 | O | X |

### 응답 포맷
```
성공: { data: <리소스>, meta: { page, total } }
에러: { error: { code: "ERR_CODE", message: "사용자 메시지", details: {...} } }
```

- 에러 응답은 일관된 코드 체계 사용 (`USER_NOT_FOUND`, `INVALID_INPUT`)
- 500 에러에서 내부 정보(스택 트레이스, DB 메시지) 절대 미노출
- pagination은 `meta.page`, `meta.total`, `meta.pageSize`로 통일

### 검증
- 입력 검증은 DTO/스키마 레벨에서 수행
- 검증 실패 시 `400 Bad Request` + 에러 상세 반환
- 인증 실패 `401`, 권한 부족 `403`

### 프로젝트 스택별 구체적 예시
`claude/examples/` 디렉토리의 프레임워크별 예시를 참조하라.

## [CUSTOMIZE] 프로젝트별 API 규칙

- API 버전 관리 방식 (URL, 헤더, 쿼리 파라미터)
- 페이징 기본값 (pageSize, maxPageSize)
- 인증 방식 (JWT, 세션, API 키)
- Rate limiting 설정
