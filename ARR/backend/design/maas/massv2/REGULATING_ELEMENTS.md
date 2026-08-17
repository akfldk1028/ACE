# 규제 요소 — 설계

## 왜

블라인드 비평 60쌍(2라운드, 서브에이전트 6)이 두 번 다 같은 두 가지를 1·2위로 지목했다:
`sentence-invisible`, `pieces-look-random`. 두 번째가 이 문서의 대상이다.

개별 매스는 적법하고, 서 있고, 채광되고, 문장의 단어도 실제로 매스를 바꾼다.
그런데 **같이 놓으면 남남**이다. 조각들이 공유하는 것이 없다.

Akin & Moustapha, *Design Studies* 25(1), 2004 — 건축가 6명의 2시간 매싱 과제 관찰.
모든 매싱 활동을 구조화한 주된 기제가 **규제 요소**였다: 대칭축, 회전 중심, 정렬축,
대각 비례선, 교점, 경계선.

> *"모든 참여자가 이 기제로 기하학적 질서를 유지했다. 매싱 요소를 자유롭게 더하고 빼면서도,
> 규제 요소를 통해 밑에 깔린 구조를 보존하고 오히려 강조할 수 있었다."*

**읽는 방향이 중요하다.** 이건 "축을 그려라"가 아니라 **"연산이 축을 만들고, 다음 연산이
그 축을 다시 쓴다"**는 관찰이다. 자유롭게 조작하면서도 구조가 남는 이유가 그것이다.

## 지금 있는 것 — 반쪽

4x4 흐름에 pivot은 살아 있다. `ops/affine.py`의 docstring이 이미 선언한다:
*"which volumes, which operator, about what pivot"*.

```python
def _verb(operator, build):
    def run(frame, op):
        picked = [...]                                   # 어느 볼륨에
        cx, cy, base, span_x, span_y, span_z = _bounds(picked)
        frame.placements = rest + _operate(picked, operator, params, (cx, cy, base))
    return run                                           #                    ↑ pivot
```

**pivot은 선언되지 않고 유도된다.** 매번 "이번에 고른 것들의 바운딩박스 중심"을 계산하고
연산이 끝나면 버린다. 문장이 *"아까 split이 낸 그 선을 기준으로 돌려라"* 라고 말할 방법이 없다.

축도 같다. `_Frame.rotation` 하나가 대지 방위를 들고 있고 `_direction()`이 그 안에서
세 방향(`long`/`cross`/`back`)만 반환한다. `siting.principal_axes()`는 존재하지만
`place_on_site` 안에서만 쓰이고 프레임에 남지 않는다.

정리: **기계는 있고 어휘가 없다.** 이 패키지에서 세 번째로 나오는 같은 진단이다
(`taper`가 도형을 대신하던 것, 파서가 책 동사를 버리던 것에 이어).

## 설계

### 1. 프레임이 이름 붙은 규제 요소를 든다

```python
@dataclass(frozen=True)
class Line:      # 정렬축 · 대칭축
    origin: tuple[float, float]
    direction: tuple[float, float]
    born: str            # 이 선을 만든 연산 ("site" | verb 이름)

@dataclass(frozen=True)
class Centre:    # 회전 중심 · 교점
    point: tuple[float, float]
    born: str

class _Frame:
    lines: dict[str, Line]
    centres: dict[str, Centre]
```

대지가 주는 것으로 초기화한다 — 발명하지 않는다:

```
lines["street"]  열린 변 방향, 버딩어블 중심을 지나는 선   (open_side_direction)
lines["spine"]   시드 사각형의 긴 축                        (seed_rectangle)
lines["cross"]   그 직교축
centres["site"]  버딩어블 중심
```

### 2. 연산이 규제 요소를 **만든다**

이게 논문이 관찰한 것이다. 볼륨을 만들거나 자르는 동사는 자기가 낸 기하를 등록한다.

```
split       자른 선을            lines[f"{first}|{second}"]
loop        고리의 중심을         centres[role]
aggregate   밭의 경계를           lines[...] × 2 (장·단축)
carve       비운 것의 중심을      centres[role]
stack       쌓은 축을             centres[role]
```

등록 비용은 사실상 0이다 — 이미 계산해서 쓰고 버리는 값들이다.

### 3. 연산이 규제 요소를 **다시 쓴다**

`on:`이 볼륨을 이름으로 가리키는 것과 **정확히 같은 방식**으로, `about:`과 `along:`이
규제 요소를 이름으로 가리킨다.

