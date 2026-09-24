"""Independent tests for the frozen Task-5 scientific contract.

The expectations in this module are test-owned.  Production verifier constants
are deliberately not imported, so agreement with a drifted verifier cannot make
the manuscript appear aligned.
"""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import re
import shutil
import tempfile
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]
SAP = REPOSITORY / (
    "docs/paper/iclr2027_oacs/latex/appendices/appendix_analysis_protocol.tex"
)
DESIGN = REPOSITORY / (
    "docs/paper/iclr2027_oacs/latex/sections/06_experimental_design.tex"
)
CLAIM_MATRIX = REPOSITORY / "docs/paper/iclr2027_oacs/claim_evidence_matrix.md"
POLICY_REGISTRY = REPOSITORY / (
    "docs/paper/iclr2027_oacs/latex/appendices/appendix_policy_provenance.tex"
)
RELATED_WORK = REPOSITORY / (
    "docs/paper/iclr2027_oacs/latex/sections/02_related_work.tex"
)
CLAIMS = REPOSITORY / ("docs/paper/iclr2027_oacs/latex/appendices/appendix_claims.tex")
MAIN = REPOSITORY / "docs/paper/iclr2027_oacs/latex/main.tex"
INTRODUCTION = REPOSITORY / (
    "docs/paper/iclr2027_oacs/latex/sections/01_introduction.tex"
)
PROBLEM_FORMULATION = REPOSITORY / (
    "docs/paper/iclr2027_oacs/latex/sections/03_problem_formulation.tex"
)
RESULTS = REPOSITORY / "docs/paper/iclr2027_oacs/latex/sections/07_results.tex"
CONCLUSION = REPOSITORY / ("docs/paper/iclr2027_oacs/latex/sections/09_conclusion.tex")
REVIEWER_ATTACK_MATRIX = REPOSITORY / (
    "docs/paper/iclr2027_oacs/reviewer_attack_matrix.md"
)
OBLIGATION_ORACLE = REPOSITORY / "iclr2027/obligation_oracle.py"
AUTHORITY_CONTRACT = REPOSITORY / "iclr2027/external_authority_acquisition.py"

