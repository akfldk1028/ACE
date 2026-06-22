# ARR Hermes — MAS 프레임워크 매핑 + Step 16~19 순차 가이드

> mas.md 스펙 ("국내외 AI 모델 연계 Sense→Think→Act→Learn + Multi-Agent + LTM + 자기학습") 관점에서 ARR Hermes 현 상태 + 남은 작업.
> 작성: 2026-04-27. 다음 갱신: Telegram E2E 통과 후.

---

## 1. mas.md 스펙 ↔ ARR Hermes 매핑

### 1.1 Sense → Think → Act → Learn 전체 흐름

```
[Sense]                   [Think]                  [Act]                    [Learn]
사용자 메시지 (Telegram)  Qwen-plus LLM            land_analyst tool        Hermes 3-layer memory
       ↓                       ↓ 의도 파악         → ARR Django REST       → 단기/중기/장기
이전 대화 컨텍스트       → 도구 선택              → Vworld + Neo4j        → 사용자 선호 누적
       ↓                       ↓ 파라미터 추출    → 응답 (BCR/FAR/규제)   → SOUL.md 진화 (피드백)
도구 결과 (외부 데이터)  → 추론 (Honesty Rule)   → 자연어 응답 생성       → 미래: Continual Fine-tune
                              ↓                                              (자체 모델 검토)
                         → 다음 행동 결정 (SKILL.md)
```

### 1.2 mas.md 핵심 요건 ↔ 현재 구현

| mas.md 요건 | ARR Hermes 현재 상태 | 위치 |
|-------------|-------------------|------|
| **국내외 AI 모델 연계** | Qwen-plus (DashScope, 외부) | `~/.hermes/.env` `DASHSCOPE_API_KEY` |
| **자체+외부 모델** | 외부 1개 (Qwen). 자체 fine-tune은 미래 | (ANTHROPIC_API_KEY 추가 가능) |
| **도메인 특화** | 한국 건축법규/토지 규제 | `gateway/SOUL.md` (건축 분석가 persona) |
| **Sense 단계** | Telegram 메시지 수신 + 도구가 외부 데이터 수집 | `tools.land_analyst()` → ARR Backend → Vworld/Neo4j |
| **Think 단계** | LLM 의도 파악 + 도구 선택 + 추론 | Hermes Gateway + SOUL.md + SKILL.md |
| **Act 단계** | 도구 실행 + 응답 생성 | `arr_gateway/tools.py` + LLM 자연어 가공 |
| **Learn 단계** | Hermes 3-layer memory (자동) | `~/.hermes/memories/` (단기/중기/장기) |
| **장기 메모리(LTM)** | Hermes 3-layer + 우리 `memory/` 폴더 | `~/.hermes/memories/`, `D:/DevCache/.../memory/` |
| **맥락 기반 추론** | 이전 대화 자동 포함 | Hermes 빌트인 |
| **자기학습 (Self-improving)** | Hermes 빌트인 (skill creation from experience) | TBD: 실제 자기학습 메커니즘 검증 필요 |
| **Multi-Agent 협력** | 현재 1 agent (land_analyst) → 미래 10 agent | `gateway/skills/<name>/SKILL.md` 추가로 확장 |
| **에이전트 간 통신** | 단일 Hermes 안 도구들 (작은 규모는 충분) | 미래 분산 시 A2A 프로토콜 |
| **분산 의사결정** | 미구현 | Multi-Hermes 인스턴스 시 Gateway pattern |

### 1.3 mas.md 성과지표 ↔ 현재 측정