```json
{"op": "split",  "along": "spine", "first": "west", "second": "east", "gap": 6}
{"op": "rotate", "on": "east", "about": "west|east", "degrees": 12}
{"op": "shift",  "on": "east", "along": "street", "ratio": 0.3}
```

구현은 두 군데뿐이다:

- `ops/affine.py::_verb` — `op.params["about"]`가 규제 요소를 이름으로 가리키면 그것을
  pivot으로 쓰고, 없으면 지금처럼 `_bounds(picked)` 중심. **하위 호환.**
- `execute.py::_direction` — `toward`가 `lines`의 이름이면 그 선의 방향을 반환하고,
  아니면 지금처럼 세 방향. **하위 호환.**

두 함수 다 fallback이 현재 동작이므로 기존 48개 문장은 한 글자도 안 바뀐다.

### 4. 잴 수 있다 — `regulating_economy`

문헌이 검사 형태까지 진술해뒀다:

> *작은 규제 요소 집합이 모든 부분 매스의 배치를 설명할 수 있는가?
> 적은 요소로 많은 부분 = 구성됨. 많거나 없음 = 두서없음.*

```
설명됨(volume, element) :=
    볼륨의 중심이 선 위에 있다        (거리 < 조인트 클리어런스 0.76m)
  | 볼륨의 한 변이 선과 평행하고 겹친다
  | 볼륨이 그 선에 대해 대칭이다
  | 볼륨의 중심이 그 중심점이다

regulating_economy := 설명된 볼륨 수 / 사용된 규제 요소 수
```

그래픽스 쪽이 독립적으로 같은 목적함수에 도달했다는 것도 근거다 —
대칭 최대화 위계 분해(Zhang, SIGGRAPH Asia 2013), 게슈탈트 그룹핑(Nan, 2011).
**둘 다 "가장 적은 분해로 구조를 설명"을 최적화한다. 3D 매싱에 적용한 사례는 없다.**

## ⚠️ 규율 — 재기만 하고, 검증 전엔 목적함수에 넣지 않는다

Stamps 1998이 분절·관절을 반증했고, McCormack & Lomas(참가자 201, 쌍비교 5,300)가
계산 지표와 지각된 미의 무상관을 보고했다. 그리고 우리 자신의 실측이 세 번 같은 말을 했다 —
`far`와 `artic`은 **라운드마다 부호가 뒤집혔다**.

그러므로 `regulating_economy`도 **선행 지표가 아니라 가설**이다. 순서:

```
1. 잰다        모든 후보에 계산해서 summary.json에 기록만 한다
2. 검정한다    VLM 쌍비교 순위와 동점보정 Spearman.
              ⚠️ 프롬프트를 한 글자도 바꾸지 말 것 — 태그 재사용 지시 한 줄로
                 어휘가 51종→17종이 되어 전/후 비교를 망친 전례가 있다
3. 두 라운드에서 부호가 유지되면 그때 목적함수에 넣는다
```

`spoken_force`가 이 절차를 통과했다(+0.67, +0.48). 통과 못 하면 안 넣는다.

## 하지 않을 것

- 대각 비례선·황금분할류는 넣지 않는다. 논문 목록에 있지만 우리 코퍼스가 그걸로 쓰이지 않았고,
  쓰이지 않은 어휘를 넣는 건 `gable`에서 한 실수의 반복이다.
- 규제 요소를 **게이트로 쓰지 않는다.** 적법·물리·건물 게이트와 달리 이건 취향이 아니라
  가설이다. 게이트는 반증된 것에만.
- 렌더러에 축을 그리지 않는다. 그림에 선을 그리는 것과 매스가 그 선을 따르는 것은 다른 일이고,
  전자는 후자 없이도 그럴듯해 보인다.

## 순서

```
A  Line/Centre 자료구조 + 프레임 초기화(대지가 주는 4개)          작음
B  _verb의 about:, _direction의 along: — 둘 다 fallback 유지     작음
C  연산이 등록: split·loop·aggregate·carve·stack                중간
D  regulating_economy 계산 + summary.json 기록만                 중간
E  VLM 2라운드 검정                                              에이전트
F  통과하면 목적함수에, 아니면 기록만 남기고 끝                    분기
```

A~D까지는 기존 문장의 출력이 **바이트 단위로 같아야 한다**(전부 fallback 경로).
그게 이 단계의 회귀 테스트다.
