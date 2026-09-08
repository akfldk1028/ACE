# massv2 저작 문법 — 한 문장 = 동사 3~5개

한 문장(scheme)은 대지 위에서 순서대로 실행된다. **치수를 쓰지 마라.** 모든 수는
비율이고, 미터는 실행기가 필지에서 가져온다. `on`은 앞 동사가 만든 볼륨 이름의 접두사.

## 동사 14개와 파라미터

| 동사 | 파라미터 | 뜻 |
|---|---|---|
| `extrude` | `height` 0.1~1.0 · `profile` | 대지 씨앗 사각형을 세운다. 보통 첫 동사 |
| `split` | `ratio` 0.3~0.75 · `along` long\|cross · `first` `second` (이름) · `contrast` · `gap` | 겨냥한 것을 이름 붙은 두 부분으로 자른다. **뒤 동사가 부분을 겨냥할 수 있게 하는 핵심 동사** |
| `stack` | `n` 2~6 · `contrast` 1.2~2.0 (단끼리 크기 차) · `align` open\|back\|cross · `height` · `grow` true | 단을 쌓는다. `grow:true`면 위가 커진다(대공간을 최상층에) |
| `aggregate` | `n` 2~6 · `spread` 1.2~2.0 · `height` 0.1~1.0 · `tie` 0.08~0.4 | 흩어진 오브젝트 n개 + 묶는 판. `spread`는 **오브젝트끼리 크기가 얼마나 벌어지는가**(1.0이면 전부 같은 크기 = 금지). `tie`는 묶는 판의 두께 비율. SANAA 필드형 |
| `loop` | `bar` 0.2~0.45 · `height` | 중정을 감싸는 고리(ㅁ자). 진짜 perimeter block일 때만 |
| `shear` | `ratio` 0.15~0.35 · `toward` long\|cross\|back · `on` | 겨냥한 볼륨을 자기 치수의 비율만큼 민다 |
| `taper` | `ratio` 0.3~0.95 · `on` | 겨냥한 것이 **올라가며 좁아진다**. 세분화로 구현됨. 상자 하나엔 안 쓴다 |
| `lift` | `clearance` 0.1~0.4 · `on` | 들어올리고 밑을 비운다. 필로티. 밑 높이는 1~2개층으로 제한됨 |
| `carve` | `size` 0.15~0.6 · `at` long\|cross\|back · `reach` 0~1 · `on` | 중정/슬롯을 판다 |
| `notch` | `size` 0.15~0.5 · `at` | **모서리**를 베어 문다. carve는 변에서 파고, notch는 코너다 |
| `puncture` | `size` 0.1~0.45 · `n` 1~3 | 안쪽에 **관통** 구멍. 하늘로 열린 중정이 아니라 통로·광정 |
| `rotate` | `degrees` -45~45 · `on` | 평면에서 돌린다. 스택에 걸면 단마다 더 돌아간다 (Kaktus·Grove) |
| `skew` | `degrees` -30~30 · `toward` long\|cross · `on` | 수직에서 **기울인다**. shear는 미는 것, skew는 넘어뜨리는 것 |
| `twist` | `degrees` 5~90 · `on` | 올라가며 단면이 **점진적으로 회전**. 세분화로 구현 (Vancouver House) |

## 기반 도형 `profile` (첫 동사에 한 번, 문장 전체에 적용)

`square` `oval` `stadium` `hexagon` `chamfered` `faceted` `trapezoidal` `triangular` `kite` `concave_l`

**정사각형이 기본이지만 기본이 정답인 경우는 드물다.** 원형 미술관은 `oval`,
각진 콘크리트 덩어리는 `faceted`, 대지 따라 꺾인 바는 `trapezoidal`.

## JSON 형식 (그대로 지켜라)

```json
{
  "name": "office_scheme_name",
  "primary_language": "solid_body | carved_body | open_figure | porous_field",
  "secondary_language": "한 줄, 이 매스가 무엇인지",
  "formal_principle": "한 문장, 무엇이 이 안을 결정하는가",
  "dominant_gesture": "한 문장, 눈에 먼저 들어오는 것",
  "reference_basis": "실제 건물명 + 도시 + 연도 + 실측 사실(치수·면적·층수)",
  "ops": [
    {"op": "extrude", "height": 0.9, "profile": "oval", "why": "한국어로 이 수의 이유"},
    {"op": "split", "ratio": 0.62, "along": "long", "first": "hall", "second": "office",
     "why": "..."}
  ]
}
```

## 검증기가 문장을 거부하는 조건 (미리 피해라)

1. **침묵한 동사**: 어떤 동사가 매스의 5% 미만을 바꾸면 문장 전체가 버려진다.
   → 작은 조각에 `on`을 겨냥하지 마라. `on`은 `split`이 만든 **큰 부분**을 가리켜야 한다.
2. **층이 방을 담아야 함**: 판 폭이 4.8m 미만이면 층이 아니다.
3. **서 있어야 함**: 캔틸레버 1/3 초과, 스팬/깊이 15 초과 금지.
4. **채광**: 한 판의 25% 넘게 창에서 6m 이상 떨어지면 안 된다 → 아주 두꺼운 판 금지.
