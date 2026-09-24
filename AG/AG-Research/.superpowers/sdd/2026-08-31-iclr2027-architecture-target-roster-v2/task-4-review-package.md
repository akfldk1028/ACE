# Task 4 review package

Reviewed Task-3 base production/test identities:

- roster production 36,852 / 7D08608C8AF8801CF79E679CE74E08807909DD5945E0850ED0299AC4B814DC18
- target-roster tests 32,210 / 9E7C6A36CA2482EAF2E62D3F2FAF45F4E1B26FF46AC3DF803D1A7CEC21D95468

Current full-file review surface:

- `D:/Data/25_ACE/AG/AG-Research/iclr2027/architecture_target_roster.py`
  — 40,429 / 2D873D179E537406273BA7BE18855A1EDD477FCA0B2A7BD58EBC5A7500ACC11D
- `D:/Data/25_ACE/AG/AG-Research/iclr2027/dataset.py`
  — 31,859 / B3469093D68E11B7F96266E1F2B5259E7AEE279AEDAFCB121E470E36FA31B99E
- `D:/Data/25_ACE/AG/AG-Research/tests/test_iclr2027_architecture_target_roster.py`
  — 41,708 / 8D609EA6995DB88FAB4D94917A6506CB502523F9DFDDC372C7A75176463ADC45

Task-4 additions are `verify_frozen_target_roster`, its secure/canonical read
helpers, `verified_development_target_count`, and
`TargetRosterDatasetIntegrationTests`. Existing legacy files are not part of
the diff; their eight exact unchanged pins are in the report.
