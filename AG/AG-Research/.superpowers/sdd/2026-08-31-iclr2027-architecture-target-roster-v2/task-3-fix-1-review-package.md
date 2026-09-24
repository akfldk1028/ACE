# Task 3 Fix Round 1 review package

Prior review identities:

- builder 11,261 / F882A4C8E073AC2AAB0DC4F75699B6EBC900FB0F6ABC48BF97F62B4AF7D1114E
- production 36,852 / 7D08608C8AF8801CF79E679CE74E08807909DD5945E0850ED0299AC4B814DC18
- tests 25,298 / 62A014815303D53EE83866D2EE9E8638953B57F7BFBEE5EE7C9C0B249FEEA74B

Post-fix full-file review surface:

- `D:/Data/25_ACE/AG/AG-Research/build_iclr2027_architecture_target_roster.py`
  — 12,515 / 7E8E39E58083F60CC27603B708EBBEAC52DCFB4D6DF0C3D0CEF7F15B57D3F86B
- `D:/Data/25_ACE/AG/AG-Research/iclr2027/architecture_target_roster.py`
  — 36,852 / 7D08608C8AF8801CF79E679CE74E08807909DD5945E0850ED0299AC4B814DC18
- `D:/Data/25_ACE/AG/AG-Research/tests/test_iclr2027_architecture_target_roster.py`
  — 32,210 / 9E7C6A36CA2482EAF2E62D3F2FAF45F4E1B26FF46AC3DF803D1A7CEC21D95468

Scope is the three Important findings in `task-3-review.md` and new breakage
from this fix. Raw-`OSError` normalization is a deferred Minor.
