# 코딩 스타일 규칙

## 핵심 원칙 (CRITICAL)

**가독성 > 똑똑함** — 코드는 쓰는 순간보다 읽는 순간이 훨씬 많다. 읽는 사람을 위해 짜라.

**일관성 > 개인 취향** — 팀의 일관성이 개인의 스타일보다 우선이다. 기존 패턴을 따르라.

**명시적 > 암시적** — 마법 같은 코드보다 명백한 코드가 좋다.

## 네이밍

- **변수/명사**: `camelCase` (JS/TS) 또는 `snake_case` (Python) — 언어 관례 따름
- **함수/동작**: 동작을 나타내는 동사형 — `getUser()`, `validateInput()`
- **클래스/타입**: `PascalCase` — `UserRepository`, `AuthConfig`
- **상수**: `UPPER_SNAKE_CASE` — `MAX_RETRIES`, `API_BASE_URL`
- **불리언**: `is`, `has`, `can` 접두어 — `isActive`, `hasPermission`
- **컬렉션**: 복수형 — `users`, `orderItems`

### 금지
- 한 글자 이름 (`i`, `j`, `k` 제외 — 루프에서만)
- 축약 (`config`, `params`, `args` 등 관례적 제외)
- 타입을 이름에 포함 (`userObj`, `nameStr`)

## 불변성 (CRITICAL)

**새 객체를 만들어라. 절대 기존 객체를 수정하지 마라.**

### 핵심 원칙
- 함수 파라미터 재할당 금지
- 컬렉션 in-place 수정 금지 (`push`, `pop`, `splice` 등)
- 읽기 전용이 기본, 변경이 불가피할 때만 변경 가능하게

### 언어별 불변 패턴

**JavaScript/TypeScript**
```
// 나쁨: 변경
function updateUser(user, name) {
  user.name = name  // 변경!
  return user
}

// 좋음: spread
function updateUser(user, name) {
  return { ...user, name }
}

// 배열: push 대신 concat/spread
const newList = [...oldList, newItem]
```

**Python**
```
# 나쁨: 변경
def update_user(user, name):
    user["name"] = name  # 변경!
    return user

# 좋음: dict 복사 / dataclasses.replace
def update_user(user, name):
    return {**user, "name": name}

# dataclass인 경우
from dataclasses import replace
new_user = replace(old_user, name=new_name)

# 리스트: append 대신 새 리스트
new_list = old_list + [new_item]
```

**Rust**
```
// Rust는 기본적으로 불변. builder 패턴으로 복사.
let new_config = old_config.with_timeout(5000);

// struct update syntax
let new_user = User { name: new_name, ..old_user };
```

**Go**
```
// Go는 값 복사. struct를 통째로 새로 만들어 반환.
func UpdateUser(user User, name string) User {
    user.Name = name  // 값 복사본이므로 원본 영향 없음
    return user
}

// 포인터를 받을 때는 명시적 복사
func UpdateUserPtr(u *User, name string) *User {
    copy := *u          // shallow copy
    copy.Name = name
    return &copy
}
```

**공통 규칙**
1. **원본을 건드리지 마라** — 함수는 새 값을 만들어 반환
2. **얕은 복사 주의** — 중첩 객체는 깊은 복사 고려
3. **의도적 변경은 문서화** — 왜 불변을 깼는지 주석으로 명시

## 파일 조직

**작은 파일 여러 개 > 큰 파일 몇 개**

- 하나의 파일: 200-400줄 권장, 800줄 절대 초과
- 기능/도메인 기준으로 구조화 (타입 기준 아님)
- 파일명은 주 export와 일치: `UserProfile.tsx` → `UserProfile`

```
feature/
├── components/    # UI 컴포넌트
├── hooks/         # 커스텀 훅
├── services/      # API 통신
├── types/         # 타입 정의
├── utils/         # 유틸리티
├── constants.ts   # 상수
└── index.ts       # barrel export (최소한으로)
```

## 함수 설계

- **크기**: 50줄 미만 권장, 100줄 초과 시 이유 명시
- **중첩**: 최대 4단계 (그 이상이면 함수 분리)
- **파라미터**: 최대 3-4개 (그 이상이면 객체로 묶음)
- **단일 책임**: 함수는 하나만 해야 함. "그리고"가 붙으면 분리
- **순수 함수 우선**: 같은 입력 → 같은 출력. 테스트 쉽고 예측 가능

## 에러 핸들링

**빠르게 실패해라. 명확하게 실패해라. 삼키지 마라.**

```
try {
  const result = await riskyOperation()
  return result
} catch (error) {
  console.error('[UserService] 사용자 업데이트 실패:', error)
  throw new Error('사용자 정보를 업데이트하지 못했습니다. 다시 시도해주세요.')
}
```

### 에러 레벨
| 레벨 | 대응 | 예시 |
|------|------|------|
| 예상됨 | 우아하게 처리 | 네트워크 재시도, 폴백 데이터 |
| 복구 가능 | 사용자 메시지 | 검증 에러, 권한 없음 |
| 치명적 | 로깅 + 알림 + 중단 | DB 다운, 인증 실패 |

### 핵심 원칙
- **Fail fast**: 검증은 빨리, 실패는 빨리
- **맥락 추가**: 어떤 작업에서 실패했는지 감싸라
- **삼키기 금지**: catch는 처리하거나 던질 목적만, 무시 금지
- **사용자 메시지**: 기술 에러를 그대로 노출하지 마라

### 로깅 규칙
- **구조화 로깅**: JSON 형식으로 `[서비스명] 메시지: 내용` 패턴
- **로그 레벨**: `info`(정상 동작), `warn`(우려 사항), `error`(실패 — 처리 가능), `fatal`(중단 — 즉시 대응)
- **금지**: 비밀번호, 토큰, API 키, 개인정보(이메일, 전화번호) 로깅
- **에러 로깅**: 스택 트레이스는 서버 로그에만, 클라이언트에는 사용자 친화적 메시지만

## 입력 검증

**외부 입력은 절대 믿지 마라. 시스템 경계에서 항상 검증.**

```
// 스키마 검증 (Zod, Yup 등)
const schema = z.object({
  email: z.string().email(),
  age: z.number().int().min(0).max(150)
})
const validated = schema.parse(input)
```

### 검증 레이어
1. **클라이언트**: UX 피드백 용도 (보안 아님)
2. **API 경계**: 필수 검증 (스키마)
3. **비즈니스 로직**: 도메인 규칙
4. **데이터베이스**: 최종 안전 장치 (제약조건)

## 품질 체크리스트

작업 완료 전 확인:
- [ ] 코드가 읽기 쉽고 이름이 명확한가
- [ ] 함수가 50줄 미만인가
- [ ] 파일이 800줄 미만인가
- [ ] 중첩이 4단계 이하인가
- [ ] 에러 핸들링이 적절한가 (삼킨 곳 없는가)
- [ ] 디버그 코드(console.log, debugger)가 없는가
- [ ] 하드코딩된 값이 없는가 (상수/설정 사용)
- [ ] 불변 패턴을 사용했는가
- [ ] 매직 넘버/스트링이 없는가
- [ ] 주석은 WHY를 설명하는가 (WHAT은 코드 자체가 보여줌)
- [ ] [CUSTOMIZE] 프로젝트별 체크항목

## [CUSTOMIZE] 프로젝트별 스타일

- 언어별 컨벤션
- 프레임워크 패턴
- 린터/포맷터 설정
