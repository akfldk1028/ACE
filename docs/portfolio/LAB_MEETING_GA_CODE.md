# 매스 자동 생성 — GA 작동 원리, 수식과 코드까지

**Lab Meeting · 7장 발표**
**Date**: 2026-05-06
**원칙**: 헤드라인은 일상 비유, 부제는 학술 용어, 본문은 *비유 + 수식 + 실제 코드 한 줄*. 수학을 학교 비유로 환산하고, 같은 내용이 *Python 코드*에서 어떻게 구현되었는지 함께 보임.
**코드 출처**: `ARR/backend/design/engine/objects.py :: SSIEAJob`

---

## 1장 · 좋은 매스가 뭔지부터 정의가 안 됩니다 — 다목적 최적화

### 본문
매스 디자인의 첫 번째 어려움은 *좋다*의 정의 자체다. 면적이 클수록 좋고, 일조가 많을수록 좋고, 이격이 충분할수록 좋은데, 셋이 *서로 충돌*한다.

수학적으로는 **목적 함수가 둘 이상**이고 그 사이에 trade-off가 있다는 뜻이다.

```
maximize:  f₁(x) = floor_area(x)
maximize:  f₂(x) = daylight_score(x)
subject to: g(x) ≤ 0  (BCR, FAR, 사선 등 법규)
```

x는 매스 한 개를 정의하는 *유전자 벡터*. 단일 점수가 없으니 *Pareto 곡선*을 찾아야 한다.

### 슬라이드 시각
- 헤드라인: **좋은 매스가 뭔지부터 정의가 안 됩니다**
- 부제: *다목적 최적화 (Multi-Objective Optimization)*
- 시각: 시소 (면적 ↔ 일조)
- 수식 박스: f₁(x), f₂(x) 동시 최대화

---

## 2장 · 매스를 숫자로 바꾸기 — 유전자 인코딩

### 본문
박스 5개를 쌓는 매스라면 박스마다 (x, y, w, d, rot) 5개 숫자, 5박스 × 5 = 25개. 거기에 전체 매스의 (num_floors, rotation, upper_scale, step_fraction) 4개를 더해 **총 29개**.

수학적으로 매스 한 개는 *연속 실수 벡터*:
```
x = [x₁, x₂, ..., x₂₉] ∈ ℝ²⁹
```

### 코드
```python
# constraint_bridge.py :: _build_additive_inputs()
def _build_additive_inputs(max_dim, min_dim, max_floors):
    """29 genes: 5 boxes × 5 + 4 global"""
    inputs = []
    for i in range(5):
        inputs.extend([
            {"name": f"b{i}_x", "type": "Continuous", "Min": ..., "Max": ...},
            {"name": f"b{i}_y", ...},
            {"name": f"b{i}_w", ...},
            {"name": f"b{i}_d", ...},
            {"name": f"b{i}_rot", ...},
        ])
    inputs.extend(_global_inputs(max_floors))  # +4
    return inputs  # len = 29
```

### 슬라이드 시각
- 헤드라인: **매스를 숫자로 바꾸기**
- 부제: *유전자 인코딩 (Gene Encoding)*
- 시각: 박스 5개 매스 → `[0.5, 2.1, 0.8, ..., 0.9]` 29개
- 강조: **x ∈ ℝ²⁹**

---

## 3장 · 부모 둘에서 자식 매스 만들기 — 교배 (Crossover, BLX-α)

### 본문
부모 A, B의 각 유전자에 대해 **단순 50/50 선택이 아니라 *블렌드 교배 (BLX-α)***를 쓴다. 두 유전자 사이의 거리 d만큼 *양 끝을 1/3만큼 확장한 범위*에서 무작위로 자식 값을 뽑는다.

수학:
```
d  = |x₁ - x₂|
y₁ = min(x₁, x₂) - d/3
y₂ = max(x₁, x₂) + d/3
child = Uniform(y₁, y₂)
```

비유: 부모 둘이 *멀리 떨어진* 특성을 가지면 자식도 *조금 더 과감하게* 그 사이뿐 아니라 바깥까지 시도할 수 있다. 단순 평균이 아니라 *탐색 공간을 살짝 넓히는* 장치다.

### 코드
```python
# objects.py :: Design.crossover() (line 64-)
for j in range(len(inputs_1)):
    x1, x2 = inputs_1[j], inputs_2[j]
    d  = abs(x1 - x2)
    y1 = min(x1, x2) - d / 3
    y2 = max(x1, x2) + d / 3
    new_val = y1 + (y2 - y1) * random.random()
    clipped = max(Min, min(new_val, Max))
```

### 슬라이드 시각
- 헤드라인: **부모 둘에서 자식 매스 만들기**
- 부제: *교배 (Crossover, BLX-α)*
- 시각: 부모 A + 부모 B → 자식 매스 (사이 + 바깥 1/3 영역)
- 수식 박스: `child = Uniform(min − d/3, max + d/3)`

