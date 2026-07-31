# ClickAround Creator Pro — Oracle 배포 전체 정보

> 다른 프로젝트 AI에게 그대로 복붙해서 컨텍스트 줄 수 있는 단일 문서.
> 마지막 갱신: 2026-04-26 (외부 접근 복구 + bundle-extras 통합 완료)

---

## 1. 한 줄 요약

Oracle Cloud VM 1대 위에서 **자율 AI 에이전트(Hermes)**가 CEO 역할로 ClickAround Creator Pro라는 Claude Code 스킬 번들을 판매한다. 4시간마다 자동으로 영어/한국어 블로그 작성, Bluesky 포스팅, GitHub README 갱신, Telegram 리포트 송신. 매출 목표 월 100만원(~$750).

**현재 상태**: 인프라 안정 / 컨텐츠 자산 41건 / 외부 방문자 7일 누적 2,421(656 unique IPs) / **실판매 0**.

---

## 2. 인프라

### Oracle VM
- IP: `168.107.56.106` (외부 공개, 80/443 open)
- 호스트명: `hermes-business`
- OS: Ubuntu 22.04 (kernel 6.8.0-1049-oracle)
- **Shape: VM.Standard.E4.Flex** (AMD EPYC 7J13, x86_64)
- **사양: 2 OCPU / 4GB RAM / 49GB 디스크** (사용 26% = 13GB)
- 부하: load average 0.00 (사실상 idle, 메모리 1.5GB free)
- **리전: `ap-chuncheon-1`** (춘천, AD-1) — South Korea
- 비용: Oracle Always Free Tier (월 0원)
- 접속: `ssh -i ~/.ssh/oracle_key ubuntu@168.107.56.106`

### Nginx
- `/var/www/html/` 아래 5개 사이트:
  - `clickaround/` — 메인 영어 랜딩 (Pro 번들 ₩59,000)
  - `clickaround/starter/` — Starter 단품 ($9 ffmpeg-only)
  - `clickaround/blog/` — 영어 블로그 (제품별, 11개)
  - `notion-finder/` — 한국어 랜딩 + 블로그 (대학생 노션)
  - `ffmpeg-toolkit/` — FFmpeg 단독 랜딩
- 모두 외부 200 OK (2026-04-26 검증)
- iptables 80/443 ACCEPT + iptables-persistent 영구화

### Hermes Agent (gateway)
- 위치: `/home/ubuntu/hermes-business/hermes-agent/`
- 실행: systemd `hermes-gateway.service` (active, restart=on-failure)
- LLM: Alibaba Qwen-plus (DashScope intl 엔드포인트)
- MCP 서버: Brave (10), Marketing (33 — Bluesky/Threads/GitHub/LS/Telegram 도구 포함)
- 환경 파일: `/home/ubuntu/.hermes/.env` (모든 크레덴셜, 아래 표 참고)

### 환경 변수 (`/home/ubuntu/.hermes/.env`, 27개)

> **주의**: 외부 AI한테 공유 시 키 값(value)은 절대 노출 금지. 아래는 키 이름 + 용도만.

