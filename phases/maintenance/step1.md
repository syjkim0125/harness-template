# Step 1: 핫스팟 리팩토링

## 작업 내용
- 자주 수정되거나 복잡한 파일/모듈 식별
- 단일 책임 원칙 적용: 함수 50줄 미만, 파일 400줄 미만 권장
- 기존 테스트를 깨뜨리지 않으며 리팩토링
- karpathy-guidelines.md 준수: 기존 코드 "개선" 금지, 요청 범위만 수정

## AC (Acceptance Criteria)
- [ ] 리팩토링 전후 테스트 전체 통과
- [ ] cyclomatic complexity 감소 (또는 동일 유지)
- [ ] public API 변경 없음 (breaking change 금지)