| 지표 (mas.md) | 우리 측정 가능? | 현재값 |
|---------------|---------------|------|
| 해석 이력 저장률 95%+ | Hermes memory 자동 | 100% (모든 대화 저장) |
| 유사 해석 추천 정확도 90%+ | 미구현 (LTM 검색 필요) | TBD |
| 학습 기반 성능 향상률 30%+ | 미구현 (baseline 측정 필요) | TBD |
| 맥락 이해 반영률 85%+ | Hermes 빌트인 | TBD (측정 도구 필요) |
| 전문가 피드백 반영 속도 24h | 수동 (SOUL.md/SKILL.md 업데이트) | < 1h (commit + restart) |
| 메모리 기반 자동 재활용률 70%+ | Hermes 3-layer | TBD |
| 데이터 신뢰성 5% 이하 오류 | Honesty Rule (SOUL.md) | TBD |

→ 측정 도구 미구현. PoC 통과 후 별도 plan.

---

## 2. 현재 진행 상태 (15/23 ✅)

### 완료 (CLI E2E 검증됨)

```
[1] SSH key 생성
[2] Oracle E4 paid VM 생성 (158.180.66.165, ~$22/월)
[3] apt 부트스트랩 (python3.10, git, nginx, iptables)
[4] gateway/ 5파일 작성 + 코드리뷰 + Critical fix
[5] git commit + push (4 commits)
[6] VM git clone (DK-BB)
[7] gateway/SOUL.md + skills/SKILL.md (persona)
[8] Smoke test (Python REPL → ARR Backend)
[9] Hermes Agent 설치
[10] uv pip install plugin (Hermes venv)
[11] ~/.hermes/plugins/arr-gateway 심볼릭 링크
[12] hermes plugins enable arr-gateway
[13] SOUL.md → ~/.hermes/SOUL.md 복사
[14] ~/.hermes/.env 작성 (BOT_TOKEN 제외)
[15] CLI oneshot E2E 통과 ⭐ — Sense→Think→Act 검증
```

### 남은 4단계 (Step 16~19) — 순차 진행

```
[16] BotFather에서 새 봇 생성 (사용자, 5분)
[17] BOT_TOKEN을 .env에 추가 (사용자 SSH, 1분)
[18] systemd 서비스 등록 + start (사용자 SSH, 30초)
[19] 실제 Telegram 메시지 E2E 검증 (사용자 핸드폰)
```

---

## 3. Step 16~19 순차 가이드

### Step 16. BotFather에서 봇 만들기 (Telegram 앱, 5분)

**목적**: ARR Hermes의 Sense 채널 (사용자 입력) 확보.

**왜 별도 봇?**: ClickAround `@DK_BA_bot`은 CEO persona (자율 마케팅). ARR은 건축 분석가 persona — 다른 SOUL.md, 다른 메모리 컨텍스트. **N agent ≠ N bot, 1 bot = 1 persona** 원칙 (memory `principle.md` 원칙 3).

#### 절차

```
1. Telegram 앱 → 검색창 → @BotFather → 채팅 시작
2. /newbot 입력
3. 봇 이름 입력 (사용자한테 보이는 이름)
   예: "DK 건축 분석가" / "ARR 건축 도우미" / "건축법규 봇"
4. username 입력 (반드시 'bot'으로 끝)
   예: "DK_arch_bot" 또는 "arr_archi_bot"
   (이미 사용 중이면 다른 이름 시도)
5. BotFather가 BOT_TOKEN 발급
   형식: "1234567890:AAH-..."
   → 안전한 곳에 보관 (채팅에 적지 말 것)
```

#### 검증

BotFather 답변에서 봇 username과 토큰 확인. 봇 검색 → 본인이 본 봇 맞는지.

---

### Step 17. BOT_TOKEN을 VM .env에 추가 (사용자 SSH, 1분)

**목적**: Hermes가 Telegram API와 통신할 수 있게 인증 정보 주입.

**보안**: 토큰은 채팅에 적지 말고 직접 SSH로 입력.

#### 절차

```bash
# 1. SSH 접속
ssh -i ~/.ssh/oracle_key_arr ubuntu@158.180.66.165

# 2. 토큰 추가 (YOUR_TOKEN 자리에 BotFather에서 받은 토큰)
echo "TELEGRAM_BOT_TOKEN=YOUR_TOKEN" >> ~/.hermes/.env

# 3. 확인 (마지막 줄에 토큰 들어갔는지)
tail -1 ~/.hermes/.env
```

