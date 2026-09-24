from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "ICLR_2027_OACS_HANDOFF.md"
CLAUDE = ROOT / "CLAUDE.md"

EXPECTED_HEADINGS = (
    "# ICLR 2027 OACS Cross-Agent Handoff",
    "## Goal",
    "## Completed",
    "## Current NO-GO state",
    "## Frozen scientific contract",
    "## Current exact pins",
    "## Safety boundaries",
    "## Next execution order",
    "## Verification commands",
)

EXPECTED_CLAUDE = """# Claude workspace instructions

Read `ICLR_2027_OACS_HANDOFF.md` and the current append-only
`ICLR_2027_ARCHITECTURE_DOMAIN_MEMORY.md` before OACS work.
Do not use the legacy COLM `HANDOFF.md` for OACS.
Do not inspect `data/`, `results/`, `models/`, protected, held-out, or OOD
namespaces without a separately reviewed authorization.
Current scientific state is `NO-GO`/`NEEDS_CONTEXT`.
"""

EXPECTED_PIN_ROWS = (
    "| Positive-intake design | `docs/superpowers/specs/2026-08-27-iclr2027-path-b-positive-intake-design.md` | 21,032 | `CF7FF5D2F105F1F1DA9C0A53937058672D65EB1ABDDD8C2B75F495C09D41597B` |",
    "| Positive-intake plan | `docs/superpowers/plans/2026-08-30-iclr2027-path-b-positive-intake.md` | 23,950 | `2DEDA53D3774ED166901967C6C3BFB73131E049F9AEA287EA2DD610332EFCD42` |",
    "| Policy-provenance design | `docs/superpowers/specs/2026-08-31-iclr2027-oacs-policy-provenance-related-work-design.md` | 16,912 | `1C314F7D882C4685CBB47CF9DB6D805A6976A472F0EAD85492361EEB9F932F65` |",
    "| Policy-provenance plan | `docs/superpowers/plans/2026-08-31-iclr2027-oacs-policy-provenance-related-work.md` | 42,793 | `C66F744F70A261CE20C5A50634ABCA2FF3A0B4BD48AE24B23A34FBAB27C62987` |",
    "| Public-source census | `.superpowers/sdd/2026-08-31-iclr2027-oacs-policy-provenance/public-source-census.md` | 9,942 | `78C561414136757DF32803C51F1AD3D4F937D43448472486048C9C3AAEFB4F73` |",
    "| SAP | `docs/paper/iclr2027_oacs/latex/appendices/appendix_analysis_protocol.tex` | 16,889 | `CE89C6169B2D91396E985E631C26B25BD9A221249927DD4879B1121FA674832C` |",
    "| Experimental design | `docs/paper/iclr2027_oacs/latex/sections/06_experimental_design.tex` | 1,876 | `20A759EE8E266D8CDB837139B1FE5AA04EEF5D5678AAD25E4952888527F8994F` |",
    "| Claim matrix | `docs/paper/iclr2027_oacs/claim_evidence_matrix.md` | 15,832 | `2048C5FDA7A0D2873B8FE59E953FF738AE0DE01C9271535C32013BDD4391E88B` |",
    "| Policy provenance appendix | `docs/paper/iclr2027_oacs/latex/appendices/appendix_policy_provenance.tex` | 11,825 | `FB369CE6755337A8C893E2857D0175A152445C21E11CFCF69C22478DB9FAAFFB` |",
    "| Static verifier | `iclr2027/paper_latex_verification.py` | 92,048 | `51DAFF058AC1A95AD2581E3E9AA6EFC8B48D7F19661012101621BA0652A6BAD3` |",
    "| Static-verifier test | `tests/test_iclr2027_paper_latex_verification.py` | 354,903 | `09DBCC5F6C895DACC34475571740B71538BADA8BC11A9E1F61F3EFA0E820275F` |",
    "| Science-alignment test | `tests/test_iclr2027_scientific_contract_alignment.py` | 39,256 | `2435F9D88346345D416773BD7B7B2EDFA6937A09F0C812BF5F0BF6F7122F7BA1` |",
    "| Source manifest | current 22-file canonical serialization | 2,275 | `EBFB0EC6F85C66AFBFB21AC4AEA87D760D3CAFF3F8546EAFFD767B235D9D1B91` |",
    "| Static receipt | not a persisted file; current deterministic `PaperStaticReceipt` canonical JSON | 844 | `1B612275AC7BBAE17FF317E3C5E7F1A486C042FBF7FB5BB803B752E2D1200600` |",
    "| Unofficial layout-fix preview PDF | `.superpowers/sdd/2026-08-31-iclr2027-oacs-policy-provenance/preview-artifacts-layoutfix-01/output/main.pdf` | 118,088 | `2D1452A18278F238A3E24C40A9DB5716D3DF7EE5262961358017E38EC26FD639` |",
    "| Layout-fix artifact manifest | `.superpowers/sdd/2026-08-31-iclr2027-oacs-policy-provenance/preview-artifacts-layoutfix-01/artifact-manifest.tsv` | 4,873 | `FEAD1F5E382CDF713819A0534C3C253E47ABF270861F54992FBEDF5BA26926D9` |",
    "| Layout-fix preview report | `.superpowers/sdd/2026-08-31-iclr2027-oacs-policy-provenance/preview-layoutfix-report.md` | 8,243 | `70F1E72902B5D02384A56D6A21163FA2220F970F40C0102774026336820B8649` |",
    "| Policy-provenance worker report | `.superpowers/sdd/2026-08-31-iclr2027-oacs-policy-provenance/task-1-worker-report.md` | 24,690 | `167A3E642F50C9F96C02AB57067E3B16FA316A8B210484E27A4C4BDF47C8E878` |",
    "| Policy-provenance literature review | `.superpowers/sdd/2026-08-31-iclr2027-oacs-policy-provenance/task-1-literature-review.md` | 19,575 | `B37B383CB48817480DF6F27E46DCF9256C0A26CA443D8DE87A66F32540781C5E` |",
    "| Policy-provenance verifier review | `.superpowers/sdd/2026-08-31-iclr2027-oacs-policy-provenance/task-1-verifier-review.md` | 12,363 | `0CBA4C2F206F383A69F79FA00EA70493AEF955F9D73EAD694C2A33667E15ED7F` |",
    "| Contract module | `iclr2027/path_b_positive_intake_contract.py` | 31,625 | `65AD68287083623F013A634AC496DE876F7FF4F3F871EB7940EDF063E99AB3D8` |",
    "| Science module | `iclr2027/path_b_positive_intake_science.py` | 44,266 | `1F7998CB90857FBDF744505BC18B4DDCD5EC8018908BCC7592522042B5D762B4` |",
    "| Public-only crypto module | `iclr2027/path_b_positive_intake_crypto.py` | 4,876 | `22536551EED74C20F30E2BDCD5F0A911AF839F60A35C2FCB47F08E433C50864C` |",
    "| No-authority orchestrator | `iclr2027/path_b_positive_intake.py` | 8,007 | `1FE99C846DA781E71CD029C0455B0C30CBAE116E704CB4951C63B352AA2E05F2` |",
    "| No-authority CLI | `validate_iclr2027_path_b_positive_intake.py` | 2,041 | `3BC483D27C1CDADFFDD347243A8E00E6982A1C685ADD954CDD0D056D9D6CEAB8` |",
    "| Contract test | `tests/test_iclr2027_path_b_positive_intake_contract.py` | 81,598 | `8131AF52F581FB56B5B22D2FBCC4B43D52DCD15AB20CF627D8BB720BD566052C` |",
    "| Science test | `tests/test_iclr2027_path_b_positive_intake_science.py` | 129,172 | `0D32F0E500B0B68D4CD3BB3D7352C0063E84365B7642904D5A073367437AF7FA` |",
    "| Crypto test | `tests/test_iclr2027_path_b_positive_intake_crypto.py` | 25,297 | `CE74A8A5E606F44F87878B944F0ADE60A372A03D9249A54A1E4D80CC78E18BA7` |",
    "| Orchestrator/CLI test | `tests/test_iclr2027_path_b_positive_intake.py` | 37,046 | `2B87F193F22FA5BADB6C7984F5688EF8C831142BAF93D6582641D12229D85161` |",
    "| Task-7 worker audit | `.superpowers/sdd/2026-08-30-iclr2027-path-b-positive-intake/task-7-worker-report.md` | 38,124 | `83CDFC4D577DC6C49336C83D16E10E65074350B285BDDF01632D6F3E245BBF5A` |",
    "| Final science review | `.superpowers/sdd/2026-08-30-iclr2027-path-b-positive-intake/task-1-science-review.md` | 42,197 | `412D602DD87D6F96627A92E1EEDE7FCEFF2DFE55F8B6CF765497DCF146A770DD` |",
    "| Final security review | `.superpowers/sdd/2026-08-30-iclr2027-path-b-positive-intake/task-1-security-review.md` | 48,154 | `7AA6F418A22985370D5C0BFD0E7F13C272398B14BEA98CBC6297541B84EC075E` |",
    "| Public Path-B work order | `docs/paper/iclr2027_oacs/path_b_external_handoff.md` | 27,915 | `6AC83C04D68AB30E1AB623A91AB1C53D6F212E57C3250468E01225156AD904D4` |",
    "| Claude pointer | `CLAUDE.md` | 388 | `073E8703D7167AAEFE79F7B725B91518B90FC3413FAF3F61F795208CA0EAD848` |",
)