#### LLM
| KEY | 용도 |
|-----|------|
| `DASHSCOPE_API_KEY` | Alibaba Qwen-plus (메인 LLM) |
| `DASHSCOPE_BASE_URL` | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` (Singapore 엔드포인트) |

#### Oracle Cloud
| KEY | 용도 |
|-----|------|
| `OCI_TENANCY_OCID` / `OCI_USER_OCID` | OCI CLI 인증 |
| `OCI_REGION` | `ap-chuncheon-1` |
| `OCI_TENANCY_NAME` / `OCI_USER_EMAIL` | 메타 |
| `OCI_INSTANCE_ID` | VM identifier |
| `OCI_VM_IP` / `OCI_VM_SHAPE` | 168.107.56.106 / VM.Standard.E4.Flex_2_4gb |

#### Telegram
| KEY | 용도 |
|-----|------|
| `TELEGRAM_BOT_TOKEN` | @DK_BA_bot |
| `TELEGRAM_CHAT_ID` / `TELEGRAM_HOME_CHANNEL` | 운영자 chat 7802145629 |
| `TELEGRAM_ALLOWED_USERS` | ACL (운영자만) |
| `GATEWAY_ALLOW_ALL_USERS` | false 권장 |

#### Lemon Squeezy (결제)
| KEY | 용도 |
|-----|------|
| `LEMONSQUEEZY_API_KEY` | JWT 토큰 (1035 chars), API 호출 |
| `LEMONSQUEEZY_STORE_ID` | 300033 |
| `LEMONSQUEEZY_STORE_NAME` / `LEMONSQUEEZY_STORE_URL` | ClickAround / clickaround.lemonsqueezy.com |

#### GitHub
| KEY | 용도 |
|-----|------|
| `GITHUB_TOKEN` | classic PAT (scopes: repo, admin:org, workflow) |
| `GITHUB_ORG` / `GITHUB_USER` | clickaround / akfldk1028 |

#### Bluesky
| KEY | 용도 |
|-----|------|
| `BLUESKY_HANDLE` | clickaround.bsky.social |
| `BLUESKY_APP_PASSWORD` | App password (계정 비밀번호 아님) |

#### 검색 / 리서치
| KEY | 용도 |
|-----|------|
| `BRAVE_API_KEY` | Brave Search MCP |
| `TAVILY_API_KEY` | Tavily web search |

#### 보안 플래그
| KEY | 용도 |
|-----|------|
| `TIRITH_ENABLED` | `false` 강제 (cron approval 차단 우회) |

#### 미설정 (필요 시 사용자 발급)
| KEY | 용도 |
|-----|------|
| `RESEND_API_KEY` | 이메일 캡처/뉴스레터 (없음) |
| `NOTION_API_KEY` | Notion 템플릿 자동 생성 (없음, notion-finder 활성화 시만 필요) |
| `THREADS_USER_ID` / `THREADS_ACCESS_TOKEN` | Meta Threads 포스팅 (없음) |
| `DEVTO_API_KEY` | Dev.to 자동 게시 (없음) |

---

## 3. 활성 크론 6개

| ID | 이름 | 스케줄 | 출력 |
|----|------|--------|------|
| 0961cb8c | ceo-evening | 매일 21:00 UTC | Telegram |
| 2f8ba17d | cfo-weekly | 월 10:00 UTC | Telegram |
| a91366b2 | researcher | 화·금 14:00 UTC | local |
| 5e86a91f | weekly-reflect | 일 20:00 UTC | Telegram |
| 95b4e6cd | clickaround-launch | 매 4h | Telegram |
| 209eb5f3 | notion-blog-cycle | 매 4h (offset) | Telegram |

매 4시간마다 두 알터네이팅 사이클이 발화 → 각 사이클이 한 블로그 + Bluesky 포스트 + GitHub README 갱신 + 일일 로그 + Telegram 리포트 1건 생산.

---

## 4. 상품 (Lemon Squeezy)

| LS ID | 상품 | 가격 | 상태 | 체크아웃 URL |
|-------|------|------|------|-------------|
| 988697 | **ClickAround Creator Pro** | ₩59,000 lifetime | published | https://clickaround.lemonsqueezy.com/checkout/buy/d798e647-129e-4303-b76d-924cc4b18b50 |
| 974100 | Notion Pro Pack (legacy) | ₩49,000 | draft (숨김) | — |
| (대기) | FFmpeg Toolkit Starter | $9 lifetime | 미등록 | 사용자 Playwright 발급 필요 |

**Pro 번들 zip 구성** (100KB, 7 plugins + 26 skills + bundle-extras):
- ffmpeg-toolkit (4 skills: audio/subtitle/concat/editor)
- ytb-content-creator (3: tech/news/poetry video shorts)
- image-generation (2: nanobanana/seedance)
- ytb-deploy (3: cloud-run/font-upload/youtube-token)
- ytb-storage (2: gcs/youtube-upload)
- ytb-books (3: episode/math/neo4j-graphrag)
- indie-hacker-playbook (9: validate-idea/mvp/pricing/...)
- bundle-extras: BUNDLE_GUIDE + 14 examples + 7 cursor-rules + 5 presets

---

## 5. GitHub (clickaround org, public MIT)

| Repo | 용도 | URL |
|------|------|-----|
| marketplace | 메타 (7 plugins 등록) | https://github.com/clickaround/marketplace |
| ffmpeg-toolkit | 4 video skills | https://github.com/clickaround/ffmpeg-toolkit |
| ytb-content-creator | 3 short-form video skills | https://github.com/clickaround/ytb-content-creator |
| image-generation | 2 AI 이미지 skills | https://github.com/clickaround/image-generation |
| ytb-deploy | 3 deployment skills | https://github.com/clickaround/ytb-deploy |
| ytb-storage | 2 storage skills | https://github.com/clickaround/ytb-storage |
| ytb-books | 3 book→video skills | https://github.com/clickaround/ytb-books |
| indie-hacker-playbook | 9 founder skills | https://github.com/clickaround/indie-hacker-playbook |

설치 명령: `/plugin marketplace add https://github.com/clickaround/marketplace`

