# Step 2: 의존성 업데이트

## 작업 내용
- 주요 의존성 최신 메이저/마이너 버전 확인
- changelog 확인: breaking change 파악
- 버전 업데이트 후 빌드 + 테스트 전체 통과
- 취약점(`npm audit`, `pip audit` 등) 확인 및 조치

## AC (Acceptance Criteria)
- [ ] `npm audit` (또는 동등 도구)에서 high/critical 취약점 없음
- [ ] 빌드 성공
- [ ] 테스트 스위트 전체 통과
- [ ] breaking change가 있으면 수정 사항 커밋에 포함