#### 검증

`tail -1 ~/.hermes/.env` 출력에 `TELEGRAM_BOT_TOKEN=...` 보이면 OK.

⚠️ `.env` 파일 권한 확인: `chmod 600 ~/.hermes/.env` (Step 14에서 이미 적용).

---

### Step 18. systemd 서비스 등록 + 시작 (사용자 SSH, 30초)

**목적**: ARR Hermes가 24/7 백그라운드 운영. 재부팅 후 자동 시작. **Sense 채널 항상 켜짐**.

#### 절차 (위 SSH 세션 그대로)

```bash
# 서비스 파일 생성
sudo tee /etc/systemd/system/hermes-arr.service > /dev/null << 'EOF'
[Unit]
Description=Hermes ARR Gateway (건축 분석 전문가)
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/25_ACE/gateway
EnvironmentFile=/home/ubuntu/.hermes/.env
Environment=PATH=/home/ubuntu/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=HOME=/home/ubuntu
ExecStart=/home/ubuntu/.local/bin/hermes gateway start
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

# 등록 + 시작
sudo systemctl daemon-reload
sudo systemctl enable hermes-arr
sudo systemctl start hermes-arr

# 상태 확인 — "Active: active (running)" 보여야 함
sudo systemctl status hermes-arr --no-pager

# 로그 확인 (실시간, Ctrl+C로 빠져나옴)
sudo journalctl -u hermes-arr -f
```

#### 검증

- `Active: active (running)` 확인
- 로그에 "Telegram gateway started" 또는 "Listening for messages" 비슷한 메시지

#### 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `Active: failed` | PATH 문제 | service 파일 `Environment=PATH=...` 라인 확인 |
| 로그에 "BOT_TOKEN missing" | .env 토큰 누락 | Step 17 다시 |
| 로그에 "Unauthorized" | 잘못된 토큰 | BotFather에서 토큰 다시 확인 |

---

### Step 19. Telegram E2E (사용자 핸드폰, 1분)

**목적**: Sense→Think→Act→Learn 전체 사이클 검증.

#### 절차

```
1. Telegram 앱 → 검색창 → 본인 봇 username
   예: @DK_arch_bot
2. /start 또는 그냥 메시지
3. 첫 테스트 메시지:
   "PNU 1168010100106770003 분석"
4. ~30초 대기
```

#### 기대 흐름 (mas.md framework)

```
[Sense] Telegram → Hermes 메시지 수신
   ↓
[Think] Qwen-plus LLM이 의도 파악:
        "PNU 분석 요청" → land_analyst 도구 선택
   ↓
[Act]   tools.land_analyst({"pnu_or_address": "1168..."}) 실행
        → ARR Backend Django POST /land/analyze/
        → Vworld + Neo4j (or partial fail)
        → JSON 응답
   ↓
[Think] LLM이 응답 가공 (SOUL.md Honesty Rule 준수)
   ↓
[Act]   Telegram 답변 전송:
        "📍 강남구 역삼동 677-3
         - 용도지역: ...
         - 건폐율: ...
         (또는 Vworld 일시 장애 안내)"
   ↓
[Learn] Hermes 3-layer memory에 자동 저장:
        - 단기: 현재 대화
        - 중기: 사용자 분석 PNU 기억
        - 장기: 사용자 선호도/패턴
```

#### 검증 (4가지 다 통과해야 완전 성공)

- [ ] 봇이 답변 받음 (30초 내)
- [ ] PNU 19자리 정확히 인식 (강남구 역삼동 677-3)
- [ ] 미구현 도구 약속 X (legal_interpreter, mass_optimizer 등 언급 X)
- [ ] 다음 사용자 메시지 "그 땅 다시 분석해줘"에서 컨텍스트 활용 (3-layer memory 작동)

