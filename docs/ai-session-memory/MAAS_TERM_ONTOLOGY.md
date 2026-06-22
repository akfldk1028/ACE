# MAAS Term Ontology

Updated: 2026-06-10

Source of truth:

- `ARR/backend/design/maas/grammar/data/maas_terms.v0.json`
- `ARR/backend/design/maas/grammar/data/maas_sequences.v0.json`

## Rule

Architectural terms are not geometry by themselves.

```text
term / intent
-> supported MAAS verb sequence
-> deterministic Shapely/MAAS geometry operation
-> legal repair/check
-> evidence
```

## Current Term Groups

- `stepback`: 스텝백, 후퇴, 계단형.
- `sunlight_step`: 정북일조, 북측 일조, 일조사선, 일조 스텝.
- `podium_tower`: 포디움, 타워, 저층부/상부타워.
- `courtyard_void`: 중정, 보이드, 내부마당.
- `split_bridge`: 분절, 브릿지, 연결부.
- `bar_slab`: 바형, 판상형, 슬래브.
- `corner_open`: 코너비움, 오픈코트.
- `taper`: 테이퍼, 상부축소.
- `interlock_overlap`: 인터락, 오버랩, 어긋난 슬래브.

## Design Principle

The ontology is for the AI translator, not for legal truth.

The model may map language to grammar. It may not:

- emit raw mesh coordinates;
- claim legal pass without evidence;
- alter a locked legal mass through image generation;
- treat daylight reference surfaces as final compliance.

## Next Additions

- Korean apartment typology terms: 판상형, 탑상형, 혼합형, 코어형.
- Urban terms: street wall, arcade, pilotis, view corridor, corner plaza.
- Program terms: core, corridor, double-loaded, single-loaded, unit bar.
- Review terms: needs evidence, hard fail, soft warning, design alternative.

## 2026-06-10 Resolver Note

The first deterministic resolver is implemented at:

- `ARR/backend/design/maas/grammar/intent.py`

It ranks sequence proposals from aliases, intent tags, and ontology term verbs.
It is only a fallback/contract layer. The planned fine-tuned model should emit
the same schema, but with better architectural-language coverage.