---

## 4장 · 자식 유전자 살짝 흔들기 — 돌연변이 (Mutation, Gaussian)

### 본문
자식의 각 유전자를 일정 확률(*mutation rate*)로 흔든다. 흔들 때는 무작위가 아니라 **정규분포 N(0, σ²)** 를 따른다. σ는 그 유전자의 *전체 범위의 1/5*.

수학:
```
변형값 = 원래값 + N(0, σ²),  σ = (Max − Min) / 5
변이율: m(t) = 0.35 − (0.35 − 0.10) · t / 50  (선형 감소)
```

비유: 변이율이 0.35라는 건 *유전자 100개 중 평균 35개가 흔들린다*는 뜻이고, 0.10이면 *10개*. 50세대 동안 *처음엔 35개씩 → 끝엔 10개씩* 점진적으로 줄어든다. 흔들 때는 ±20%(σ) 정도 정규분포로 흔들리니, 99% 확률로 *±60% 이내* 변형.

### 코드
```python
# objects.py :: Design.mutate() (line 112-128)
goal_range = float(abs(Max - Min))
for _input in input_set:
    if random.random() < mutation_rate:
        new_input = _input + random.gauss(0, goal_range / 5.0)
        new_input = max(Min, min(new_input, Max))

# objects.py :: SSIEAJob._evolve_step() (line 474-477)
mutation_rate = self.initial_mutation - (
    (self.initial_mutation - self.final_mutation)
    * self.gen / max(1, self.max_gen)
)
```

### 슬라이드 시각
- 헤드라인: **자식 유전자 살짝 흔들기**
- 부제: *돌연변이 (Mutation), 변이율 0.35 → 0.10*
- 시각: 자식 벡터 일부 색 변경 + 정규분포 종 모양 곡선 (σ = range/5)
- 수식 박스: `mutation_rate = 0.35 - 0.25·(t/50)`

---

## 5장 · 좋은 부모가 자주 뽑히기 — 선택 (Tournament, k=8)

### 본문
*어떻게 부모를 뽑느냐*가 진화 속도를 결정한다. 본 시스템은 **토너먼트 선택**을 쓴다. 한 섬에서 무작위로 8명을 뽑아 *그 중 점수 최고를 부모*로 채택. 두 번 반복해 부모 A, B를 결정한다.

수학:
```
candidates = random.sample(island, k=8)
parent     = argmin_{x ∈ candidates} fitness_key(x)
```

여기서 `fitness_key`는 (penalty, score). 즉 **법규 위반 적은 매스를 우선 선정**, 같으면 점수가 좋은 매스를 선정.

비유: 운동회 *1조 8명 줄 세워 1등 뽑기*. 8명 중 1등이니 상위 12.5%. 너무 작으면 약한 매스도 부모, 너무 크면 강한 매스만 부모 → *다양성 loss*. **8은 균형점**.

### 코드
```python
# objects.py :: SSIEAJob._tournament_select() (line 544-551)
def _tournament_select(self, island, k=2):
    selected = []
    for _ in range(k):
        candidates = random.sample(island, min(self.tournament_size, len(island)))
        best = min(candidates, key=self._fitness_key)  # tournament_size = 8
        selected.append(best)
    return selected

# fitness_key: (penalty 우선, 그 다음 objective score)
def _fitness_key(self, d):
    return (d.penalty, score)
```

### 슬라이드 시각
- 헤드라인: **좋은 부모가 자주 뽑히기**
- 부제: *선택 (Tournament Selection), k = 8*
- 시각: 8명 중 1등에 별표 → 부모로 이동
- 강조: **상위 12.5% 매스가 부모**

---

## 6장 · 5개 섬에서 동시에 진화 — Island 모델 + Steady-State

### 본문
지금까지가 GA 본체. 본 시스템의 *확장 메커니즘 두 가지*를 더한다.

**(a) Island 모델**: 75명을 한 그룹에서 진화시키면 *조기 수렴*이 발생해 다 비슷해진다. 그래서 5개 섬에 15명씩 분산.

**(b) Steady-State 교체**: 일반 GA는 한 세대마다 *전부 갈아치움*. 본 시스템은 한 step에 *섬당 자식 1명만* 만들고 *그 섬의 worst 1명과 교체*. 좋은 매스는 명시적으로 교체되기 전까지 *영원히 살아남음*.

**(c) Ring Migration**: 10세대마다 각 섬의 best 2명을 옆 섬 worst 자리로 이주.

수학:
```
총 평가 매스:  75 (초기) + 50 × 5 (세대당 5섬 자식) = 325개
이주 횟수:     50 / 10 = 5회 × 5섬 × 2명 = 매번 10명 자리 교체
```