#### 추가 테스트 (Learn 단계 검증)

```
첫 메시지: "PNU 1168010100106770003 분석"
두 번째 메시지: "그 땅 정리해서 다시 알려줘"
→ 2번째 메시지에서 "그 땅" = 1168...로 자동 매핑 (중기 메모리)
```

---

## 4. PoC 통과 후 다음 (Step 20~23, mas.md Multi-Agent 확장)

mas.md "Multi-Agent 협력" 요건 충족 위해:

### Step 20: 도구 9개 추가 (memory `agents-roster.md` Phase 1~4)

```
현재: land_analyst (1)
+ legal_interpreter (법조항 검색, light)
+ validator (규제 검증, light)
+ document_summarizer (도면 vision, light)
+ mass_optimizer (NSGA-II, heavy → Celery)
+ floor_planner (5종 평면, heavy → Celery)
+ spec_writer (시방서, heavy)
+ structural_reviewer (구조 검토, heavy)
+ cost_estimator (견적, heavy)
+ schedule_planner (CPM 일정, heavy)
```

각각 `arr_gateway/tools.py`에 함수 추가 + `schemas.py`에 schema + `__init__.py`에 register_tool. SKILL.md는 영역별 추가.

### Step 21: 인증 (`/link <token>`) — mas.md "전문가 피드백 통합 인터페이스"

`/link 6자리토큰` 명령어로 Telegram user_id ↔ Django User 매핑. 본인 외 사용자 받기 시 필수.

### Step 22: Multi-Agent 협력 — mas.md "역할 분담형 에이전트 아키텍처"

도구 4개 이상 시 Hermes의 자동 도구 선택 외에 명시적 협력 패턴:
- **Sequential**: land_analyst → mass_optimizer → spec_writer
- **Parallel**: land_analyst + legal_interpreter 동시 실행
- **Validator**: 결과 → validator 통과 후 사용자 답변

`skills/<name>/SKILL.md`로 정의.

### Step 23: 자기학습 (Self-improving) — mas.md "지속 학습 엔진"

- Hermes 빌트인 skill creation from experience 검증
- 사용자 피드백 누적 → SOUL.md 자동 업데이트 (실험적)
- LTM DB (별도) 구축: 과거 분석 결과 + 정확도 추적
- Continual fine-tuning (자체 모델 검토 시)

mas.md 성과지표 측정 시작 (지표 7개).

---

## 5. 박제 위치 (다음 세션 참조)

```
D:/DevCache/claude-data/projects/D--Data-25-ACE/memory/
├── MEMORY.md                               # 인덱스 (자동 로드)
└── agent-architecture/
    ├── README.md                           # 폴더 인덱스
    ├── decision.md                         # Hermes 채택 + 6 결정
    ├── infrastructure.md                   # 23단계 진행 (15/23 ✅)
    ├── execution-pattern.md                # 추상화 + schema 형식
    ├── agents-roster.md                    # 10 agent 명세
    ├── principle.md                        # 3 원칙
    ├── gateway-files-guide.md              # 파일별 역할 (식당 비유)
    ├── hermes-runtime-notes.md             # ⚠️ 6개 함정 + 8단계 절차
    └── frontend-chat-roadmap.md            # 캐릭터 채팅 UI 옵션 3
```

다음 세션 AI는 자동으로 MEMORY.md 로드하면서 위 8개 파일 인덱스 봄.

---

## 6. 한 줄 요약

> ARR Hermes는 mas.md "Sense→Think→Act→Learn 도메인 특화 Agentic AI" 의 **건축 분석 도메인 인스턴스**. 현재 1 agent 작동 (CLI E2E 검증), Telegram E2E (Step 16~19) 통과 후 Multi-Agent 확장 (Step 20~23, 도구 9개 + 인증 + 협력 + 자기학습 측정).