EXPECTED_MANUSCRIPT_TITLE = (
    "Planned Is Not Executed: Receipt-Bound Evaluation of Multi-Agent Coordination"
)
EXPECTED_RAW_MANUSCRIPT_TITLE = (
    r"Planned Is Not Executed: Receipt-Bound\\Evaluation of Multi-Agent Coordination"
)
EXPECTED_EVALUATION_IDENTITIES = (
    "requested action",
    "verified complete-bundle execution",
    "current terminal assessment",
    "scorer final-key set",
)
EXPECTED_CLAIM_UPDATES = {
    "C-DEV-DIAGNOSTIC": ("ready", "immutable failed development diagnostic"),
    "C-THESIS": ("structural", "prospective complete-bundle hypothesis"),
    "C-ARCH-FLAGSHIP": ("structural", "prospective Architecture stress test"),
    "C-JCI-REPLICATION": ("structural", "planned unpooled replication"),
}
FROZEN_DIAGNOSTIC_PARAGRAPH = (
    "The frozen Architecture development diagnostic completed execution and "
    "artifact closure but failed its prespecified terminal-reliability gate. A "
    "later public-synthetic audit exposed a mismatch between cumulative provenance "
    "and current terminal assessment. The frozen no-rescore rule leaves the V1 "
    "result unchanged. It therefore estimates neither OACS benefit nor harm and "
    "provides no evidence about the corrected V2 evaluator. Its narrower role is "
    "to document failed evaluability and motivate fresh, versioned evidence."
)
EXPECTED_RESULT_SLOT_IDS = (
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
EXPECTED_POLICY_COUNT = 22
EXPECTED_EMPIRICAL_STATUS = "no_go_needs_context"
EXPECTED_POLICY_IDS = (
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
EXPECTED_BLOCKED_CLAIMS = (
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

EXPECTED_PARENT_FIELDS = (
    "site_ref",
    "case_ref",
    "prefix_ref",
    "raw_transcript_prefix",
    "numeric_residual_serialization",
    "complete_capability_table",
    "opaque_packet_binding_cards",
    "costs",
    "admissibility",
    "examples",
    "split_fold",
    "learner_class_capacity",
    "tuning_optimization_opportunity",
    "target_action_roster",
    "action_space_tie_rule",
)
EXPECTED_SHARED_FIELDS = (
    "costs",
    "admissibility",
    "examples",
    "split_fold",
    "learner_class_capacity",
    "tuning_optimization_opportunity",
    "action_space_tie_rule",
)
EXPECTED_E2_ENDPOINT = (
    "blind_terminal_obligation_closure_quality_present_high_minus_low_minus_"
    "absent_high_minus_low"
)
EXPECTED_E2_TEX_SPAN = (
    "Within each frozen residual-present and residual-absent stratum, opaque\n"
    "complete-bundle packet assignment is randomized over the authenticated\n"
    "complete cyclic-crossover assignment space; residual status itself is not\n"
    "randomized. The primary endpoint is the residual-present high-minus-low\n"
    "complete-bundle effect minus the matched residual-absent high-minus-low effect."
)
EXPECTED_E2_MATRIX_CLAIM = (
    "Architecture E2 estimates (residual-present high-minus-low) minus "
    "(residual-absent high-minus-low): opaque complete-bundle packet assignment "
    "is randomized within frozen residual-present and residual-absent strata; "
    "residual status itself is not randomized."
)
EXPECTED_E2_CONTRACT_SENTENCE = (
    "opaque complete-bundle packet assignment is randomized within frozen "
    "residual-present and residual-absent strata; residual status itself is not "
    "randomized; endpoint: (residual-present high-minus-low) minus "
    "(residual-absent high-minus-low)."
)
EXPECTED_MUTATION_SHA256 = {
    "learner_capacity parent": (
        "b0bd994f65653975a66431aacb51553fc5d2aa93935dedb9db3a20e9b74372ad"
    ),
    "learner_capacity shared": (
        "98d96b856598b948e47331d72b5fc8eee7f9916c38de4062e7f010a527faa016"
    ),
    "randomized residual status": (
        "b2d13a23eb764903a47e7dd0dfd08114bbf49fa07d614fc271d69f7b4e0092f5"
    ),
    "presence-versus-absence treatment": (
        "e43abd5724df82bdd35a71a506b3532521385abc8c61ef2e082749fd9699b01c"
    ),
    "swapped subtraction": (
        "20b8a51e77cd9d9a84722ccf662f8239b9cd3b08a6600d11a39426f202683c6b"
    ),
    "omitted absent high-minus-low": (
        "fe8e91969b4e36b5e895472fcc8410389df5d08dea288d660a72a39a797de3e0"
    ),
    "causal residual-status wording": (
        "151740a7376a7ad13d98e44867c45cecb2242c182b795a64bbd3f837ef1480a6"
    ),
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _literal_assignment(path: Path, name: str) -> object:
    tree = ast.parse(_read(path), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == name
                for target in node.targets
            ):
                return ast.literal_eval(node.value)
    raise AssertionError(f"missing literal assignment: {name}")


def _frozen_endpoint_from_ast() -> str:
    scalars = _literal_assignment(AUTHORITY_CONTRACT, "_FROZEN_ONE_THESIS_SCALARS")
    return dict(scalars)["e2_primary_endpoint"]


def _active_tex(text: str) -> str:
    """Return rendered TeX text, excluding comments and false conditionals."""
    text = re.sub(r"(?<!\\)%[^\r\n]*", "", text)
    token_pattern = re.compile(r"\\(?P<kind>iffalse|iftrue|else|fi)\b")
    active_stack = [True]
    rendered: list[str] = []
    cursor = 0
    for token in token_pattern.finditer(text):
        if active_stack[-1]:
            rendered.append(text[cursor : token.start()])
        kind = token.group("kind")
        if kind == "iffalse":
            active_stack.append(False)
        elif kind == "iftrue":
            active_stack.append(active_stack[-1])
        elif kind == "else":
            if len(active_stack) == 1:
                raise AssertionError("unmatched TeX \\else")
            parent_active = active_stack[-2]
            active_stack[-1] = parent_active and not active_stack[-1]
        else:
            if len(active_stack) == 1:
                raise AssertionError("unmatched TeX \\fi")
            active_stack.pop()
        cursor = token.end()
    if len(active_stack) != 1:
        raise AssertionError("unterminated TeX conditional")
    if active_stack[-1]:
        rendered.append(text[cursor:])
    return _strip_nonrendered_macro_definitions("".join(rendered))


def _strip_nonrendered_macro_definitions(text: str) -> str:
    """Remove new-command definitions whose arguments are not rendered in place."""
    definition = re.compile(r"\\(?:newcommand|renewcommand|providecommand)\*?")

    def consume_balanced(position: int, opening: str, closing: str) -> int:
        if position >= len(text) or text[position] != opening:
            raise AssertionError("malformed TeX macro definition")
        depth = 0
        for index in range(position, len(text)):
            if text[index] == opening:
                depth += 1
            elif text[index] == closing:
                depth -= 1
                if depth == 0:
                    return index + 1
        raise AssertionError("unterminated TeX macro definition")

    pieces: list[str] = []
    cursor = 0
    while match := definition.search(text, cursor):
        pieces.append(text[cursor : match.start()])
        position = match.end()
        while position < len(text) and text[position].isspace():
            position += 1
        if position < len(text) and text[position] == "{":
            position = consume_balanced(position, "{", "}")
        elif position < len(text) and text[position] == "\\":
            command = re.match(r"\\[A-Za-z@]+", text[position:])
            if command is None:
                raise AssertionError("malformed TeX macro name")
            position += command.end()
        else:
            raise AssertionError("missing TeX macro name")
        while True:
            while position < len(text) and text[position].isspace():
                position += 1
            if position < len(text) and text[position] == "[":
                position = consume_balanced(position, "[", "]")
                continue
            break
        while position < len(text) and text[position].isspace():
            position += 1
        position = consume_balanced(position, "{", "}")
        cursor = position
    pieces.append(text[cursor:])
    return "".join(pieces)


def _tex_section(text: str, start: str, next_pattern: str) -> str:
    active = _active_tex(text)
    starts = [match.end() for match in re.finditer(re.escape(start), active)]
    if len(starts) != 1:
        raise AssertionError(f"expected one active TeX section: {start}")
    section_start = starts[0]
    next_match = re.search(next_pattern, active[section_start:])
    section_end = (
        len(active) if next_match is None else section_start + next_match.start()
    )
    return active[section_start:section_end]


def _require_top_level_balanced_group(text: str, opening_index: int) -> None:
    """Require one candidate opening brace at top-level in balanced frozen TeX."""

    def follows_control_token() -> bool:
        token_end = opening_index
        while token_end > 0 and text[token_end - 1].isspace():
            token_end -= 1
        if token_end == 0:
            return False
        token_last = text[token_end - 1]
        if token_last == "\\":
            raise AssertionError(
                "ambiguous trailing TeX control syntax before SAP parity owner"
            )
        if token_last.isalpha() or token_last == "@":
            token_start = token_end - 1
            while token_start > 0 and (
                text[token_start - 1].isalpha() or text[token_start - 1] == "@"
            ):
                token_start -= 1
            escape_index = token_start - 1
        else:
            escape_index = token_end - 2
        if escape_index < 0 or text[escape_index] != "\\":
            return False
        escape_run_start = escape_index
        while escape_run_start > 0 and text[escape_run_start - 1] == "\\":
            escape_run_start -= 1
        return (escape_index - escape_run_start + 1) % 2 == 1

    depth = 0
    candidate_depth: int | None = None
    index = 0
    while index < len(text):
        if index == opening_index:
            candidate_depth = depth
        character = text[index]
        if character == "\\":
            index += 1
            if index >= len(text):
                raise AssertionError("trailing TeX escape in E3 section")
            if text[index].isalpha() or text[index] == "@":
                while index + 1 < len(text) and (
                    text[index + 1].isalpha() or text[index + 1] == "@"
                ):
                    index += 1
            index += 1
            continue
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth < 0:
                raise AssertionError("TeX brace underflow in E3 section")
        index += 1
    if depth != 0:
        raise AssertionError("unbalanced TeX braces in E3 section")
    if candidate_depth != 0:
        raise AssertionError("SAP parity inventory owner is not top-level")
    if follows_control_token():
        raise AssertionError("SAP parity inventory owner is a TeX control argument")


def _sap_lists(text: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    e3 = _tex_section(text, r"\item[E3 estimand and parity.]", r"\\item\[")
    parent_anchor = (
        "Both views are complete bijections over exactly 15 canonical parent payload"
    )
    shared_anchor = "The seven opportunity\n  objects are byte-identical:"
    shared_terminator = r"action\_space\_tie\_rule."
    owner_matches = list(
        re.finditer(r"\{\s*\\raggedright\s+" + re.escape(parent_anchor), e3)
    )
    if len(owner_matches) != 1:
        raise AssertionError("expected one rendered SAP parity inventory owner")
    _require_top_level_balanced_group(e3, owner_matches[0].start())
    inventory_start = owner_matches[0].end() - len(parent_anchor)
    shared_start = e3.find(shared_anchor, inventory_start)
    if shared_start < 0:
        raise AssertionError("SAP shared inventory anchor is missing")
    inventory_end = e3.find(shared_terminator, shared_start)
    if inventory_end < 0:
        raise AssertionError("SAP shared inventory terminator is missing")
    inventory_end += len(shared_terminator)
    inventory = e3[inventory_start:inventory_end]
    if (
        re.search(r"\\(?!_)", inventory)
        or re.fullmatch(r"[A-Za-z0-9\s,.:\\_-]+", inventory) is None
    ):
        raise AssertionError("unsupported control or token in SAP parity inventory")
    parent_match = re.search(
        r"Both views are complete bijections over exactly 15 canonical parent payload\n"
        r"\s*fields: (.+?)\. The seven opportunity",
        inventory,
        flags=re.DOTALL,
    )
    shared_match = re.search(
        r"The seven opportunity\n\s*objects are byte-identical: (.+?)\.$",
        inventory,
        flags=re.DOTALL,
    )
    if parent_match is None or shared_match is None:
        raise AssertionError("SAP parity lists are missing")

    def parse(match: re.Match[str]) -> tuple[str, ...]:
        return tuple(
            field.strip().replace(r"\_", "_")
            for field in re.sub(r"\s+", " ", match.group(1)).split(",")
        )

    return parse(parent_match), parse(shared_match)


def _active_markdown(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    active_lines: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        stripped = line.lstrip()
        marker = stripped[:3]
        if fence is None and marker in {"```", "~~~"}:
            fence = marker
            continue
        if fence is not None:
            if marker == fence:
                fence = None
            continue
        active_lines.append(line)
    if fence is not None:
        raise AssertionError("unterminated Markdown fence")
    return "\n".join(active_lines)


def _matrix_claim(text: str, claim_id: str) -> str:
    active = _active_markdown(text)
    registry_headings = list(re.finditer(r"(?m)^## Registry\s*$", active))
    if len(registry_headings) != 1:
        raise AssertionError("expected exactly one live Registry table")
    registry_start = registry_headings[0].end()
    next_heading = re.search(r"(?m)^##\s+", active[registry_start:])
    registry_end = (
        len(active) if next_heading is None else registry_start + next_heading.start()
    )
    registry = active[registry_start:registry_end]
    header = (
        "| `claim_id` | `paper_location` | `claim_text` | `evidence_required` | "
        "`current_status` | `allowed_wording` | `forbidden_wording` | "
        "`failure_fallback` | `authority_pin` |"
    )
    separator = "|---|---|---|---|---|---|---|---|---|"
    registry_lines = registry.splitlines()
    first_content = next(
        (index for index, line in enumerate(registry_lines) if line.strip()),
        None,
    )
    if first_content is None or registry_lines[first_content] != header:
        raise AssertionError("Registry table header is missing or displaced")
    separator_index = first_content + 1
    if (
        separator_index >= len(registry_lines)
        or registry_lines[separator_index] != separator
    ):
        raise AssertionError("Registry table separator is missing or displaced")
    table_rows: list[str] = []
    for line in registry_lines[separator_index + 1 :]:
        if not (line.startswith("|") and line.endswith("|")):
            break
        table_rows.append(line)
    prefix = f"| `{claim_id}` |"
    rows = [line for line in table_rows if line.startswith(prefix)]
    if len(rows) != 1:
        raise AssertionError(f"expected exactly one Registry row for {claim_id}")
    return rows[0].split("|")[3].strip()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _replace_second(text: str, old: str, new: str) -> str:
    first = text.index(old)
    second = text.index(old, first + len(old))
    return f"{text[:second]}{new}{text[second + len(old) :]}"


def _mutations() -> dict[str, tuple[str, str]]:
    sap = _read(SAP)
    design = _read(DESIGN)
    matrix = _read(CLAIM_MATRIX)
    tex_capacity = r"learner\_class\_capacity"
    matrix_endpoint = (
        "(residual-present high-minus-low) minus (residual-absent high-minus-low)"
    )
    return {
        "learner_capacity parent": (
            "sap",
            sap.replace(tex_capacity, r"learner\_capacity", 1),
        ),
        "learner_capacity shared": (
            "sap",
            _replace_second(sap, tex_capacity, r"learner\_capacity"),
        ),
        "randomized residual status": (
            "design",
            design.replace(
                "residual status itself is not\nrandomized",
                "residual status itself is\nrandomized",
            ),
        ),
        "presence-versus-absence treatment": (
            "design",
            design.replace(
                "the residual-present high-minus-low\ncomplete-bundle effect minus the "
                "matched residual-absent high-minus-low effect",
                "complete-bundle presence minus residual absence",
            ),
        ),
        "swapped subtraction": (
            "matrix",
            matrix.replace(
                matrix_endpoint,
                "(residual-absent high-minus-low) minus "
                "(residual-present high-minus-low)",
            ),
        ),
        "omitted absent high-minus-low": (
            "matrix",
            matrix.replace(matrix_endpoint, "(residual-present high-minus-low)"),
        ),
        "causal residual-status wording": (
            "matrix",
            matrix.replace(
                "residual status itself is not randomized",
                "residual status causally determines closure quality",
            ),
        ),
    }


def _assert_sap_contract(text: str) -> None:
    parent_fields, shared_fields = _sap_lists(text)
    if parent_fields != EXPECTED_PARENT_FIELDS:
        raise AssertionError("E3 parent inventory contract drift")
    if shared_fields != EXPECTED_SHARED_FIELDS:
        raise AssertionError("E3 shared inventory contract drift")


def _assert_design_contract(text: str) -> None:
    e2 = _tex_section(
        text,
        r"\paragraph{E2: randomized executed-bundle mechanism.}",
        r"\\paragraph\{",
    )
    expected_prefix = re.sub(r"\s+", " ", EXPECTED_E2_TEX_SPAN).strip()
    normalized_e2 = re.sub(r"\s+", " ", e2).strip()
    if not normalized_e2.startswith(expected_prefix):
        raise AssertionError("E2 randomization or endpoint contract drift")
    rendered_prefix: list[str] = []
    prefix_source_end = 0
    for prefix_source_end, character in enumerate(e2.lstrip(), start=1):
        if character.isspace():
            if rendered_prefix and rendered_prefix[-1] != " ":
                rendered_prefix.append(" ")
        else:
            rendered_prefix.append(character)
        if len(rendered_prefix) >= len(expected_prefix):
            break
    prefix_source = e2.lstrip()[:prefix_source_end]
    if re.search(r"\\[A-Za-z@]+", prefix_source):
        raise AssertionError("unsupported control sequence in E2 contract prefix")


def _assert_matrix_contract(text: str) -> None:
    claim = _matrix_claim(text, "C-E2-ARCH-MECHANISM")
    if claim != EXPECTED_E2_MATRIX_CLAIM:
        raise AssertionError("E2 matrix randomization or endpoint contract drift")


def _validator(kind: str):
    return {
        "sap": _assert_sap_contract,
        "design": _assert_design_contract,
        "matrix": _assert_matrix_contract,
    }[kind]


def _normalized_active_tex(text: str) -> str:
    return re.sub(r"\s+", " ", _active_tex(text).replace(r"\_", "_")).strip()


def _normalized_manuscript_title(text: str) -> str:
    titles = tuple(re.findall(r"\\title\s*\{([^{}]*)\}", _active_tex(text), re.DOTALL))
    if len(titles) != 1:
        raise AssertionError("manuscript title grammar drift")
    return re.sub(r"\s+", " ", titles[0].replace(r"\\", " ")).strip()


def _matrix_status_rows(text: str) -> tuple[tuple[str, str], ...]:
    active = _active_markdown(text)
    registry_start = active.index("\n## Registry\n")
    registry_end = active.index("\n## Exact blocked insertion markers", registry_start)
    rows = []
    for line in active[registry_start:registry_end].splitlines():
        if not line.startswith("| `C-"):
            continue
        cells = tuple(cell.strip() for cell in line.split("|")[1:-1])
        if len(cells) != 9:
            raise AssertionError("claim-matrix row width drift")
        rows.append((cells[0].strip("`"), cells[4].strip("`")))
    return tuple(rows)


def _claim_registry_rows(text: str) -> tuple[tuple[str, str, str], ...]:
    return tuple(
        (claim_id, status.strip(), role.strip())
        for claim_id, status, role in re.findall(
            r"\\claim\{([^{}]+)\}\s*&\s*([^&]+?)\s*&\s*([^\\]+?)\\\\",
            _active_tex(text),
        )
    )


def _assert_cross_file_science_contract(
    *,
    registry: str,
    sap: str,
    related: str,
    claims: str,
    design: str,
    matrix: str,
) -> None:
    active_registry = _active_tex(registry)
    registry_policy_ids = tuple(
        policy.replace(r"\_", "_")
        for policy in re.findall(
            r"\\item\s+\\texttt\{([^{}]+)\}",
            active_registry,
        )
    )
    if (
        len(registry_policy_ids) != EXPECTED_POLICY_COUNT
        or registry_policy_ids != EXPECTED_POLICY_IDS
    ):
        raise AssertionError("policy-registry count or identity drift")
    registry_statuses = tuple(
        status.replace(r"\_", "_")
        for status in re.findall(
            r"\\textbf\{implementation\\_authentication\\_status\}="
            r"\\texttt\{([^{}]+)\}",
            active_registry,
        )
    )
    if (
        registry_statuses
        != ("blocked_pending_authenticated_roster",) * EXPECTED_POLICY_COUNT
    ):
        raise AssertionError("policy-registry authentication promotion")
    if "adapter verified" in _normalized_active_tex(registry).casefold():
        raise AssertionError("adapter-verification promotion")

    normalized_sap = _normalized_active_tex(sap)
    sap_policy_ids = tuple(
        policy.replace(r"\_", "_")
        for policy in re.findall(r"\\texttt\{([^{}]+)\}", _active_tex(sap))
    )
    if sap_policy_ids != EXPECTED_POLICY_IDS:
        raise AssertionError("SAP policy count or identity drift")
    empirical_span = "empirical status remains " + EXPECTED_EMPIRICAL_STATUS
    if normalized_sap.count(empirical_span) != 1:
        raise AssertionError("empirical no-go status drift")
    _assert_sap_contract(sap)
    _assert_design_contract(design)
    _assert_matrix_contract(matrix)

    sap_nonpooling = (
        "Architecture is a prospective stress-test ontology only; JCI-Repair-v1 "
        "is a planned, separate, unpooled replication, and the two ontologies are "
        "never pooled."
    )
    if normalized_sap.count(sap_nonpooling) != 1:
        raise AssertionError("Architecture/JCI SAP nonpooling drift")
    if _matrix_claim(matrix, "C-JCI-REPLICATION") != (
        "JCI is a planned independent E2/E3 replication with its own ontology and "
        "inference; effects are never pooled with Architecture."
    ):
        raise AssertionError("Architecture/JCI matrix nonpooling drift")

    normalized_claims = _normalized_active_tex(claims)
    claim_rows = _claim_registry_rows(claims)
    if len(claim_rows) != 23:
        raise AssertionError("claim-registry cardinality drift")
    claim_statuses = tuple((claim_id, status) for claim_id, status, _role in claim_rows)
    claim_map = {claim_id: (status, role) for claim_id, status, role in claim_rows}
    if {
        claim_id: claim_map.get(claim_id) for claim_id in EXPECTED_CLAIM_UPDATES
    } != EXPECTED_CLAIM_UPDATES:
        raise AssertionError("evaluation-validity claim mapping drift")
    if "C-ACCEPTANCE" in claim_map:
        raise AssertionError("acceptance remains a scientific claim row")
    blocked_claims = tuple(
        claim_id for claim_id, status in claim_statuses if status == "blocked"
    )
    if blocked_claims != EXPECTED_BLOCKED_CLAIMS:
        raise AssertionError("blocked claim set drift")
    matrix_blocked = tuple(
        claim_id
        for claim_id, status in _matrix_status_rows(matrix)
        if status == "BLOCKED"
    )
    if matrix_blocked != EXPECTED_BLOCKED_CLAIMS:
        raise AssertionError("claim-matrix blocked set drift")
    sap_blocked = tuple(re.findall(r"\[\[BLOCKED:([^:]+):", _active_tex(sap)))
    if sap_blocked != EXPECTED_BLOCKED_CLAIMS:
        raise AssertionError("SAP blocked marker set drift")

    for kill_clause in (
        "The symmetric kill chain is load-bearing.",
        "E2 failure in either ontology kills the causal mechanism and ICLR-main thesis.",
        "After positive E2, E3 failure in either ontology kills the OACS method and ICLR-main policy claim.",
    ):
        if normalized_claims.count(kill_clause) != 1:
            raise AssertionError("E2/E3 kill-chain drift")
    normalized_matrix = re.sub(r"\s+", " ", _active_markdown(matrix)).strip()
    if (
        normalized_matrix.count("E1 never rescues E2 or E3. E4 never precedes them.")
        != 1
    ):
        raise AssertionError("E1--E4 kill-chain drift")

    normalized_related = _normalized_active_tex(related)
    if normalized_related.count("The retrospective oracle is not a 23rd policy") != 1:
        raise AssertionError("Related Work retrospective-oracle drift")
    if (
        normalized_sap.count(
            "The retrospective oracle is excluded from the 22-policy roster"
        )
        != 1
    ):
        raise AssertionError("SAP retrospective-oracle drift")


class ScientificContractAlignmentTests(unittest.TestCase):
    def test_related_work_preregisters_a_prospective_test(self) -> None:
        related = _normalized_active_tex(_read(RELATED_WORK))
        self.assertIn(
            "The paper specifies and preregisters a prospective, falsifiable test "
            "for verified executed bundles under a fixed causal and equal-information "
            "protocol; it does not claim that routing, specialization, noncompliance "
            "correction, or orthogonal scores are new in isolation.",
            related,
        )
        self.assertNotIn("The paper tests a joint, falsifiable implication", related)

    def test_conclusion_uses_manuscript_framing(self) -> None:
        conclusion = _normalized_active_tex(_read(CONCLUSION))
        self.assertIn(
            "This manuscript makes a narrow proposition testable:",
            conclusion,
        )
        self.assertNotIn("This blueprint", conclusion)

    def test_e2_nonestimability_sentence_is_grammatical_and_exact(self) -> None:
        problem = _normalized_active_tex(_read(PROBLEM_FORMULATION))
        self.assertIn(
            "Any required primary or negative-control cell mismatch, noncompliance, "
            "missing receipt, or attrition renders the entire ontology-specific "
            "confirmatory E2 estimand nonestimable and every confirmatory numeric "
            "field None.",
            problem,
        )
        self.assertNotIn(
            "makes the entire ontology-specific confirmatory E2 estimand and every "
            "confirmatory numeric field are nonestimable/None",
            problem,
        )

    def test_reviewer_attack_owner_states_current_evidence_boundary(self) -> None:
        matrix = _active_markdown(_read(REVIEWER_ATTACK_MATRIX))
        for required in (
            "**Date:** 2026-09-01",
            "The frozen failed V1 Architecture development diagnostic is the only "
            "observed object discussed here; it is an immutable development "
            "diagnostic outside E1--E4.",
            "Architecture is a prospective stress-test ontology; no real site/target "
            "roster exists, and it supplies no observed performance or "
            "generalization evidence.",
            "JCI is a planned, unexecuted, independent, unpooled replication; no JCI "
            "roster or evidence exists.",
            "E1--E4 are prospective and unexecuted.",
            "Acceptance is a venue outcome nonclaim outside the scientific registry.",
            "No observed evidence supports lower cost, safety, deployment readiness, "
            "or generalization.",
        ):
            with self.subTest(required=required):
                self.assertIn(required, matrix)
        for stale in (
            "**Date:** 2026-08-22",
            "Architecture flagship and JCI independent replication have separate rosters",
            "This blueprint",
        ):
            with self.subTest(stale=stale):
                self.assertNotIn(stale, matrix)

    def test_evaluation_validity_title_claims_narrative_and_slots(self) -> None:
        main_source = _read(MAIN)
        main = _normalized_active_tex(main_source)
        intro = _normalized_active_tex(_read(INTRODUCTION))
        problem = _normalized_active_tex(_read(PROBLEM_FORMULATION))
        results = _normalized_active_tex(_read(RESULTS))
        claims = _read(CLAIMS)
        matrix = _read(CLAIM_MATRIX)

        self.assertEqual(
            _active_tex(main_source).count(
                rf"\title{{{EXPECTED_RAW_MANUSCRIPT_TITLE}}}"
            ),
            1,
        )
        self.assertEqual(
            _normalized_manuscript_title(main_source), EXPECTED_MANUSCRIPT_TITLE
        )
        self.assertNotRegex(main_source, r"\\hyphenation\s*\{")
        for identity in EXPECTED_EVALUATION_IDENTITIES:
            self.assertIn(identity, main)
            self.assertIn(identity, intro)

        claim_rows = _claim_registry_rows(claims)
        self.assertEqual(len(claim_rows), 23)
        claim_map = {claim_id: (status, role) for claim_id, status, role in claim_rows}
        self.assertEqual(
            {claim_id: claim_map[claim_id] for claim_id in EXPECTED_CLAIM_UPDATES},
            EXPECTED_CLAIM_UPDATES,
        )
        self.assertNotIn("C-ACCEPTANCE", claim_map)

        matrix_statuses = dict(_matrix_status_rows(matrix))
        self.assertEqual(len(matrix_statuses), 23)
        self.assertEqual(matrix_statuses["C-DEV-DIAGNOSTIC"], "READY")
        for claim_id in (
            "C-THESIS",
            "C-ARCH-FLAGSHIP",
            "C-JCI-REPLICATION",
        ):
            self.assertEqual(matrix_statuses[claim_id], "STRUCTURAL_ONLY")
        self.assertNotIn("C-ACCEPTANCE", matrix_statuses)
        self.assertIn(
            "Acceptance is a venue outcome nonclaim outside the scientific registry.",
            _active_markdown(matrix),
        )

        self.assertEqual(results.count(FROZEN_DIAGNOSTIC_PARAGRAPH), 1)
        self.assertEqual(
            tuple(re.findall(r"\\blocked\{([^{}]+)\}", _read(RESULTS))),
            EXPECTED_RESULT_SLOT_IDS,
        )
        closure = " ".join((main, intro, problem, results))
        for span in (
            "A completed orchestration trace is not an identified coordination treatment.",
            "failed its prespecified terminal-reliability gate",
            "The frozen no-rescore rule leaves the V1 result unchanged.",
            "V2 is prospective.",
            "It therefore estimates neither OACS benefit nor harm",
            "Receipt failure makes the corresponding estimand nonestimable.",
        ):
            self.assertIn(span, closure)

    def test_cross_file_policy_empirical_and_kill_chain_contract(self) -> None:
        _assert_cross_file_science_contract(
            registry=_read(POLICY_REGISTRY),
            sap=_read(SAP),
            related=_read(RELATED_WORK),
            claims=_read(CLAIMS),
            design=_read(DESIGN),
            matrix=_read(CLAIM_MATRIX),
        )
        self.assertEqual(_frozen_endpoint_from_ast(), EXPECTED_E2_ENDPOINT)

    def test_adapter_verified_registry_attack_rejects_without_sap_change(
        self,
    ) -> None:
        sources = {
            "registry": POLICY_REGISTRY,
            "sap": SAP,
            "related": RELATED_WORK,
            "claims": CLAIMS,
            "design": DESIGN,
            "matrix": CLAIM_MATRIX,
        }
        with tempfile.TemporaryDirectory() as temporary:
            copied_root = Path(temporary) / "copied-science-root"
            copied = {}
            for name, source in sources.items():
                destination = copied_root / source.relative_to(REPOSITORY)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
                copied[name] = destination
            baseline = {name: _read(path) for name, path in copied.items()}
            _assert_cross_file_science_contract(
                **baseline,
            )
            sap_before = copied["sap"].read_bytes()
            registry = baseline["registry"]
            attacked_registry = registry.replace(
                r"\citep{zhang2025agentprune}",
                "adapter verified",
                1,
            )
            self.assertNotEqual(attacked_registry, registry)
            copied["registry"].write_text(
                attacked_registry,
                encoding="utf-8",
                newline="\n",
            )
            self.assertEqual(copied["sap"].read_bytes(), sap_before)
            attacked = {name: _read(path) for name, path in copied.items()}
            with self.assertRaises(AssertionError):
                _assert_cross_file_science_contract(**attacked)

    def test_authority_ast_matches_test_owned_fields_and_endpoint(self) -> None:
        self.assertEqual(
            _literal_assignment(OBLIGATION_ORACLE, "_E3_PARENT_FIELDS"),
            EXPECTED_PARENT_FIELDS,
        )
        self.assertEqual(
            _literal_assignment(OBLIGATION_ORACLE, "_E3_SHARED_FIELDS"),
            EXPECTED_SHARED_FIELDS,
        )
        self.assertEqual(_frozen_endpoint_from_ast(), EXPECTED_E2_ENDPOINT)

    def test_sap_parent_fields_match_authority_contract(self) -> None:
        observed_parent, _observed_shared = _sap_lists(_read(SAP))
        self.assertEqual(observed_parent, EXPECTED_PARENT_FIELDS)

    def test_sap_shared_fields_match_authority_contract(self) -> None:
        _observed_parent, observed_shared = _sap_lists(_read(SAP))
        self.assertEqual(observed_shared, EXPECTED_SHARED_FIELDS)

    def test_rendered_design_states_within_stratum_e2_contract(self) -> None:
        _assert_design_contract(_read(DESIGN))

    def test_claim_matrix_states_exact_e2_estimand(self) -> None:
        self.assertEqual(
            _matrix_claim(_read(CLAIM_MATRIX), "C-E2-ARCH-MECHANISM"),
            EXPECTED_E2_MATRIX_CLAIM,
        )

    def test_mutation_family_has_test_owned_expected_hashes(self) -> None:
        observed = {name: _sha256(text) for name, (_kind, text) in _mutations().items()}
        self.assertEqual(observed, EXPECTED_MUTATION_SHA256)

    def test_mutations_are_rejected_by_the_independent_contract(self) -> None:
        for name, (kind, mutation) in _mutations().items():
            with self.subTest(name=name):
                with self.assertRaises(AssertionError):
                    _validator(kind)(mutation)

    def test_inactive_e2_decoy_cannot_satisfy_active_paragraph(self) -> None:
        active_bad = _read(DESIGN).replace(
            EXPECTED_E2_TEX_SPAN,
            "The primary endpoint is complete-bundle presence minus residual absence.",
        )
        attacked = f"{active_bad}\n\\iffalse\n{EXPECTED_E2_TEX_SPAN}\n\\fi\n"
        validator = globals().get("_assert_design_contract", lambda _text: None)
        with self.assertRaises(AssertionError):
            validator(attacked)

    def test_nonrendered_e2_macro_argument_cannot_satisfy_active_paragraph(
        self,
    ) -> None:
        decoy = (
            "The primary endpoint is complete-bundle presence minus residual absence.\n"
            f"\\newcommand{{\\eTwoDecoy}}{{{EXPECTED_E2_TEX_SPAN}}}"
        )
        attacked = _read(DESIGN).replace(EXPECTED_E2_TEX_SPAN, decoy)
        with self.assertRaises(AssertionError):
            _assert_design_contract(attacked)

    def test_nonrendered_e2_label_argument_cannot_satisfy_active_paragraph(
        self,
    ) -> None:
        decoy = (
            "Residual status is randomized and presence versus absence is the treatment.\n"
            f"\\label{{{EXPECTED_E2_TEX_SPAN}}}"
        )
        attacked = _read(DESIGN).replace(EXPECTED_E2_TEX_SPAN, decoy)
        with self.assertRaises(AssertionError):
            _assert_design_contract(attacked)

    def test_inactive_sap_inventory_decoy_cannot_satisfy_live_e3(self) -> None:
        sap = _read(SAP)
        active_bad = sap.replace(
            r"learner\_class\_capacity",
            r"learner\_capacity",
        )
        attacked = f"{active_bad}\n\\iffalse\n{sap}\n\\fi\n"
        validator = globals().get("_assert_sap_contract", lambda _text: None)
        with self.assertRaises(AssertionError):
            validator(attacked)

    def test_nonrendered_sap_label_argument_cannot_satisfy_live_e3(self) -> None:
        sap = _read(SAP)
        start = sap.index(
            "Both views are complete bijections over exactly 15 canonical parent payload"
        )
        terminator = "Both projected"
        end = sap.index(terminator, start) + len(terminator)
        inventory_decoy = sap[start:end]
        attacked = (
            f"{sap[:start]}Rendered parity inventories are unavailable.\n"
            f"\\label{{{inventory_decoy}}}{sap[end:]}"
        )
        with self.assertRaises(AssertionError):
            _assert_sap_contract(attacked)

    def test_complete_sap_owner_nested_in_label_argument_is_rejected(self) -> None:
        sap = _read(SAP)
        owner_start = sap.index(r"{\raggedright")
        owner_end_marker = "  \\par\n  }"
        owner_end = sap.index(owner_end_marker, owner_start) + len(owner_end_marker)
        owner = sap[owner_start:owner_end]
        attacked = f"{sap[:owner_start]}\\label{{{owner}}}{sap[owner_end:]}"
        with self.assertRaises(AssertionError):
            _assert_sap_contract(attacked)

    def test_sap_owner_argument_brace_for_label_is_rejected(self) -> None:
        sap = _read(SAP)
        owner_start = sap.index(r"{\raggedright")
        attacked = sap[:owner_start] + r"\label{" + sap[owner_start + 1 :]
        self.assertEqual(
            _sha256(attacked),
            "073534f48b2754207b2a363e204ec8296bee9625839228f3561eac885ec971db",
        )
        with self.assertRaises(AssertionError):
            _assert_sap_contract(attacked)

    def test_sap_owner_argument_brace_for_generic_control_word_is_rejected(
        self,
    ) -> None:
        sap = _read(SAP)
        owner_start = sap.index(r"{\raggedright")
        attacked = sap[:owner_start] + r"\inventoryholder " + sap[owner_start:]
        self.assertEqual(
            _sha256(attacked),
            "66fe093baadb124cd310637b442ead3ccdf55f0fafdecb0838d211ef99d3c7b2",
        )
        with self.assertRaises(AssertionError):
            _assert_sap_contract(attacked)

    def test_sap_owner_rejects_unclosed_outer_brace(self) -> None:
        attacked = _read(SAP).replace(
            r"{\raggedright",
            r"{{\raggedright",
            1,
        )
        with self.assertRaises(AssertionError):
            _assert_sap_contract(attacked)

    def test_sap_owner_rejects_brace_underflow(self) -> None:
        attacked = _read(SAP).replace(
            r"{\raggedright",
            r"}{\raggedright",
            1,
        )
        with self.assertRaises(AssertionError):
            _assert_sap_contract(attacked)

    def test_out_of_registry_matrix_row_decoy_cannot_satisfy_registry(self) -> None:
        matrix = _read(CLAIM_MATRIX)
        row = next(
            line
            for line in matrix.splitlines()
            if line.startswith("| `C-E2-ARCH-MECHANISM` |")
        )
        active_bad = matrix.replace(
            EXPECTED_E2_MATRIX_CLAIM, "Architecture E2 is causal."
        )
        attacked = f"{active_bad}\n## Decoy rows\n\n{row}\n"
        validator = globals().get("_assert_matrix_contract", lambda _text: None)
        with self.assertRaises(AssertionError):
            validator(attacked)

    def test_fenced_matrix_row_decoy_cannot_satisfy_registry(self) -> None:
        matrix = _read(CLAIM_MATRIX)
        row = next(
            line
            for line in matrix.splitlines()
            if line.startswith("| `C-E2-ARCH-MECHANISM` |")
        )
        active_bad = matrix.replace(
            EXPECTED_E2_MATRIX_CLAIM, "Architecture E2 is causal."
        )
        attacked = f"{active_bad}\n```markdown\n{row}\n```\n"
        validator = globals().get("_assert_matrix_contract", lambda _text: None)
        with self.assertRaises(AssertionError):
            validator(attacked)

    def test_html_comment_matrix_row_decoy_cannot_satisfy_registry(self) -> None:
        matrix = _read(CLAIM_MATRIX)
        row = next(
            line
            for line in matrix.splitlines()
            if line.startswith("| `C-E2-ARCH-MECHANISM` |")
        )
        active_bad = matrix.replace(
            EXPECTED_E2_MATRIX_CLAIM, "Architecture E2 is causal."
        )
        attacked = f"{active_bad}\n<!--\n{row}\n-->\n"
        validator = globals().get("_assert_matrix_contract", lambda _text: None)
        with self.assertRaises(AssertionError):
            validator(attacked)

    def test_registry_section_nontable_row_decoy_cannot_satisfy_live_table(
        self,
    ) -> None:
        matrix = _read(CLAIM_MATRIX)
        row = next(
            line
            for line in matrix.splitlines()
            if line.startswith("| `C-E2-ARCH-MECHANISM` |")
        )
        active_bad = matrix.replace(
            "| `C-E2-ARCH-MECHANISM` |",
            "| `C-E2-ARCH-MECHANISM-DRIFTED` |",
            1,
        )
        next_section = active_bad.index("\n## Exact blocked insertion markers")
        attacked = (
            f"{active_bad[:next_section]}\n### Decoy outside the live table\n\n"
            f"{row}\n{active_bad[next_section:]}"
        )
        with self.assertRaises(AssertionError):
            _assert_matrix_contract(attacked)

    def test_parent_inventory_learner_capacity_mutation_is_rejected(self) -> None:
        mutated = _read(SAP).replace(
            r"learner\_class\_capacity",
            r"learner\_capacity",
            1,
        )
        validator = globals().get("_assert_sap_contract", lambda _text: None)
        with self.assertRaises(AssertionError):
            validator(mutated)

    def test_shared_inventory_learner_capacity_mutation_is_rejected(self) -> None:
        sap = _read(SAP)
        token = r"learner\_class\_capacity"
        first = sap.index(token)
        second = sap.index(token, first + len(token))
        mutated = f"{sap[:second]}learner\\_capacity{sap[second + len(token) :]}"
        validator = globals().get("_assert_sap_contract", lambda _text: None)
        with self.assertRaises(AssertionError):
            validator(mutated)

    def test_randomized_residual_status_full_design_mutation_is_rejected(self) -> None:
        mutated = _read(DESIGN).replace(
            "residual status itself is not\nrandomized",
            "residual status itself is\nrandomized",
        )
        validator = globals().get("_assert_design_contract", lambda _text: None)
        with self.assertRaises(AssertionError):
            validator(mutated)

    def test_presence_versus_absence_full_design_mutation_is_rejected(self) -> None:
        mutated = _read(DESIGN).replace(
            "the residual-present high-minus-low\ncomplete-bundle effect minus the matched residual-absent high-minus-low effect",
            "complete-bundle presence minus residual absence",
        )
        validator = globals().get("_assert_design_contract", lambda _text: None)
        with self.assertRaises(AssertionError):
            validator(mutated)

    def test_swapped_subtraction_full_matrix_mutation_is_rejected(self) -> None:
        mutated = _read(CLAIM_MATRIX).replace(
            "(residual-present high-minus-low) minus (residual-absent high-minus-low)",
            "(residual-absent high-minus-low) minus (residual-present high-minus-low)",
        )
        validator = globals().get("_assert_matrix_contract", lambda _text: None)
        with self.assertRaises(AssertionError):
            validator(mutated)

    def test_omitted_absent_high_low_full_matrix_mutation_is_rejected(self) -> None:
        mutated = _read(CLAIM_MATRIX).replace(
            "(residual-present high-minus-low) minus (residual-absent high-minus-low)",
            "(residual-present high-minus-low)",
        )
        validator = globals().get("_assert_matrix_contract", lambda _text: None)
        with self.assertRaises(AssertionError):
            validator(mutated)

    def test_causal_residual_wording_full_matrix_mutation_is_rejected(self) -> None:
        mutated = _read(CLAIM_MATRIX).replace(
            "residual status itself is not randomized",
            "residual status causally determines closure quality",
        )
        validator = globals().get("_assert_matrix_contract", lambda _text: None)
        with self.assertRaises(AssertionError):
            validator(mutated)


if __name__ == "__main__":
    unittest.main()
