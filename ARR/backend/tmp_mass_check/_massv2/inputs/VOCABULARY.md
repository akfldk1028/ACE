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
- `gable` {pitch 0.15-1.2, along} — 용마루에서 만나는 두 경사면. **pitch는 기하 경사(run당 rise, 1.0 = 45°)** — 볼륨 높이의 몫이 아니다. 낙차는 몸통 높이 안에서 캡되므로, 가파른 박공을 원하면 몸통부터 집 비례여야 한다(폭 30m 슬래브에 45°는 물리적으로 불가 — `unit:"house"`나 compress로 좁힌 바 위에 쓸 것). along 기본 "long" = 볼륨 자신의 실제 긴 축.
- `grade` {..., smooth: true} — 연속 경사 (계단이면 smooth 없이).

## 기존 변형·절단 (요약)
split, carve, lift{clearance}, notch, puncture, branch{n,reach,height}, embed{size,depth,at},
shift{toward,ratio}, offset, rotate{degrees}, skew, taper, twist, shear, bend, pinch,
compress/expand/inflate{ratio,toward}, fracture, intersect{size,level,climb,degrees}.

## 좋은 문장의 기준 (박제된 교훈)
- 형태 라벨이 아니라 **논지**: "왜 이 관계인가"가 formal_principle에 서야 한다.
- 방위·좌표계 다양성 (15/16이 단일 방위였던 레고 문제).
- 사무소 저작 정체성: 그 사무소가 그 건물에서 실제로 한 '수'를 동사로.