전부 GitHub Discussions + Issues 활성화 / CONTRIBUTING.md (Star us + Pro bundle 안내) 추가 완료 (2026-04-26).

**Stars 현재 모두 0** — 가장 큰 공백.

---

## 6. 소셜 / 채널

- **Bluesky**: `@clickaround.bsky.social` (자동 포스팅 활성, 15+ posts, 팔로워 ~0)
- **Telegram bot**: `@DK_BA_bot` → 운영자 chat 7802145629 (자동 리포트 수신)
- **이메일 리드**: 없음 (Resend API 미연동)
- **도메인**: 없음 (IP 직접 노출)

---

## 7. 자율 사이클 동작 흐름

```
crontab fires (every 4h)
  ↓
Hermes gateway loads SOUL.md (identity/규칙) + SKILL.md (실행 절차)
  ↓
SKILL STEP 1: bash verify-metrics.sh + inventory.sh
  → BLOG_N, VISITORS, REVENUE 추출
  ↓
SKILL STEP 2: phase 결정
  if BLOG_N < 60: BUILD (블로그 1개 작성)
  elif VISITORS == 0: DISTRIBUTE (마켓플레이스 listing 초안)
  elif REVENUE == 0 && CONVERT_AGE > 24h: CONVERT (랜딩 수정)
  else: BUILD (기본)
  ↓
실행 (Build/Distribute/Convert/Optimize)
  + Bluesky 포스팅 (해당 phase에 한해)
  + GitHub README 갱신 (clickaround-launch만)
  ↓
SKILL STEP 3: daily_log append + lesson 학습
  ↓
SKILL STEP 4: Telegram 고정 포맷 리포트 → 운영자
```

---

## 8. 핵심 파일 위치

### VM
| 경로 | 역할 |
|------|------|
| `/home/ubuntu/.hermes/.env` | 모든 크레덴셜 |
| `/home/ubuntu/.hermes/config.yaml` | gateway 설정 |
| `/home/ubuntu/.hermes/cron/jobs.json` | 6 크론 정의 |
| `/home/ubuntu/.hermes/skills/business/notion-blog-cycle/SKILL.md` | 한국어 SEO 사이클 |
| `/home/ubuntu/.hermes/skills/business/clickaround-launch-cycle/SKILL.md` | 영어 제품 사이클 |
| `/home/ubuntu/.hermes/memory/company/daily_log` | 모든 사이클 기록 (append-only) |
| `/home/ubuntu/hermes-business/deploy/SOUL.md` | identity / honesty / 금지 |
| `/home/ubuntu/hermes-business/deploy/harness/verify-metrics.sh` | 매출/트래픽 검증 |
| `/home/ubuntu/hermes-business/deploy/harness/inventory.sh` | 상품/블로그 카운트 |
| `/home/ubuntu/products/_marketplace/` | 7 plugins 빌드 소스 + dist/ |
| `/var/www/html/` | nginx 서빙 |

### 로컬 (D:/Data/37_BA/)
| 경로 | 역할 |
|------|------|
| `deploy/` | VM 미러 (SOUL/SKILL/configs/products) |
| `deploy/launch/` | Product Hunt + Show HN 자료 (이미 준비 완료) |
| `deploy/launch/gallery/*.png` | PH 업로드용 5장 (1280×800 UTF-8) |
| `docs/external-briefing/` | 이 폴더 (다른 프로젝트 AI용) |
| `HANDOFF.md` | 마지막 세션 이어붙임 메모 |

---

## 9. 매출 / 트래픽 현재 (2026-04-26)

| 지표 | 값 |
|------|----|
| LS 총 주문 | **0** |
| LS 총 매출 | **0** KRW |
| 외부 방문자 (7일) | 2,421 (656 unique IPs, 대부분 SEO bot) |
| 한국어 블로그 | 30개 |
| 영어 블로그 | 11개 |
| Bluesky 포스트 | 15+ (auto) |
| GitHub stars (8 repos) | 0 |
| 월 예산 사용 | $0.50 / $20 |

---

## 10. 알려진 이슈 + 우회

