"""Static verification for the fixed Task-11 ICLR 2027 paper closure."""

from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import json
from pathlib import Path
import re

from iclr2027.secure_files import AuthenticatedTree


class PaperLatexVerificationError(RuntimeError):
    """A frozen-vocabulary static-verification failure."""

    def __init__(self, reason_code: str) -> None:
        if reason_code not in {
            "source_identity_invalid",
            "source_bytes_invalid",
            "source_grammar_invalid",
            "scientific_boundary_invalid",
            "primary_source_manifest_invalid",
        }:
            raise ValueError("invalid paper verification reason code")
        self.reason_code = reason_code
        super().__init__(reason_code)


@dataclass(frozen=True, slots=True, init=False)
class PaperStaticReceipt:
    """Sealed receipt for the fixed static paper verification."""

    schema_version: str
    status: str
    source_manifest_sha256: str
    source_file_count: int
    primary_source_manifest_sha256: str
    primary_source_keys: tuple[str, ...]
    primary_source_count: int
    claim_count: int
    blocked_slot_count: int
    policy_count: int
    attack_count: int
    citation_authority_status: str
    pdf_compile_verified: bool
    empirical_status: str
    receipt_sha256: str

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("PaperStaticReceipt cannot be constructed directly")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del cls, kwargs
        raise TypeError("PaperStaticReceipt cannot be subclassed")

    def to_dict(self) -> dict[str, object]:
        try:
            payload = {
                "schema_version": self.schema_version,
                "status": self.status,
                "source_manifest_sha256": self.source_manifest_sha256,
                "source_file_count": self.source_file_count,
                "primary_source_manifest_sha256": self.primary_source_manifest_sha256,
                "primary_source_keys": list(self.primary_source_keys),
                "primary_source_count": self.primary_source_count,
                "claim_count": self.claim_count,
                "blocked_slot_count": self.blocked_slot_count,
                "policy_count": self.policy_count,
                "attack_count": self.attack_count,
                "citation_authority_status": self.citation_authority_status,
                "pdf_compile_verified": self.pdf_compile_verified,
                "empirical_status": self.empirical_status,
                "receipt_sha256": self.receipt_sha256,
            }
            PaperStaticReceipt._from_dict(payload)
            return payload
        except PaperLatexVerificationError:
            raise
        except (AttributeError, KeyError, TypeError, ValueError) as error:
            raise PaperLatexVerificationError("source_identity_invalid") from error

    def canonical_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    @classmethod
    def from_dict(
        cls,
        value: dict[str, object],
        *,
        repository_root: Path,
    ) -> PaperStaticReceipt:
        try:
            parsed = cls._from_dict(value)
            fresh = _verify_static_paper_latex_at(repository_root)
            if parsed != fresh:
                raise ValueError("receipt does not match verified source closure")
            return fresh
        except PaperLatexVerificationError:
            raise
        except (AttributeError, KeyError, TypeError, ValueError) as error:
            raise PaperLatexVerificationError("source_identity_invalid") from error

    @classmethod
    def from_json(
        cls,
        value: str,
        *,
        repository_root: Path,
    ) -> PaperStaticReceipt:
        try:
            if type(value) is not str:
                raise TypeError("receipt JSON must be a string")

            def object_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
                result: dict[str, object] = {}
                for key, item in pairs:
                    if key in result:
                        raise ValueError("duplicate receipt key")
                    result[key] = item
                return result

            def parse_int(token: str) -> int:
                if token == "-0":
                    raise ValueError("negative zero is not canonical")
                return int(token)

            def reject_number(_token: str) -> object:
                raise ValueError("non-integral or non-finite number")

            decoded = json.loads(
                value,
                object_pairs_hook=object_pairs,
                parse_int=parse_int,
                parse_float=reject_number,
                parse_constant=reject_number,
            )
            receipt = cls.from_dict(
                decoded,
                repository_root=repository_root,
            )
            if value != receipt.canonical_json():
                raise ValueError("receipt JSON is not canonical")
            return receipt
        except PaperLatexVerificationError:
            raise
        except (json.JSONDecodeError, TypeError, ValueError) as error:
            raise PaperLatexVerificationError("source_identity_invalid") from error

    @classmethod
    def _from_dict(cls, value: dict[str, object]) -> PaperStaticReceipt:
        expected_keys = tuple(field.name for field in fields(cls))
        if type(value) is not dict or set(value) != set(expected_keys):
            raise ValueError("receipt key set is invalid")
        string_fields = {
            "schema_version",
            "status",
            "source_manifest_sha256",
            "primary_source_manifest_sha256",
            "citation_authority_status",
            "empirical_status",
            "receipt_sha256",
        }
        integer_fields = {
            "source_file_count",
            "primary_source_count",
            "claim_count",
            "blocked_slot_count",
            "policy_count",
            "attack_count",
        }
        if any(type(value[key]) is not str for key in string_fields):
            raise TypeError("receipt string field is invalid")
        if any(type(value[key]) is not int or value[key] < 0 for key in integer_fields):
            raise TypeError("receipt integer field is invalid")
        if type(value["pdf_compile_verified"]) is not bool:
            raise TypeError("receipt Boolean field is invalid")
        keys = value["primary_source_keys"]
        if type(keys) is not list or any(type(key) is not str for key in keys):
            raise TypeError("primary source keys are invalid")
        expected_constants: dict[str, object] = {
            "schema_version": "ace.iclr2027.paper_latex_static.v1",
            "status": "literature_corrected_static_ready",
            "source_file_count": 22,
            "primary_source_keys": [
                "bala2026setvalued",
                "dellapenna2026brace",
                "flynn2026sparse",
                "girard2026fast",
                "kallus2018instrument",
                "oprescu2025amriv",
                "qin2026oe2d",
                "wong2026eureka",
                "yang2026star",
                "zhang2026icore",
            ],
            "primary_source_count": 10,
            "claim_count": 23,
            "blocked_slot_count": 9,
            "policy_count": 22,
            "attack_count": 24,
            "citation_authority_status": "blocked_pending_authenticated_roster",
            "pdf_compile_verified": False,
            "empirical_status": "no_go_needs_context",
        }
        if any(value[key] != expected for key, expected in expected_constants.items()):
            raise ValueError("receipt constant is invalid")
        for key in (
            "source_manifest_sha256",
            "primary_source_manifest_sha256",
            "receipt_sha256",
        ):
            if re.fullmatch(r"[0-9a-f]{64}", value[key]) is None:
                raise ValueError("receipt digest is invalid")
        unhashed = {key: value[key] for key in expected_keys[:-1]}
        canonical = json.dumps(
            unhashed,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        expected_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        if value["receipt_sha256"] != expected_hash:
            raise ValueError("receipt self-hash is invalid")
        instance = object.__new__(cls)
        for key in expected_keys:
            item = tuple(keys) if key == "primary_source_keys" else value[key]
            object.__setattr__(instance, key, item)
        return instance


def _make_receipt(
    source_manifest_sha256: str,
    primary_source_manifest_sha256: str,
) -> PaperStaticReceipt:
    payload: dict[str, object] = {
        "schema_version": "ace.iclr2027.paper_latex_static.v1",
        "status": "literature_corrected_static_ready",
        "source_manifest_sha256": source_manifest_sha256,
        "source_file_count": 22,
        "primary_source_manifest_sha256": primary_source_manifest_sha256,
        "primary_source_keys": [
            "bala2026setvalued",
            "dellapenna2026brace",
            "flynn2026sparse",
            "girard2026fast",
            "kallus2018instrument",
            "oprescu2025amriv",
            "qin2026oe2d",
            "wong2026eureka",
            "yang2026star",
            "zhang2026icore",
        ],
        "primary_source_count": 10,
        "claim_count": 23,
        "blocked_slot_count": 9,
        "policy_count": 22,
        "attack_count": 24,
        "citation_authority_status": "blocked_pending_authenticated_roster",
        "pdf_compile_verified": False,
        "empirical_status": "no_go_needs_context",
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    payload["receipt_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return PaperStaticReceipt._from_dict(payload)


_PAPER_RELATIVE = Path("docs/paper/iclr2027_oacs")
_OFFICIAL_STYLE_ARCHIVE_URL = (
    "https://media.iclr.cc/Conferences/ICLR2027/iclr-2027-style-files.zip"
)
_OFFICIAL_STYLE_ARCHIVE_LENGTH = 39_348
_OFFICIAL_STYLE_ARCHIVE_SHA256 = (
    "0D940DFA9398AE99A18F24A85A8A683F367204B6AF6D17D2899E60A67102529E"
)
_VENDOR_SOURCE_IDENTITIES = (
    (
        "latex/fancyhdr.sty",
        20_521,
        "B56EC4434B9F4607529A4B23DC68AD8D4B94F1F631C8CDDAF7DA78140D53A5EA",
    ),
    (
        "latex/iclr2027_conference.bst",
        26_973,
        "2D67552DB7ED38CCFCCB5957B52F95656E25C249724761D3CF5F7922AD1844C5",
    ),
    (
        "latex/iclr2027_conference.sty",
        9_025,
        "797DEEF41724E93761426AC0CBCCA46279A91CC650DD1F0CE76A4F08D2098EA6",
    ),
    (
        "latex/natbib.sty",
        45_154,
        "88BC70C0E48461934CAB5B2ACCEF06B74A8B3AC45AD03CCD3F2A6B7E0D6D530D",
    ),
)
_OMITTED_ARCHIVE_MEMBERS = (
    "iclr2027/iclr2027_conference.bib",
    "iclr2027/iclr2027_conference.tex",
    "iclr2027/math_commands.tex",
)
_MANUSCRIPT_SOURCE_PATHS = (
    "latex/README.md",
    "latex/appendices/appendix_analysis_protocol.tex",
    "latex/appendices/appendix_claims.tex",
    "latex/appendices/appendix_policy_provenance.tex",
    "latex/appendices/appendix_reviewer_attacks.tex",
    "latex/appendices/appendix_theory.tex",
    "latex/main.tex",
    "latex/references.bib",
    "latex/sections/01_introduction.tex",
    "latex/sections/02_related_work.tex",
    "latex/sections/03_problem_formulation.tex",
    "latex/sections/04_method.tex",
    "latex/sections/05_supporting_theory.tex",
    "latex/sections/06_experimental_design.tex",
    "latex/sections/07_results.tex",
    "latex/sections/08_limitations.tex",
    "latex/sections/09_conclusion.tex",
    "latex/sections/10_submission_statements.tex",
)
_VENDOR_SOURCE_PATHS = tuple(
    relative for relative, _length, _digest in _VENDOR_SOURCE_IDENTITIES
)
_SOURCE_PATHS = tuple(
    sorted(
        (*_MANUSCRIPT_SOURCE_PATHS, *_VENDOR_SOURCE_PATHS),
        key=lambda value: value.encode("utf-8"),
    )
)
_PINNED_SOURCE_SHA256 = {
    "latex/appendices/appendix_analysis_protocol.tex": "D5E653A19094C2D0B19475C1FC126308DA1994567C86A2A31D15BC9C36DBC149",
    "latex/appendices/appendix_claims.tex": "A61388B1DF0F8665495A892459900915EAD2443E60DED8C632091F72735CFF77",
    "latex/appendices/appendix_policy_provenance.tex": "E947C55C6F2C9F18293A163E9C19A0FADD041416B0416A636B92D6F5B72C3D0C",
    "latex/appendices/appendix_theory.tex": "3AE7B93C307F0FD2B840E9B02315F6733719237668E2AD5A746FBFCB0BC3CE64",
    "latex/main.tex": "010AA6D5DE6B8787470CFE2C58B542A665B409B733C150965DECD026584FD99D",
    "latex/sections/05_supporting_theory.tex": "87945EF21652F56887EC1C8F4C4050CB8B6CE5FA875CAB3802300438D1DADB81",
    "latex/sections/06_experimental_design.tex": "E78F7ADB77675761C986D551D381F82E210CB62DE7C23E96B85655A50790F056",
    "latex/sections/07_results.tex": "97B402E82313F8B44B697438D5A61A16DA439C69B602448DED19C2D56EE95D84",
    "latex/sections/08_limitations.tex": "A5E17D5EF767CF0AA6F7BBB3419F34DCAC1B38C0EBBEF547F693E04393EE813A",
    "latex/sections/10_submission_statements.tex": "B20C836964F08013DCE30467339C0A92D5B3AFE44D187F10566F1E327262A839",
}
_PRIMARY_MANIFEST_SHA256 = (
    "9A84A93002562DFDE19008C759C960E809DB5CB11CB95CC7AE2790F4A98B7108"
)
_ROOT_ENTRIES = {
    "claim_evidence_matrix.md": False,
    "latex": True,
    "literature_primary_source_manifest.md": False,
    "paper_blueprint.md": False,
    "path_b_external_handoff.md": False,
    "reviewer_attack_matrix.md": False,
    "theory_appendix_map.md": False,
}
_LATEX_ENTRIES = {
    "README.md": False,
    "appendices": True,
    "fancyhdr.sty": False,
    "iclr2027_conference.bst": False,
    "iclr2027_conference.sty": False,
    "main.tex": False,
    "natbib.sty": False,
    "references.bib": False,
    "sections": True,
}
_SECTION_ENTRIES = {
    **{
        f"{index:02d}_{name}.tex": False
        for index, name in enumerate(
            (
                "introduction",
                "related_work",
                "problem_formulation",
                "method",
                "supporting_theory",
                "experimental_design",
                "results",
                "limitations",
                "conclusion",
            ),
            1,
        )
    },
    "10_submission_statements.tex": False,
}
_APPENDIX_ENTRIES = {
    "appendix_analysis_protocol.tex": False,
    "appendix_claims.tex": False,
    "appendix_policy_provenance.tex": False,
    "appendix_reviewer_attacks.tex": False,
    "appendix_theory.tex": False,
}
_EDITABLE_ROLES = {
    "latex/sections/01_introduction.tex": (
        {"begin", "claim", "emph", "end", "item", "section", "structural"},
        ("enumerate",),
    ),
    "latex/sections/02_related_work.tex": (
        {"cite", "citet", "citep", "claim", "section"},
        (),
    ),
    "latex/sections/03_problem_formulation.tex": (
        {"in", "lambda", "ref", "section", "top"},
        (),
    ),
    "latex/sections/04_method.tex": ({"oacs", "section"}, ()),
    "latex/sections/09_conclusion.tex": ({"section"}, ()),
    "latex/appendices/appendix_reviewer_attacks.tex": (
        {"begin", "end", "item", "section", "textbf"},
        ("enumerate",),
    ),
    "latex/appendices/appendix_policy_provenance.tex": (
        {
            "begin",
            "citep",
            "end",
            "item",
            "par",
            "raggedright",
            "section",
            "small",
            "textbf",
            "texttt",
        },
        ("enumerate",),
    ),
}
_ACTIVE_PROSE_PATHS = (
    "latex/README.md",
    "latex/appendices/appendix_analysis_protocol.tex",
    "latex/appendices/appendix_policy_provenance.tex",
    "latex/appendices/appendix_reviewer_attacks.tex",
    "latex/sections/01_introduction.tex",
    "latex/sections/02_related_work.tex",
    "latex/sections/03_problem_formulation.tex",
    "latex/sections/04_method.tex",
    "latex/sections/09_conclusion.tex",
    "latex/sections/10_submission_statements.tex",
)
_ACTIVE_PROSE_MANIFEST_SHA256 = (
    "a4ec9dd45c1299ac17891f4a12f16ffea36a69114c5086f3ce90f05e9d3081cd"
)
_CANONICAL_ACTIVE_MAIN_SHA256 = (
    "69DE6587279835C81E7FA2ADB5A3BC440A029E7FCBED5725984830F87556B467"
)
_CANONICAL_ACTIVE_STATEMENTS_SHA256 = (
    "B20C836964F08013DCE30467339C0A92D5B3AFE44D187F10566F1E327262A839"
)
_CANONICAL_ACTIVE_MANUSCRIPT_TEX_SHA256 = {
    "latex/appendices/appendix_analysis_protocol.tex": (
        "D5E653A19094C2D0B19475C1FC126308DA1994567C86A2A31D15BC9C36DBC149"
    ),
    "latex/appendices/appendix_claims.tex": (
        "A61388B1DF0F8665495A892459900915EAD2443E60DED8C632091F72735CFF77"
    ),
    "latex/appendices/appendix_policy_provenance.tex": (
        "E947C55C6F2C9F18293A163E9C19A0FADD041416B0416A636B92D6F5B72C3D0C"
    ),
    "latex/appendices/appendix_reviewer_attacks.tex": (
        "1B9DDB20873E16CADFFCF71BBCB9BA538DBB62D16AA25F72C47467CA15E6BE59"
    ),
    "latex/appendices/appendix_theory.tex": (
        "3AE7B93C307F0FD2B840E9B02315F6733719237668E2AD5A746FBFCB0BC3CE64"
    ),
    "latex/main.tex": (
        "69DE6587279835C81E7FA2ADB5A3BC440A029E7FCBED5725984830F87556B467"
    ),
    "latex/sections/01_introduction.tex": (
        "8A7A66623B0BD50D615140EAE4ECC4F82F0B6ED4053B3584BC5481E5F02F0395"
    ),
    "latex/sections/02_related_work.tex": (
        "2D9971B29924542601DF2F4C9FFCA9A44D798E86F5E4E79B8D7C58FC16B045B3"
    ),
    "latex/sections/03_problem_formulation.tex": (
        "29E251DE1816A44E98F5DFBAFD302F325F8217BB2C36D4E03DA5519F54AAC28B"
    ),
    "latex/sections/04_method.tex": (
        "9429D165B37CB751C693706CE2C19041F6AC65FD1FF2709D31132F4F69999D92"
    ),
    "latex/sections/05_supporting_theory.tex": (
        "87945EF21652F56887EC1C8F4C4050CB8B6CE5FA875CAB3802300438D1DADB81"
    ),
    "latex/sections/06_experimental_design.tex": (
        "E78F7ADB77675761C986D551D381F82E210CB62DE7C23E96B85655A50790F056"
    ),
    "latex/sections/07_results.tex": (
        "97B402E82313F8B44B697438D5A61A16DA439C69B602448DED19C2D56EE95D84"
    ),
    "latex/sections/08_limitations.tex": (
        "A5E17D5EF767CF0AA6F7BBB3419F34DCAC1B38C0EBBEF547F693E04393EE813A"
    ),
    "latex/sections/09_conclusion.tex": (
        "E3D1F619B544E2DD8EB0181B5C90431D4E1F39A8F604A8072072E8B3EDD76D20"
    ),
    "latex/sections/10_submission_statements.tex": (
        "B20C836964F08013DCE30467339C0A92D5B3AFE44D187F10566F1E327262A839"
    ),
}
_COMMAND_SIGNATURES = {
    "begin": (1, False, {"enumerate": "[leftmargin=*]"}),
    "cite": (1, False, {}),
    "citet": (1, False, {}),
    "citep": (1, False, {}),
    "claim": (1, False, {}),
    "emph": (1, False, {}),
    "end": (1, False, {}),
    "in": (0, False, {"": "[0,1]"}),
    "input": (1, False, {}),
    "item": (0, False, {}),
    "label": (1, False, {}),
    "lambda": (0, False, {}),
    "oacs": (0, True, {}),
    "par": (0, False, {}),
    "raggedright": (0, False, {}),
    "ref": (1, False, {}),
    "section": (1, False, {}),
    "small": (0, False, {}),
    "structural": (1, False, {}),
    "textbf": (1, False, {}),
    "texttt": (1, False, {}),
    "top": (0, False, {}),
}
_CONTROL_SYMBOL_SIGNATURES = {
    "\\": (0, False, {}),
    "_": (0, False, {}),
}
_MAIN_INPUTS = (
    "sections/01_introduction",
    "sections/02_related_work",
    "sections/03_problem_formulation",
    "sections/04_method",
    "sections/05_supporting_theory",
    "sections/06_experimental_design",
    "sections/07_results",
    "sections/08_limitations",
    "sections/09_conclusion",
    "sections/10_submission_statements",
    "appendices/appendix_theory",
    "appendices/appendix_analysis_protocol",
    "appendices/appendix_policy_provenance",
    "appendices/appendix_claims",
    "appendices/appendix_reviewer_attacks",
)
_PRIMARY_KEYS = (
    "bala2026setvalued",
    "dellapenna2026brace",
    "flynn2026sparse",
    "girard2026fast",
    "kallus2018instrument",
    "oprescu2025amriv",
    "qin2026oe2d",
    "wong2026eureka",
    "yang2026star",
    "zhang2026icore",
)
_ALL_BIBLIOGRAPHY_KEYS = (
    "chernozhukov2018double",
    "lattimore2020bandit",
    "auer2002finite",
    "bala2026setvalued",
    "dellapenna2026brace",
    "kallus2018instrument",
    "oprescu2025amriv",
    "wong2026eureka",
    "yang2026star",
    "zhang2026icore",
    "aggarwal2024automix",
    "amayuelas2025selfresource",
    "du2024multiagentdebate",
    "feng2026graphplanner",
    "keyu2026bicsrouter",
    "kim2026outgrow",
    "li2024moreagents",
    "li2025rirs",
    "lu2024zooter",
    "ong2025routellm",
    "smit2024mad",
    "wang2026conformalthinking",
    "wu2024autogen",
    "xu2026verimap",
    "yang2026costawareprotocol",
    "yue2025masrouter",
    "zhang2025agentprune",
    "zhang2026vmao",
    "zhuge2024gptswarm",
)
_DISPOSITIONS = (
    "iCORE establishes obligation--evidence--responsibility coupling and audit intervention as prior art; our obligation representation is measurement instrumentation, not a first obligation graph.",
    "Eureka establishes dynamic obligation-graph orchestration and acceptance semantics as prior art; our contribution is not obligation-graph construction.",
    "STAR establishes typed execution/failure-state specialist routing as prior art; our contribution is not execution-aware routing.",
    "Set-valued routing establishes fixed-catalog capability coverage and cost-aware selection as prior art; our contribution is not a first set-valued selector.",
    "BRACE is the closest product-bias/compliance prior; B1 is model-specific supporting theory rather than a first orthogonal remainder claim.",
)
_METHOD_BOUNDARY = "OACS is the prospective study policy, not the first obligation graph, execution-aware router, or capability-set selector."
_NOVELTY_BOUNDARY = (
    "We use the reviewed primary roster as a non-exhaustive positioning aid."
)
_FORBIDDEN_NOVELTY_PHRASES = (
    "latest",
    "first",
    "no prior work",
    "unprecedented",
    "exhaustive",
    "state-of-the-art",
)
_BIBLIOGRAPHIC_PROVENANCE_STATUS = (
    "bibliographic\\_provenance\\_status="
    "public\\_source\\_mapped\\_or\\_protocol\\_defined."
)
_IMPLEMENTATION_AUTHENTICATION_STATUS = (
    "implementation\\_authentication\\_status="
    "blocked\\_pending\\_authenticated\\_roster."
)
_FORBIDDEN_AUTHENTICATION_PROMOTIONS = (
    "adapter authenticated",
    "implementation verified",
    "version verified",
    "roster authenticated",
    "roster verified",
    "policy ready",
)
_SAP_POLICY_ROSTER_BLOCK = (
    "The pre-outcome policy family is exactly: "
    "\\begin{quote}\\small\\raggedright "
    "\\texttt{agentprune}, \\texttt{agora}, \\texttt{always\\_all\\_specialists}, "
    "\\texttt{automix}, \\texttt{bicsrouter}, \\texttt{conformal\\_thinking}, "
    "\\texttt{cost\\_aware\\_protocol\\_routing}, "
    "\\texttt{difficulty\\_confidence}, \\texttt{fixed\\_topology}, "
    "\\texttt{gptswarm}, \\texttt{graphplanner}, \\texttt{masrouter}, "
    "\\texttt{matched\\_compute\\_self\\_agent\\_scaling}, "
    "\\texttt{random\\_admissible\\_action}, "
    "\\texttt{rirs\\_talk\\_to\\_right\\_specialists}, \\texttt{routellm}, "
    "\\texttt{self\\_resource\\_allocation}, "
    "\\texttt{separated\\_router\\_stopper}, \\texttt{solo}, \\texttt{verimap}, "
    "\\texttt{vmao}, \\texttt{zooter\\_adaptation}. Self-resource allocation and "
    "matched-compute self-agent scaling are nonalias IDs with nonshared declared "
    "source/version commitments. \\end{quote}"
)
_SAP_E3_ALIGNED_BLOCKS = (
    "\\[\n"
    "  \\begin{aligned}\n"
    "  V_i(a)\n"
    "    &= \\operatorname{mean}_{r}\\{Y_{iar}(a)-\\lambda_K^\\top K_{iar}(a)\\},\\\\\n"
    "  \\operatorname{Reg}_i(\\pi)\n"
    "    &= \\max_{a\\in\\mathcal A_i}V_i(a)-V_i(\\pi(X_i)).\n"
    "  \\end{aligned}\n"
    "  \\]",
    "\\[\n"
    "  \\begin{aligned}\n"
    "  \\Delta^{\\mathrm{raw}}_{E3}\n"
    "    &= \\operatorname{mean}_{s}\\operatorname{mean}_{c\\mid s}\n"
    "       \\operatorname{mean}_{i\\mid sc}\n"
    "       \\{\\operatorname{Reg}_i(\\pi_O^{-s})-\\operatorname{Reg}_i(\\pi_R^{-s})\\},\\\\\n"
    "  D_i\n"
    "    &= V_i(\\pi_R^{-s}(X_i))-V_i(\\pi_O^{-s}(X_i)).\n"
    "  \\end{aligned}\n"
    "  \\]",
)
_UNDERFULL_LAYOUT_SCOPES = (
    (
        "latex/sections/05_supporting_theory.tex",
        "superior, or that receipt binding alone establishes evaluation validity.\n\n",
        "{\\raggedright\n",
        "",
        "\\par\n}\n",
    ),
    (
        "latex/sections/06_experimental_design.tex",
        "\\paragraph{E1: predictive diagnostic.}\n",
        "{\\raggedright\n",
        "\n\\paragraph{E2: randomized executed-bundle mechanism.}",
        "\\par\n}\n",
    ),
    (
        "latex/main.tex",
        "\\bibliographystyle{iclr2027_conference}\n",
        "\\begingroup\n\\raggedright\n",
        "\n\\appendix",
        "\\par\n\\endgroup\n",
    ),
    (
        "latex/appendices/appendix_policy_provenance.tex",
        "",
        "{\\small\n\\raggedright\n",
        "\n\\begin{enumerate}",
        "\\par\n}\n",
    ),
    (
        "latex/appendices/appendix_policy_provenance.tex",
        "\\begin{enumerate}\n",
        "\\small\n\\raggedright\n",
        "\\item \\texttt{agentprune}",
        "",
    ),
    (
        "latex/appendices/appendix_analysis_protocol.tex",
        "never increase degrees of freedom.\n\n",
        "  {\\raggedright\n",
        "\n  \\item[Policy eligibility and oracle.]",
        "  \\par\n  }\n",
    ),
    (
        "latex/appendices/appendix_analysis_protocol.tex",
        "  source/version commitments. \\end{quote}\n",
        "  {\\raggedright\n",
        "\n  The retrospective oracle is excluded",
        "  \\par\n  }\n",
    ),
    (
        "latex/appendices/appendix_analysis_protocol.tex",
        "  \\item[Empty result shells.] ",
        "{\\raggedright\n",
        "\n  \\item[Blocked evidence markers.]",
        "  \\par\n  }\n",
    ),
    (
        "latex/appendices/appendix_analysis_protocol.tex",
        "  \\item[Blocked evidence markers.]\n",
        "  {\\raggedright\n",
        "\n  \\item[Nonclaims and status.]",
        "  \\par\n  }\n",
    ),
)
_UNDERFULL_RAGGEDRIGHT_COUNTS = {
    "latex/appendices/appendix_analysis_protocol.tex": 5,
    "latex/appendices/appendix_claims.tex": 0,
    "latex/appendices/appendix_policy_provenance.tex": 2,
    "latex/appendices/appendix_reviewer_attacks.tex": 0,
    "latex/appendices/appendix_theory.tex": 0,
    "latex/main.tex": 1,
    "latex/sections/01_introduction.tex": 0,
    "latex/sections/02_related_work.tex": 0,
    "latex/sections/03_problem_formulation.tex": 0,
    "latex/sections/04_method.tex": 0,
    "latex/sections/05_supporting_theory.tex": 1,
    "latex/sections/06_experimental_design.tex": 1,
    "latex/sections/07_results.tex": 0,
    "latex/sections/08_limitations.tex": 0,
    "latex/sections/09_conclusion.tex": 0,
    "latex/sections/10_submission_statements.tex": 0,
}
_FORBIDDEN_LAYOUT_ESCAPE_PATTERNS = (
    r"\\sloppy\b",
    r"\\sloppypar\b|\\(?:begin|end)\s*\{\s*sloppypar\s*\}",
    r"\\emergencystretch\b",
    r"\\[hv]badness\b",
    r"\\[hv]fuzz\b",
    r"\\raggedbottom\b",
    r"\\enlargethispage\b",
    r"\\(?:resizebox|scalebox)\b",
    r"\\(?:fontsize|selectfont|fontspec|setmainfont)\b",
    r"\\(?:vspace|hspace|kern|mkern|vskip|hskip)\*?\s*(?:\{\s*)?-",
    r"\\(?:geometry|setlength|addtolength|paperwidth|paperheight|pdfpagewidth|"
    r"pdfpageheight|textwidth|textheight|oddsidemargin|evensidemargin|"
    r"topmargin|hoffset|voffset|headheight|footskip|columnsep|parskip|"
    r"topskip|marginparwidth|marginparsep|baselinestretch|linespread)\b",
)
_RA_NOVELTY_ITEM = (
    r"\textbf{Novelty (RA-NOV-01 and RA-NOV-02):} iCORE removes obligation-graph "
    "novelty, Eureka removes obligation-graph construction novelty, STAR "
    "removes execution-aware-routing novelty, and set-valued routing removes "
    "selector novelty; absent compliant E2/E3 kills ICLR-main novelty. "
    "Component prior art and theorem stitching remove theory-first language."
)
_CANONICAL_NOVELTY_SPANS = (
    "The intended contributions are deliberately conditional. They are "
    "receipt-bound instrumentation rather than first contributions: prior "
    "obligation-state and execution-aware representations are operationalized "
    "here for causal measurement.",
    _NOVELTY_BOUNDARY,
    *_DISPOSITIONS,
    "We claim neither the first graph, router, selector, verifier, conformal "
    "stopper, orthogonal score, regret algorithm, nor collaboration framework.",
    "The paper specifies and preregisters a prospective, falsifiable test for "
    "verified executed bundles under a fixed causal and equal-information protocol; "
    "it does not claim that routing, specialization, noncompliance correction, or "
    "orthogonal scores are new in isolation.",
    _METHOD_BOUNDARY,
    "CATS remains motivation and a comparator rather than a contribution "
    "(\\claim{C-CATS-ROLE}).",
    "\\item a claim/provenance discipline in which nonestimability and failed "
    "gates are first-class outcomes, with theory retained only as support.",
    "None of the four contributions asserts coordination value, policy "
    "superiority, cost savings, safety, deployment readiness, generalization, or "
    "acceptance.",
    "It does not license an as-if-complete treatment label, a fallback metric, or "
    "a new threshold.",
    "The version layer treats evaluator changes as new protocols.",
    "The present contributions are a receipt-bound evaluation contract, the "
    "bounded account of an immutable failed diagnostic, a prospective E1--E4 "
    "and JCI protocol, and a claim/provenance discipline that treats "
    "nonestimability as an outcome.",
    _RA_NOVELTY_ITEM,
)
_CANONICAL_FULL_NOVELTY_SPANS = (
    *_CANONICAL_NOVELTY_SPANS,
    "The standard same-information obstruction and structural estimator separation "
    "remain appendix boundaries, not headline novelty.",
    "It is not a new joint nuisance minimax lower bound.",
    "The scoped literature does not establish a standalone theory-first novelty claim.",
    "The paper tier is evaluation validity with supporting theory only.",
)
_CANONICAL_AUTHORIAL_NONCLAIM_SPANS = (
    "We therefore contribute an evaluation contract, a bounded account of the "
    "failed diagnostic, a prospective Architecture E1--E4 protocol with planned "
    "unpooled JCI replication, and a claim/provenance discipline in which receipt "
    "failure yields nonestimability.",
    "Our evaluation contract keeps four identities separate: requested action, "
    "verified complete-bundle execution, current terminal assessment, and scorer "
    "final-key set.",
    "Our current claim is narrower: assigned coordination, verified execution, "
    "terminal assessment, and scorer provenance must be bound before such a "
    "comparison is identified.",
    "OACS complementarity remains a prospective hypothesis.",
    "This section defines the policy interface, not an authenticated implementation "
    "or performance result.",
    "OACS, the raw router, and every ready member of the exact 22-policy family act "
    "on byte-equivalent projected opportunities.",
    "This manuscript makes a narrow proposition testable: coordination should be "
    "evaluated through residual obligations and the verified complete bundle that "
    "was actually executed, not through an assigned topology label alone.",
    "This manuscript does not claim confirmatory empirical reproducibility: no "
    "authenticated external source package, no signed site/target roster, no fresh "
    "V2 execution receipt, policy-decision bundle, or confirmatory result artifact "
    "is available in the current state.",
    "The conclusion is conditional by construction.",
    "We conclude that receipt-verified evaluability is a prerequisite for, not "
    "evidence of, coordination value.",
)
_AUTHORIAL_CLAIM_SUBJECT = re.compile(
    r"^(?:OACS\b|We\b|Our\b|This (?:approach|contribution|manuscript|method|paper|"
    r"representation|router|scaffold|selector|study|system|work)\b|The (?:approach|"
    r"contribution|method|novelty|originality|paper|representation|router|selector|"
    r"study|system|work)\b)",
    re.IGNORECASE,
)
_PROVENANCE_ATTRIBUTE = (
    r"(?:attribution|authentication|bibliograph\w*|certification|citation\w*|"
    r"doi|origin|provenance|reference|release|revision|roster|source\w*|"
    r"version\w*)"
)
_PROVENANCE_POSSESSION = re.compile(
    rf"\b(?:carries|carry|has|have)\b(?:\s+\S+){{0,4}}\s+\b{_PROVENANCE_ATTRIBUTE}\b",
    re.IGNORECASE,
)
_PROVENANCE_PASSIVE = re.compile(
    rf"\b(?:is|are)\b(?:\s+\S+){{0,3}}\s+\b(?:assigned|attributed|"
    rf"authenticated|certified|cited|documented|registered|sourced|verified)\b"
    rf"(?:\s+\S+){{0,4}}\s+\b{_PROVENANCE_ATTRIBUTE}\b|"
    rf"\b{_PROVENANCE_ATTRIBUTE}\b(?:\s+\S+){{0,4}}\s+\b(?:is|are)\b(?:\s+\S+){{0,2}}"
    rf"\b(?:assigned|attributed|authenticated|certified|cited|complete|current|"
    rf"documented|official|registered|sourced|verified)\b",
    re.IGNORECASE,
)
_FORBIDDEN_POSITIVES = (
    "first obligation graph",
    "novel obligation graph",
    "first execution-aware router",
    "novel execution-aware router",
    "first set-valued selector",
    "novel set-valued selector",
    "first orthogonal remainder",
    "E1 predictive improvement observed",
    "E1 accuracy = 0.80",
    "E2 causal mechanism established",
    "E2 effect estimate = 0.20",
    "E3 policy superiority shown",
    "E3 regret reduction = 0.20",
    "E4 deployment gain = 0.20",
    "design-lock PASS obtained",
    "external source authority authenticated",
    "22-policy roster authenticated",
    "22-policy roster verified",
    "power target achieved",
    "actual cost reduced",
    "safety established",
    "cross-domain generalization established",
    "empirical execution complete",
    "empirical results available",
    "submission ready",
    "acceptance ready",
    "PDF verified",
)
_POLICY_IDS = (
    "agentprune",
    "agora",
    "always_all_specialists",
    "automix",
    "bicsrouter",
    "conformal_thinking",
    "cost_aware_protocol_routing",
    "difficulty_confidence",
    "fixed_topology",
    "gptswarm",
    "graphplanner",
    "masrouter",
    "matched_compute_self_agent_scaling",
    "random_admissible_action",
    "rirs_talk_to_right_specialists",
    "routellm",
    "self_resource_allocation",
    "separated_router_stopper",
    "solo",
    "verimap",
    "vmao",
    "zooter_adaptation",
)
_POLICY_PROVENANCE_ROWS = (
    (
        "agentprune",
        "published_method",
        "zhang2025agentprune",
        "AgentPrune / Cut the Crap communication-pruning family; adapter execution remains blocked pending authenticated roster",
        "blocked_pending_authenticated_roster",
    ),
    (
        "agora",
        "protocol_defined_comparator",
        None,
        "inputs=frozen public packet, capability and cost cards, action menu, and admissibility; action_choice=maximum positive declared capability-minus-cost surplus; stopping=STOP only when the hard terminal gate passes and no surplus is positive, otherwise SOLO_SYNTHESIS; cost=all attempted selector, specialist, retry, verifier, and synthesis compute; inadmissibility=exclude the action before bidding; ties=byte-ordinal action ID; synthesis=the common bounded synthesizer after the selected specialist",
        "blocked_pending_authenticated_roster",
    ),
    (
        "always_all_specialists",
        "protocol_defined_comparator",
        None,
        "inputs=frozen public packet, complete action menu, costs, and admissibility; action_choice=invoke every admissible specialist exactly once in byte-ordinal action order; stopping=terminate after the common synthesizer, using SOLO_SYNTHESIS when no specialist is admissible; cost=all specialist, retry, verifier, and synthesis compute; inadmissibility=skip only actions masked before execution; ties=byte-ordinal action ID; synthesis=one common bounded synthesis over all retained specialist outputs",
        "blocked_pending_authenticated_roster",
    ),
    (
        "automix",
        "published_method",
        "aggarwal2024automix",
        "AutoMix confidence- and cost-aware model routing; adapter execution remains blocked pending authenticated roster",
        "blocked_pending_authenticated_roster",
    ),
    (
        "bicsrouter",
        "published_method",
        "keyu2026bicsrouter",
        "BiCSRouter single-agent versus multi-agent cross-system routing; adapter execution remains blocked pending authenticated roster",
        "blocked_pending_authenticated_roster",
    ),
    (
        "conformal_thinking",
        "published_method",
        "wang2026conformalthinking",
        "Conformal Thinking risk-controlled compute and stopping; adapter execution remains blocked pending authenticated roster",
        "blocked_pending_authenticated_roster",
    ),
    (
        "cost_aware_protocol_routing",
        "published_method",
        "yang2026costawareprotocol",
        "Cost-Aware Protocol Routing across fixed collaboration protocols; adapter execution remains blocked pending authenticated roster",
        "blocked_pending_authenticated_roster",
    ),
    (
        "difficulty_confidence",
        "protocol_defined_comparator",
        None,
        "inputs=frozen difficulty and confidence features plus action menu, costs, and admissibility only; action_choice=frozen multiclass learner with the common learner class, capacity, split, and tuning budget; stopping=frozen STOP threshold learned without residual-obligation or capability-profile features; cost=all router, specialist, retry, verifier, and synthesis compute; inadmissibility=mask before prediction and fall back to SOLO_SYNTHESIS if no predicted specialist remains; ties=byte-ordinal action ID; synthesis=the common bounded synthesizer",
        "blocked_pending_authenticated_roster",
    ),
    (
        "fixed_topology",
        "protocol_defined_comparator",
        None,
        "inputs=frozen public packet and one topology selected on the development split before evaluation; action_choice=the same topology and specialist order for every evaluation case; stopping=the topology's predeclared terminal step with no case-adaptive early exit; cost=all topology, retry, verifier, and synthesis compute; inadmissibility=fall back to SOLO_SYNTHESIS if a required topology action is masked; ties=byte-ordinal topology ID during development selection; synthesis=the common bounded synthesizer",
        "blocked_pending_authenticated_roster",
    ),
    (
        "gptswarm",
        "published_method",
        "zhuge2024gptswarm",
        "GPTSwarm language-agent graph optimization; adapter execution remains blocked pending authenticated roster",
        "blocked_pending_authenticated_roster",
    ),
    (
        "graphplanner",
        "published_method",
        "feng2026graphplanner",
        "GraphPlanner graph-memory agentic routing; adapter execution remains blocked pending authenticated roster",
        "blocked_pending_authenticated_roster",
    ),
    (
        "masrouter",
        "published_method",
        "yue2025masrouter",
        "MasRouter collaboration-mode, role, and model routing; adapter execution remains blocked pending authenticated roster",
        "blocked_pending_authenticated_roster",
    ),
    (
        "matched_compute_self_agent_scaling",
        "protocol_defined_comparator",
        None,
        "inputs=frozen public packet and the case-level complete-compute ceiling; action_choice=independent solo-agent samples until the predeclared ceiling without specialist packets; stopping=the frozen sample count or compute ceiling, whichever occurs first; cost=all solo samples, retries, verifier, aggregation, and synthesis compute; inadmissibility=specialist actions are never eligible; ties=byte-ordinal normalized candidate output; synthesis=the common bounded synthesizer over the frozen self-agent sample set",
        "blocked_pending_authenticated_roster",
    ),
    (
        "random_admissible_action",
        "protocol_defined_comparator",
        None,
        "inputs=complete action menu, costs, admissibility mask, and frozen randomization seed only; action_choice=uniform draw over currently admissible actions; stopping=terminate immediately when STOP is drawn; cost=all selected action, retry, verifier, and synthesis compute; inadmissibility=exclude before the draw and use SOLO_SYNTHESIS if the eligible set is empty; ties=the frozen randomization stream; synthesis=the common bounded synthesizer after any non-STOP draw",
        "blocked_pending_authenticated_roster",
    ),
    (
        "rirs_talk_to_right_specialists",
        "published_method",
        "li2025rirs",
        "RIRS / Talk to Right Specialists iterative specialist routing; adapter execution remains blocked pending authenticated roster",
        "blocked_pending_authenticated_roster",
    ),
    (
        "routellm",
        "published_method",
        "ong2025routellm",
        "RouteLLM preference-data model routing; adapter execution remains blocked pending authenticated roster",
        "blocked_pending_authenticated_roster",
    ),
    (
        "self_resource_allocation",
        "published_method",
        "amayuelas2025selfresource",
        "Self-Resource Allocation planner/orchestrator family; adapter execution remains blocked pending authenticated roster",
        "blocked_pending_authenticated_roster",
    ),
    (
        "separated_router_stopper",
        "protocol_defined_comparator",
        None,
        "inputs=the full parity public packet, capability table, costs, action menu, and admissibility; action_choice=a frozen non-STOP router trained separately from the stopper; stopping=a separately trained binary stopper evaluated before router execution; cost=both models plus all selected action, retry, verifier, and synthesis compute; inadmissibility=mask before routing and fall back to SOLO_SYNTHESIS if no routed action remains; ties=byte-ordinal action ID; synthesis=the common bounded synthesizer",
        "blocked_pending_authenticated_roster",
    ),
    (
        "solo",
        "protocol_defined_comparator",
        None,
        "inputs=frozen public packet only; action_choice=SOLO_SYNTHESIS exactly once; stopping=terminate after that bounded synthesis; cost=all solo, retry, and verifier compute; inadmissibility=no specialist action is eligible; ties=not applicable; synthesis=the common bounded synthesizer is the sole generation path",
        "blocked_pending_authenticated_roster",
    ),
    (
        "verimap",
        "published_method",
        "xu2026verimap",
        "VeriMAP verification-aware multi-agent planning; adapter execution remains blocked pending authenticated roster",
        "blocked_pending_authenticated_roster",
    ),
    (
        "vmao",
        "published_method",
        "zhang2026vmao",
        "VMAO plan-execute-verify-replan orchestration; adapter execution remains blocked pending authenticated roster",
        "blocked_pending_authenticated_roster",
    ),
    (
        "zooter_adaptation",
        "published_method_adaptation",
        "lu2024zooter",
        "OACS-compatible adaptation of ZOOTER reward-guided model routing; adapter execution remains blocked pending authenticated roster",
        "blocked_pending_authenticated_roster",
    ),
)
_ATTACK_IDS = (
    "RA-NOV-01",
    "RA-NOV-02",
    "RA-ID-01",
    "RA-ID-02",
    "RA-EXEC-01",
    "RA-EXEC-02",
    "RA-ONT-01",
    "RA-ONT-02",
    "RA-PAR-01",
    "RA-PAR-02",
    "RA-BASE-01",
    "RA-BASE-02",
    "RA-ORACLE-01",
    "RA-ORACLE-02",
    "RA-POWER-01",
    "RA-POWER-02",
    "RA-COST-01",
    "RA-COST-02",
    "RA-KILL-01",
    "RA-KILL-02",
    "RA-THEORY-01",
    "RA-THEORY-02",
    "RA-PROV-01",
    "RA-PROV-02",
)
_EXPECTED_MANUSCRIPT_TITLE = (
    "Planned Is Not Executed: Receipt-Bound Evaluation of Multi-Agent Coordination"
)
_TITLE_LINE_BREAK = r"\\"
_EXPECTED_MANUSCRIPT_TITLE_TEX = (
    r"Planned Is Not Executed: Receipt-Bound\\Evaluation of Multi-Agent Coordination"
)
_EXPECTED_EVALUATION_IDENTITIES = (
    "requested action",
    "verified complete-bundle execution",
    "current terminal assessment",
    "scorer final-key set",
)
_FROZEN_DIAGNOSTIC_PARAGRAPH = (
    "The frozen Architecture development diagnostic completed execution and "
    "artifact closure but failed its prespecified terminal-reliability gate. A "
    "later public-synthetic audit exposed a mismatch between cumulative provenance "
    "and current terminal assessment. The frozen no-rescore rule leaves the V1 "
    "result unchanged. It therefore estimates neither OACS benefit nor harm and "
    "provides no evidence about the corrected V2 evaluator. Its narrower role is "
    "to document failed evaluability and motivate fresh, versioned evidence."
)
_REQUIRED_EVALUATION_VALIDITY_SPANS = (
    "A completed orchestration trace is not an identified coordination treatment.",
    "failed its prespecified terminal-reliability gate",
    "The frozen no-rescore rule leaves the V1 result unchanged.",
    "V2 is prospective.",
    "It therefore estimates neither OACS benefit nor harm",
    "Receipt failure makes the corresponding estimand nonestimable.",
)
_AUTHORIAL_ATTACK_FRAMING = re.compile(
    r"^\s*(?:(?:a|an|the)\s+)?(?:forbidden|invalid|rejected|disallowed)\s+"
    r"(?:claim|interpretation|assertion|reading)\b|"
    r"\b(?:forbidden|invalid|rejected|disallowed)\s+"
    r"(?:claim|interpretation|assertion|reading)\s*[.!?]?\s*$",
    re.I,
)
_AUTHORIAL_EXPLICIT_NEGATION = re.compile(
    r"\b(?:is|are|was|were|has|have|had|do|does|did|can|could|should|would|"
    r"may|might|must|will)\s+not\b|\b(?:cannot|can't|never)\b|"
    r"^\s*(?:no|none)\b",
    re.I,
)
_AUTHORIAL_NEGATION_TOKEN = re.compile(
    r"\b(?:not|never|cannot|no|none)\b|can't",
    re.I,
)
_AUTHORIAL_UNSAFE_NEGATION_STRUCTURE = re.compile(
    r"[,;:]|\b(?:although|and|because|but|except|however|nevertheless|"
    r"nonetheless|not only|not just|not merely|or|provided|so|that|though|"
    r"unless|whereas|while|yet)\b",
    re.I,
)
_CANONICAL_AUTHORIAL_SENTENCE_COUNT = 507
_CANONICAL_AUTHORIAL_SENTENCE_MANIFEST_SHA256 = (
    "A57AE2A0D52B1F224F9A16BD73F9F7CF4BD234CFBAE48D19B03B05691BBDE780"
)
_CLAIM_ROWS = (
    ("C-THESIS", "structural", "prospective complete-bundle hypothesis"),
    ("C-ARCH-FLAGSHIP", "structural", "prospective Architecture stress test"),
    ("C-JCI-REPLICATION", "structural", "planned unpooled replication"),
    ("C-CATS-ROLE", "structural", "motivation and comparator"),
    ("C-E1-PREDICTION", "blocked", "predictive diagnostic"),
    ("C-E2-ARCH-MECHANISM", "blocked", "Architecture randomized mechanism"),
    ("C-E2-JCI-MECHANISM", "blocked", "JCI randomized mechanism"),
    ("C-E3-ARCH-POLICY", "blocked", "Architecture policy consequence"),
    ("C-E3-JCI-POLICY", "blocked", "JCI policy consequence"),
    ("C-ORACLE-DESCRIPTIVE", "structural", "post-outcome upper bound"),
    ("C-E4-DEPLOYMENT", "blocked", "fresh downstream question"),
    ("C-THEORY-B1-IDENTITY", "ready", "conditional identity"),
    ("C-THEORY-B2-CONFIDENCE", "ready", "conditional sparse radius"),
    ("C-THEORY-B3-BOUNDARY", "ready", "first-order decision boundary"),
    ("C-THEORY-B4-STANDARD-LB", "ready", "standard obstruction"),
    ("C-THEORY-B5-ESTIMATOR", "ready", "estimator separation"),
    ("C-THEORY-REGRET", "killed", "no cumulative-regret theorem"),
    ("C-THEORY-JOINT-MINIMAX", "killed", "no joint-minimax theorem"),
    ("C-THEORY-POLICY-SUPERIOR", "killed", "no policy-superiority theorem"),
    ("C-COST", "blocked", "actual cost only"),
    ("C-SAFETY", "blocked", "separate safety evidence"),
    ("C-GENERALIZATION", "blocked", "external-validity evidence"),
    ("C-DEV-DIAGNOSTIC", "ready", "immutable failed development diagnostic"),
)
_RESULTS_SLOT_IDS = (
    "C-E1-PREDICTION",
    "C-E2-ARCH-MECHANISM",
    "C-E2-JCI-MECHANISM",
    "C-E3-ARCH-POLICY",
    "C-E3-JCI-POLICY",
    "C-E4-DEPLOYMENT",
    "C-COST",
    "C-SAFETY",
    "C-GENERALIZATION",
)


def _strip_tex_comments(text: str) -> str:
    output = []
    for line in text.splitlines(keepends=True):
        newline = "\n" if line.endswith("\n") else ""
        content = line[:-1] if newline else line
        stop = len(content)
        for index, character in enumerate(content):
            if character != "%":
                continue
            slash_count = 0
            cursor = index - 1
            while cursor >= 0 and content[cursor] == "\\":
                slash_count += 1
                cursor -= 1
            if slash_count % 2 == 0:
                stop = index
                break
        output.append(content[:stop] + newline)
    return "".join(output)


def _lossless_active_tex(text: str) -> str:
    """Strip true TeX comments while preserving every remaining active byte."""
    output = []
    for line in text.splitlines(keepends=True):
        stop = len(line)
        for index, character in enumerate(line):
            if character != "%":
                continue
            slash_count = 0
            cursor = index - 1
            while cursor >= 0 and line[cursor] == "\\":
                slash_count += 1
                cursor -= 1
            if slash_count % 2 == 0:
                stop = index
                break
        output.append(line[:stop])
    active = "".join(output)
    if "^^" in active:
        raise PaperLatexVerificationError("source_grammar_invalid")
    return active


def _balanced_argument(text: str, start: int) -> tuple[str, int]:
    if start >= len(text) or text[start] != "{":
        raise PaperLatexVerificationError("source_grammar_invalid")
    depth = 1
    cursor = start + 1
    while cursor < len(text) and depth:
        if text[cursor] == "\\":
            cursor += 2
            continue
        if text[cursor] == "{":
            depth += 1
        elif text[cursor] == "}":
            depth -= 1
        cursor += 1
    if depth:
        raise PaperLatexVerificationError("source_grammar_invalid")
    return text[start + 1 : cursor - 1], cursor


def _scan_tex_document(
    text: str,
    *,
    allowed_commands: set[str],
    allowed_environments: tuple[str, ...],
) -> dict[str, tuple[str, ...]]:
    active = _strip_tex_comments(text)
    if "^^" in active:
        raise PaperLatexVerificationError("source_grammar_invalid")
    captures: dict[str, list[str]] = {}
    environment_stack: list[str] = []
    brace_depth = 0
    math_mode = False
    cursor = 0
    while cursor < len(active):
        character = active[cursor]
        if character == "\\":
            if cursor + 1 >= len(active):
                raise PaperLatexVerificationError("source_grammar_invalid")
            next_character = active[cursor + 1]
            if next_character.isalpha():
                end = cursor + 2
                while end < len(active) and active[end].isalpha():
                    end += 1
                command = active[cursor + 1 : end]
                if (
                    command not in allowed_commands
                    or command not in _COMMAND_SIGNATURES
                ):
                    raise PaperLatexVerificationError("source_grammar_invalid")
                arity, permits_empty_delimiter, allowed_suffixes = _COMMAND_SIGNATURES[
                    command
                ]
            else:
                command = next_character
                end = cursor + 2
                if command not in _CONTROL_SYMBOL_SIGNATURES:
                    raise PaperLatexVerificationError("source_grammar_invalid")
                arity, permits_empty_delimiter, allowed_suffixes = (
                    _CONTROL_SYMBOL_SIGNATURES[command]
                )
            suffix_was_consumed = False
            argument_start = end
            while argument_start < len(active) and active[argument_start] in " \t\n":
                argument_start += 1
            has_argument = (
                argument_start < len(active) and active[argument_start] == "{"
            )
            if arity == 1 and not has_argument:
                raise PaperLatexVerificationError("source_grammar_invalid")
            if has_argument:
                argument, argument_end = _balanced_argument(active, argument_start)
                if arity == 0 and (not permits_empty_delimiter or argument):
                    raise PaperLatexVerificationError("source_grammar_invalid")
                captures.setdefault(command, []).append(argument)
                if command == "begin":
                    environment = argument.strip()
                    if (
                        environment not in allowed_environments
                        or environment != argument
                    ):
                        raise PaperLatexVerificationError("source_grammar_invalid")
                    environment_stack.append(environment)
                elif command == "end":
                    environment = argument.strip()
                    if (
                        environment not in allowed_environments
                        or not environment_stack
                        or environment_stack.pop() != environment
                    ):
                        raise PaperLatexVerificationError("source_grammar_invalid")
                suffix = allowed_suffixes.get(argument)
                suffix_end = argument_end
                if suffix is not None and active.startswith(suffix, suffix_end):
                    suffix_end += len(suffix)
                    suffix_was_consumed = True
                modifier_start = suffix_end
            else:
                suffix = allowed_suffixes.get("")
                suffix_end = end
                if suffix is not None and active.startswith(suffix, suffix_end):
                    suffix_end += len(suffix)
                    suffix_was_consumed = True
                modifier_start = suffix_end
            if (
                suffix_was_consumed
                and suffix_end + 1 < len(active)
                and active[suffix_end] == "\\"
                and active[suffix_end + 1] in _CONTROL_SYMBOL_SIGNATURES
            ):
                raise PaperLatexVerificationError("source_grammar_invalid")
            while modifier_start < len(active) and active[modifier_start] in " \t\n":
                modifier_start += 1
            reviewed_related_scope = (
                command == "end"
                and argument == "quote"
                and active.startswith("\n{\\raggedright\n", argument_end)
            )
            if (
                arity == 1
                and modifier_start < len(active)
                and active[modifier_start] == "{"
                and not reviewed_related_scope
            ):
                raise PaperLatexVerificationError("source_grammar_invalid")
            if modifier_start < len(active) and active[modifier_start] in "*[":
                raise PaperLatexVerificationError("source_grammar_invalid")
            cursor = end
            continue
        if character == "$":
            math_mode = not math_mode
            cursor += 1
            continue
        if character == "_" and brace_depth == 0 and not math_mode:
            raise PaperLatexVerificationError("source_grammar_invalid")
        if character == "{":
            brace_depth += 1
        elif character == "}":
            brace_depth -= 1
            if brace_depth < 0:
                raise PaperLatexVerificationError("source_grammar_invalid")
        cursor += 1
    if brace_depth or math_mode or environment_stack:
        raise PaperLatexVerificationError("source_grammar_invalid")
    observed_environments = tuple(captures.get("begin", ()))
    if observed_environments != allowed_environments:
        raise PaperLatexVerificationError("source_grammar_invalid")
    return {command: tuple(arguments) for command, arguments in captures.items()}


def _extract_literal_arguments(
    text: str, commands: tuple[str, ...]
) -> dict[str, tuple[str, ...]]:
    active = _strip_tex_comments(text)
    found: dict[str, list[str]] = {command: [] for command in commands}
    pattern = re.compile(
        r"\\(" + "|".join(re.escape(command) for command in commands) + r")(?=\s*\{)"
    )
    for match in pattern.finditer(active):
        start = match.end()
        while start < len(active) and active[start] in " \t\n":
            start += 1
        argument, _end = _balanced_argument(active, start)
        found[match.group(1)].append(argument)
    return {command: tuple(arguments) for command, arguments in found.items()}


def _parse_policy_provenance_registry(
    text: str,
) -> tuple[tuple[str, str, str | None, str, str], ...]:
    """Parse the exact reviewed enumerate subset or fail source grammar."""

    active = _strip_tex_comments(text)
    math_mode = False
    cursor = 0
    while cursor < len(active):
        character = active[cursor]
        if character == "\\":
            cursor += 2
            continue
        if character == "$":
            math_mode = not math_mode
        elif character == "_" and not math_mode:
            raise PaperLatexVerificationError("source_grammar_invalid")
        cursor += 1

    scan = _scan_tex_document(
        text,
        allowed_commands={
            "begin",
            "citep",
            "end",
            "item",
            "par",
            "raggedright",
            "section",
            "small",
            "textbf",
            "texttt",
        },
        allowed_environments=("enumerate",),
    )
    literals = _extract_literal_arguments(
        text,
        ("begin", "citep", "end", "section", "textbf", "texttt"),
    )
    if (
        scan.get("begin") != ("enumerate",)
        or scan.get("end") != ("enumerate",)
        or literals["begin"] != ("enumerate",)
        or literals["end"] != ("enumerate",)
        or literals["section"]
        != ("Policy provenance and protocol-defined comparators",)
    ):
        raise PaperLatexVerificationError("source_grammar_invalid")

    begin = r"\begin{enumerate}"
    end = r"\end{enumerate}"
    if active.count(begin) != 1 or active.count(end) != 1:
        raise PaperLatexVerificationError("source_grammar_invalid")
    begin_index = active.index(begin) + len(begin)
    end_index = active.index(end, begin_index)
    item_positions = []
    item_cursor = 0
    while True:
        item_position = active.find(r"\item", item_cursor)
        if item_position < 0:
            break
        item_end = item_position + len(r"\item")
        if item_end == len(active) or not active[item_end].isalpha():
            item_positions.append(item_position)
        item_cursor = item_end
    if any(
        item_position < begin_index or item_position >= end_index
        for item_position in item_positions
    ):
        raise PaperLatexVerificationError("source_grammar_invalid")
    if active[end_index + len(end) :].strip():
        raise PaperLatexVerificationError("source_grammar_invalid")
    if (
        active.count(_BIBLIOGRAPHIC_PROVENANCE_STATUS) != 1
        or active.count(_IMPLEMENTATION_AUTHENTICATION_STATUS) != 1
    ):
        raise PaperLatexVerificationError("scientific_boundary_invalid")

    body = active[begin_index:end_index]
    expected_layout_prefix = "\n\\small\n\\raggedright\n"
    if not body.startswith(expected_layout_prefix):
        raise PaperLatexVerificationError("source_grammar_invalid")
    body = body[len(expected_layout_prefix) :]
    pieces = body.split(r"\item")
    if pieces[0].strip() or len(pieces) != len(_POLICY_PROVENANCE_ROWS) + 1:
        raise PaperLatexVerificationError("source_grammar_invalid")

    def skip_space(value: str, position: int) -> int:
        while position < len(value) and value[position] in " \t\n":
            position += 1
        return position

    def take_literal(value: str, position: int, literal: str) -> int:
        position = skip_space(value, position)
        if not value.startswith(literal, position):
            raise PaperLatexVerificationError("source_grammar_invalid")
        return position + len(literal)

    def take_command(value: str, position: int, command: str) -> tuple[str, int]:
        position = take_literal(value, position, "\\" + command)
        position = skip_space(value, position)
        argument, position = _balanced_argument(value, position)
        return argument, position

    rows: list[tuple[str, str, str | None, str, str]] = []
    for piece in pieces[1:]:
        item = piece.strip()
        captured = _extract_literal_arguments(
            item,
            ("citep", "textbf", "texttt"),
        )
        position = 0
        policy, position = take_command(item, position, "texttt")
        position = take_literal(item, position, ".")
        label, position = take_command(item, position, "textbf")
        if label != r"provenance\_class":
            raise PaperLatexVerificationError("source_grammar_invalid")
        position = take_literal(item, position, "=")
        kind, position = take_command(item, position, "texttt")
        position = take_literal(item, position, ";")
        label, position = take_command(item, position, "textbf")
        if label != r"public\_reference":
            raise PaperLatexVerificationError("source_grammar_invalid")
        position = take_literal(item, position, "=")
        position = skip_space(item, position)
        if item.startswith(r"\citep", position):
            reference, position = take_command(item, position, "citep")
            if not reference or any(
                not ("a" <= character <= "z" or "0" <= character <= "9")
                for character in reference
            ):
                raise PaperLatexVerificationError("source_grammar_invalid")
        elif item.startswith(r"\texttt", position):
            none_value, position = take_command(item, position, "texttt")
            if none_value != "none":
                raise PaperLatexVerificationError("source_grammar_invalid")
            reference = None
        else:
            raise PaperLatexVerificationError("source_grammar_invalid")
        position = take_literal(item, position, ";")
        label, position = take_command(item, position, "textbf")
        if label != r"protocol\_role":
            raise PaperLatexVerificationError("source_grammar_invalid")
        position = take_literal(item, position, "=")
        status_marker = r"\textbf{implementation\_authentication\_status}"
        marker_index = item.find(status_marker, position)
        if marker_index < 0:
            raise PaperLatexVerificationError("source_grammar_invalid")
        role_source = item[position:marker_index].rstrip()
        if not role_source.endswith(";"):
            raise PaperLatexVerificationError("source_grammar_invalid")
        role_source = role_source[:-1]
        position = marker_index
        label, position = take_command(item, position, "textbf")
        if label != r"implementation\_authentication\_status":
            raise PaperLatexVerificationError("source_grammar_invalid")
        position = take_literal(item, position, "=")
        status, position = take_command(item, position, "texttt")
        position = take_literal(item, position, ".")
        if item[skip_space(item, position) :]:
            raise PaperLatexVerificationError("source_grammar_invalid")

        expected_textbf = (
            r"provenance\_class",
            r"public\_reference",
            r"protocol\_role",
            r"implementation\_authentication\_status",
        )
        if captured["textbf"] != expected_textbf:
            raise PaperLatexVerificationError("source_grammar_invalid")
        if reference is None:
            expected_texttt = (policy, kind, "none", status)
            expected_citep: tuple[str, ...] = ()
        else:
            expected_texttt = (policy, kind, status)
            expected_citep = (reference,)
        if captured["texttt"] != expected_texttt or captured["citep"] != expected_citep:
            raise PaperLatexVerificationError("source_grammar_invalid")

        role = re.sub(r"[ \t\r\n\f\v]+", " ", role_source).strip()
        policy, kind, role, status = (
            value.replace(r"\_", "_") for value in (policy, kind, role, status)
        )
        rows.append((policy, kind, reference, role, status))
    parsed = tuple(rows)
    if parsed != _POLICY_PROVENANCE_ROWS:
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    return parsed


def _parse_bibtex(text: str) -> tuple[str, ...]:
    active = _strip_tex_comments(text)
    if "#" in active or re.search(
        r"@(string|preamble|comment)\s*[{(]", active, re.IGNORECASE
    ):
        raise PaperLatexVerificationError("source_grammar_invalid")
    keys = []
    cursor = 0
    while True:
        match = re.search(r"@([A-Za-z]+)\{([^,{}]+),", active[cursor:])
        if match is None:
            break
        key = match.group(2)
        entry_start = cursor + match.start() + match.group(0).index("{")
        _body, entry_end = _balanced_argument(active, entry_start)
        keys.append(key)
        cursor = entry_end
    if len(keys) != len(set(key.lower() for key in keys)):
        raise PaperLatexVerificationError("source_grammar_invalid")
    return tuple(keys)


def _normalize_active(text: str, relative: str) -> str:
    if relative.endswith(".md"):
        active = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    else:
        active = _strip_tex_comments(text)
    if relative.endswith(".tex"):
        active = active.replace(r"\%", " ")
    return re.sub(r"[ \t\r\n\f\v]+", " ", active).strip()


def _extract_normalized_manuscript_title(text: str) -> str:
    """Extract the one title and render its reviewed TeX line break as whitespace."""

    active = _lossless_active_tex(text)
    titles = tuple(re.findall(r"\\title\s*\{([^{}]*)\}", active, re.DOTALL))
    if len(titles) != 1:
        raise PaperLatexVerificationError("source_grammar_invalid")
    semantic = titles[0].replace(_TITLE_LINE_BREAK, " ")
    return re.sub(r"[ \t\r\n\f\v]+", " ", semantic).strip()


def _active_prose_manifest_sha256(active: dict[str, str]) -> str:
    lines = []
    for relative in _ACTIVE_PROSE_PATHS:
        active_prose = active[relative]
        if relative.endswith(".tex"):
            active_prose = re.sub(r"(\\[A-Za-z]+) +(?=\{)", r"\1", active_prose)
            active_prose = re.sub(r"([\{\[]) +", r"\1", active_prose)
            active_prose = re.sub(r" +([\}\]])", r"\1", active_prose)
        active_bytes = active_prose.encode("utf-8")
        digest = hashlib.sha256(active_bytes).hexdigest().upper()
        lines.append(f"{relative}\t{len(active_bytes)}\t{digest}\n")
    return hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()


def _rendered_boundary_text(text: str, relative: str) -> str:
    """Render the reviewed prose subset before structural boundary checks."""
    active = (
        re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
        if relative.endswith(".md")
        else _strip_tex_comments(text)
    )
    if relative == "latex/main.tex":
        active = active.replace(_TITLE_LINE_BREAK, " ")
    rendered = []
    cursor = 0
    prose_boundaries = {"begin", "end", "input", "item", "section"}
    while cursor < len(active):
        character = active[cursor]
        if character == "\\" and cursor + 1 < len(active):
            next_character = active[cursor + 1]
            if next_character.isalpha():
                cursor += 2
                start = cursor - 1
                while cursor < len(active) and active[cursor].isalpha():
                    cursor += 1
                command = active[start:cursor]
                if command in prose_boundaries:
                    while cursor < len(active) and active[cursor] in " \t\n":
                        cursor += 1
                    if cursor < len(active) and active[cursor] == "{":
                        _argument, cursor = _balanced_argument(active, cursor)
                    rendered.append(". ")
                continue
            rendered.append(
                "_"
                if next_character == "_"
                else ". "
                if next_character == "\\"
                else " "
            )
            cursor += 2
            continue
        if character not in "{}[]":
            rendered.append(character)
        cursor += 1
    return re.sub(r"[ \t\r\n\f\v]+", " ", "".join(rendered)).strip()


def _remove_exact_once(text: str, span: str) -> str:
    if text.count(span) != 1:
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    start = text.find(span)
    return text[:start] + text[start + len(span) :]


def _contains_provenance_assignment(rendered: str) -> bool:
    """Recognize attribution grammar independently of its asserted polarity."""
    return any(
        _PROVENANCE_POSSESSION.search(clause) or _PROVENANCE_PASSIVE.search(clause)
        for clause in re.split(r"(?<=[.!?])\s+", rendered)
    )


def _contains_unapproved_authorial_claim(rendered_closure: str) -> bool:
    """Permit only the reviewed exact authorial claim-bearing prose spans."""
    remainder = rendered_closure
    for source_span in (
        *_CANONICAL_FULL_NOVELTY_SPANS,
        *_CANONICAL_AUTHORIAL_NONCLAIM_SPANS,
    ):
        span = _rendered_boundary_text(source_span, ".tex")
        expected_count = 2 if source_span == _METHOD_BOUNDARY else 1
        if remainder.count(span) != expected_count:
            raise PaperLatexVerificationError("scientific_boundary_invalid")
        remainder = remainder.replace(span, "", expected_count)
    return any(
        _AUTHORIAL_CLAIM_SUBJECT.search(sentence.strip())
        for sentence in re.split(r"(?<=[.!?])\s+", remainder)
        if sentence.strip()
    )


def _validate_canonical_manuscript_tex(source_text: dict[str, str]) -> None:
    """Authenticate every active manuscript TeX source before heuristics."""
    tex_paths = tuple(
        relative for relative in _MANUSCRIPT_SOURCE_PATHS if relative.endswith(".tex")
    )
    if tuple(_CANONICAL_ACTIVE_MANUSCRIPT_TEX_SHA256) != tex_paths:
        raise PaperLatexVerificationError("source_identity_invalid")
    for relative, expected_digest in _CANONICAL_ACTIVE_MANUSCRIPT_TEX_SHA256.items():
        active = _lossless_active_tex(source_text[relative])
        observed_digest = hashlib.sha256(active.encode("utf-8")).hexdigest().upper()
        if observed_digest != expected_digest:
            reason_code = (
                "scientific_boundary_invalid"
                if relative == "latex/sections/10_submission_statements.tex"
                else "source_grammar_invalid"
            )
            raise PaperLatexVerificationError(reason_code)


def _validate_manuscript_anonymity(source_text: dict[str, str]) -> None:
    """Reject identifying channels in active manuscript TeX, never BibTeX."""
    forbidden_control = re.compile(
        r"\\(?:author|hypersetup|pdfinfo|pdfauthor|pdfcreator|pdfsubject|"
        r"thanks|affiliation|institute|email|orcid)\b",
        re.IGNORECASE,
    )
    forbidden_label = re.compile(
        r"(?im)(?:^|[;\n])\s*(?:pdf\s*)?(?:author|creator|affiliation|"
        r"funding|acknowledg(?:e)?ments?|orcid|researcherid|"
        r"scopus\s+author\s+id|isni)\s*[:=]",
    )
    acknowledgment_section = re.compile(
        r"\\section\*?\s*\{\s*acknowledg(?:e)?ments?\s*\}",
        re.IGNORECASE,
    )
    stable_identifier = re.compile(
        r"(?<!\d)\d{4}-\d{4}-\d{4}-[\dX](?:\d{3})?(?!\d)",
        re.IGNORECASE,
    )
    identifying_url = re.compile(r"https?://[^\s{}]+", re.IGNORECASE)
    anonymous_author = r"\author{Anonymous Authors}"
    for relative in _MANUSCRIPT_SOURCE_PATHS:
        if not relative.endswith(".tex"):
            continue
        active = _lossless_active_tex(source_text[relative])
        if relative == "latex/main.tex":
            active = active.replace(anonymous_author, "", 1)
        if (
            forbidden_control.search(active)
            or forbidden_label.search(active)
            or acknowledgment_section.search(active)
            or stable_identifier.search(active)
            or identifying_url.search(active)
        ):
            raise PaperLatexVerificationError("source_grammar_invalid")


def _validate_sap_e3_layout(source_text: dict[str, str]) -> None:
    """Require the two reviewed E3 definition pairs on separate aligned rows."""
    sap = _lossless_active_tex(
        source_text["latex/appendices/appendix_analysis_protocol.tex"]
    )
    start_marker = r"\item[E3 estimand and parity.]"
    end_marker = r"\item[Policy eligibility and oracle.]"
    if (
        sap.count(start_marker) != 1
        or sap.count(end_marker) != 1
        or any(sap.count(block) != 1 for block in _SAP_E3_ALIGNED_BLOCKS)
    ):
        raise PaperLatexVerificationError("source_grammar_invalid")
    start = sap.index(start_marker) + len(start_marker)
    end = sap.index(end_marker, start)
    e3_item = sap[start:end]
    if (
        e3_item.count(r"\begin{aligned}") != 2
        or e3_item.count(r"\end{aligned}") != 2
        or e3_item.count(r"\\") != 2
        or r"\qquad" in e3_item
    ):
        raise PaperLatexVerificationError("source_grammar_invalid")


def _validate_underfull_layout_scopes(source_text: dict[str, str]) -> None:
    """Allow only the nine reviewed local ragged-right corrections."""

    active_tex = {
        relative: _lossless_active_tex(source_text[relative])
        for relative in _MANUSCRIPT_SOURCE_PATHS
        if relative.endswith(".tex")
    }
    if tuple(_UNDERFULL_RAGGEDRIGHT_COUNTS) != tuple(active_tex):
        raise PaperLatexVerificationError("source_grammar_invalid")
    for relative, before, opening, after, closing in _UNDERFULL_LAYOUT_SCOPES:
        active = active_tex[relative]
        opening_is_exact = (
            active.count(before + opening) == 1
            if before
            else active.startswith(opening) and active.count(opening) == 1
        )
        if not opening_is_exact or active.count(closing + after) != 1:
            raise PaperLatexVerificationError("source_grammar_invalid")
    if any(
        active_tex[relative].count(r"\raggedright") != expected
        for relative, expected in _UNDERFULL_RAGGEDRIGHT_COUNTS.items()
    ):
        raise PaperLatexVerificationError("source_grammar_invalid")
    manuscript = "\n".join(active_tex.values())
    if any(
        re.search(pattern, manuscript, re.IGNORECASE)
        for pattern in _FORBIDDEN_LAYOUT_ESCAPE_PATTERNS
    ):
        raise PaperLatexVerificationError("source_grammar_invalid")


def _is_robust_authorial_negation(sentence: str) -> bool:
    """Accept a single-clause explicit negation without an affirmative escape."""

    return (
        _AUTHORIAL_EXPLICIT_NEGATION.search(sentence) is not None
        and len(tuple(_AUTHORIAL_NEGATION_TOKEN.finditer(sentence))) == 1
        and _AUTHORIAL_UNSAFE_NEGATION_STRUCTURE.search(sentence) is None
    )


def _authorial_sentence_manifest(
    source_text: dict[str, str],
) -> tuple[int, str]:
    """Bind every normalized non-exempt sentence in the authorial source closure."""

    manifest_lines: list[str] = []
    for relative in _MANUSCRIPT_SOURCE_PATHS:
        if relative == "latex/references.bib":
            continue
        rendered = _rendered_boundary_text(source_text[relative], relative)
        for sentence in re.split(r"(?<=[.!?])\s+", rendered):
            sentence = sentence.strip()
            if not sentence:
                continue
            if _AUTHORIAL_ATTACK_FRAMING.search(sentence) is not None:
                continue
            if _is_robust_authorial_negation(sentence):
                continue
            sentence_bytes = sentence.encode("utf-8")
            manifest_lines.append(
                f"{len(sentence_bytes)}\t"
                f"{hashlib.sha256(sentence_bytes).hexdigest().upper()}\n"
            )
    manifest_bytes = "".join(manifest_lines).encode("utf-8")
    return len(manifest_lines), hashlib.sha256(manifest_bytes).hexdigest().upper()


def _validate_evaluation_validity_semantics(source_text: dict[str, str]) -> None:
    """Reject scientific reinterpretation before byte-identity authentication."""

    active = {
        relative: _normalize_active(text, relative)
        for relative, text in source_text.items()
    }
    closure = " ".join(active[relative] for relative in _MANUSCRIPT_SOURCE_PATHS)
    main = active["latex/main.tex"]
    if _extract_normalized_manuscript_title(main) != _EXPECTED_MANUSCRIPT_TITLE:
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    if any(main.count(identity) != 1 for identity in _EXPECTED_EVALUATION_IDENTITIES):
        raise PaperLatexVerificationError("scientific_boundary_invalid")

    claims = active["latex/appendices/appendix_claims.tex"]
    claim_rows = tuple(
        (identifier, state.strip(), role.strip())
        for identifier, state, role in re.findall(
            r"\\claim\{([^}]+)\}\s*&\s*([^&]+?)\s*&\s*([^\\]+?)\\\\",
            claims,
        )
    )
    if claim_rows != _CLAIM_ROWS or "C-ACCEPTANCE" in claims:
        raise PaperLatexVerificationError("scientific_boundary_invalid")

    results = active["latex/sections/07_results.tex"]
    if results.count(_FROZEN_DIAGNOSTIC_PARAGRAPH) != 1:
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    if tuple(re.findall(r"\\blocked\{([^}]+)\}", results)) != _RESULTS_SLOT_IDS:
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    if any(span not in closure for span in _REQUIRED_EVALUATION_VALIDITY_SPANS):
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    if _authorial_sentence_manifest(source_text) != (
        _CANONICAL_AUTHORIAL_SENTENCE_COUNT,
        _CANONICAL_AUTHORIAL_SENTENCE_MANIFEST_SHA256,
    ):
        raise PaperLatexVerificationError("scientific_boundary_invalid")


def _validate_iclr2027_venue_overlay(source_text: dict[str, str]) -> None:
    """Validate the fixed official ICLR 2027 anonymous source overlay."""

    for relative, (allowed_commands, allowed_environments) in _EDITABLE_ROLES.items():
        _scan_tex_document(
            source_text[relative],
            allowed_commands=allowed_commands,
            allowed_environments=allowed_environments,
        )
    indirect_metadata_control = re.compile(
        r"\\(?:csname|endcsname|expandafter|(?:e|g|x)?def|let)\b",
        re.IGNORECASE,
    )
    if any(
        indirect_metadata_control.search(_lossless_active_tex(source_text[relative]))
        for relative in _MANUSCRIPT_SOURCE_PATHS
        if relative.endswith(".tex")
    ):
        raise PaperLatexVerificationError("source_grammar_invalid")
    _validate_manuscript_anonymity(source_text)
    _validate_sap_e3_layout(source_text)
    _validate_underfull_layout_scopes(source_text)
    main_active = _lossless_active_tex(source_text["latex/main.tex"])
    required_main_literals = (
        r"\documentclass{article}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage{iclr2027_conference,times}",
        rf"\title{{{_EXPECTED_MANUSCRIPT_TITLE_TEX}}}",
        r"\author{Anonymous Authors}",
        r"\input{sections/10_submission_statements}",
        r"\bibliographystyle{iclr2027_conference}",
        r"\bibliography{references}",
        r"\appendix",
    )
    if any(main_active.count(literal) != 1 for literal in required_main_literals):
        raise PaperLatexVerificationError("source_grammar_invalid")
    if len(re.findall(r"\\author\s*\{", main_active)) != 1:
        raise PaperLatexVerificationError("source_grammar_invalid")
    if (
        tuple(re.findall(r"\\hyphenation\s*\{[^{}]*\}", main_active))
        or main_active.count(_TITLE_LINE_BREAK) != 1
    ):
        raise PaperLatexVerificationError("source_grammar_invalid")
    forbidden_main_patterns = (
        r"\\(?:iclrfinalcopy|geometry|thanks|affiliation|email|orcid|"
        r"acknowledg[A-Za-z]*|textwidth|textheight|oddsidemargin|"
        r"evensidemargin|topmargin|baselinestretch|linespread)\b",
        r"\\usepackage\s*(?:\[[^][]*\]\s*)?\{geometry\}",
        r"\\usepackage\s*(?:\[[^][]*\]\s*)?\{fontspec\}",
        r"\\(?:setmainfont|ifxetex|ifluatex|ifpdftex|fontsize)\b",
        r"\\(?:renewcommand|def)\s*\{?\\rmdefault\}?",
        r"\\usepackage\s*\{natbib\}",
        r"\\bibliographystyle\s*\{plainnat\}",
        r"\\(?:include|includeonly|InputIfFileExists|@input)\b|"
        r"\\openin(?=\d|\s|=|$)",
    )
    if any(
        re.search(pattern, main_active, re.IGNORECASE)
        for pattern in forbidden_main_patterns
    ):
        raise PaperLatexVerificationError("source_grammar_invalid")

    fontenc = r"\usepackage[T1]{fontenc}"
    fontenc_calls = tuple(
        re.findall(
            r"\\usepackage\s*(?:\[[^][]*\]\s*)?\{fontenc\}",
            main_active,
        )
    )
    if (
        fontenc_calls != (fontenc,)
        or not main_active.startswith(
            r"\documentclass{article}" + "\n" + fontenc + "\n"
        )
        or main_active.index(fontenc)
        > main_active.index(r"\usepackage{iclr2027_conference,times}")
    ):
        raise PaperLatexVerificationError("source_grammar_invalid")

    conclusion_input = r"\input{sections/09_conclusion}"
    statement_input = r"\input{sections/10_submission_statements}"
    bibliography_style = r"\bibliographystyle{iclr2027_conference}"
    bibliography = r"\bibliography{references}"
    appendix = r"\appendix"
    appendix_inputs = (
        r"\input{appendices/appendix_theory}",
        r"\input{appendices/appendix_analysis_protocol}",
        r"\input{appendices/appendix_claims}",
        r"\input{appendices/appendix_reviewer_attacks}",
    )
    ordered_literals = (
        conclusion_input,
        statement_input,
        bibliography_style,
        bibliography,
        appendix,
        *appendix_inputs,
    )
    if any(main_active.count(literal) != 1 for literal in ordered_literals):
        raise PaperLatexVerificationError("source_grammar_invalid")
    indices = tuple(main_active.index(literal) for literal in ordered_literals)
    if indices != tuple(sorted(indices)):
        raise PaperLatexVerificationError("source_grammar_invalid")
    if main_active.index(r"\documentclass{article}") > main_active.index(fontenc):
        raise PaperLatexVerificationError("source_grammar_invalid")

    email_address = re.compile(
        r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@"
        r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![A-Za-z0-9.-])"
    )
    if any(
        email_address.search(_strip_tex_comments(source_text[relative]))
        for relative in _MANUSCRIPT_SOURCE_PATHS
        if relative.endswith(".tex")
    ):
        raise PaperLatexVerificationError("source_grammar_invalid")

    _validate_evaluation_validity_semantics(source_text)
    _validate_canonical_manuscript_tex(source_text)
    main_digest = hashlib.sha256(main_active.encode("utf-8")).hexdigest().upper()
    if main_digest != _CANONICAL_ACTIVE_MAIN_SHA256:
        raise PaperLatexVerificationError("source_grammar_invalid")

    statements = _lossless_active_tex(
        source_text["latex/sections/10_submission_statements.tex"]
    )
    statement_digest = hashlib.sha256(statements.encode("utf-8")).hexdigest().upper()
    if statement_digest != _CANONICAL_ACTIVE_STATEMENTS_SHA256:
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    if (
        statements.count(r"\section*{AI Use Statement}") != 1
        or statements.count(r"\section*{Reproducibility Statement}") != 1
    ):
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    required_statement_spans = (
        "research ideation and refinement of the residual-obligation hypothesis",
        "design, critique, and documentation of the E1--E4 evaluation program",
        "static manuscript-verification software and tests",
        "drafting, editing, and\nstructuring portions of the manuscript",
        "literature organization, comparison, and source discovery",
        "No generative-AI output is presented as authenticated empirical data",
        "no model output was generated or rescored for\nthis rewrite",
        "Submission remains blocked until all authors review",
        "claim-locked evaluation-validity manuscript",
        "does not claim confirmatory empirical reproducibility",
        "no authenticated external source package",
        "no signed site/target roster",
        "no fresh V2 execution receipt, policy-decision bundle, or confirmatory result\nartifact",
    )
    if any(statements.count(span) != 1 for span in required_statement_spans):
        raise PaperLatexVerificationError("scientific_boundary_invalid")

    active_manuscript = " ".join(
        _normalize_active(source_text[relative], relative)
        for relative in _MANUSCRIPT_SOURCE_PATHS
        if relative != "latex/references.bib"
    ).lower()
    forbidden_positive_phrases = (
        "submission-ready",
        "page-limit compliant",
        "pdf verified",
        "experiments were run",
        "results are reproducible",
        "accepted at iclr",
    )
    if any(phrase in active_manuscript for phrase in forbidden_positive_phrases):
        raise PaperLatexVerificationError("scientific_boundary_invalid")


def _validate_tex_bibliography_and_science(
    source_text: dict[str, str],
    source_bytes: dict[str, bytes],
) -> None:
    scans = {}
    for relative, (allowed_commands, allowed_environments) in _EDITABLE_ROLES.items():
        scans[relative] = _scan_tex_document(
            source_text[relative],
            allowed_commands=allowed_commands,
            allowed_environments=allowed_environments,
        )
    main_arguments = _extract_literal_arguments(
        source_text["latex/main.tex"],
        ("input", "label", "ref", "cite", "citet", "citep"),
    )
    if main_arguments["input"] != _MAIN_INPUTS:
        raise PaperLatexVerificationError("source_grammar_invalid")

    bibliography = source_text["latex/references.bib"]
    bibliography_keys = _parse_bibtex(bibliography)
    if bibliography_keys != _ALL_BIBLIOGRAPHY_KEYS:
        raise PaperLatexVerificationError("source_grammar_invalid")
    policy_rows = _parse_policy_provenance_registry(
        source_text["latex/appendices/appendix_policy_provenance.tex"]
    )
    for _policy, kind, reference, _role, _status in policy_rows:
        if kind == "protocol_defined_comparator":
            if reference is not None:
                raise PaperLatexVerificationError("scientific_boundary_invalid")
        elif reference is None or reference not in bibliography_keys:
            raise PaperLatexVerificationError("scientific_boundary_invalid")

    citations = []
    labels = []
    references = []
    for relative in _MANUSCRIPT_SOURCE_PATHS:
        if not relative.endswith(".tex"):
            continue
        arguments = _extract_literal_arguments(
            source_text[relative],
            ("cite", "citet", "citep", "label", "ref"),
        )
        for command in ("cite", "citet", "citep"):
            for argument in arguments[command]:
                citations.extend(key.strip() for key in argument.split(","))
        labels.extend(argument.strip() for argument in arguments["label"])
        references.extend(argument.strip() for argument in arguments["ref"])
    if (
        any(not key or key not in bibliography_keys for key in citations)
        or set(citations) != set(bibliography_keys)
        or len(labels) != len(set(labels))
        or any(reference not in labels for reference in references)
    ):
        raise PaperLatexVerificationError("source_grammar_invalid")

    _validate_iclr2027_venue_overlay(source_text)
    if (
        hashlib.sha256(source_bytes["latex/references.bib"][:1202]).hexdigest()
        != "10716dbd880c487e70a7cbd9fed4546a5f160d4b2126a4971943ca032b707659"
    ):
        raise PaperLatexVerificationError("source_grammar_invalid")
    if (
        hashlib.sha256(source_bytes["latex/references.bib"]).hexdigest()
        != "2a172632cab4467cb7feda55debfdc8eb2b6b646333a48a14b6a3e22c8cd8b00"
    ):
        raise PaperLatexVerificationError("source_grammar_invalid")

    active = {
        relative: _normalize_active(text, relative)
        for relative, text in source_text.items()
    }
    if _active_prose_manifest_sha256(active) != _ACTIVE_PROSE_MANIFEST_SHA256:
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    rendered = {
        relative: _rendered_boundary_text(text, relative)
        for relative, text in source_text.items()
    }
    rendered_closure = ". ".join(
        rendered[relative] for relative in _MANUSCRIPT_SOURCE_PATHS
    )
    rendered_policy_registry = rendered[
        "latex/appendices/appendix_policy_provenance.tex"
    ]
    provenance_remainder = _remove_exact_once(
        rendered_closure,
        rendered_policy_registry,
    )
    if _contains_provenance_assignment(provenance_remainder):
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    if _contains_unapproved_authorial_claim(rendered_closure):
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    related = active["latex/sections/02_related_work.tex"]
    related_casefold = related.casefold()
    if related_casefold.count("off-policy") != 2:
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    if (
        "the present paper performs neither direct nor logged off-policy evaluation"
        not in related_casefold
        or "any future off-policy comparison is protocol-only" not in related_casefold
    ):
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    if related.count("paired direct policy evaluation") != 1:
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    if related.count("score-level orthogonality") != 1:
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    if related.count("our first-order action-choice proposition") != 1:
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    if any(related.count(sentence) != 1 for sentence in _DISPOSITIONS):
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    if (
        related.count(
            "citation\\_authority\\_status=blocked\\_pending\\_authenticated\\_roster."
        )
        != 1
    ):
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    if related.count(_NOVELTY_BOUNDARY) != 1:
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    normalized_closure = " ".join(
        active[relative] for relative in _MANUSCRIPT_SOURCE_PATHS
    )
    sap_policy_text = active["latex/appendices/appendix_analysis_protocol.tex"]
    sap_policies = tuple(
        token.replace("\\_", "_")
        for token in re.findall(r"\\texttt\{([^{}]+)\}", sap_policy_text)
    )
    if (
        sap_policy_text.count(_SAP_POLICY_ROSTER_BLOCK) != 1
        or sap_policies != _POLICY_IDS
    ):
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    policy_remainder = " ".join(
        active[relative]
        for relative in _MANUSCRIPT_SOURCE_PATHS
        if relative
        not in {
            "latex/appendices/appendix_analysis_protocol.tex",
            "latex/appendices/appendix_policy_provenance.tex",
            "latex/references.bib",
        }
    ).replace(r"\_", "_")
    if any(
        re.search(
            r"(?<![A-Za-z0-9_])" + re.escape(policy) + r"(?![A-Za-z0-9_])",
            policy_remainder,
        )
        for policy in _POLICY_IDS
    ):
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    related_citations = []
    related_arguments = _extract_literal_arguments(
        source_text["latex/sections/02_related_work.tex"],
        ("cite", "citet", "citep"),
    )
    for command in ("cite", "citet", "citep"):
        for argument in related_arguments[command]:
            related_citations.extend(key.strip() for key in argument.split(","))
    if tuple(key for key in related_citations if key in _PRIMARY_KEYS) != (
        "kallus2018instrument",
        "oprescu2025amriv",
        "dellapenna2026brace",
        "zhang2026icore",
        "wong2026eureka",
        "yang2026star",
        "bala2026setvalued",
    ):
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    if "retrospective oracle is not a 23rd policy" not in related:
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    attack_text = active["latex/appendices/appendix_reviewer_attacks.tex"]
    attacks = tuple(re.findall(r"RA-[A-Z]+-\d\d", attack_text))
    attack_items = attack_text.split(r"\item")[1:]
    if (
        attacks != _ATTACK_IDS
        or not attack_items
        or attack_items[0].strip() != _RA_NOVELTY_ITEM
    ):
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    required = (
        (
            "latex/sections/01_introduction.tex",
            "instrumentation rather than first contributions",
        ),
        (
            "latex/sections/03_problem_formulation.tex",
            "$Z_{it}$ the pre-outcome randomized bundle assignment",
        ),
        (
            "latex/sections/03_problem_formulation.tex",
            "$E_{it}$ the verified realized execution",
        ),
        (
            "latex/sections/03_problem_formulation.tex",
            "entire ontology-specific confirmatory E2 estimand nonestimable and every confirmatory numeric field None",
        ),
        (
            "latex/sections/03_problem_formulation.tex",
            "No required repeat, cell, target, or site may be dropped, replaced, filtered, or analyzed as-treated/per-protocol.",
        ),
        ("latex/sections/04_method.tex", _METHOD_BOUNDARY),
        ("latex/sections/04_method.tex", "Study Policy: Obligation-Aware Coordination"),
        (
            "latex/sections/09_conclusion.tex",
            "The present contributions are a receipt-bound evaluation contract, the bounded account of an immutable failed diagnostic, a prospective E1--E4 and JCI protocol, and a claim/provenance discipline that treats nonestimability as an outcome.",
        ),
        (
            "latex/sections/09_conclusion.tex",
            "receipt-verified evaluability is a prerequisite for, not evidence of, coordination value",
        ),
    )
    if any(active[relative].count(sentence) != 1 for relative, sentence in required):
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    problem_without_boundary = active[
        "latex/sections/03_problem_formulation.tex"
    ].replace(
        "No required repeat, cell, target, or site may be dropped, replaced, filtered, or analyzed as-treated/per-protocol.",
        "",
        1,
    )
    if any(
        word in problem_without_boundary
        for word in ("as-treated", "per-protocol", "dropped", "replaced", "filtered")
    ):
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    closure = " ".join(active[relative] for relative in _MANUSCRIPT_SOURCE_PATHS)
    for sentence in _DISPOSITIONS:
        closure = closure.replace(sentence, "", 1)
    if closure.count(_METHOD_BOUNDARY) != 2:
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    closure = closure.replace(_METHOD_BOUNDARY, "", 2)
    if any(phrase in closure for phrase in _FORBIDDEN_POSITIVES):
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    related_novelty = related.replace(_NOVELTY_BOUNDARY, "", 1)
    for sentence in _DISPOSITIONS:
        related_novelty = related_novelty.replace(sentence, "", 1)
    related_novelty = related_novelty.replace(_METHOD_BOUNDARY, "", 1)
    related_novelty = related_novelty.replace(
        "We claim neither the first graph, router, selector, verifier, conformal stopper, orthogonal score, regret algorithm, nor collaboration framework.",
        "",
        1,
    ).replace(
        "It does not establish our first-order action-choice proposition for generated features or execution-map errors.",
        "",
        1,
    )
    if any(phrase in related_novelty.lower() for phrase in _FORBIDDEN_NOVELTY_PHRASES):
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    editable_novelty = " ".join(
        active[relative]
        for relative in _EDITABLE_ROLES
        if relative != "latex/appendices/appendix_policy_provenance.tex"
    )
    for span in _CANONICAL_NOVELTY_SPANS:
        expected_count = 2 if span == _METHOD_BOUNDARY else 1
        if editable_novelty.count(span) != expected_count:
            raise PaperLatexVerificationError("scientific_boundary_invalid")
        editable_novelty = editable_novelty.replace(span, "", expected_count)
    editable_novelty = editable_novelty.replace(
        "It does not establish our first-order action-choice proposition for generated features or execution-map errors.",
        "",
        1,
    )
    if re.search(
        r"\b(?:breakthrough|contribut\w*|exhaustive|first|innovat\w*|invent\w*|"
        r"latest|new\w*|novel\w*|originat\w*|original\w*|pioneer\w*|"
        r"state-of-the-art|unprecedented)\b",
        editable_novelty,
        re.IGNORECASE,
    ):
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    if any(
        promotion in normalized_closure.casefold()
        for promotion in _FORBIDDEN_AUTHENTICATION_PROMOTIONS
    ):
        raise PaperLatexVerificationError("scientific_boundary_invalid")


def _validate_relative_source_path(relative: str) -> str:
    path = Path(relative)
    if (
        type(relative) is not str
        or relative.startswith(("/", "\\"))
        or "\\" in relative
        or path.is_absolute()
        or not path.parts
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise PaperLatexVerificationError("source_identity_invalid")
    return path.as_posix()


def _entry_map(entries: tuple[object, ...]) -> dict[str, bool]:
    return {entry.name: entry.is_directory for entry in entries}


def _validated_text(data: bytes, *, primary_manifest: bool = False) -> str:
    reason = (
        "primary_source_manifest_invalid"
        if primary_manifest
        else "source_bytes_invalid"
    )
    if (
        data.startswith(b"\xef\xbb\xbf")
        or b"\r" in data
        or b"\x00" in data
        or not data.endswith(b"\n")
    ):
        raise PaperLatexVerificationError(reason)
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PaperLatexVerificationError(reason) from error


def _verify_static_paper_latex_at(
    repository_root: Path,
    *,
    read_observer=None,
    post_file_validation_hook=None,
    directory_validation_hook=None,
    name_observer=None,
) -> PaperStaticReceipt:
    if not isinstance(repository_root, Path):
        raise PaperLatexVerificationError("source_identity_invalid")
    paper_root = repository_root / _PAPER_RELATIVE
    try:
        with AuthenticatedTree(
            paper_root,
            label="ICLR 2027 paper root",
            read_observer=read_observer,
            post_file_validation_hook=post_file_validation_hook,
            directory_validation_hook=directory_validation_hook,
            name_observer=name_observer,
        ) as tree:
            observed = _entry_map(tree.list_directory(None, label="paper root"))
            if observed != _ROOT_ENTRIES:
                raise PaperLatexVerificationError("source_identity_invalid")
            for relative, expected in (
                ("latex", _LATEX_ENTRIES),
                ("latex/sections", _SECTION_ENTRIES),
                ("latex/appendices", _APPENDIX_ENTRIES),
            ):
                observed = _entry_map(tree.list_directory(relative, label=relative))
                if observed != expected:
                    raise PaperLatexVerificationError("source_identity_invalid")
            source_bytes = {
                relative: tree.read_bytes(relative, label=relative)
                for relative in _SOURCE_PATHS
            }
            primary_bytes = tree.read_bytes(
                "literature_primary_source_manifest.md",
                label="primary-source manifest",
            )
    except PaperLatexVerificationError:
        raise
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        raise PaperLatexVerificationError("source_identity_invalid") from error

    source_text = {
        relative: _validated_text(source_bytes[relative])
        for relative in _MANUSCRIPT_SOURCE_PATHS
    }
    _validated_text(primary_bytes, primary_manifest=True)
    for relative, expected_digest in _PINNED_SOURCE_SHA256.items():
        observed_digest = hashlib.sha256(source_bytes[relative]).hexdigest().upper()
        if observed_digest != expected_digest:
            raise PaperLatexVerificationError("source_bytes_invalid")
    for relative, expected_length, expected_digest in _VENDOR_SOURCE_IDENTITIES:
        vendor_bytes = source_bytes[relative]
        observed_digest = hashlib.sha256(vendor_bytes).hexdigest().upper()
        if len(vendor_bytes) != expected_length or observed_digest != expected_digest:
            raise PaperLatexVerificationError("source_bytes_invalid")
    primary_digest = hashlib.sha256(primary_bytes).hexdigest().upper()
    if primary_digest != _PRIMARY_MANIFEST_SHA256:
        raise PaperLatexVerificationError("primary_source_manifest_invalid")
    _validate_tex_bibliography_and_science(source_text, source_bytes)
    manifest = "".join(
        f"{relative}\t{len(source_bytes[relative])}\t"
        f"{hashlib.sha256(source_bytes[relative]).hexdigest().upper()}\n"
        for relative in _SOURCE_PATHS
    )
    source_digest = hashlib.sha256(manifest.encode("utf-8")).hexdigest()
    del source_text
    return _make_receipt(source_digest, primary_digest.lower())


def verify_static_paper_latex() -> PaperStaticReceipt:
    """Verify the one fixed repository paper root."""

    return _verify_static_paper_latex_at(Path(__file__).resolve().parents[1])


@dataclass(frozen=True, slots=True)
class EstimandReceiptManuscriptReceipt:
    """Verification receipt for the registered estimand-receipt manuscript."""

    status: str
    title: str
    evidence_objects: tuple[str, ...]
    format_status: str
    source_manifest_sha256: str
    source_file_count: int


_ESTIMAND_RECEIPT_TITLE = (
    "When Is Planned Coordination Evaluable? Estimand-Specific Receipts for "
    "Randomized Multi-Agent Experiments"
)
_ESTIMAND_RECEIPT_SECTIONS = (
    "Problem",
    "Declared Model and Estimands",
    "Estimand-Support Lattice and Gate",
    "Synthetic Stress Benchmark and Independent Boundary",
    "Frozen Synthetic Results",
    "Limitations and Validity Boundaries",
    "Conclusion",
    "Mathematical Details and Assumptions",
)
_ESTIMAND_RECEIPT_EVIDENCE_OBJECTS = (
    "fig:estimand-support-lattice",
    "fig:inference-consequence",
    "tab:evaluator-comparison",
)
_ESTIMAND_RECEIPT_CITATIONS = (
    "beyondlocalaccuracy2026",
    "telemetrysuffbench2026",
    "traceassurance2026",
    "agenttelemetry2026",
    "horvitzthompson1952",
    "rubin1974",
    "manski1990",
    "imbensmanski2004",
    "robinsrotnitzkyzhao1994",
    "bross1954",
)
_ESTIMAND_RECEIPT_SOURCE_IDENTITIES = {
    "latex/main.tex": (
        33891,
        "05AFFF37862FD3D6DA08742DD0FFCE5CB30B6F68122E572F5F1537ACDB465D00",
    ),
    "latex/references.bib": (
        3859,
        "DBA10388200748DE5D2CEB9F9B2390AE02A59095614D5CDC165DAAE9AC85F962",
    ),
    "latex/iclr2027_conference.sty": (
        9025,
        "797DEEF41724E93761426AC0CBCCA46279A91CC650DD1F0CE76A4F08D2098EA6",
    ),
    "latex/iclr2027_conference.bst": (
        26973,
        "2D67552DB7ED38CCFCCB5957B52F95656E25C249724761D3CF5F7922AD1844C5",
    ),
}
_ESTIMAND_RECEIPT_REQUIRED_SPANS = (
    "We specialize existing support-identifiability principles to randomized "
    "multi-agent experiments.",
    "The benchmark is synthetic and provides no causal result about real "
    "buildings or evidence about a sampled Architecture population.",
    "These labels are relative to the declared receipt-visible records absent "
    "additional validation data or an explicit measurement-error model.",
    "The original V2 held-out run was an invalid harness, not a case-level "
    "result; V3 was a vocabulary-only technical rerun.",
    "We do not describe V2 as rescued.",
    "The external AgentTelemetry check tests schema-identity transport only; "
    "it is not causal evidence and does not validate the synthetic "
    "Architecture setting.",
    "No live large language model, model provider, paid API, human-derived "
    "hidden case, or production agent service was evaluated.",
    "Two matching roots are retained, but the post-hoc custody correction "
    "cannot cryptographically prove the historical absence of a deleted third "
    "execution.",
    "Humans remain responsible for every claim, source, proof, implementation "
    "decision, result interpretation, and the final text.",
    "For each simulated replicate, $U$ is uniform over its fixed 64-position "
    "synthetic roster, and $\\E$ in the three estimands is the finite-roster "
    "mean conditional on that replicate's generated potential outcomes and "
    "retained design objects.",
    "The eight finite witnesses cover one declared component--target example "
    "for each of $Z,A,E,B,T,S,G,P$; they do not cover every required "
    "component--target pair.",
    "The frozen evidence establishes a target-specific structural separation "
    "against the co-designed oracle in this synthetic fault census:",
    "It does not establish independent empirical validity, general "
    "fault-diagnosis ability, causal recovery, or comparative inferential "
    "improvement.",
    "This table is a post-hoc descriptive extraction from the pre-specified "
    "frozen configurations, not a confirmatory comparison backed by an "
    "external time-stamped commitment.",
    "The strongest independent held-out/external macro comparison was not "
    "preserved in the frozen payload, so we make no claim that its "
    "pre-specified margin criterion was met.",
    "No defensible pooled Monte Carlo standard error is recoverable because "
    "replicate-level joint sufficient statistics and cross-estimand and "
    "cross-configuration covariance were not persisted.",
    "pre-specified in the retained design narrative",
    "synthetic Architecture stress vocabulary",
    "These foundations supply identification tools; they are not contributions "
    "of this paper.",
    "None of the trace or telemetry studies establishes our synthetic outcome "
    "model or comparative evaluator performance.",
    "\\section{Mathematical Details and Assumptions}",
    "\\subsection{Assumptions and support lattice}",
    "\\subsection{Component-relative nonidentification}",
    "\\subsection{Overlap-aware bounded contrast error}",
    "\\subsection{Terminal misclassification and selection}",
    "E & $\\tau_{\\mathrm{CB}}$ & 0/20{,}653 & 20{,}653/24{,}000 & 20{,}653/20{,}653",
    "B & All three & 0/20{,}636 & 20{,}636/24{,}000 & 20{,}636/20{,}636",
    "T & All three & 0/20{,}565 & 20{,}565/24{,}000 & 20{,}565/20{,}565",
    "S & All three & 0/20{,}619 & 20{,}619/24{,}000 & 20{,}619/20{,}619",
    "G & All three & 0/20{,}600 & 20{,}600/24{,}000 & 20{,}600/20{,}600",
    "P & $\\Psi_N$ & 0/20{,}579 & 20{,}579/24{,}000 & 20{,}579/20{,}579",
    "0/1,408,516",
    "373,484/373,484",
    "354{,}574/373{,}484=0.9493686477",
    "4,479/89,660",
    "0.0499553870",
    "4,479/89,660, namely $0.0499553870$",
    "0/54,000",
    "389/12,000",
    "0.0324167",
)
_ESTIMAND_RECEIPT_FORBIDDEN_SPANS = (
    "topology-aware termination dynamics",
    "experiment 01",
    "fig_exp",
    "first general support-identifiability theorem",
    "the v2 failure was rescued",
    "causally validates the architecture setting",
    "causal gains for real architecture workflows",
    "task 7",
    "task 11",
    "clopper--pearson",
    "[0, 0.00000261898]",
    "[0.9999901231,1]",
    "[0.9486606790, 0.9500696340]",
    "[0.0485384137, 0.0514015660]",
    "preregistered",
    "registered thresholds",
    "the independent held-out/external macro criterion was met",
    "superior fault diagnosis and inferential validity",
)
_ESTIMAND_RECEIPT_BIB_SNIPPETS = (
    "Beyond Local Accuracy: A Protocol-Level Identifiability Audit",
    "TelemetrySuffBench}: Is Agent Telemetry Sufficient",
    "AgentTelemetry}: A Fault Detection Benchmark and Toolkit",
    "A Trace-Based Assurance Framework for Agentic {AI} Orchestration",
    "10.1145/3805760.3814931",
    "A Generalization of Sampling Without Replacement from a Finite Universe",
    "Estimating Causal Effects of Treatments in Randomized and Nonrandomized Studies",
    "Nonparametric Bounds on Treatment Effects",
    "Confidence Intervals for Partially Identified Parameters",
    "Estimation of Regression Coefficients When Some Regressors Are Not Always "
    "Observed",
    "Misclassification in 2 x 2 Tables",
    "8ba0ae753d51cc2837f4ef2fa450e103c3be904a",
)


def _estimand_receipt_title(active: str) -> str:
    titles = tuple(re.findall(r"\\title\s*\{([^{}]*)\}", active, re.DOTALL))
    if len(titles) != 1:
        raise PaperLatexVerificationError("source_grammar_invalid")
    semantic = titles[0].replace("\\\\", " ")
    return re.sub(r"\s+", " ", semantic).strip()


def _validate_estimand_receipt_structure(main: str) -> tuple[str, ...]:
    active = _strip_tex_comments(main)
    documentclass = r"\documentclass{article}"
    font_encoding = r"\usepackage[T1]{fontenc}"
    conference_style = r"\usepackage{iclr2027_conference}"
    bibliography_style = r"\bibliographystyle{iclr2027_conference}"
    spacing_package = r"\usepackage{xspace}"
    raw_title = (
        "\\title{When Is Planned Coordination Evaluable?\\\\\n"
        "Estimand-Specific Receipts for Randomized\\\\\n"
        "Multi-Agent Experiments}"
    )
    if active.count(documentclass) != 1:
        raise PaperLatexVerificationError("source_grammar_invalid")
    if active.count(conference_style) != 1 or "colm" in active.casefold():
        raise PaperLatexVerificationError("source_grammar_invalid")
    font_encoding_calls = tuple(
        re.findall(
            r"\\usepackage\s*(?:\[[^][]*\]\s*)?\{fontenc\}",
            active,
        )
    )
    if (
        font_encoding_calls != (font_encoding,)
        or not active.startswith(documentclass + "\n" + font_encoding + "\n")
        or active.index(font_encoding) > active.index(conference_style)
    ):
        raise PaperLatexVerificationError("source_grammar_invalid")
    if (
        active.count(spacing_package) != 1
        or active.count(raw_title) != 1
        or r"\hyphenation{Experiments}" in active
    ):
        raise PaperLatexVerificationError("source_grammar_invalid")
    status_macros = (
        r"\newcommand{\cert}{\textsc{Certified}\xspace}",
        r"\newcommand{\bounded}{\textsc{Bounded}\xspace}",
        r"\newcommand{\notcert}{\textsc{Not-Certified}\xspace}",
    )
    if any(active.count(macro) != 1 for macro in status_macros):
        raise PaperLatexVerificationError("source_grammar_invalid")
    forbidden_controls = (
        "\\input",
        "\\include{",
        "\\includegraphics",
        "\\write18",
        "\\openout",
    )
    if any(control in active for control in forbidden_controls):
        raise PaperLatexVerificationError("source_grammar_invalid")
    if active.count("\\begin{document}") != 1 or active.count("\\end{document}") != 1:
        raise PaperLatexVerificationError("source_grammar_invalid")
    if active.count("\\begin{abstract}") != 1 or active.count("\\end{abstract}") != 1:
        raise PaperLatexVerificationError("source_grammar_invalid")
    sections = tuple(re.findall(r"\\section\{([^{}]+)\}", active))
    if sections != _ESTIMAND_RECEIPT_SECTIONS:
        raise PaperLatexVerificationError("source_grammar_invalid")
    if len(re.findall(r"\\begin\{figure\*?\}", active)) != 2:
        raise PaperLatexVerificationError("source_grammar_invalid")
    if len(re.findall(r"\\begin\{table\*?\}", active)) != 1:
        raise PaperLatexVerificationError("source_grammar_invalid")
    if active.count("\\bibliography{references}") != 1:
        raise PaperLatexVerificationError("source_grammar_invalid")
    if active.count(bibliography_style) != 1:
        raise PaperLatexVerificationError("source_grammar_invalid")
    if (
        active.count("\\appendix") != 1
        or active.index("\\bibliography{references}") > active.index("\\appendix")
        or active.count("\\label{app:mathematical-details}") != 1
        or active[active.index("\\appendix") :].count("\\paragraph{Proof.}") < 3
    ):
        raise PaperLatexVerificationError("source_grammar_invalid")
    labels = tuple(
        label
        for label in _ESTIMAND_RECEIPT_EVIDENCE_OBJECTS
        if active.count(f"\\label{{{label}}}") == 1
    )
    if labels != _ESTIMAND_RECEIPT_EVIDENCE_OBJECTS:
        raise PaperLatexVerificationError("source_grammar_invalid")
    return labels


def _validate_estimand_receipt_science(main: str, bibliography: str) -> None:
    active = _strip_tex_comments(main)
    if _estimand_receipt_title(active) != _ESTIMAND_RECEIPT_TITLE:
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    if any(span not in active for span in _ESTIMAND_RECEIPT_REQUIRED_SPANS):
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    lowered = active.casefold()
    if any(span in lowered for span in _ESTIMAND_RECEIPT_FORBIDDEN_SPANS):
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    cited_keys: list[str] = []
    for argument in re.findall(r"\\citep\{([^{}]+)\}", active):
        cited_keys.extend(key.strip() for key in argument.split(","))
    if set(cited_keys) != set(_ESTIMAND_RECEIPT_CITATIONS):
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    bib_keys = tuple(re.findall(r"@[A-Za-z]+\s*\{\s*([^,\s]+)\s*,", bibliography))
    if bib_keys != _ESTIMAND_RECEIPT_CITATIONS:
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    if any(span not in bibliography for span in _ESTIMAND_RECEIPT_BIB_SNIPPETS[:-1]):
        raise PaperLatexVerificationError("scientific_boundary_invalid")
    if "commit \\texttt{" + _ESTIMAND_RECEIPT_BIB_SNIPPETS[-1] + "}" not in active:
        raise PaperLatexVerificationError("scientific_boundary_invalid")


def verify_estimand_receipt_manuscript_at(
    repository_root: Path,
) -> EstimandReceiptManuscriptReceipt:
    """Verify the official-style estimand-receipt manuscript closure."""

    if not isinstance(repository_root, Path):
        raise PaperLatexVerificationError("source_identity_invalid")
    source_bytes: dict[str, bytes] = {}
    for relative in _ESTIMAND_RECEIPT_SOURCE_IDENTITIES:
        path = repository_root / relative
        try:
            if path.is_symlink() or not path.is_file():
                raise PaperLatexVerificationError("source_identity_invalid")
            source_bytes[relative] = path.read_bytes()
        except PaperLatexVerificationError:
            raise
        except OSError as error:
            raise PaperLatexVerificationError("source_identity_invalid") from error
    source_text = {
        relative: _validated_text(data) for relative, data in source_bytes.items()
    }
    labels = _validate_estimand_receipt_structure(source_text["latex/main.tex"])
    _validate_estimand_receipt_science(
        source_text["latex/main.tex"], source_text["latex/references.bib"]
    )
    manifest_rows: list[str] = []
    for relative, (
        expected_size,
        expected_hash,
    ) in _ESTIMAND_RECEIPT_SOURCE_IDENTITIES.items():
        data = source_bytes[relative]
        observed_hash = hashlib.sha256(data).hexdigest().upper()
        if len(data) != expected_size or observed_hash != expected_hash:
            raise PaperLatexVerificationError("source_bytes_invalid")
        manifest_rows.append(f"{relative}\t{len(data)}\t{observed_hash}\n")
    manifest_hash = hashlib.sha256("".join(manifest_rows).encode("utf-8")).hexdigest()
    return EstimandReceiptManuscriptReceipt(
        status="verified",
        title=_ESTIMAND_RECEIPT_TITLE,
        evidence_objects=labels,
        format_status="official-iclr2027-submission",
        source_manifest_sha256=manifest_hash,
        source_file_count=len(_ESTIMAND_RECEIPT_SOURCE_IDENTITIES),
    )


def verify_estimand_receipt_manuscript() -> EstimandReceiptManuscriptReceipt:
    """Verify the registered manuscript in this repository."""

    return verify_estimand_receipt_manuscript_at(Path(__file__).resolve().parents[1])


__all__ = (
    "PaperLatexVerificationError",
    "PaperStaticReceipt",
    "verify_static_paper_latex",
)
