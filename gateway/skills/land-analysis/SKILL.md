# Land Analysis Cycle — Skill

> Hermes가 사용자 메시지를 받으면 이 SKILL.md를 시스템 프롬프트에 추가. LLM이 분석 흐름 따름.

## Trigger

사용자 메시지에 다음 중 하나 포함 시:
- PNU 19자리 패턴 (`\d{19}`)
- 한국 주소 (시/구/동/번지)
- 키워드: "분석", "규제", "건폐율", "용적률", "용도지역", "이 땅"

## STEP 1 — 입력 파싱

사용자 입력에서 추출:
- **PNU**: 19자리 숫자 직접
- **주소**: "강남구 역삼동 677" 같은 형식
- **불명확 시**: 사용자에게 명확화 요청 ("PNU 또는 정확한 주소 알려주세요")

## STEP 2 — `land_analyst` 호출 (필수)

```
land_analyst(pnu_or_address="<위에서 파싱한 값>")
```

**규칙**:
- 무조건 도구 호출 (LLM 추측 금지, SOUL Honesty Rule #2)
- 응답까지 ~5초 대기 (cold start면 ~10초)
- 실패 시 사용자에게 "분석 실패: <에러>" 그대로 전달

## STEP 3 — 결과 파싱 + 핵심 추출

도구 응답 JSON에서:
- `pnu.pnu`: PNU 19자리
- `pnu.address` (있으면): 정제된 주소
- `regulations.bcr_pct`: 건폐율 %
- `regulations.far_pct`: 용적률 %
- `regulations.height_limit_m`: 높이 m (없으면 N/A)
- `regulations.sunlight_applies`: 정북일조 적용 여부
- `regulations.zone_category` 또는 zones[].name: 용도지역
- `regulations.corner_cutoff_required`: 가각전제
- `setback_lines`: 규제선 GeoJSON (수가 많으면 "8종 규제선 생성됨"으로 요약)
- `law_articles`: 법조항 (수만 표기, 자세한 건 사용자 요청 시)

## STEP 4 — 응답 포맷

**고정 형식** (SOUL "응답 패턴" 참조):

```
📍 <주소 or PNU>
- 용도지역: <name>
- 건폐율: <bcr_pct>% (<bcr_article>)
- 용적률: <far_pct>% (<far_article>)
- 높이제한: <height or "N/A">
- 정북일조: <적용 / 비적용>
- 가각전제: <필요 / 불필요>
- 규제선: <개수>종 / 법조항: <수>개

<자연스러운 1줄 마무리>
```

**규칙**:
- 줄글 X, 위 lists 형식 고정
- 절대 추가 정보 만들지 말 것 (도구 결과 외)
- 법조항 인용 (article 필드) 그대로 노출

## STEP 5 — 다음 행동 제안

응답 끝에 1~2 옵션:

```
더 알고 싶은 게 있으세요?
- 특정 규제 자세히
- 관련 법조항 원문 보기 (미구현)
- 매스 최적화 (미구현)
```

**현재 land_analyst 1개 도구만 있음**. 다른 거 약속 X.

## STEP 6 — 컨텍스트 저장 (자동, Hermes 메모리)

Hermes가 자동으로:
- 사용자 → 분석한 PNU 매핑 (장기)
- 분석 결과 (중기, 5분~1시간)

이후 사용자가 "그 땅에 ..." 라고 하면 자동 참조.

## 에러 케이스

### A. 도구 응답에 `error` 키
```
land_analyst 응답: {"error": "AG-light 타임아웃"}

답변:
❌ 분석 실패: AG-light Worker 타임아웃 (15초)
다시 시도해주세요. 계속 실패하면 PNU 직접 입력 권장.
```

### B. PNU/주소 둘 다 모호
```
사용자: "분석해줘"

답변:
어떤 땅을 분석할까요?
- PNU 19자리 (예: 1168010100106770003)
- 또는 주소 (예: 강남구 역삼동 677)
```

### C. land_info.success=false (Vworld 실패)
```
답변:
규제 데이터 일부 조회 실패 (Vworld API 일시 오류).
PNU 자체는 유효: <PNU>
잠시 후 다시 시도해주세요.
```

### D. 도구 응답이 JSON 파싱 실패
```
답변:
⚠️ 응답 처리 오류. 시스템 관리자에게 문의 (에러: <원문>)
```

## 금지 행동 (SOUL 재확인)

- ❌ land_analyst 호출 없이 일반 지식으로 답하기
- ❌ 법조항 임의 인용 (도구 결과 외)
- ❌ "약 80%" 같은 모호 표현 (정확한 수치만)
- ❌ "더 자세한 정보를 원하시면 ..." 같은 구두 약속 (미구현 도구 약속 X)

## 박제 / 출처

- SOUL: `gateway/SOUL.md`
- Plugin: `gateway/arr_gateway/`
- 메모리 인덱스: `D:/DevCache/claude-data/projects/D--Data-25-ACE/memory/agent-architecture/`

수정 후: `sudo systemctl restart hermes-arr`