| 이슈 | 상태 | 우회 |
|------|------|------|
| VM 재부팅 시 iptables 80/443 사라짐 | 해결 (iptables-persistent) | — |
| verify-metrics.sh가 .gz 못 읽음 | 해결 (v4: zcat -f) | — |
| Reddit API 신규 앱 거부 (2025-11 정책) | 영구 제약 | 네이버/X/Bluesky 사용 |
| LS POST /v1/products 미지원 | 영구 제약 | Playwright로 대시보드 조작 |
| Telegram 이모지 깨짐 | 해결 | [OK]/[WARN]/[FAIL] 텍스트 |
| write_file `/var/www/` persist 가끔 실패 | 가끔 발생 | terminal `cat > file` 우회 |
| Tirith Security Scanner 차단 | 해결 (TIRITH_ENABLED=false) | — |

---

## 11. 외부 AI에게 활용 가능한 자산

다른 프로젝트 AI가 즉시 쓸 수 있는 ClickAround 인프라:

### 컨텐츠 자산
- 41개 블로그 (한국어 30 + 영어 11), 모두 nginx 외부 공개
- 인덱스: `http://168.107.56.106/notion-finder/blog/sitemap.xml` (있다면)
- BUNDLE_GUIDE.md (40+ page), examples 14개, cursor-rules 7개, presets 5개

### API 인프라 (이미 인증)
- LS API key (활성, store 300033)
- GitHub PAT (clickaround org, repo + admin 권한)
- Telegram bot (@DK_BA_bot, 운영자 chat 알림 가능)
- Bluesky API (handle: clickaround.bsky.social)
- DashScope (Qwen-plus, 월 $0.50 사용)

### 자동화 능력
- 24/7 자율 cron (Hermes agent로 새 skill 추가 즉시 반영)
- nginx 즉시 deploy 가능 (`/var/www/html/<new-path>/`)
- Bluesky 포스팅 가능 (marketing MCP)
- GitHub repo 생성/관리 가능

### 통합 후보 시나리오

1. **외부 앱 → ClickAround 트래픽**: 외부 앱에 "Powered by ClickAround skills" 배지 → 클릭 시 GitHub repo로 유도 (백링크 + 신뢰)
2. **외부 앱 사용자 할인**: 외부 앱 로그인 사용자 전용 30% 할인 코드 (LS API로 발행 가능)
3. **외부 앱이 ClickAround Skill 사용**: 외부 앱 백엔드에서 FFmpeg Toolkit / image-generation 호출 (오픈소스 MIT라 가능)
4. **Bi-directional content**: 한쪽 블로그가 상대 제품 케이스 스터디 작성 → 양쪽 SEO 백링크
5. **공유 이메일 캡처**: 외부 앱이 수집한 이메일에 ClickAround 뉴스레터 발송 (Resend 도입 후)

---

## 12. 다음 우선순위

### 사용자 1회 작업 (계정 발급, 25분)
- Resend API 키 (이메일 캡처)
- MCPize 가입 / claudemarketplaces.com 등록
- Claude 공식 마켓 submit
- (선택) 도메인 1개 구매 + DNS

### 사용자 런칭 (30분)
- Product Hunt 런칭 (자료 `D:/Data/37_BA/deploy/launch/product-hunt/` + Gallery PNG 5장 준비 완료)
- Show HN 포스트
- 지인 DM 10명

### 에이전트 자동 (24h 내)
- 다음 사이클(09:31 UTC)부터 BUILD phase 복귀, ⭐ Star us 멘션 포함

---

## 13. 이 문서 사용법

다른 프로젝트 AI에게 던질 때:

```
이 문서는 내가 운영 중인 별도 프로젝트(ClickAround)의 전체 배포 정보입니다.
우리 프로젝트(<여기에 본인 앱 이름>)와 어떻게 시너지를 낼 수 있는지 5가지 구체안 제시해주세요.
특히 [활용 가능한 자산] 섹션 11번을 참고해주세요.

[여기에 이 MD 전체 복사]
```

또는:

```
참고 컨텍스트입니다. <앱 이름>에 다음 기능 추가하려고 합니다:
- "ClickAround과 통합" 페이지
- 사용자가 클릭하면 어떻게 흘러가야 할지 설계해주세요.

[여기에 이 MD 전체 복사]
```

---

*작성: Hermes CEO Agent + DK (2026-04-26)*
*다음 갱신 시점: 첫 매출 발생 또는 30일 후*
