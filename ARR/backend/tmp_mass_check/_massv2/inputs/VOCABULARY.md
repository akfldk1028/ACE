# massv2 저작 어휘 명세 (2026-08-19, 관계동사 확장판)

문장(parti)은 `{"schemes": [...]}` JSON. 각 scheme:

```json
{
  "name": "office_building_short_slug",
  "primary_language": "solid_body | carved_body | open_figure | porous_field",
  "secondary_language": "one line, what the building is as a body",
  "formal_principle": "한 문장 - 이 매스가 왜 이 형태인가 (시트에 인쇄됨)",
  "dominant_gesture": "한 구절",
  "reference_basis": "실존 건물이면 사실 근거(건축가·위치·연도). 창작이면 '저작 신작'이라 쓰고 거짓 근거 금지",
  "ops": [ {"op": "...", ..., "why": "이 단어가 왜 있는가"} ]
}
```

## 규칙
- **첫 단어는 extrude | loop | aggregate | stack 만** (볼륨을 세우는 말).
- 모든 파라미터는 비율. 좌표·미터 하드코딩 없음.
- `on:` 은 볼륨 role의 접두 매칭 (`aggregate`가 만드는 것들은 `object_0..n-1`).
- 말하지 않은 단어는 침묵 게이트가 잡는다 — 모든 단어는 매스를 실측 가능하게 바꿔야 한다.
- 대지 꽉 찬 몸(bare extrude) 위에 면 밖으로 나가는 관계동사를 쓰면 법규선이 먹는다 — 관계는 여유 있는 몸에서 말할 것.

## 볼륨을 세우는 말 (openers)
- `extrude` — 대지형 프리즘.
- `loop` {bar 0.15-0.4, height} — 마당을 도는 네 바.
- `stack` — 줄어드는 밴드 타워.
- `aggregate` {n 2-12, spread≥1, height, tie 0-0.4, turn(도), method, storeys}
  - `method: "pack"`(기본, 그리드 정착) | `"stack"`(**적층** — 단위들이 서로 위에 엇놓임, 층마다 turn 부호 교대)
  - method stack일 때 `storeys`(1-5, 기본 2) = 단위 한 채의 층수. 총높이의 적법은 법규 클립이 심판.
  - `reach`(0-0.6, 기본 0) = **바 끝이 자기 축으로 교대로 미끄러져 더미 밖으로 낢** (VitraHaus의 나는 끝). 지상층은 고정. 서는지는 캔틸레버 게이트(backspan 1.6)가 심판 — 실측: 0.28은 델리버리까지 통과, 0.35는 성장 후 1.61로 기각.
  - `unit: "slab"`(기본) | `"house"`(**기본 볼륨** BOOK 030 — 단면이 집: 깊이가 자기 높이에서 유도되고 45° 박공이 태생부터 붙는다. gable 단어 불필요. VitraHaus = `method:stack unit:house` 한 단어)

## 관계동사 (신규 — 한 몸이 다른 몸에게 하는 일, 호스트 단위공간)
- `lodge` {size 0.15-0.6, over 0.05-0.6, height 0.2-1.0, at 0-1} — 바가 호스트 지붕 위에 **걸쳐** 양쪽으로 내민다.
- `overlap` {bite 0.15-0.6, slip 0-0.5, height} — 쌍둥이가 밀려 평면을 **겹친다**.
- `interlock` {bite 0.3-0.75, size, reach} — 반대 면에서 온 두 팔이 다른 높이에서 **맞물린다**.
- `nest` {size 0.15-0.6, proud 0.1-1.0} — 안에 **포갠** 몸이 지붕 위로 솟는다.
- `merge` {height} — 서 있는 몸들이 **하나로 병합** (선언된 유일한 union).
- `extract` {size, gap, height, level} — 조각을 **빼내** 소켓 옆에 세운다 (보이드+조각 한 쌍).
- `inscribe` {size 0.15-0.6, depth 0.1-0.5} — 지붕에 모서리 안 닿는 도형을 **새긴다** (침강 마당).