### 코드
```python
# objects.py :: SSIEAJob.__init__ (line 410-417)
self.num_islands       = 5
self.pop_per_island    = 15
self.max_gen           = 50
self.migration_interval = 10
self.migrants_count    = 2
self.tournament_size   = 8
self.initial_mutation  = 0.35
self.final_mutation    = 0.10

# Steady-state 교체 (line 498-501)
worst_idx = self._find_worst(island)
if self._should_replace(child, island[worst_idx]):
    island[worst_idx] = child

# Ring migration (line 553-576)
dst = self.islands[(i + 1) % n]   # ring 구조
worst_list = sorted_dst[-self.migrants_count:]
```

### 슬라이드 시각
- 헤드라인: **5개 섬에서 동시에 진화**
- 부제: *Island 모델 + Steady-State + Ring Migration*
- 시각: 5섬 + 화살표 (best→worst), 한 명씩 교체 표현
- 강조: **75 + 250 = 325개 매스 평가, 5회 이주**

---

## 7장 · 컴퓨터는 메뉴판을 차리고, 건축가가 고릅니다 — Pareto Front

### 본문
50세대 후 알고리즘이 출력하는 건 *모든 평가 매스 325개 중 Pareto-optimal subset*.

수학:
```
PF = {x* : ¬∃ x ∈ X s.t.  fᵢ(x) ≥ fᵢ(x*) ∀i  ∧  ∃j fⱼ(x) > fⱼ(x*)}
```

말로 풀면: *"어떤 매스도 모든 기준에서 더 우월하지 않은 매스들의 집합."* 곡선의 한쪽 끝 = 면적 극대(수익형), 반대쪽 = 일조 극대(환경형), 중간 = 균형형.

**알고리즘은 결정 X, 곡선만 그림.** 사용자(건축가, 시행사)가 사업 목표에 따라 곡선 위에서 직접 매스 선택.

### 코드
```python
# objects.py :: SSIEAJob.get_pareto_front() (line 578-)
feasible = [d for d in self.all_designs if d.objectives and d.penalty == 0]
ranking, _, _ = rank(feasible, self.spec["outputs"])
best_rank = max(ranking)
pareto_front = [d for d, r in zip(feasible, ranking) if r == best_rank]
```

### 슬라이드 시각
- 헤드라인: **컴퓨터는 메뉴판을 차리고, 건축가가 고릅니다**
- 부제: *Pareto Front + 사용자 결정*
- 시각: 매스 3종 진열 (수익형/균형형/환경형) + 손가락 클릭
- 강조: **알고리즘은 결정 X, 선택지만 제공**

---

## 핵심 수치·코드 빠른 정리 (질문 답변용)

| 메커니즘 | 수식 | 코드 위치 | 학교 비유 |
|---------|------|----------|---------|
| 인코딩 | `x ∈ ℝ²⁹` | `_build_additive_inputs()` | DNA 29글자 |
| 교배 (BLX-α) | `child = U(min − d/3, max + d/3)` | `Design.crossover()` line 64 | 부모 둘 사이 + 바깥 1/3 |
| 돌연변이 | `x' = x + N(0, σ²), σ = range/5` | `Design.mutate()` line 122 | 100개 중 35개 → 10개 흔들기 |
| Adaptive | `m(t) = 0.35 − 0.25·t/50` | `_evolve_step()` line 474 | 초반 탐색, 후반 수렴 |
| 선택 | `argmin_{S} fitness, S = sample(island, 8)` | `_tournament_select()` line 544 | 1조 8명 중 1등 |
| Steady-State | `replace worst if child better` | `_should_replace()` line 535 | 꼴찌만 새 학생으로 |
| Ring Migration | `dst = islands[(i+1) % 5]` | `_migrate()` line 553 | 10세대마다 우등생 옆 반 이주 |
| Pareto | `PF = {x : ¬∃ y dominates x}` | `get_pareto_front()` line 578 | 비기는 매스들의 집합 |

---

## 발표 마무리 한 줄

> *"매스를 29차원 벡터로 인코딩하고, BLX-α 교배 + Gaussian 돌연변이 + Tournament 선택의 GA 본체에 5섬 + Steady-State + Ring Migration + Adaptive Mutation 4가지 확장을 더해 50세대 진화시킨 뒤, Pareto-optimal subset을 사용자에게 제시합니다. 결정은 사용자가 합니다."*

---

## 톤 가이드 (NotebookLM에 전달)

- **배경**: 흰색
- **언어**: 한국어
- **시각**: 일상 비유 일러스트 + 수식 박스 + 실제 코드 박스 (Python syntax highlighting)
- **헤드라인**: 큰 한국어 비유
- **부제**: 영문 학술 용어
- **본문**: *비유 1줄 + 수식 1줄 + 코드 박스 (3-5줄)* 의 3단 구성
- **금지**: 화려한 효과
- **목표**: 교수님이 슬라이드 보고 (1) 비유로 직관 (2) 수식으로 정확성 (3) 코드로 구현 검증 — 세 층위 모두 확보
