# massv2 HANDOFF — 이걸 읽으면 바로 이어서 할 수 있다

대상: 다음 세션의 Claude, Codex 에이전트, MassAgent. 코드보다 이 파일과 `FLOW.md`를 먼저 읽는다.
갱신: 2026-09-05 밤.

## 지금 상태 한 문단

효돈동 필지(PNU 4115011300106840001, 건폐율 60% = 1,497.877 ㎡, 용적률 250% = 6,241.962 ㎡)에
매스 보드 **35석**(저작 7 + BOOK 28)이 새 시대(20260904-2107)로 앉아 있고 같은 URL에 발행돼 있다.
BOOK은 서브에이전트가 저작한 40개(`c260-book/payload-llm01.json`)를 필지 크기로 수입해 게이트를
통과한 것이고, 저작 라운드는 `agent08`이다. 이전 판은 `runs/board-archive-20260904-2107`에 통째로 있다.

## 한 사이클을 돌리는 법

```
cd D:/Data/25_ACE/agents/MassAgent
bash skills/mass-cycle/scripts/cycle.sh <라운드명> [문장수]     # 12단계, 실패 시 정지
bash skills/mass-cycle/scripts/cycle.sh <라운드명> --from=8      # 재개
```

BOOK 저작만 예외다. `--author-mode llm`은 OpenAI 크레딧이 없어 막혀 있으니 **서브에이전트가
저자**가 된다: `geometry_language/llm_adapter.py`의 GEOMETRY_AUTHOR_PROMPT_CONTRACT ·
BASE_SEED_SPECS · BASE_FORM_SPECS · AUTHOR_GEOMETRY_GATE_POLICY와
`creative_program_author.authored_programs_from_payload`를 읽고 페이로드 JSON을 쓴 뒤

```
cd D:/Data/25_ACE/ARR/backend
python -X utf8 manage.py generate_maas_creative_100 --count 40 --pnu 4115011300106840001 \
  --capacity-ceiling-m2 1497.877 --output-root tmp_mass_check/c260-book --run-id <id> \
  --author-mode payload --author-payload <payload.json>
cd tmp_mass_check/_massv2 && python -X utf8 tools/book_import.py <c260-book/id 절대경로> <id>
```

`recipe_fixture`는 데모용이다. 그걸로 돌리면 십자·L·중정만 나온다.

## 오늘(09-05) 무엇이 바뀌었나 — 커밋 순

| 커밋 | 내용 | 검증 |
|---|---|---|
| 78467be | FLOW.md 신설. BOOK이 필지 크기로 오고(`book_import._to_parcel_size`) 서는가·방이 되는가 게이트 통과 | 40 중 5 탈락(떠 있는 판 등) |
| 5cc1caf | BOOK 좌석 복귀(퇴거는 오답이었다) | 통과 16/42 → 25/38 |
| b245dbd | FLOW: 저자는 서브에이전트, 전후는 시대로 가른다 | — |
| d10629b | 서브에이전트 저작 40 프로그램 페이로드 | 40/40 게이트 통과 |
| 6dde677 | `execute.delivered()` = realign → regulated(캐리어 가드). `compile._own_figure` | massv2 26 테스트 통과, 7석 전부 섬 |
| 59f592c | **점수는 그림의 것**: `shape_id`가 key→shortlist→ledger→board, 앵커는 정체성 일치·자기 라운드 제외 | 보정 `median_drift` 작동, 11/11 |
| 다음 커밋 | 저작 BOOK 경로가 책 슬롯에 **증가경로 매칭**으로 붙는다(`creative_floor_portfolio.build_creative_floor_portfolio_report`, 픽스처 경로의 `augment`와 같은 원리) | 포트폴리오 30 테스트 통과. 순서 의존 실증: 로테이션 전 35/40 → **40/40**, 커밋 순서 40/40 그대로, 2초 |

## 왜 그렇게 했나 — 세 문장

1. BOOK이 못생겼던 건 언어가 아니라 **필지 없이·게이트 없이** 심사대에 올린 것이었다.
2. 덩어리로 읽히는 건 봉투 팔각형(꼭짓점 5.98→5.86, 무시할 만함)이 아니라 **정렬**이었고, `regulate.py`는 있었는데 아무도 안 불렀다.
3. **앵커가 부러져 있었다**: 엔진 변경으로 그림이 바뀐 좌석이 옛 점수로 앵커를 타 델타 스프레드 1.32, 자가 안 움직여 한 라운드가 raw로 기록됐다. 안 바뀐 그림이 0.4~1.0 떨어졌다.

## 남은 일 — 결과에 미치는 순

1. **IR 일반화**(가장 큼): 볼륨 = 다각형 × 높이라 곡선 평면·경사 지반·2축 곡면·아트리움을 못 말한다. 당선작 발화 상위 5가 전부 이것. 지붕 동사·datum은 특수 튜플.
2. 평면 어휘 10가족뿐. 곡선은 1 없이는 못 온다.
3. ~~BOOK 슬롯 배정이 순서 의존~~ → 증가경로 매칭으로 수정(위 표).
4. `full_ground` 변형이 비스듬한 필지에서 필지 모양 판이 된다(O12). 깨끗한 도형으로 바꿀지, 배심이 낮게 주는 걸로 둘지 **사용자 결정**.
5. 절대 점수 → **쌍비교**. 같은 그림도 타일당 ±0.5 흔들린다(cascade 4.33→3.75). develop은 이미 쌍비교.
6. ~~`judge.sh`가 TILE 줄 개수만 센다~~ → `--verify`(채점기와 같은 읽기)로 검사, 거부되면 같은 심사원을 한 번 더 앉힌다.
7. 배심 취향 검증 없음(문헌: VLM≈전문가 52%).
8. develop이 심은 문장의 `why`가 변이값과 안 맞음.
9. 스윕에 책 단위 중복 가족 검사 없음.
10. 한국 트랙 K0(보류).

## 함정 — 반드시

- `--new-era`로 보드를 비우면 BOOK부터 재수입. 스테이지는 심사원 파일을 지운다(`--from=N`).
- **엔진(실행기·컴파일·렌더)이 바뀌면**: 굽기 → 픽셀 diff → 바뀐 라운드만 재스테이지·재심사·재채점. 안 바뀐 좌석 점수만 유효.
- 커밋은 바깥 저장소(`D:/Data/25_ACE`)에서. `ARR/backend`에서 커밋하면 안쪽 저장소로 들어간다.
- `.gitignore:130`이 `tmp_mass_check/*/`를 무시한다. 페이로드는 `git add -f`.
- 레거시 maas stage 테스트 12건(`test_maas_mass_stage`·`test_maas_program_massing`)은 **클린 HEAD에서도 실패**(7F+5E). 오늘 작업과 무관.
- pytest는 Django 픽스처 에러가 난다. `python -X utf8 manage.py test <module>`로.

## 산출물

- 보드·시트: `runs/board/`, `runs/study-after/study.html`
- 아티팩트(같은 URL): https://claude.ai/code/artifact/4ca086d7-f893-4034-9d3d-d37f5d6901a0
- 메모리 정본: `D:/DevCache/claude-data/projects/D--Data-25-ACE/memory/massv2-triple-review-2026-09-02.md` 끝 절
