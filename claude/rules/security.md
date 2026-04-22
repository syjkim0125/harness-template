# 보안 규칙

## 핵심 원칙

1. **외부 입력은 절대 믿지 마라** — 검증, 정제, 이스케이프
2. **최소 권한** — 필요한 권한만 부여
3. **다중 방어** — 여러 층의 보안
4. **안전한 실패** — 에러가 내부 정보를 노출하면 안 됨
5. **코드에 시크릿 금지** — 환경변수/설정에서만

## 시크릿 관리

```
// 절대 금지
const apiKey = "sk-proj-xxxxx"

// 항상 환경변수
const apiKey = process.env.API_KEY
if (!apiKey) throw new Error('API_KEY가 설정되지 않았습니다')
```

### 체크리스트
- [ ] 소스 코드에 API 키/비밀번호/토큰 없음
- [ ] `.env` 파일이 `.gitignore`에 포함
- [ ] 에러 메시지/로그에 시크릿 누출 없음
- [ ] 커밋 메시지에 시크릿 없음
- [ ] 정기적으로 시크릿 로테이션

### 저장 계층
1. **개발**: 로컬 `.env` (gitignore)
2. **CI/CD**: 파이프라인 시크릿 변수
3. **운영**: Secrets Manager (AWS, HashiCorp Vault)
4. **절대 금지**: 소스 컨트롤, 설정 파일, 주석

## 입력 검증

**모든 외부 입력은 검증 + 정제 + 길이 제한.**

| 공격 타입 | 방어 |
|----------|------|
| SQL Injection | 파라미터화된 쿼리, ORM, 문자열 연결 금지 |
| XSS | 출력 인코딩, CSP 헤더, HTML 입력 정제 |
| Command Injection | 사용자 입력을 셸 명령에 전달 금지 |
| Path Traversal | 파일 경로 검증, 허용 경로 화이트리스트 |
| SSRF | URL 검증, 내부 접근 allowlist |

## 인증 & 인가

### 인증
- 직접 만들지 말고 검증된 라이브러리 사용
- 로그인 시도 rate limiting 적용
- 세션 쿠키: `HttpOnly`, `Secure`, `SameSite=Strict` (또는 `Lax`)
- 로그아웃 시 서버 세션 무효화

### 인가
- **모든** 요청에서 권한 확인
- 클라이언트-side는 UX일 뿐 — 서버에서 강제
- 자원 소유 확인 (자신의 데이터만 접근)
- 기본은 거부 (명시적 허용 방식)

## API 보안

### 필수 헤더
```
Content-Security-Policy: default-src 'self'
Strict-Transport-Security: max-age=31536000
```

### Rate Limiting
- 모든 공개 엔드포인트에 적용
- 엔드포인트 민감도에 따라 차등
- `429 Too Many Requests` + `Retry-After` 반환

### CORS
- 운영에서 `*` 금지 — origin 화이트리스트
- 필요한 메서드만 허용 (GET, POST 등)
- 와일드카드 origin에 `Allow-Credentials: true` 금지

## 데이터 보호

- **전송 중**: HTTPS 필수, TLS 1.3 권장 (TLS 1.2 최소)
- **저장 시**: 민감 데이터(PII, 금융, 건강) 암호화
- **로그**: 비밀번호, 토큰, API 키, 신용카드, SSN, PII 절대 로깅 금지

## 의존성 관리

- [ ] 공식 소스에서 의존성 설치
- [ ] 버전 고정 (`*` 또는 `latest` 금지)
- [ ] 정기 취약점 점검 (`npm audit`, `pip audit`)
- [ ] Lock 파일 필수 (`package-lock.json`, `Cargo.lock`)
- [ ] 미사용 의존성 제거

## 보안 이슈 발견 시

1. **중단** — 개발 계속하지 마라
2. **격리** — 해당 코드 병합 금지
3. **진단** — `security-reviewer` 에이전트로 분석
4. **수정** — 치명적 이슈를 먼저 해결
5. **로테이션** — 노출된 시크릿 교체
6. **감사** — 코드베이스 전체에서 유사 문제 탐색
7. **기록** — incident와 대응 기록

| 심각도 | 대응 시간 | 조치 |
|--------|----------|------|
| 치명적 | 즉시 | 병합 차단, 즉시 수정, 시크릿 로테이션 |
| 높음 | 24시간 이내 | 다음 릴리스 전 수정 |
| 중간 | 7일 이내 | 다음 스프린트에 포함 |
| 낮음 | 30일 이내 | 백로그 추가 |

## 커밋 전 보안 체크리스트

- [ ] 하드코딩 시크릿 없음
- [ ] 모든 사용자 입력 검증됨
- [ ] SQL Injection 방어 (파라미터 쿼리)
- [ ] XSS 방어 (출력 인코딩)
- [ ] CSRF 보호 (SameSite 쿠키 + API 기반 서비스는 CORS로 충분)
- [ ] 인증/인가 확인
- [ ] Rate limiting 설정
- [ ] 에러 메시지에 민감 정보 없음
- [ ] HTTPS 적용
- [ ] CORS 설정 확인

## [CUSTOMIZE] 프로젝트별 보안

- 인증 방식 (OAuth2, SAML, 자체)
- 인가 규칙 및 역할
- 암호화 요구사항
- 규제 준수 (GDPR, HIPAA, PCI DSS)