REQUIRED_HANDOFF_LITERALS = (
    "The current structural position is 5 sites, 30 cases, and 0-of-6 standardized actions; Task6-vNext is absent.",
    "Generation 0's Task-7 baseline received independent `C0/I0/M0` reviews; later hardening bytes require their own exact rereview and local green tests alone confer no authority.",
    "Repo-external launcher, trust policy, root keys, signed locator/current head/challenge, immutable package, signatures, approvals, and custody objects remain absent.",
    "The layout-fix preview is 16 US-Letter pages, counted main text ends on page 7, the appendix starts on page 8, and all 16 pages were individually inspected.",
    "Full discovery ran exactly once: 1,042 tests, 1,040 passes, 9 skips, and 2 pre-refresh handoff-pin failures; the dedicated refreshed handoff suite closes those two documentation failures without rerunning discovery.",
    "The prior `C0/I0/M0` literature and verifier reviews cover the pre-layout scientific tokens; the later layout-only raw bytes have local reconstruction, mutation, static, compile, and visual verification but no newly minted independent authority.",
    "(residual-present high-minus-low) - (residual-absent high-minus-low)",
    "E2 is not a randomized effect of residual status.",
    "Path-B is non-continuity intake only.",
    "it cannot authorize source access, simulation, paid execution, design-lock PASS, submission, or empirical claims.",
    "This document does not claim acceptance, authenticated Path-B, data access, empirical readiness, submission readiness, or a positive empirical result.",
    "Do not inspect `data/`, `results/`, `models/`, protected, held-out, or OOD namespaces without separately reviewed authorization.",
    "Do not mint external identity, authentication, signatures, reviews, pins, receipts, approval, or a PASS state from workspace content.",
    "no branch, commit, worktree, or VCS mutation for this handoff task.",
    "The static receipt is not a persisted file: its canonical JSON serialization is exactly 844 UTF-8 bytes (the CLI adds one LF for an 845-byte output stream).",
    "`schema_version=ace.iclr2027.paper_latex_static.v1`",
    "`pdf_compile_verified=false`",
    "`empirical_status=no_go_needs_context`",
)

