# Step 1: 보안 강화

## 작업 내용
- security.md 전 항목 점검
- 하드코딩 시크릿 전수 검사
- 모든 입력 검증 검증 (SQL Injection, XSS, Command Injection)
- CORS 설정 확인 (운영에서 `*` origin 금지)
- Rate limiting 적용
- 보안 헤더 설정 (CSP, HSTS, X-Content-Type-Options, X-Frame-Options)
- 의존성 취약점 점검 (`npm audit` 또는 동등 도구)

## AC (Acceptance Criteria)
- [ ] 소스 코드에 시크릿 없음 (grep으로 확인)
- [ ] 모든 외부 입력 검증됨 (스키마 기반)
- [ ] CORS origin 화이트리스트 설정
- [ ] Rate limiting 공개 엔드포인트 적용
- [ ] 보안 헤더 응답에 포함
- [ ] high/critical 취약점 0개