## 지붕 (낙차는 선언한 만큼 정확히 그려짐 — 한 층 캡 아님)
- `gable` {pitch 0.15-1.2, along, bays 1-6, at 0.15-0.85} — 용마루에서 만나는 두 경사면. **pitch는 기하 경사(run당 rise, 1.0 = 45°)** — 볼륨 높이의 몫이 아니다. 낙차는 몸통 높이 안에서 캡되므로, 가파른 박공을 원하면 몸통부터 집 비례여야 한다(폭 30m 슬래브에 45°는 물리적으로 불가 — `unit:"house"`나 compress로 좁힌 바 위에 쓸 것). along 기본 "long" = 볼륨 자신의 실제 긴 축. `bays: n` = 다련 박공(M지붕·톱니 — 몸통을 능선 직각으로 n등분, 각 스트립이 자기 능선). `at` = 용마루 위치(0.5 대칭 기본, 그 외 saltbox — 같은 경사, 긴 쪽이 낮게 닿음).
- `butterfly` {pitch 0.15-1.2, at 0.2-0.8, along} — 두 면이 안쪽 골짜기로 떨어지는 V지붕 (Breuer Geller). 골짜기 깊이 = 짧은 run 쪽이 선언 경사를 가짐.
- `mansard` {pitch 0.15-1.2, shoulder 0.1-0.4, along} — 가파른 어깨 + 평평한 정수리 (오스만 단면). **낙차는 1.5층 캡** — 어깨 run은 선언 경사로 역산. ⚠️ 넓은 저층 몸통에서는 정수리가 좁아져 텐트에 가깝고 단어도 조용함(0.05 문턱 근처) — 좁고 선 가로벽(고밀 필지)이 제 자리.
- `vault` {rise 0.15-1.2, bays 1-6, along} — 배럴 볼트(곡면 지붕). 프로파일을 16점으로 샘플링한 호. **낙차는 박공·맨사드와 같은 1.5층 캡.** 렌더는 점 6개 초과 프로파일의 이음선을 그리지 않는다(샘플링 아티팩트이지 접힘이 아니므로).
- (IR) 단면 프리미티브 `top_profile` — 윗면 = 한 축 위의 꺾은선 높이 프로파일. shed·박공·saltbox·맨사드·버터플라이가 전부 특수 경우. **볼트는 표현 안이었다**(꺾은선에 점을 충분히 주면 곡선) — 진짜 2축이 필요한 것은 힙뿐.
- `grade` {..., smooth: true} — 연속 경사 (계단이면 smooth 없이).
- `fold` {folds 1-3, pitch 0.15-1.2, along} — 한 축을 따라 여러 번 오르내리는 **접힌 판**(톱니·콘체르티나·folded plate). 볼트와 같은 `top_profile` 프리미티브이고 점만 더 쓴다. **접힘 n개 = 점 2n+1개**이고 렌더는 점이 `MAX_CREASED_PROFILE_POINTS`(8)를 넘으면 이음선을 안 그리므로 folds는 3에서 잘린다 — 넷째 접힘은 볼트로 보인다. **선언 pitch는 한 면(facet)의 경사**라 접힘이 늘면 면당 run이 줄어 낙차가 얕아진다(진짜 접힌 판이 그렇다). 낙차는 박공과 같은 1.5층 캡.
- `cantilever` {reach 0.15-0.40, levels 2-4, toward, on} — 위 켜가 아래 켜를 넘어 **나간다**. 단면 IR에는 평면 내밈을 말할 항이 없어 `shear`처럼 밴드를 미는 동사다. **천장 0.40은 구조 게이트에서 역산** (`structure`가 backspan의 1.6배에서 거부 → 스텝 r/(1+r)의 2/3). 기본 0.28은 `aggregate.reach`가 실측으로 남긴 값(0.28 배달 통과, 0.35는 성장 뒤 1.61로 기각). 밑동은 안 움직이고 켜마다 같은 몫씩 나가므로 levels를 늘려도 부재 비율은 일정하다.

### ⚠️ 단면 저작 규칙 (2026-08-26 실측)
1. **좁히지 말고 잘라라.** `compress`는 최소 0.6이라 55m 씨앗을 35m까지밖에 못 줄이는데 지붕 낙차는 1.5층(4.5m)에서 잘린다 → 35m 폭 위의 볼트는 1:8, 둥근 상자로 보인다. `split`으로 진짜 바를 만들어라. 또는 `bays`/`folds`로 **면당 run**을 줄여라 — 잘 읽힌 킴벨(bays 4)과 톱니(folds 3)가 그 경우다.
2. **`cantilever`는 두 켜가 있어야 말한다.** 한 층짜리 몸에는 할 말이 없어 조용히 통과한다(그건 `lift`가 할 말이다). `split`의 `contrast`가 작은 조각의 높이를 나누므로 자른 뒤에도 켜가 둘 남게 `storeys`를 선언하라.
3. **대지를 꽉 채운 몸 위에서 내밀지 마라.** 일조 봉투가 내밈을 먼저 가져가 그림에 안 남는다. `split`이나 `carve` 뒤 여유가 생긴 자리에 말하라.
4. **이미 밴드로 나뉜 볼륨에 또 단면을 얹지 마라.** `grade`(계단) 뒤에 `fold`를 더했더니 밴드마다 지붕이 생겨 23개 변형 전부가 캔틸레버 초과로 기각됐다. 계단 자체가 그 문장의 단면이다.
5. **논지가 아닌 틈은 선언하지 마라.** 바를 만들려고 `split`에 `gap`을 붙이면 그 틈이 배달되지 않을 때 문장 전체가 거부된다 — 말하지 않은 틈은 닫혀도 거짓이 아니다.

## 기존 변형·절단 (요약)
split, carve, lift{clearance}, notch, puncture, branch{n,reach,height}, embed{size,depth,at},
shift{toward,ratio}, offset, rotate{degrees}, skew, taper, twist, shear, bend, pinch,
compress/expand/inflate{ratio,toward}, fracture, intersect{size,level,climb,degrees}.

## 좋은 문장의 기준 (박제된 교훈)
- 형태 라벨이 아니라 **논지**: "왜 이 관계인가"가 formal_principle에 서야 한다.
- 방위·좌표계 다양성 (15/16이 단일 방위였던 레고 문제).
- 사무소 저작 정체성: 그 사무소가 그 건물에서 실제로 한 '수'를 동사로.