EXPECTED_NEXT_STEPS = (
    "1. Provision the complete repo-external Phase-2 bootstrap under accountable owners.",
    "2. Review and freeze a Generation-1 amendment against those exact external bytes.",
    "3. Run Generation-1 authenticated intake through the externally pinned launcher.",
    "4. Commission and independently review a separate Task6-vNext authority.",
    "5. Run the separately reviewed design lock.",
    "6. Resolve site/target rosters and power/feasibility under authenticated authority.",
    "7. Obtain separate simulation and paid-execution authorization.",
    "8. Execute, then perform evidence and result review before any empirical claim.",
)

SECRET_PATTERNS = (
    re.compile(r"\b(?:sk|xai)-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bAIza[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\b(?:OPENAI_API_KEY|ANTHROPIC_API_KEY)\s*[:=]\s*\S+"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)

SECRET_SENTINELS = (
    "sk-aaaaaaaaaaaaaaaa",
    "AIzaaaaaaaaaaaaaaaaaaaaa",
    "OPENAI_API_KEY=synthetic_value",
    "ghp_aaaaaaaaaaaaaaaaaaaa",
    "github_pat_aaaaaaaaaaaaaaaaaaaa",
    "AKIAABCDEFGHIJKLMNOP",
    "-----BEGIN PRIVATE KEY-----",
)

_FILE_PIN_ROW = re.compile(
    r"^\| (?P<object>[^|]+?) \| `(?P<path>[^`]+)` \| "
    r"(?P<byte_count>[0-9,]+) \| `(?P<sha256>[0-9A-F]{64})` \|$"
)
_NON_FILE_PIN_OBJECTS = frozenset(("Source manifest", "Static receipt"))


def _file_pin_failures(text: str) -> tuple[str, ...]:
    failures: list[str] = []
    for line in text.splitlines():
        match = _FILE_PIN_ROW.fullmatch(line)
        if match is None:
            continue
        object_name = match.group("object")
        if object_name in _NON_FILE_PIN_OBJECTS:
            continue
        relative = Path(match.group("path"))
        path = (ROOT.parent if relative.parts[0] == ".superpowers" else ROOT) / relative
        if not path.is_file():
            failures.append(f"{object_name}:missing")
            continue
        raw = path.read_bytes()
        expected = (
            int(match.group("byte_count").replace(",", "")),
            match.group("sha256"),
        )
        actual = (len(raw), sha256(raw).hexdigest().upper())
        if actual != expected:
            failures.append(f"{object_name}:pin-drift:{actual[0]}:{actual[1]}")
    return tuple(failures)


class CrossAgentHandoffTests(unittest.TestCase):
    def test_every_file_backed_handoff_pin_matches_actual_local_bytes(self) -> None:
        text = HANDOFF.read_text(encoding="utf-8")

        self.assertEqual(_file_pin_failures(text), ())

    def test_file_pin_oracle_detects_a_test_owned_digest_mutation(self) -> None:
        text = HANDOFF.read_text(encoding="utf-8")
        mutated = text.replace(
            "CF7FF5D2F105F1F1DA9C0A53937058672D65EB1ABDDD8C2B75F495C09D41597B",
            "0" * 64,
            1,
        )

        self.assertEqual(
            _file_pin_failures(mutated),
            (
                "Positive-intake design:pin-drift:21032:"
                "CF7FF5D2F105F1F1DA9C0A53937058672D65EB1ABDDD8C2B75F495C09D41597B",
            ),
        )

    def test_cross_agent_handoff_is_closed_and_model_neutral(self) -> None:
        text = HANDOFF.read_text(encoding="utf-8")

        self.assertEqual(
            tuple(
                line
                for line in text.splitlines()
                if line.startswith("##") or line.startswith("# ")
            ),
            EXPECTED_HEADINGS,
        )
        for literal in (
            "Codex",
            "Claude",
            "NO-GO",
            "NEEDS_CONTEXT",
            "learner_class_capacity",
        ):
            self.assertIn(literal, text)

    def test_cross_agent_handoff_closes_pins_state_safety_and_order(self) -> None:
        text = HANDOFF.read_text(encoding="utf-8")

        for row in EXPECTED_PIN_ROWS:
            self.assertIn(row, text)
        for literal in REQUIRED_HANDOFF_LITERALS:
            self.assertIn(literal, text)
        positions = [text.index(step) for step in EXPECTED_NEXT_STEPS]
        self.assertEqual(positions, sorted(positions))

    def test_public_handoff_files_reject_secret_like_tokens(self) -> None:
        for path in (HANDOFF, CLAUDE):
            text = path.read_text(encoding="utf-8")
            for pattern in SECRET_PATTERNS:
                with self.subTest(path=path.name, pattern=pattern.pattern):
                    self.assertIsNone(pattern.search(text))

    def test_secret_patterns_match_test_owned_harmless_sentinels(self) -> None:
        self.assertEqual(len(SECRET_PATTERNS), len(SECRET_SENTINELS))
        for pattern, sentinel in zip(SECRET_PATTERNS, SECRET_SENTINELS, strict=True):
            with self.subTest(pattern=pattern.pattern):
                self.assertIsNotNone(pattern.search(sentinel))

    def test_claude_instruction_is_only_the_oacs_pointer_and_safety_boundary(
        self,
    ) -> None:
        text = CLAUDE.read_text(encoding="utf-8")

        self.assertEqual(text, EXPECTED_CLAUDE)
        self.assertNotIn("Read `HANDOFF.md`", text)


if __name__ == "__main__":
    unittest.main()
