# Task 2 review package

No commits were created. The reviewed Task-1 base identities were:

- production 8,522 bytes / 11D7E304600ADE22E0A5B9C192A2FA74CAFED989EDCF7ED7A4ECD7515FFA7B70
- tests 4,915 bytes / 527EEE6208D386E80CF5BD3CB454DE6C24F4F8DF6C205212D8668C82D835DCC8

Task-2 current identities are:

- `D:/Data/25_ACE/AG/AG-Research/iclr2027/architecture_target_roster.py`
  — 25,993 bytes / 9CE913335E42A124221D6A8A21F7F3DD1EDE672C97867A0930416C5BEDE32C9D
- `D:/Data/25_ACE/AG/AG-Research/tests/test_iclr2027_architecture_target_roster.py`
  — 11,938 bytes / 2602B69896ECCBCE859F3C5C13F5DC3031C14C5119109F85209B8029318D49E8

Read each complete current file once as the review surface. Task-2 additions
are the source/locator/target-spec/geometry/blind records, their set validators,
`AdmissionBindingV1`, `verify_admission_inputs`, and
`TargetRosterAdmissionTests`. Task-1 public-roster code was already reviewed;
flag it only if Task 2 regressed it.
