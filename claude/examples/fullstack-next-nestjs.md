# 풀스택 예시: Next.js 16 + NestJS v11

Next.js 16 (프론트) + NestJS v11 (백엔드) 풀스택 프로젝트의 실제 구조와 코드 예시다.

---

## 디렉토리 구조

### 프론트엔드

```
frontend/
├── src/
│   ├── app/               # 페이지 + Server Actions (App Router)
│   │   ├── layout.tsx     # 루트 레이아웃 (Server Component)
│   │   ├── page.tsx       # 메인 페이지 (Server Component)
│   │   └── loading.tsx    # Suspense 폴백
│   ├── components/        # UI 컴포넌트
│   │   ├── ui/            # 프리젠테이션 컴포넌트 (Client Component)
│   │   └── layout/        # 레이아웃 컴포넌트
│   ├── hooks/             # 커스텀 훅
│   ├── services/          # API 통신
│   ├── actions/           # Server Actions (뮤테이션 로직)
│   ├── types/             # TypeScript 타입
│   └── lib/               # 유틸리티
├── public/                # 정적 자산
└── package.json
```

### 백엔드 (NestJS v11)

```
backend/
├── src/
│   ├── main.ts                  # 엔트리 포인트
│   ├── app.module.ts            # 루트 모듈
│   ├── common/                  # 공유 (가드, 인터셉터, 필터, 파이프)
│   │   ├── guards/              # AuthGuard, RolesGuard
│   │   ├── interceptors/        # LoggingInterceptor, TimeoutInterceptor
│   │   ├── filters/             # HttpExceptionFilter
│   │   └── pipes/               # ValidationPipe (글로벌)
│   ├── config/                  # 환경 설정 (ConfigModule)
│   │   ├── database.config.ts
│   │   └── jwt.config.ts
│   ├── modules/                 # 기능별 모듈
│   │   ├── auth/                # 인증
│   │   │   ├── auth.module.ts
│   │   │   ├── auth.controller.ts
│   │   │   ├── auth.service.ts
│   │   │   ├── dto/             # 요청/응답 DTO (class-validator)
│   │   │   │   ├── login.dto.ts
│   │   │   │   └── register.dto.ts
│   │   │   └── strategies/      # Passport strategies
│   │   │       └── jwt.strategy.ts
│   │   ├── users/               # 사용자
│   │   │   ├── users.module.ts
│   │   │   ├── users.controller.ts
│   │   │   ├── users.service.ts
│   │   │   └── entities/
│   │   │       └── user.entity.ts
│   │   └── {도메인}/            # 추가 도메인별 모듈
│   └── database/
│       ├── migrations/          # TypeORM/Prisma 마이그레이션
│       └── seeds/               # 시드 데이터
├── test/                        # E2E 테스트
│   └── app.e2e-spec.ts
├── nest-cli.json
├── tsconfig.json
└── package.json
```

---

## Next.js 16 핵심 패턴

### Server Component (데이터 조회)

```tsx
// app/page.tsx — 기본은 Server Component
async function getPosts() {
  const res = await fetch('https://api.example.com/posts', {
    next: { revalidate: 60 } // ISR: 60초 캐시
  })
  return res.json()
}

export default async function Page() {
  const posts = await getPosts()
  return <PostList posts={posts} />
}
```

### Server Action (뮤테이션)

```tsx
// app/actions/user.ts
'use server'

export async function createUser(formData: FormData) {
  const name = formData.get('name') as string
  const email = formData.get('email') as string

  // DB 저장 로직
  return { success: true, message: '사용자 생성 완료' }
}
```

### React 19.2 `'use cache'` (Next.js 16 신기능)

```tsx
// app/actions/products.ts
'use server'

// 'use cache' — 결과를 자동 캐시 (React 19.2+)
export async function getRecommendations(userId: string) {
  'use cache'
  return computeRecommendations(userId)
}
```

### Client Component (인터랙션)

```tsx
// app/components/search.tsx
'use client'

export default function Search() {
  const [query, setQuery] = useState('')
  return <input value={query} onChange={e => setQuery(e.target.value)} />
}
```

### Layout + Suspense (로딩)

```tsx
// app/layout.tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  )
}

// app/posts/loading.tsx
export default function Loading() {
  return <div>로딩 중...</div>
}
```

---

## NestJS v11 핵심 패턴

### 모듈 구조

```typescript
// app.module.ts — 루트 모듈
@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    TypeOrmModule.forRoot(databaseConfig),
    AuthModule,
    UsersModule,
  ],
})
export class AppModule {}
```

### Controller (REST) + Swagger

```typescript
import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger'

@Controller('users')
@UseGuards(JwtAuthGuard)
@ApiTags('users')
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Get(':id')
  @ApiOperation({ summary: '사용자 조회' })
  @ApiResponse({ status: 200, type: UserResponseDto })
  @ApiResponse({ status: 404, description: '사용자 없음' })
  findOne(@Param('id', ParseIntPipe) id: number) {
    return this.usersService.findOne(id)
  }

  @Post()
  @HttpCode(201)
  @ApiOperation({ summary: '사용자 생성' })
  @ApiResponse({ status: 201 })
  create(@Body() dto: CreateUserDto) {
    return this.usersService.create(dto)
  }
}
```

### Service (비즈니스 로직)

```typescript
@Injectable()
export class UsersService {
  constructor(
    @InjectRepository(User)
    private readonly repo: Repository<User>,
  ) {}

  async findOne(id: number): Promise<User> {
    const user = await this.repo.findOneBy({ id })
    if (!user) throw new NotFoundException('사용자를 찾을 수 없습니다')
    return user
  }
}
```

### DTO 검증

```typescript
// main.ts
app.useGlobalPipes(new ValidationPipe({
  transform: true,
  whitelist: true,
  forbidNonWhitelisted: true,
}))
```

### 예외 필터

```typescript
@Catch(HttpException)
export class GlobalExceptionFilter implements ExceptionFilter {
  catch(exception: HttpException, host: ArgumentsHost) {
    const ctx = host.switchToHttp()
    const response = ctx.getResponse<Response>()
    const status = exception.getStatus()
    const message = exception.message

    response.status(status).json({
      error: { code: exception.name, message, details: null },
    })
  }
}
```

---

## 데이터 흐름

**조회 (Server Component)**:
```
Client → Next.js Server Component → 외부 API/DB → 응답 → SSR HTML → Client
```

**뮤테이션 (Server Action)**:
```
Client Form → Server Action → 검증 → DB → revalidatePath → UI 갱신
```

**API 호출 (별도 백엔드)**:
```
Client → Next.js UI → fetch('/api/v1/...') → NestJS Controller → Service → TypeORM → PostgreSQL
```

---

## Trade-off

| 장점 | 단점 | 언제 분리해야 하는가 |
|------|------|------|
| 프론트+백엔드 통합 개발 | 배포 복잡 (2개 서비스) | 프론트/백엔드 팀이 완전히 분리될 때 |
| 타입 공유 (DTO → TypeScript) | 초기 설정 비용 | 매우 단순한 프로젝트 (Lean Mode 권장) |
| 단일 레포 — 코드 공유 용이 | 빌드 시간 증가 | 모바일 앱만 필요하고 웹 불필요 시 |
