"""Independent scientific-boundary tests for the Task-11 manuscript subset.

This module deliberately owns its review literals.  It imports neither the
future static verifier nor manuscript constants, so a shared bad constant
cannot make both the paper and its checker agree.
"""

from __future__ import annotations

import ast
import builtins
from collections import Counter
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import socket
import subprocess
import tempfile
import unittest
from unittest import mock
from pathlib import Path

import iclr2027.paper_latex_verification as _paper_verification
import verify_iclr2027_paper_latex as _paper_cli
from iclr2027.paper_latex_verification import (
    PaperLatexVerificationError,
    PaperStaticReceipt,
    verify_static_paper_latex,
)


REPOSITORY = Path(__file__).resolve().parents[1]
PAPER = Path("docs/paper/iclr2027_oacs")
PRIMARY_MANIFEST = REPOSITORY / PAPER / "literature_primary_source_manifest.md"
SPEC_SHA256 = "5924ebdbca94814c538a4317967e4fa99da96ffcc92f7e59f75b30d5d46798fd"
PREFIX_BIB_SHA256 = "10716dbd880c487e70a7cbd9fed4546a5f160d4b2126a4971943ca032b707659"
BASE_MANUSCRIPT_SOURCE_CLOSURE = (
    "latex/main.tex",
    "latex/README.md",
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
    "latex/appendices/appendix_claims.tex",
    "latex/appendices/appendix_analysis_protocol.tex",
    "latex/appendices/appendix_policy_provenance.tex",
    "latex/appendices/appendix_reviewer_attacks.tex",
    "latex/appendices/appendix_theory.tex",
)
OFFICIAL_STYLE_ARCHIVE_URL = (
    "https://media.iclr.cc/Conferences/ICLR2027/iclr-2027-style-files.zip"
)
OFFICIAL_STYLE_ARCHIVE_LENGTH = 39_348
OFFICIAL_STYLE_ARCHIVE_SHA256 = (
    "0D940DFA9398AE99A18F24A85A8A683F367204B6AF6D17D2899E60A67102529E"
)
VENDOR_SOURCE_IDENTITIES = (
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
OMITTED_ARCHIVE_MEMBERS = (
    "iclr2027/iclr2027_conference.bib",
    "iclr2027/iclr2027_conference.tex",
    "iclr2027/math_commands.tex",
)
SUBMISSION_STATEMENTS_RELATIVE = "latex/sections/10_submission_statements.tex"
MANUSCRIPT_SOURCE_CLOSURE = tuple(
    sorted(
        (*BASE_MANUSCRIPT_SOURCE_CLOSURE, SUBMISSION_STATEMENTS_RELATIVE),
        key=lambda value: value.encode("utf-8"),
    )
)
VENDOR_SOURCE_CLOSURE = tuple(
    path for path, _length, _digest in VENDOR_SOURCE_IDENTITIES
)
VENUE_SOURCE_CLOSURE = tuple(
    sorted(
        (*MANUSCRIPT_SOURCE_CLOSURE, *VENDOR_SOURCE_CLOSURE),
        key=lambda value: value.encode("utf-8"),
    )
)
SOURCE_CLOSURE = VENUE_SOURCE_CLOSURE
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
FROZEN_DIAGNOSTIC_PARAGRAPH = (
    "The frozen Architecture development diagnostic completed execution and "
    "artifact closure but failed its prespecified terminal-reliability gate. A "
    "later public-synthetic audit exposed a mismatch between cumulative provenance "
    "and current terminal assessment. The frozen no-rescore rule leaves the V1 "
    "result unchanged. It therefore estimates neither OACS benefit nor harm and "
    "provides no evidence about the corrected V2 evaluator. Its narrower role is "
    "to document failed evaluability and motivate fresh, versioned evidence."
)
REQUIRED_EVALUATION_VALIDITY_SPANS = (
    "A completed orchestration trace is not an identified coordination treatment.",
    "failed its prespecified terminal-reliability gate",
    "The frozen no-rescore rule leaves the V1 result unchanged.",
    "V2 is prospective.",
    "It therefore estimates neither OACS benefit nor harm",
    "Receipt failure makes the corresponding estimand nonestimable.",
)
FORBIDDEN_EVALUATION_VALIDITY_ATTACKS = (
    "V2 repairs the historical V1 result",
    "the development diagnostic supports OACS benefit",
    "the development diagnostic refutes OACS benefit",
    "the development diagnostic is confirmatory E2 evidence",
    "the threshold was retrospectively replaced",
    "Architecture establishes generality",
    "JCI replication is complete",
)
COMPOSITIONAL_EVALUATION_VALIDITY_ATTACKS = (
    (
        "retrospective V2 repair",
        "The corrected evaluator retroactively repairs the frozen V1 diagnostic.",
    ),
    (
        "retrospective V2 supersession",
        "The V1 failure no longer governs because the V2 assessment supersedes it.",
    ),
    (
        "diagnostic benefit",
        "Observed diagnostic evidence demonstrates that OACS improves outcomes.",
    ),
    (
        "diagnostic harm",
        "Observed diagnostic evidence demonstrates that OACS degrades outcomes.",
    ),
    (
        "E1 promotion",
        "Historical diagnostic evidence supplies confirmatory support for E1.",
    ),
    (
        "E2 promotion",
        "Historical diagnostic evidence supports the E2 mechanism claim.",
    ),
    (
        "E3 promotion",
        "Historical diagnostic evidence validates the E3 policy comparison.",
    ),
    (
        "E4 promotion",
        "Historical diagnostic evidence establishes E4 deployment effectiveness.",
    ),
    (
        "retrospective threshold substitution",
        "The historical terminal gate is recomputed with the corrected threshold.",
    ),
    (
        "retrospective metric substitution",
        "A replacement metric now determines the V1 result.",
    ),
    (
        "Architecture external-validity promotion",
        "Success in the Architecture setting establishes broad external validity.",
    ),
    (
        "Architecture cross-domain promotion",
        "The typed Architecture ontology generalizes across domains.",
    ),
    (
        "completed JCI execution",
        "The independent JCI study has finished execution.",
    ),
    (
        "completed JCI evidence",
        "JCI now provides completed replication evidence.",
    ),
    (
        "positive cost",
        "Observed evidence establishes lower operating cost for OACS.",
    ),
    (
        "positive safety",
        "Observed evidence proves OACS is safer.",
    ),
    (
        "positive deployment",
        "Observed evidence confirms OACS deployment readiness.",
    ),
    (
        "positive generalization",
        "Observed evidence establishes cross-domain generalization.",
    ),
    (
        "positive acceptance",
        "Conference acceptance has been secured.",
    ),
)
HIGH_RISK_AUTHORIAL_SENTENCE_ATTACKS = (
    ("V1 repair", "The corrected evaluator fixes the historical V1 diagnostic."),
    (
        "diagnostic benefit",
        "The historical diagnostic indicates an OACS benefit.",
    ),
    (
        "diagnostic harm",
        "The V1 diagnostic reveals that OACS harms outcomes.",
    ),
    ("E1 promotion", "The V1 diagnostic serves as evidence for E1."),
    ("E2 promotion", "The V1 diagnostic serves as evidence for E2."),
    ("E3 promotion", "The V1 diagnostic serves as evidence for E3."),
    ("E4 promotion", "The V1 diagnostic serves as evidence for E4."),
    (
        "corrected metric",
        "The historical terminal gate now uses the corrected metric.",
    ),
    (
        "Architecture cross-domain conclusion",
        "Architecture warrants cross-domain conclusions.",
    ),
    ("completed JCI", "The JCI replication is now done."),
    ("positive cost", "Operating expenses fall under OACS."),
    (
        "positive safety",
        "The deployment meets all safety requirements under OACS.",
    ),
    ("positive deployment", "Deployment suitability holds for OACS."),
    (
        "positive generalization",
        "Transfer across domains holds for OACS.",
    ),
    ("positive acceptance", "The venue approved this paper."),
)
LEGACY_HIGH_RISK_EVALUATION_TOPIC = re.compile(
    r"\b(?:OACS|JCI|V1|V2|diagnostic|confirmatory|E[1-4]|threshold|metrics?|"
    r"costs?|expenses?|affordab\w*|efficien\w*|safety|safe|safer|deployment|"
    r"deployable|generality|generali[sz]\w*|cross-domain|external validity|"
    r"transfer across domains)\b|"
    r"\b(?:venue|conference|ICLR)\b[^.!?]{0,120}\b(?:accept\w*|approv\w*|"
    r"paper|manuscript|decision|outcome)\b|"
    r"\b(?:paper|manuscript)\b[^.!?]{0,120}\b(?:venue|conference|ICLR)\b",
    re.IGNORECASE,
)
SYNONYM_ONLY_AUTHORIAL_SENTENCE_ATTACKS = (
    (
        "frozen-result rehabilitation",
        "The amended evaluator rehabilitates the frozen result.",
    ),
    ("historical efficacy", "The historical run demonstrates efficacy."),
    ("revised cutoff", "The old gate now uses a revised cutoff."),
    (
        "built-environment transfer",
        "The built-environment setting warrants broad transfer.",
    ),
    (
        "finished second setting",
        "The second-setting replication has finished.",
    ),
    ("lower operational expenditure", "Operational expenditure falls."),
    ("controlled risk", "Risk is demonstrably controlled."),
    ("production justification", "Production use is justified."),
    ("broad findings transfer", "Findings transfer broadly."),
    (
        "reviewer approval",
        "Reviewers have approved the submission.",
    ),
)
HIGH_RISK_AUTHORIAL_SENTENCE_NONCLAIMS = (
    (
        "common explicit negation",
        "The JCI study has not finished execution.",
    ),
    (
        "preposed attack framing",
        "A forbidden interpretation is that the corrected evaluator repairs "
        "historical V1.",
    ),
    (
        "postposed attack framing",
        "The claim that the corrected evaluator repairs historical V1 is a "
        "forbidden interpretation.",
    ),
)
SAP_RELATIVE = "latex/appendices/appendix_analysis_protocol.tex"
SAP_INPUT = "appendices/appendix_analysis_protocol"
POLICY_PROVENANCE_RELATIVE = "latex/appendices/appendix_policy_provenance.tex"
POLICY_PROVENANCE_INPUT = "appendices/appendix_policy_provenance"
SAP_EXPECTED_INPUTS = (
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
    SAP_INPUT,
    POLICY_PROVENANCE_INPUT,
    "appendices/appendix_claims",
    "appendices/appendix_reviewer_attacks",
)
SAP_EXPECTED_SOURCE_CLOSURE = tuple(
    sorted(SOURCE_CLOSURE, key=lambda path: path.encode("utf-8"))
)
OFFICIAL_PACKAGE_INVOCATION = r"\usepackage{iclr2027_conference,times}"
T1_FONT_ENCODING_INVOCATION = r"\usepackage[T1]{fontenc}"
OFFICIAL_BIBLIOGRAPHY_STYLE = r"\bibliographystyle{iclr2027_conference}"
SUBMISSION_STATEMENTS_INPUT = r"\input{sections/10_submission_statements}"
AI_USE_REQUIRED_SPANS = (
    "research ideation and refinement of the residual-obligation hypothesis",
    "design, critique, and documentation of the E1--E4 evaluation program",
    "static manuscript-verification software and tests",
    "literature organization, comparison, and source discovery",
    "No generative-AI output is presented as authenticated empirical data",
    "Submission remains blocked until all authors review",
)
REPRODUCIBILITY_REQUIRED_SPANS = (
    "claim-locked evaluation-validity manuscript",
    "does not claim confirmatory empirical reproducibility",
    "no authenticated external source package",
    "no signed site/target roster",
    "no fresh V2 execution receipt, policy-decision bundle, or confirmatory result\nartifact",
)
AI_USE_TASK_MUTATIONS = (
    (
        "ideation and hypothesis refinement",
        "research ideation and refinement of the residual-obligation hypothesis",
        "generic language assistance",
    ),
    (
        "evaluation-program design and critique",
        "design, critique, and documentation of the E1--E4 evaluation program",
        "generic language assistance",
    ),
    (
        "static-verifier implementation and review",
        "static manuscript-verification software and tests",
        "generic language assistance",
    ),
    (
        "manuscript drafting editing and structure",
        "drafting, editing, and\nstructuring portions of the manuscript",
        "generic language assistance",
    ),
    (
        "literature organization comparison and discovery",
        "literature organization, comparison, and source discovery",
        "generic language assistance",
    ),
)
STATEMENT_TRUTH_MUTATIONS = (
    *AI_USE_TASK_MUTATIONS,
    (
        "authenticated empirical-data nonclaim",
        "No generative-AI output is presented as authenticated empirical data",
        "AI assistance was documented",
    ),
    (
        "evaluation-validity manuscript status",
        "claim-locked evaluation-validity manuscript",
        "research report",
    ),
    (
        "empirical-reproducibility nonclaim",
        "does not claim confirmatory empirical reproducibility",
        "discusses empirical reproducibility",
    ),
    (
        "external-source-package absence",
        "no authenticated external source package",
        "an external source package",
    ),
    (
        "signed-roster absence",
        "no signed site/target roster",
        "a site/target roster",
    ),
    (
        "fresh-V2 artifact absence",
        "no fresh V2 execution receipt, policy-decision bundle, or confirmatory result\nartifact",
        "supporting materials",
    ),
)
VENUE_FORBIDDEN_POSITIVE_PHRASES = (
    "submission-ready",
    "page-limit compliant",
    "PDF verified",
    "experiments were run",
    "results are reproducible",
    "accepted at ICLR",
)
SAP_PARITY_PARENT_FIELDS = (
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
SAP_SHARED_OPPORTUNITY_FIELDS = (
    "costs",
    "admissibility",
    "examples",
    "split_fold",
    "learner_class_capacity",
    "tuning_optimization_opportunity",
    "action_space_tie_rule",
)
SAP_BLOCKED_MARKERS = (
    "[[BLOCKED:C-E1-PREDICTION:authenticated held-out learner and calibration evidence]]",
    "[[BLOCKED:C-E2-ARCH-MECHANISM:authenticated Architecture assignment-execution-outcome receipt]]",
    "[[BLOCKED:C-E2-JCI-MECHANISM:authenticated JCI assignment-execution-outcome receipt]]",
    "[[BLOCKED:C-E3-ARCH-POLICY:authenticated Architecture equal-information decision bundle]]",
    "[[BLOCKED:C-E3-JCI-POLICY:authenticated JCI equal-information decision bundle]]",
    "[[BLOCKED:C-E4-DEPLOYMENT:fresh downstream protocol and prerequisite passes]]",
    "[[BLOCKED:C-COST:signed manifests rates and execution census]]",
    "[[BLOCKED:C-SAFETY:separate safety study]]",
    "[[BLOCKED:C-GENERALIZATION:positive compliant evidence in both ontologies and external validation]]",
)
SAP_ITEM_LABELS = (
    "Scope and hierarchy.",
    "E1 predictive protocol.",
    "E2 estimand and controls.",
    "Identification, compliance, and support.",
    "E2 inference.",
    "E3 estimand and parity.",
    "Policy eligibility and oracle.",
    "Multiplicity and kill chain.",
    "Empty result shells.",
    "Blocked evidence markers.",
    "Nonclaims and status.",
)
SAP_REVIEW_SUPPORT_SPAN = (
    "Pre-outcome adequate support requires both packet assignments, the "
    "residual-absent control, the uniform-random control, and frozen cost, "
    "information, budget, tool, synthesis-path, and admissibility balance "
    "functions and thresholds in the Phase-B freeze receipt before paid calls."
)
SAP_REVIEW_PRECALL_STOP_SPAN = (
    "The pre-call structural STOP fires if ontologies or the capability audit "
    "are not frozen, common support is weak or empty, complete crossover, "
    "manifest, or isolation cannot be authenticated, evaluator invariance or "
    "audit agreement fails its frozen criterion, mandatory baseline fidelity is "
    "unresolved, JCI is not independently deterministic, or the frozen design "
    "cannot meet its power or budget criterion."
)
SAP_REVIEW_E1_FAILURE_SPAN = (
    "No held-out E1 predictive improvement removes the difficulty headline and "
    "blocks E1-dependent E4, but neither kills nor rescues a separately "
    "compliant E2/E3 result."
)
SAP_REVIEW_E2_FALSIFICATION_SPAN = (
    "The E2 mechanism claim also fails if its sign disappears under packet "
    "main-effect or global-strength adjustment, the residual-absent contrast is "
    "equally large, or relabel or misbinding placebos reproduce the effect."
)
SAP_REVIEW_CASE_REPORTING_SPAN = (
    "Every case-level and site-level aggregate is reported for E2 and E3; no "
    "row-level regression standard error is primary."
)
SAP_REVIEW_FIX_SPANS = (
    SAP_REVIEW_SUPPORT_SPAN,
    SAP_REVIEW_PRECALL_STOP_SPAN,
    SAP_REVIEW_E1_FAILURE_SPAN,
    SAP_REVIEW_E2_FALSIFICATION_SPAN,
    SAP_REVIEW_CASE_REPORTING_SPAN,
)
SAP_REVIEW_FIX_MUTATIONS = (
    (
        "support packet assignments",
        SAP_REVIEW_SUPPORT_SPAN,
        "both packet assignments",
        "one packet assignment",
    ),
    (
        "support residual-absent",
        SAP_REVIEW_SUPPORT_SPAN,
        "the residual-absent control",
        "an optional residual-absent control",
    ),
    (
        "support uniform control",
        SAP_REVIEW_SUPPORT_SPAN,
        "the uniform-random control",
        "an optional uniform-random control",
    ),
    (
        "support balance family",
        SAP_REVIEW_SUPPORT_SPAN,
        "cost, information, budget, tool, synthesis-path, and admissibility",
        "cost and information",
    ),
    (
        "support Phase-B threshold freeze",
        SAP_REVIEW_SUPPORT_SPAN,
        "functions and thresholds in the Phase-B freeze receipt before paid calls",
        "functions selected after outcomes",
    ),
    (
        "pre-call ontology freeze",
        SAP_REVIEW_PRECALL_STOP_SPAN,
        "ontologies or the capability audit are not frozen",
        "the Architecture ontology is not frozen",
    ),
    (
        "pre-call common support",
        SAP_REVIEW_PRECALL_STOP_SPAN,
        "common support is weak or empty",
        "common support is empty",
    ),
    (
        "pre-call execution authentication",
        SAP_REVIEW_PRECALL_STOP_SPAN,
        "complete crossover, manifest, or isolation cannot be authenticated",
        "the advertised packet name is missing",
    ),
    (
        "pre-call evaluator criterion",
        SAP_REVIEW_PRECALL_STOP_SPAN,
        "evaluator invariance or audit agreement fails its frozen criterion",
        "the evaluator is unavailable",
    ),
    (
        "pre-call baseline fidelity",
        SAP_REVIEW_PRECALL_STOP_SPAN,
        "mandatory baseline fidelity is unresolved",
        "one baseline is inconvenient",
    ),
    (
        "pre-call JCI determinism",
        SAP_REVIEW_PRECALL_STOP_SPAN,
        "JCI is not independently deterministic",
        "JCI is not available",
    ),
    (
        "pre-call power budget",
        SAP_REVIEW_PRECALL_STOP_SPAN,
        "cannot meet its power or budget criterion",
        "has not reported a result",
    ),
    (
        "E1 failure headline",
        SAP_REVIEW_E1_FAILURE_SPAN,
        "removes the difficulty headline",
        "retains the difficulty headline",
    ),
    (
        "E1-dependent E4 blocked",
        SAP_REVIEW_E1_FAILURE_SPAN,
        "blocks E1-dependent E4",
        "permits E1-dependent E4",
    ),
    (
        "E1 cannot kill E2/E3",
        SAP_REVIEW_E1_FAILURE_SPAN,
        "neither kills nor rescues",
        "kills but does not rescue",
    ),
    (
        "E1 cannot rescue E2/E3",
        SAP_REVIEW_E1_FAILURE_SPAN,
        "neither kills nor rescues",
        "does not kill but rescues",
    ),
    (
        "E1 compliant E2/E3 scope",
        SAP_REVIEW_E1_FAILURE_SPAN,
        "a separately compliant E2/E3 result",
        "an E1-selected E2 subgroup",
    ),
    (
        "E2 packet adjustment",
        SAP_REVIEW_E2_FALSIFICATION_SPAN,
        "packet main-effect or global-strength adjustment",
        "an optional adjusted model",
    ),
    (
        "E2 absent contrast",
        SAP_REVIEW_E2_FALSIFICATION_SPAN,
        "the residual-absent contrast is equally large",
        "the residual-absent contrast is omitted",
    ),
    (
        "E2 placebo reproduction",
        SAP_REVIEW_E2_FALSIFICATION_SPAN,
        "relabel or misbinding placebos reproduce the effect",
        "one placebo is favorable",
    ),
    (
        "case-level E2/E3",
        SAP_REVIEW_CASE_REPORTING_SPAN,
        "Every case-level and site-level aggregate is reported for E2 and E3",
        "Only pooled row-level aggregates are reported",
    ),
    (
        "row-level SE nonprimary",
        SAP_REVIEW_CASE_REPORTING_SPAN,
        "no row-level regression standard error is primary",
        "a row-level regression standard error is primary",
    ),
)
SAP_E3_EXPECTED_SCIENCE_ROWS = (
    (
        r"V_i(a)=\operatorname{mean}_{r}\{Y_{iar}(a)-\lambda_K^\topK_{iar}(a)\},",
        r"\operatorname{Reg}_i(\pi)=\max_{a\in\mathcalA_i}V_i(a)-V_i(\pi(X_i)).",
    ),
    (
        r"\Delta^{\mathrm{raw}}_{E3}=\operatorname{mean}_{s}"
        r"\operatorname{mean}_{c\mids}\operatorname{mean}_{i\midsc}"
        r"\{\operatorname{Reg}_i(\pi_O^{-s})-\operatorname{Reg}_i(\pi_R^{-s})\},",
        r"D_i=V_i(\pi_R^{-s}(X_i))-V_i(\pi_O^{-s}(X_i)).",
    ),
)
SAP_E3_EXPECTED_ALIGNED_DISPLAYS = (
    r"""\begin{aligned}
  V_i(a)
    &= \operatorname{mean}_{r}\{Y_{iar}(a)-\lambda_K^\top K_{iar}(a)\},\\
  \operatorname{Reg}_i(\pi)
    &= \max_{a\in\mathcal A_i}V_i(a)-V_i(\pi(X_i)).
  \end{aligned}""",
    r"""\begin{aligned}
  \Delta^{\mathrm{raw}}_{E3}
    &= \operatorname{mean}_{s}\operatorname{mean}_{c\mid s}
       \operatorname{mean}_{i\mid sc}
       \{\operatorname{Reg}_i(\pi_O^{-s})-\operatorname{Reg}_i(\pi_R^{-s})\},\\
  D_i
    &= V_i(\pi_R^{-s}(X_i))-V_i(\pi_O^{-s}(X_i)).
  \end{aligned}""",
)
UNDERFULL_PRE_FIX_SOURCE_IDENTITIES = (
    (
        "latex/appendices/appendix_analysis_protocol.tex",
        17_051,
        "FEA775BBF81842F12B2B0356F8D3AEA6A1109F3B65AAB43B4DE275F977E3F9BC",
    ),
    (
        "latex/appendices/appendix_policy_provenance.tex",
        11_934,
        "D90B1E2CF8ADC7A0B74E64CEC503FB4D0D4CD3A200E96B9C47FA977863A43E15",
    ),
    (
        "latex/main.tex",
        2_377,
        "1760DF0DD749209D3448758CAD5D7CCF5E953772C4665E72877C58EC1A8CC957",
    ),
    (
        "latex/sections/05_supporting_theory.tex",
        1_556,
        "B39237819D4EF60194BA674533F3593A38ED46497C38A81AFD1EC920BE2521D1",
    ),
    (
        "latex/sections/06_experimental_design.tex",
        2_466,
        "F360DB1D45512FE3B449BA360E7922FCCC0953B5F70F531CDFCA5D89EBD5ECCF",
    ),
)
RELATED_WORK_STATUS_BLOCK = (
    r"""Future E3 would use paired direct policy evaluation because every admissible
terminal action would be executed from the same frozen prefix; the present
paper performs neither direct nor logged off-policy evaluation.  Any future
off-policy comparison is protocol-only until its logging and receipt contract
is separately frozen.
Self-resource allocation and matched-compute self-agent scaling are distinct
methods.  The retrospective oracle is not a 23rd policy: it is a separate,
post-outcome descriptive upper bound (\claim{C-ORACLE-DESCRIPTIVE}).  The
provenance registry and SAP are the two exact roster owners; Related Work does
not restate the 22 identifiers.  Public references identify method families
only and do not authenticate an adapter, version, code, configuration, parity,
or empirical readiness; implementation authentication remains blocked pending
the authenticated external roster.  For executable-policy identity,
citation\_authority\_status=blocked\_pending\_authenticated\_roster."""
    + "\n"
)
UNDERFULL_SUPPORTING_THEORY_INNER = (
    r"""\killed{The current model does not support a product-rate cumulative-regret
theorem (\claim{C-THEORY-REGRET}).  It does not support a joint
audit/receipt minimax theorem (\claim{C-THEORY-JOINT-MINIMAX}).
It also does not support a same-information policy-superiority
theorem (\claim{C-THEORY-POLICY-SUPERIOR}).}
The standard same-information obstruction and structural estimator separation
remain appendix boundaries, not headline novelty."""
    + "\n"
)
UNDERFULL_E1_INNER = (
    r"""E1 asks whether pre-outcome signals predict an escalation label under held-out
site folds and calibrated evaluation.  It is noncausal and nonprimary
(\claim{C-E1-PREDICTION})."""
    + "\n"
)
UNDERFULL_BIBLIOGRAPHY_INNER = r"\bibliography{references}" + "\n"
UNDERFULL_POLICY_PROLOGUE_INNER = (
    r"""\section{Policy provenance and protocol-defined comparators}

bibliographic\_provenance\_status=public\_source\_mapped\_or\_protocol\_defined.
implementation\_authentication\_status=blocked\_pending\_authenticated\_roster.
Public references identify method families only; they authenticate no adapter,
version, code, configuration, parity, or empirical readiness.
This registry is input to a future E3 protocol only.  It is not evidence that
any comparison ran, that a policy is ready, or that OACS has a favorable rank."""
    + "\n"
)
UNDERFULL_POLICY_REGISTRY_PREFIX = "\\small\n\\raggedright\n"
UNDERFULL_SAP_PARITY_INNER = (
    r"""  Both views are complete bijections over exactly 15 canonical parent payload
  fields: site\_ref, case\_ref, prefix\_ref, raw\_transcript\_prefix,
  numeric\_residual\_serialization, complete\_capability\_table,
  opaque\_packet\_binding\_cards, costs, admissibility, examples, split\_fold,
  learner\_class\_capacity, tuning\_optimization\_opportunity,
  target\_action\_roster, action\_space\_tie\_rule. The seven opportunity
  objects are byte-identical: costs, admissibility, examples, split\_fold,
  learner\_class\_capacity, tuning\_optimization\_opportunity,
  action\_space\_tie\_rule. Both projected byte strings replay, both decisions
  are pre-outcome admissible reconstructed actions, and the only validator
  interface is validate\_paired\_information\_parity(receipt,
  replay\_bundle); the replay bundle's nested OACS/raw decision bytes are the
  sole decision authority."""
    + "\n"
)
UNDERFULL_SAP_READINESS_INNER = (
    r"""  The readiness cross-product is exact: supported means ready\_verified;
  reviewed inapplicability means domain\_inapplicable plus a deterministic
  adaptation identity; unsupported official interface means exactly one of
  official\_interface\_absent, official\_interface\_incompatible, or
  faithfulness\_failed; missing dependency means exactly one of
  dependency\_unavailable or license\_or\_access\_blocked. Supported or adapted
  methods additionally require source/version commitment, parity,
  projection/input replay, environment/adapter binding, and an admissible
  direct decision; unresolved readiness or fidelity blocks main E3. Closed
  unsupported and inapplicable statuses are reported and never become
  favorable omissions or eligible contrasts; semantic source/version
  ownership remains blocked on the external Phase-B trust root and same-handle
  actual-byte authentication."""
    + "\n"
)
UNDERFULL_SAP_SHELLS_INNER = (
    r"""Roster/support/conformance shell:
  status=BLOCKED; values=UNPOPULATED; fields=ontology, signed
  site/case/target/pair/repeat census, support status, control roster,
  assignment closure, manifest/isolation/usage conformance, and attrition by
  arm and reason. E1 shell: status=BLOCKED; values=UNPOPULATED;
  fields=ontology, site-fold label support, log-loss contrast, discrimination,
  calibration, uncertainty, and authentication/gate status. Primary E2 shell:
  status=BLOCKED; values=UNPOPULATED; fields=tau-plus, tau-zero, theta-E2,
  95-percent randomization and Neyman intervals, randomization result, Monte
  Carlo uncertainty if used, support/missingness sensitivity, per-site and
  leave-one-site-out results, diagnostics, and gate. Primary E3 shell:
  status=BLOCKED; values=UNPOPULATED; fields=OACS--raw paired regret, site
  interval and degrees of freedom, parity receipt, per-site,
  leave-one-site-out, wild sensitivity, costs, action frequencies, and gate.
  No source/version is authenticated; 22-policy readiness shell:
  status=BLOCKED; values=UNPOPULATED; fields=ID, source/version commitment,
  status/reason, executed or adaptation identity, replay/conformance, and
  eligibility. Policy-family contrast shell: status=BLOCKED;
  values=UNPOPULATED; fields=ontology, eligible comparator, paired OACS
  difference, unadjusted effect and interval, Holm-adjusted result, and
  parity/conformance/exclusion status. Descriptive oracle shell:
  status=BLOCKED; values=UNPOPULATED; fields=direct-value table closure,
  admissible subset, inherited tie rule, oracle gap, and explicit post-outcome,
  descriptive, nondeployable status. Claim/gate summary shell: status=BLOCKED;
  values=UNPOPULATED; fields=claim ID, ontology, prerequisite receipts,
  decision, survivor boundary, and blocked or killed status."""
    + "\n"
)
UNDERFULL_SAP_MARKERS_INNER = (
    r"""  [[BLOCKED:C-E1-PREDICTION:authenticated held-out learner and calibration evidence]]
  [[BLOCKED:C-E2-ARCH-MECHANISM:authenticated Architecture assignment-execution-outcome receipt]]
  [[BLOCKED:C-E2-JCI-MECHANISM:authenticated JCI assignment-execution-outcome receipt]]
  [[BLOCKED:C-E3-ARCH-POLICY:authenticated Architecture equal-information decision bundle]]
  [[BLOCKED:C-E3-JCI-POLICY:authenticated JCI equal-information decision bundle]]
  [[BLOCKED:C-E4-DEPLOYMENT:fresh downstream protocol and prerequisite passes]]
  [[BLOCKED:C-COST:signed manifests rates and execution census]]
  [[BLOCKED:C-SAFETY:separate safety study]]
  [[BLOCKED:C-GENERALIZATION:positive compliant evidence in both ontologies and external validation]]"""
    + "\n"
)
UNDERFULL_SCOPE_CONTRACTS = (
    (
        "supporting theory withdrawn paragraph",
        "latex/sections/05_supporting_theory.tex",
        "superior, or that receipt binding alone establishes evaluation validity.\n\n",
        "{\\raggedright\n",
        UNDERFULL_SUPPORTING_THEORY_INNER,
        "\\par\n}\n",
    ),
    (
        "E1 predictive paragraph",
        "latex/sections/06_experimental_design.tex",
        "\\paragraph{E1: predictive diagnostic.}\n",
        "{\\raggedright\n",
        UNDERFULL_E1_INNER,
        "\\par\n}\n",
    ),
    (
        "official bibliography output",
        "latex/main.tex",
        "\\bibliographystyle{iclr2027_conference}\n",
        "\\begingroup\n\\raggedright\n",
        UNDERFULL_BIBLIOGRAPHY_INNER,
        "\\par\n\\endgroup\n",
    ),
    (
        "policy registry prologue",
        POLICY_PROVENANCE_RELATIVE,
        "",
        "{\\small\n\\raggedright\n",
        UNDERFULL_POLICY_PROLOGUE_INNER,
        "\\par\n}\n",
    ),
    (
        "SAP parity inventory",
        SAP_RELATIVE,
        "never increase degrees of freedom.\n\n",
        "  {\\raggedright\n",
        UNDERFULL_SAP_PARITY_INNER,
        "  \\par\n  }\n",
    ),
    (
        "SAP readiness taxonomy",
        SAP_RELATIVE,
        "  source/version commitments. \\end{quote}\n",
        "  {\\raggedright\n",
        UNDERFULL_SAP_READINESS_INNER,
        "  \\par\n  }\n",
    ),
    (
        "SAP empty result shells",
        SAP_RELATIVE,
        "  \\item[Empty result shells.] ",
        "{\\raggedright\n",
        UNDERFULL_SAP_SHELLS_INNER,
        "  \\par\n  }\n",
    ),
    (
        "SAP blocked evidence markers",
        SAP_RELATIVE,
        "  \\item[Blocked evidence markers.]\n",
        "  {\\raggedright\n",
        UNDERFULL_SAP_MARKERS_INNER,
        "  \\par\n  }\n",
    ),
)
UNDERFULL_TEX_RAGGEDRIGHT_COUNTS = {
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
UNDERFULL_FORBIDDEN_LAYOUT_PATTERNS = (
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
UNDERFULL_LAYOUT_ESCAPE_MUTATIONS = (
    ("global sloppy", r"\sloppy"),
    ("sloppy environment", r"\begin{sloppypar}masked\end{sloppypar}"),
    ("emergency stretch", r"\emergencystretch=3em"),
    ("horizontal badness", r"\hbadness=10000"),
    ("vertical badness", r"\vbadness=10000"),
    ("horizontal fuzz", r"\hfuzz=999pt"),
    ("vertical fuzz", r"\vfuzz=999pt"),
    ("ragged bottom", r"\raggedbottom"),
    ("enlarge page", r"\enlargethispage{2\baselineskip}"),
    ("resize", r"\resizebox{\linewidth}{!}{masked}"),
    ("scale", r"\scalebox{0.9}{masked}"),
    ("font size", r"\fontsize{8}{9}\selectfont"),
    ("negative vertical space", r"\vspace{-3pt}"),
    ("negative horizontal space", r"\hspace{-3pt}"),
    ("margin", r"\geometry{margin=0.5in}"),
    ("text width", r"\setlength{\textwidth}{7in}"),
    ("line spacing", r"\linespread{0.9}"),
)
SAP_REQUIRED_ACTIVE_SPANS = (
    r"\section{Statistical Analysis Protocol}",
    "The complete-bundle thesis is prospective; the observed object is an immutable failed development diagnostic outside E1--E4.",
    "The V1 diagnostic remains failed and immutable under the no-rescore rule; V2 is prospective and requires fresh execution.",
    "Architecture is a prospective stress-test ontology only; JCI-Repair-v1 is a planned, separate, unpooled replication, and the two ontologies are never pooled.",
    "The hierarchy is site/project outer cluster, case nested within site, immutable-prefix target nested within case, predeclared packet pair nested within target, and repeat/seed execution draw nested within pair.",
    "Aggregation gives equal weight in the order site, case, eligible target, packet pair, and repeat; raw-row weighting is prohibited, and prefixes or repeats are never independent sites.",
    "CATS remains negative motivation and a baseline only; E4 is fresh and downstream; the retrospective oracle is post-outcome, evaluation-only, descriptive, and nondeployable.",
    "E1 is predictive, noncausal, nonprimary held-out-site motivation only.",
    r"The same-target packet and single-agent SOLO\_synthesis action roster and every repeat/seed cell are frozen before outcomes.",
    r"H_i=\mathbf{1}\{\max_b[\overline Y_i(b)-\overline Y_i(\mathrm{solo\_synthesis})]>0\}",
    "An incomplete action or cell blocks the label; observed survivors, dropped actions, and incomplete cells never shrink the maximum.",
    "The sole prespecified contrast is site-held-out log-loss improvement; no focal-site label enters its training fold, while discrimination and calibration are descriptive.",
    r"\tau^+_{iq}=\operatorname{mean}_{r}\{Y_{iqr}(b^+_{iq})-Y_{iqr}(b^-_{iq})\}",
    r"\tau^0_{iq}=\sum_{j\in\mathcal N_{iq}}v_{ijq}\operatorname{mean}_{r}\{Y_{jqr}(b^+_{iq})-Y_{jqr}(b^-_{iq})\}",
    r"\psi_{iq}=\tau^+_{iq}-\tau^0_{iq}",
    r"\theta_{E2}=\operatorname{mean}_{s}\operatorname{mean}_{c\mid s}\operatorname{mean}_{i\mid sc}\operatorname{mean}_{q\mid i}\psi_{iq}",
    "Residual-absent controls are predeclared, distinct, same-site, adequate-support targets with identical packet identities, inherited orientation only, strictly positive pre-outcome weights summing exactly to one, and exactly matching focal repeat/seed cells.",
    "Opaque actual complete bundles are randomized within each frozen $(i,q,r)$ block at recorded positive probabilities over the authenticated complete cyclic-crossover assignment space.",
    "The estimand is heterogeneity in randomized, actually executed complete-bundle effects indexed by frozen structure; it is not a causal effect of the alignment score, residual state, capability score, or intrinsic specialist ability.",
    "Mandatory nonreplacement diagnostics are unadjusted residual-present and residual-absent effects, packet main effects, uniform random admissible, all-specialists, fixed-topology, relabel, semantic-name/order, actual-packet-misbinding, and global-strength controls.",
    r"K=(T,L,C)\quad\text{and}\quad U=Y-\lambda_K^\top K",
    r"The nonnegative $\lambda_K$ is frozen before paid calls; $T$, $L$, and $C$ are complete processed tokens, latency, and frozen-list-price cost.",
    r"The utility secondary replaces $Y$ by $U$ inside the identical blocked $\tau^+$, $\tau^0$, $\psi$, and hierarchical $\theta_{E2}$ contrast; every $K$ component is reported separately, and realized $K$ never defines support, exclusion, or a primary analysis.",
    r"The continuous alignment-by-cost interaction is estimable only when every required binding is frozen pre-call as predeclared\_continuous\_secondary; otherwise it is exactly None.",
    "Component attribution requires separate factorial randomization and cannot be supplied by this complete-bundle experiment.",
    "Residual snapshots, audit-site capability relations, assignments, probabilities, actual manifests, evaluator, isolation, usage, and blind terminal receipts are frozen before the corresponding outcome.",
    "Every required present arm, absent arm, and uniform-admissible control is manifest-verified; missing, nonverified, misbound, selectively retried, attrited, or incomplete required arms block confirmatory E2 arithmetic.",
    r"Weak or empty support sets every confirmatory E2 numeric to None with non\_estimable\_support.",
    "No merging, imputation, transport, caliper widening, as-treated or per-protocol substitution, replacement, stitching, carryover, cross-target reuse, selective retry, dropped bad repeat, or favorable omission is allowed.",
    "Horvitz--Thompson applies only to a predeclared unequal-probability design and never rescues a missing required arm.",
    r"Arm-specific attrition and $Y\in[0,1]$ worst/best bounds are reported; a possible null or reversal kills the mechanism claim.",
    "Inference aggregates repeat to pair to target to case to site.",
    "Blocked Fisher randomization inference uses the authenticated assignment space, exactly or with a pre-frozen Monte Carlo draw count and seed plus the add-one p-value.",
    "Fisher inference is exact only for the sharp no-effect null and does not by itself test the weak average-effect null.",
    "No permutation crosses site, case, prefix, pair/repeat block, admissibility stratum, or ontology.",
    r"The confirmatory E2 gate requires a two-sided 95\% interval with lower endpoint above zero; a conservative Neyman interval, every per-site effect, and leave-one-site-out estimates are mandatory, while CR2, wild-cluster, and adjusted models are sensitivity only.",
    r"V_i(a) &= \operatorname{mean}_{r}\{Y_{iar}(a)-\lambda_K^\top K_{iar}(a)\}",
    r"\operatorname{Reg}_i(\pi) &= \max_{a\in\mathcal A_i}V_i(a)-V_i(\pi(X_i))",
    "Every action value is a direct terminal execution from the same immutable prefix; no stitched transition, imputed action, cross-repeat splice, selected-action-as-treatment shortcut, post-hoc maximum, or single-draw maximum is allowed.",
    r"\Delta^{\mathrm{raw}}_{E3} &= \operatorname{mean}_{s}\operatorname{mean}_{c\mid s} \operatorname{mean}_{i\mid sc} \{\operatorname{Reg}_i(\pi_O^{-s})-\operatorname{Reg}_i(\pi_R^{-s})\}",
    r"D_i &= V_i(\pi_R^{-s}(X_i))-V_i(\pi_O^{-s}(X_i))",
    r"A negative $\Delta^{\mathrm{raw}}_{E3}$ favors OACS; the two-sided 95\% paired site-aggregate Student interval must have upper endpoint below zero with $|\mathcal S|-1$ degrees of freedom.",
    "Per-site effects, leave-one-site-out intervals, and the predeclared wild-cluster sensitivity are reported; prefixes and repeats never increase degrees of freedom.",
    "Both views are complete bijections over exactly 15 canonical parent payload fields:",
    "The seven opportunity objects are byte-identical:",
    r"Both projected byte strings replay, both decisions are pre-outcome admissible reconstructed actions, and the only validator interface is validate\_paired\_information\_parity(receipt, replay\_bundle); the replay bundle's nested OACS/raw decision bytes are the sole decision authority.",
    r"The readiness cross-product is exact: supported means ready\_verified; reviewed inapplicability means domain\_inapplicable plus a deterministic adaptation identity; unsupported official interface means exactly one of official\_interface\_absent, official\_interface\_incompatible, or faithfulness\_failed; missing dependency means exactly one of dependency\_unavailable or license\_or\_access\_blocked.",
    "Supported or adapted methods additionally require source/version commitment, parity, projection/input replay, environment/adapter binding, and an admissible direct decision; unresolved readiness or fidelity blocks main E3.",
    "Closed unsupported and inapplicable statuses are reported and never become favorable omissions or eligible contrasts; semantic source/version ownership remains blocked on the external Phase-B trust root and same-handle actual-byte authentication.",
    "The retrospective oracle is excluded from the 22-policy roster and every primary, parity, readiness, and deployment comparison.",
    "Its post-outcome table is complete and roster ordered; maximization is over the nonempty admissible subset only, ties inherit roster order, and reporting is descriptive, evaluation-only, and nondeployable.",
    "The main claim is the unpooled conjunction of Architecture E2 lower endpoint above zero, JCI E2 lower endpoint above zero, Architecture E3-raw upper endpoint below zero, and JCI E3-raw upper endpoint below zero.",
    "Holm familywise-error control at 0.05 applies within each ontology to secondary E2 families and to nonprimary E3 policy contrasts.",
    "E2 failure in either ontology kills the mechanism and ICLR-main thesis; positive E2 followed by null, inconclusive, or parity-invalid E3 in either ontology kills the OACS method and ICLR-main decision claim.",
    "Architecture E2 failure leaves at most a narrower JCI descriptive or randomized executed-bundle report; JCI E2 failure leaves at most a narrower Architecture executed-bundle report.",
    "After positive E2, an E3 failure in either ontology leaves only the corresponding compliant ontology-specific bundle-effect report, never a policy, main, replication, or generalization claim.",
    "No pooling, cross-ontology rescue, or post-outcome utility, baseline, site, ontology, margin, or fold change is allowed; E4 remains downstream, and its failure kills deployment-frontier language only.",
    "Roster/support/conformance shell: status=BLOCKED; values=UNPOPULATED; fields=ontology, signed site/case/target/pair/repeat census, support status, control roster, assignment closure, manifest/isolation/usage conformance, and attrition by arm and reason.",
    "E1 shell: status=BLOCKED; values=UNPOPULATED; fields=ontology, site-fold label support, log-loss contrast, discrimination, calibration, uncertainty, and authentication/gate status.",
    "Primary E2 shell: status=BLOCKED; values=UNPOPULATED; fields=tau-plus, tau-zero, theta-E2, 95-percent randomization and Neyman intervals, randomization result, Monte Carlo uncertainty if used, support/missingness sensitivity, per-site and leave-one-site-out results, diagnostics, and gate.",
    "Primary E3 shell: status=BLOCKED; values=UNPOPULATED; fields=OACS--raw paired regret, site interval and degrees of freedom, parity receipt, per-site, leave-one-site-out, wild sensitivity, costs, action frequencies, and gate.",
    "No source/version is authenticated; 22-policy readiness shell: status=BLOCKED; values=UNPOPULATED; fields=ID, source/version commitment, status/reason, executed or adaptation identity, replay/conformance, and eligibility.",
    "Policy-family contrast shell: status=BLOCKED; values=UNPOPULATED; fields=ontology, eligible comparator, paired OACS difference, unadjusted effect and interval, Holm-adjusted result, and parity/conformance/exclusion status.",
    "Descriptive oracle shell: status=BLOCKED; values=UNPOPULATED; fields=direct-value table closure, admissible subset, inherited tie rule, oracle gap, and explicit post-outcome, descriptive, nondeployable status.",
    "Claim/gate summary shell: status=BLOCKED; values=UNPOPULATED; fields=claim ID, ontology, prerequisite receipts, decision, survivor boundary, and blocked or killed status.",
    "No source, data, held-out/OOD, or authenticated-result access is established.",
    "No site or target sufficiency, power, MDE, numeric cost, feasibility, or runtime is established.",
    "No positive E1, E2, E3, or E4 effect, policy superiority, safety, robustness, deployment readiness, generalization, or acceptance probability is established.",
    "No Task6-vNext design-lock PASS, simulation authorization, paid-call authorization, PDF or venue validity, submission readiness, or Task12 gate is established.",
    "No cumulative-regret, joint-minimax, or theorem-level same-information policy-superiority result is established.",
    "Difficulty has no novelty, sufficiency, or causal status; no causal payoff is assigned to an alignment score, residual state, component, or intrinsic specialist ability.",
    "Blinding does not eliminate all evaluator bias, baseline risk guarantees do not transfer to OACS, and offline branches do not establish sequential or deployment validity.",
    "Prefixes and repeats do not replace independent sites, and Architecture plus JCI does not establish broad or universal generalization.",
    "Weak support, missing or unsupported baselines, incomplete branches, noncompliance, synthetic fixtures, historical counts, the retrospective oracle, and supporting theory are never favorable empirical evidence.",
    "No numeric affordability, cost, or sub-one-percent safety evidence is established.",
    r"The only attained state is analysis\_protocol\_static\_ready; empirical status remains no\_go\_needs\_context and PDF compile verification remains false.",
    *SAP_REVIEW_FIX_SPANS,
)
SAP_FORBIDDEN_POSITIVE_CLAIMS = (
    "E1 predictive improvement observed",
    "E2 causal mechanism established",
    "E3 policy superiority shown",
    "E4 deployment gain observed",
    "design-lock PASS obtained",
    "source authority authenticated",
    "power target achieved",
    "actual cost reduced",
    "safety established",
    "cross-domain generalization established",
    "submission ready",
    "acceptance likely",
    "PDF verified",
)

# key, title, ordered authors, year, url, optional DOI, disposition
PRIMARY_SOURCES = (
    (
        "zhang2026icore",
        "Auditing Emergent LLM-Agent Collaboration through Cooperation-Obligation Coupling",
        ("Zuyuan Zhang", "Hanqing Yang", "Carlee Joe-Wong", "Tian Lan"),
        "2026",
        "https://arxiv.org/abs/2607.27429",
        None,
        "obligation/evidence/responsibility coupling and audit intervention are prior art",
    ),
    (
        "wong2026eureka",
        "Eureka: Task-Conditioned Meta-Agent Orchestration for Scientific Discovery",
        (
            "Alizer Wong",
            "Heng Cui",
            "Yi Tan",
            "Xiongchao Zhan",
            "Liang Lin",
            "Yuxiang Guo",
            "Zhaorong Dai",
            "Zixin Zeng",
            "Wenyuan Li",
        ),
        "2026",
        "https://arxiv.org/abs/2608.19047",
        None,
        "dynamic obligation-graph orchestration and acceptance semantics are prior art",
    ),
    (
        "yang2026star",
        "STAR: Failure-Aware Markovian Routing for Multi-Agent Spatiotemporal Reasoning",
        ("Ruiyi Yang", "Lihuan Li", "Hao Xue", "Flora D. Salim"),
        "2026",
        "https://arxiv.org/abs/2605.10057",
        None,
        "typed execution/failure-state specialist routing is prior art",
    ),
    (
        "bala2026setvalued",
        "Multi-Agent Routing as Set-Valued Prediction: A WildChat Benchmark and Cost-Aware Evaluation",
        ("Ananto Nayan Bala", "Faisal Muhammad Shah"),
        "2026",
        "https://arxiv.org/abs/2606.28925",
        None,
        "fixed-catalog set-valued selection and cost-aware capability coverage are prior art",
    ),
    (
        "kallus2018instrument",
        "Instrument-Armed Bandits",
        ("Nathan Kallus",),
        "2018",
        "https://proceedings.mlr.press/v83/kallus18a.html",
        None,
        "recommendation and delivered treatment can diverge",
    ),
    (
        "oprescu2025amriv",
        "Efficient Adaptive Experimentation with Noncompliance",
        ("Miruna Oprescu", "Brian Cho", "Nathan Kallus"),
        "2025",
        "https://proceedings.neurips.cc/paper_files/paper/2025/hash/3ca380c5fe9f174a71a230478741169f-Abstract-Conference.html",
        "10.52202/085713-1414",
        "adaptive noncompliance and multiply robust inference are prior art",
    ),
    (
        "dellapenna2026brace",
        "What Do We Care About in Bandits with Noncompliance? BRACE: Bandits with Recommendations, Abstention, and Certified Effects",
        ("Nicolás Della Penna",),
        "2026",
        "https://arxiv.org/abs/2603.09532",
        None,
        "closest product-bias/compliance prior; B1 is model-specific support",
    ),
    (
        "flynn2026sparse",
        "Sparse Nonparametric Contextual Bandits",
        ("Hamish Flynn", "Julia Olkhovskaya", "Paul Rognon-Vael"),
        "2026",
        "https://proceedings.mlr.press/v313/flynn26a.html",
        None,
        "sparse contextual-bandit upper/lower theory raises the proof bar",
    ),
    (
        "qin2026oe2d",
        "Taming the Monster Every Context: Complexity Measure and Unified Framework for Offline-Oracle Efficient Contextual Bandits",
        ("Hao Qin", "Chicheng Zhang"),
        "2026",
        "https://proceedings.mlr.press/v336/qin26a.html",
        None,
        "offline-oracle contextual-bandit reduction is prior art",
    ),
    (
        "girard2026fast",
        "Fast Best-in-Class Regret for Contextual Bandits",
        (
            "Samuel Girard",
            "Aurélien Bibaut",
            "Jill-Jênn Vie",
            "Arthur Gretton",
            "Nathan Kallus",
            "Houssam Zenati",
        ),
        "2026",
        "https://proceedings.mlr.press/v337/girard26a.html",
        None,
        "fast best-in-class regret is prior art",
    ),
)

# key, exact entry type, complete ordered (field, value) tuple
BIBLIOGRAPHY_ENTRIES = (
    (
        "bala2026setvalued",
        "misc",
        (
            (
                "title",
                "Multi-Agent Routing as Set-Valued Prediction: A WildChat Benchmark and Cost-Aware Evaluation",
            ),
            ("author", "Ananto Nayan Bala and Faisal Muhammad Shah"),
            ("year", "2026"),
            ("url", "https://arxiv.org/abs/2606.28925"),
        ),
    ),
    (
        "dellapenna2026brace",
        "misc",
        (
            (
                "title",
                "What Do We Care About in Bandits with Noncompliance? {BRACE}: Bandits with Recommendations, Abstention, and Certified Effects",
            ),
            ("author", "{Della Penna}, Nicolás"),
            ("year", "2026"),
            ("url", "https://arxiv.org/abs/2603.09532"),
        ),
    ),
    (
        "flynn2026sparse",
        "inproceedings",
        (
            ("title", "Sparse Nonparametric Contextual Bandits"),
            ("author", "Hamish Flynn and Julia Olkhovskaya and Paul Rognon-Vael"),
            (
                "booktitle",
                "Proceedings of The 37th International Conference on Algorithmic Learning Theory",
            ),
            ("pages", "1--44"),
            ("year", "2026"),
            ("volume", "313"),
            ("series", "Proceedings of Machine Learning Research"),
            ("publisher", "PMLR"),
            ("url", "https://proceedings.mlr.press/v313/flynn26a.html"),
        ),
    ),
    (
        "girard2026fast",
        "inproceedings",
        (
            ("title", "Fast Best-in-Class Regret for Contextual Bandits"),
            (
                "author",
                "Samuel Girard and Aurélien Bibaut and Jill-Jênn Vie and Arthur Gretton and Nathan Kallus and Houssam Zenati",
            ),
            (
                "booktitle",
                "Proceedings of the 42nd Conference on Uncertainty in Artificial Intelligence",
            ),
            ("pages", "1695--1724"),
            ("year", "2026"),
            ("volume", "337"),
            ("series", "Proceedings of Machine Learning Research"),
            ("publisher", "PMLR"),
            ("url", "https://proceedings.mlr.press/v337/girard26a.html"),
        ),
    ),
    (
        "kallus2018instrument",
        "inproceedings",
        (
            ("title", "Instrument-Armed Bandits"),
            ("author", "Nathan Kallus"),
            ("booktitle", "Proceedings of Algorithmic Learning Theory"),
            ("pages", "529--546"),
            ("year", "2018"),
            ("volume", "83"),
            ("series", "Proceedings of Machine Learning Research"),
            ("publisher", "PMLR"),
            ("url", "https://proceedings.mlr.press/v83/kallus18a.html"),
        ),
    ),
    (
        "oprescu2025amriv",
        "inproceedings",
        (
            ("title", "Efficient Adaptive Experimentation with Noncompliance"),
            ("author", "Miruna Oprescu and Brian Cho and Nathan Kallus"),
            ("booktitle", "Advances in Neural Information Processing Systems"),
            ("pages", "42462--42498"),
            ("year", "2025"),
            ("volume", "38, Main Conference"),
            ("publisher", "Curran Associates, Inc."),
            ("doi", "10.52202/085713-1414"),
            (
                "url",
                "https://proceedings.neurips.cc/paper_files/paper/2025/hash/3ca380c5fe9f174a71a230478741169f-Abstract-Conference.html",
            ),
        ),
    ),
    (
        "qin2026oe2d",
        "inproceedings",
        (
            (
                "title",
                "Taming the Monster Every Context: Complexity Measure and Unified Framework for Offline-Oracle Efficient Contextual Bandits",
            ),
            ("author", "Hao Qin and Chicheng Zhang"),
            ("booktitle", "Proceedings of Thirty Ninth Conference on Learning Theory"),
            ("pages", "5399--5464"),
            ("year", "2026"),
            ("volume", "336"),
            ("series", "Proceedings of Machine Learning Research"),
            ("publisher", "PMLR"),
            ("url", "https://proceedings.mlr.press/v336/qin26a.html"),
        ),
    ),
    (
        "wong2026eureka",
        "misc",
        (
            (
                "title",
                "Eureka: Task-Conditioned Meta-Agent Orchestration for Scientific Discovery",
            ),
            (
                "author",
                "Alizer Wong and Heng Cui and Yi Tan and Xiongchao Zhan and Liang Lin and Yuxiang Guo and Zhaorong Dai and Zixin Zeng and Wenyuan Li",
            ),
            ("year", "2026"),
            ("url", "https://arxiv.org/abs/2608.19047"),
        ),
    ),
    (
        "yang2026star",
        "misc",
        (
            (
                "title",
                "{STAR}: Failure-Aware Markovian Routing for Multi-Agent Spatiotemporal Reasoning",
            ),
            ("author", "Ruiyi Yang and Lihuan Li and Hao Xue and Flora D. Salim"),
            ("year", "2026"),
            ("url", "https://arxiv.org/abs/2605.10057"),
        ),
    ),
    (
        "zhang2026icore",
        "misc",
        (
            (
                "title",
                "Auditing Emergent {LLM}-Agent Collaboration through Cooperation-Obligation Coupling",
            ),
            (
                "author",
                "Zuyuan Zhang and Hanqing Yang and Carlee Joe-Wong and Tian Lan",
            ),
            ("year", "2026"),
            ("url", "https://arxiv.org/abs/2607.27429"),
        ),
    ),
)

# Exact Task-3 authority: 19 added works plus normalized Auer and DML.
# Each row owns key, entry type, Task-1 review_status, and ordered BibTeX fields.
TASK3_BIBLIOGRAPHY_AUTHORITY = (
    (
        "aggarwal2024automix",
        "inproceedings",
        "peer_reviewed",
        (
            ("title", "{AutoMix}: Automatically Mixing Language Models"),
            (
                "author",
                "Pranjal Aggarwal and Aman Madaan and Ankit Anand and Srividya Pranavi Potharaju and Swaroop Mishra and Pei Zhou and Aditya Gupta and Dheeraj Rajagopal and Karthik Kappaganthu and Yiming Yang and Shyam Upadhyay and Manaal Faruqui and Mausam",
            ),
            ("booktitle", "Advances in Neural Information Processing Systems"),
            ("year", "2024"),
            ("volume", "37"),
            ("pages", "131000--131034"),
            ("doi", "10.52202/079017-4164"),
            (
                "url",
                "https://proceedings.neurips.cc/paper_files/paper/2024/hash/ecda225cb187b40ea8edc1f46b03ffda-Abstract-Conference.html",
            ),
        ),
    ),
    (
        "amayuelas2025selfresource",
        "misc",
        "public_preprint",
        (
            ("title", "Self-Resource Allocation in Multi-Agent {LLM} Systems"),
            (
                "author",
                "Alfonso Amayuelas and Jingbo Yang and Saaket Agashe and Ashwin Nagarajan and Antonis Antoniades and Xin Eric Wang and William Wang",
            ),
            ("howpublished", "arXiv"),
            ("year", "2025"),
            ("eprint", "2504.02051"),
            ("note", "arXiv v2"),
            ("url", "https://arxiv.org/abs/2504.02051"),
        ),
    ),
    (
        "auer2002finite",
        "article",
        "peer_reviewed",
        (
            ("title", "Finite-time Analysis of the Multiarmed Bandit Problem"),
            ("author", "Peter Auer and Nicolò Cesa-Bianchi and Paul Fischer"),
            ("journal", "Machine Learning"),
            ("year", "2002"),
            ("volume", "47"),
            ("pages", "235--256"),
            ("doi", "10.1023/A:1013689704352"),
            ("url", "https://link.springer.com/article/10.1023/A:1013689704352"),
        ),
    ),
    (
        "chernozhukov2018double",
        "article",
        "peer_reviewed",
        (
            (
                "title",
                "Double/debiased machine learning for treatment and structural parameters",
            ),
            (
                "author",
                "Victor Chernozhukov and Denis Chetverikov and Mert Demirer and Esther Duflo and Christian Hansen and Whitney Newey and James Robins",
            ),
            ("journal", "The Econometrics Journal"),
            ("year", "2018"),
            ("volume", "21"),
            ("pages", "C1--C68"),
            ("doi", "10.1111/ectj.12097"),
            ("url", "https://onlinelibrary.wiley.com/doi/10.1111/ectj.12097"),
        ),
    ),
    (
        "du2024multiagentdebate",
        "inproceedings",
        "peer_reviewed",
        (
            (
                "title",
                "Improving Factuality and Reasoning in Language Models through Multiagent Debate",
            ),
            (
                "author",
                "Yilun Du and Shuang Li and Antonio Torralba and Joshua B. Tenenbaum and Igor Mordatch",
            ),
            (
                "booktitle",
                "Proceedings of the 41st International Conference on Machine Learning",
            ),
            ("year", "2024"),
            ("volume", "235"),
            ("pages", "11733--11763"),
            ("url", "https://proceedings.mlr.press/v235/du24e.html"),
        ),
    ),
    (
        "feng2026graphplanner",
        "inproceedings",
        "peer_reviewed",
        (
            (
                "title",
                "{GraphPlanner}: Graph Memory-Augmented Agentic Routing for Multi-Agent {LLMs}",
            ),
            (
                "author",
                "Tao Feng and Haozhen Zhang and Zijie Lei and Peixuan Han and Jiaxuan You",
            ),
            ("booktitle", "International Conference on Learning Representations"),
            ("year", "2026"),
            ("volume", "2026"),
            ("pages", "123309--123340"),
            (
                "url",
                "https://proceedings.iclr.cc/paper_files/paper/2026/hash/c86ed90b14e55f2ecf838a755e404b06-Abstract-Conference.html",
            ),
        ),
    ),
    (
        "keyu2026bicsrouter",
        "inproceedings",
        "peer_reviewed",
        (
            (
                "title",
                "{BiCSRouter}: Bi-Level Cross-System Routing for Utility-Aware {LLM} Inference",
            ),
            ("author", "Mao Keyu and Eiki Murata and Ukyo Honda"),
            (
                "booktitle",
                "Findings of the Association for Computational Linguistics: ACL 2026",
            ),
            ("year", "2026"),
            ("pages", "18979--18993"),
            ("doi", "10.18653/v1/2026.findings-acl.947"),
            ("url", "https://aclanthology.org/2026.findings-acl.947/"),
        ),
    ),
    (
        "kim2026outgrow",
        "article",
        "peer_reviewed",
        (
            (
                "title",
                "Capable language models can outgrow the benefits of collaboration",
            ),
            (
                "author",
                "Yubin Kim and Ken Gu and Chanwoo Park and Chunjong Park and Samuel Schmidgall and A. Ali Heydari and Yao Yan and Zhihan Zhang and Yuchen Zhuang and Yun Liu and Mark Malhotra and Paul Pu Liang and Hae Won Park and Yuzhe Yang and Xuhai Xu and Yilun Du and Shwetak Patel and Tim Althoff and Daniel McDuff and Xin Liu",
            ),
            ("journal", "Nature Machine Intelligence"),
            ("year", "2026"),
            ("volume", "8"),
            ("pages", "1157--1172"),
            ("doi", "10.1038/s42256-026-01268-y"),
            ("url", "https://www.nature.com/articles/s42256-026-01268-y"),
        ),
    ),
    (
        "li2024moreagents",
        "article",
        "peer_reviewed",
        (
            ("title", "More Agents Is All You Need"),
            (
                "author",
                "Junyou Li and Qin Zhang and Yangbin Yu and Qiang Fu and Deheng Ye",
            ),
            ("journal", "Transactions on Machine Learning Research"),
            ("year", "2024"),
            ("url", "https://openreview.net/forum?id=bgzUSZ8aeg"),
        ),
    ),
    (
        "li2025rirs",
        "misc",
        "public_preprint",
        (
            (
                "title",
                "Talk to Right Specialists: Iterative Routing in Multi-agent Systems for Question Answering",
            ),
            (
                "author",
                "Feijie Wu and Zitao Li and Fei Wei and Yaliang Li and Bolin Ding and Jing Gao",
            ),
            ("howpublished", "arXiv"),
            ("year", "2025"),
            ("eprint", "2501.07813"),
            ("note", "arXiv v2"),
            ("url", "https://arxiv.org/abs/2501.07813"),
        ),
    ),
    (
        "lu2024zooter",
        "inproceedings",
        "peer_reviewed",
        (
            (
                "title",
                "Routing to the Expert: Efficient Reward-guided Ensemble of Large Language Models",
            ),
            (
                "author",
                "Keming Lu and Hongyi Yuan and Runji Lin and Junyang Lin and Zheng Yuan and Chang Zhou and Jingren Zhou",
            ),
            (
                "booktitle",
                "Proceedings of the 2024 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (Volume 1: Long Papers)",
            ),
            ("year", "2024"),
            ("pages", "1964--1974"),
            ("doi", "10.18653/v1/2024.naacl-long.109"),
            ("url", "https://aclanthology.org/2024.naacl-long.109/"),
        ),
    ),
    (
        "ong2025routellm",
        "inproceedings",
        "peer_reviewed",
        (
            ("title", "{RouteLLM}: Learning to Route {LLMs} from Preference Data"),
            (
                "author",
                "Isaac Ong and Amjad Almahairi and Vincent Wu and Wei-Lin Chiang and Tianhao Wu and Joseph E. Gonzalez and M. Waleed Kadous and Ion Stoica",
            ),
            ("booktitle", "International Conference on Learning Representations"),
            ("year", "2025"),
            ("volume", "2025"),
            ("pages", "34433--34448"),
            (
                "url",
                "https://proceedings.iclr.cc/paper_files/paper/2025/hash/5503a7c69d48a2f86fc00b3dc09de686-Abstract-Conference.html",
            ),
        ),
    ),
    (
        "smit2024mad",
        "inproceedings",
        "peer_reviewed",
        (
            (
                "title",
                "Should we be going {MAD}? A Look at Multi-Agent Debate Strategies for {LLMs}",
            ),
            (
                "author",
                "Andries Petrus Smit and Nathan Grinsztajn and Paul Duckworth and Thomas D Barrett and Arnu Pretorius",
            ),
            (
                "booktitle",
                "Proceedings of the 41st International Conference on Machine Learning",
            ),
            ("year", "2024"),
            ("volume", "235"),
            ("pages", "45883--45905"),
            ("url", "https://proceedings.mlr.press/v235/smit24a.html"),
        ),
    ),
    (
        "wang2026conformalthinking",
        "inproceedings",
        "peer_reviewed",
        (
            (
                "title",
                "Conformal Thinking: Risk Control for Reasoning on a Compute Budget",
            ),
            (
                "author",
                "Xi Wang and Anushri Suresh and Alvin Zhang and Rishi More and William Jurayj and Benjamin Van Durme and Mehrdad Farajtabar and Daniel Khashabi and Eric Nalisnick",
            ),
            ("booktitle", "International Conference on Machine Learning"),
            ("year", "2026"),
            ("eprint", "2602.03814"),
            ("note", "arXiv v2; ICML 2026 regular"),
            ("url", "https://arxiv.org/abs/2602.03814"),
        ),
    ),
    (
        "wu2024autogen",
        "inproceedings",
        "peer_reviewed",
        (
            (
                "title",
                "{AutoGen}: Enabling Next-Gen {LLM} Applications via Multi-Agent Conversations",
            ),
            (
                "author",
                "Qingyun Wu and Gagan Bansal and Jieyu Zhang and Yiran Wu and Beibin Li and Erkang Zhu and Li Jiang and Xiaoyun Zhang and Shaokun Zhang and Jiale Liu and Ahmed Hassan Awadallah and Ryen W. White and Doug Burger and Chi Wang",
            ),
            ("booktitle", "First Conference on Language Modeling"),
            ("year", "2024"),
            ("url", "https://openreview.net/forum?id=BAakY1hNKS"),
        ),
    ),
    (
        "xu2026verimap",
        "inproceedings",
        "peer_reviewed",
        (
            ("title", "Verification-Aware Planning for Multi-Agent Systems"),
            (
                "author",
                "Tianyang Xu and Dan Zhang and Kushan Mitra and Estevam Hruschka",
            ),
            (
                "booktitle",
                "Proceedings of the 19th Conference of the European Chapter of the Association for Computational Linguistics (Volume 1: Long Papers)",
            ),
            ("year", "2026"),
            ("pages", "7528--7546"),
            ("doi", "10.18653/v1/2026.eacl-long.353"),
            ("url", "https://aclanthology.org/2026.eacl-long.353/"),
        ),
    ),
    (
        "yang2026costawareprotocol",
        "misc",
        "public_preprint",
        (
            (
                "title",
                "{LLMs} Can Predict Failure Risk, But Struggle to Predict Which Collaboration Protocol Pays Off: Cost-Aware Protocol Routing Across Reasoning Tasks",
            ),
            (
                "author",
                "Chih-Hsuan Yang and Jingyan Jiang and Cheng-Hau Yang and Vikram Vasudevan and Huihuo Zheng and Venkatram Vishwanath and Rajeev Thakur",
            ),
            ("howpublished", "arXiv"),
            ("year", "2026"),
            ("eprint", "2608.14927"),
            ("note", "arXiv v1"),
            ("url", "https://arxiv.org/abs/2608.14927"),
        ),
    ),
    (
        "yue2025masrouter",
        "inproceedings",
        "peer_reviewed",
        (
            ("title", "{MasRouter}: Learning to Route {LLMs} for Multi-Agent Systems"),
            (
                "author",
                "Yanwei Yue and Guibin Zhang and Boyang Liu and Guancheng Wan and Kun Wang and Dawei Cheng and Yiyan Qi",
            ),
            (
                "booktitle",
                "Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)",
            ),
            ("year", "2025"),
            ("pages", "15549--15572"),
            ("doi", "10.18653/v1/2025.acl-long.757"),
            ("url", "https://aclanthology.org/2025.acl-long.757/"),
        ),
    ),
    (
        "zhang2025agentprune",
        "inproceedings",
        "peer_reviewed",
        (
            (
                "title",
                "Cut the Crap: An Economical Communication Pipeline for {LLM}-based Multi-Agent Systems",
            ),
            (
                "author",
                "Guibin Zhang and Yanwei Yue and Zhixun Li and Sukwon Yun and Guancheng Wan and Kun Wang and Dawei Cheng and Jeffrey Yu and Tianlong Chen",
            ),
            ("booktitle", "International Conference on Learning Representations"),
            ("year", "2025"),
            ("volume", "2025"),
            ("pages", "75389--75428"),
            (
                "url",
                "https://proceedings.iclr.cc/paper_files/paper/2025/hash/bbc461518c59a2a8d64e70e2c38c4a0e-Abstract-Conference.html",
            ),
        ),
    ),
    (
        "zhang2026vmao",
        "inproceedings",
        "peer_reviewed_workshop",
        (
            (
                "title",
                "Verified Multi-Agent Orchestration: A Plan-Execute-Verify-Replan Framework for Complex Query Resolution",
            ),
            (
                "author",
                "Xing Zhang and Yanwei Cui and Guanghui Wang and Wei Qiu and Ziyuan Li and Fangwei Han and Yajing Huang and Hengzhi Qiu and Bing Zhu and Peiyang He",
            ),
            (
                "booktitle",
                "ICLR 2026 Workshop on Multi-Agent Learning and Its Opportunities in the Era of Generative AI",
            ),
            ("year", "2026"),
            ("eprint", "2603.11445"),
            ("note", "ICLR 2026 MALGAI workshop paper; arXiv v2"),
            ("url", "https://openreview.net/forum?id=WUmz4LUbvU"),
        ),
    ),
    (
        "zhuge2024gptswarm",
        "inproceedings",
        "peer_reviewed",
        (
            ("title", "{GPTSwarm}: Language Agents as Optimizable Graphs"),
            (
                "author",
                "Mingchen Zhuge and Wenyi Wang and Louis Kirsch and Francesco Faccio and Dmitrii Khizbullin and Jürgen Schmidhuber",
            ),
            (
                "booktitle",
                "Proceedings of the 41st International Conference on Machine Learning",
            ),
            ("year", "2024"),
            ("volume", "235"),
            ("pages", "62743--62767"),
            ("url", "https://proceedings.mlr.press/v235/zhuge24a.html"),
        ),
    ),
)

CLAIM_ROWS = (
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
EXPECTED_CLAIM_UPDATES = {
    "C-DEV-DIAGNOSTIC": ("ready", "immutable failed development diagnostic"),
    "C-THESIS": ("structural", "prospective complete-bundle hypothesis"),
    "C-ARCH-FLAGSHIP": ("structural", "prospective Architecture stress test"),
    "C-JCI-REPLICATION": ("structural", "planned unpooled replication"),
}
BLOCKED_STATE_IDS = (
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
RESULTS_SLOT_IDS = (
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
POLICY_IDS = (
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
POLICY_PUBLIC_KEYS = {
    "agentprune": "zhang2025agentprune",
    "automix": "aggarwal2024automix",
    "bicsrouter": "keyu2026bicsrouter",
    "conformal_thinking": "wang2026conformalthinking",
    "cost_aware_protocol_routing": "yang2026costawareprotocol",
    "gptswarm": "zhuge2024gptswarm",
    "graphplanner": "feng2026graphplanner",
    "masrouter": "yue2025masrouter",
    "rirs_talk_to_right_specialists": "li2025rirs",
    "routellm": "ong2025routellm",
    "self_resource_allocation": "amayuelas2025selfresource",
    "verimap": "xu2026verimap",
    "vmao": "zhang2026vmao",
    "zooter_adaptation": "lu2024zooter",
}
ALL_BIBLIOGRAPHY_KEYS = (
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
RELATED_PRIMARY_CITATIONS = (
    "kallus2018instrument",
    "oprescu2025amriv",
    "dellapenna2026brace",
    "zhang2026icore",
    "wong2026eureka",
    "yang2026star",
    "bala2026setvalued",
)
PROTOCOL_DEFINED_POLICY_IDS = (
    "agora",
    "always_all_specialists",
    "difficulty_confidence",
    "fixed_topology",
    "matched_compute_self_agent_scaling",
    "random_admissible_action",
    "separated_router_stopper",
    "solo",
)
PROTOCOL_DEFINED_ROLES = {
    "agora": (
        "inputs=frozen public packet, capability and cost cards, action menu, and admissibility; "
        "action_choice=maximum positive declared capability-minus-cost surplus; "
        "stopping=STOP only when the hard terminal gate passes and no surplus is positive, otherwise SOLO_SYNTHESIS; "
        "cost=all attempted selector, specialist, retry, verifier, and synthesis compute; "
        "inadmissibility=exclude the action before bidding; ties=byte-ordinal action ID; "
        "synthesis=the common bounded synthesizer after the selected specialist"
    ),
    "always_all_specialists": (
        "inputs=frozen public packet, complete action menu, costs, and admissibility; "
        "action_choice=invoke every admissible specialist exactly once in byte-ordinal action order; "
        "stopping=terminate after the common synthesizer, using SOLO_SYNTHESIS when no specialist is admissible; "
        "cost=all specialist, retry, verifier, and synthesis compute; "
        "inadmissibility=skip only actions masked before execution; ties=byte-ordinal action ID; "
        "synthesis=one common bounded synthesis over all retained specialist outputs"
    ),
    "difficulty_confidence": (
        "inputs=frozen difficulty and confidence features plus action menu, costs, and admissibility only; "
        "action_choice=frozen multiclass learner with the common learner class, capacity, split, and tuning budget; "
        "stopping=frozen STOP threshold learned without residual-obligation or capability-profile features; "
        "cost=all router, specialist, retry, verifier, and synthesis compute; "
        "inadmissibility=mask before prediction and fall back to SOLO_SYNTHESIS if no predicted specialist remains; "
        "ties=byte-ordinal action ID; synthesis=the common bounded synthesizer"
    ),
    "fixed_topology": (
        "inputs=frozen public packet and one topology selected on the development split before evaluation; "
        "action_choice=the same topology and specialist order for every evaluation case; "
        "stopping=the topology's predeclared terminal step with no case-adaptive early exit; "
        "cost=all topology, retry, verifier, and synthesis compute; "
        "inadmissibility=fall back to SOLO_SYNTHESIS if a required topology action is masked; "
        "ties=byte-ordinal topology ID during development selection; synthesis=the common bounded synthesizer"
    ),
    "matched_compute_self_agent_scaling": (
        "inputs=frozen public packet and the case-level complete-compute ceiling; "
        "action_choice=independent solo-agent samples until the predeclared ceiling without specialist packets; "
        "stopping=the frozen sample count or compute ceiling, whichever occurs first; "
        "cost=all solo samples, retries, verifier, aggregation, and synthesis compute; "
        "inadmissibility=specialist actions are never eligible; ties=byte-ordinal normalized candidate output; "
        "synthesis=the common bounded synthesizer over the frozen self-agent sample set"
    ),
    "random_admissible_action": (
        "inputs=complete action menu, costs, admissibility mask, and frozen randomization seed only; "
        "action_choice=uniform draw over currently admissible actions; stopping=terminate immediately when STOP is drawn; "
        "cost=all selected action, retry, verifier, and synthesis compute; "
        "inadmissibility=exclude before the draw and use SOLO_SYNTHESIS if the eligible set is empty; "
        "ties=the frozen randomization stream; synthesis=the common bounded synthesizer after any non-STOP draw"
    ),
    "separated_router_stopper": (
        "inputs=the full parity public packet, capability table, costs, action menu, and admissibility; "
        "action_choice=a frozen non-STOP router trained separately from the stopper; "
        "stopping=a separately trained binary stopper evaluated before router execution; "
        "cost=both models plus all selected action, retry, verifier, and synthesis compute; "
        "inadmissibility=mask before routing and fall back to SOLO_SYNTHESIS if no routed action remains; "
        "ties=byte-ordinal action ID; synthesis=the common bounded synthesizer"
    ),
    "solo": (
        "inputs=frozen public packet only; action_choice=SOLO_SYNTHESIS exactly once; "
        "stopping=terminate after that bounded synthesis; cost=all solo, retry, and verifier compute; "
        "inadmissibility=no specialist action is eligible; ties=not applicable; "
        "synthesis=the common bounded synthesizer is the sole generation path"
    ),
}
POLICY_PROVENANCE_ROWS = (
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
        PROTOCOL_DEFINED_ROLES["agora"],
        "blocked_pending_authenticated_roster",
    ),
    (
        "always_all_specialists",
        "protocol_defined_comparator",
        None,
        PROTOCOL_DEFINED_ROLES["always_all_specialists"],
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
        PROTOCOL_DEFINED_ROLES["difficulty_confidence"],
        "blocked_pending_authenticated_roster",
    ),
    (
        "fixed_topology",
        "protocol_defined_comparator",
        None,
        PROTOCOL_DEFINED_ROLES["fixed_topology"],
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
        PROTOCOL_DEFINED_ROLES["matched_compute_self_agent_scaling"],
        "blocked_pending_authenticated_roster",
    ),
    (
        "random_admissible_action",
        "protocol_defined_comparator",
        None,
        PROTOCOL_DEFINED_ROLES["random_admissible_action"],
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
        PROTOCOL_DEFINED_ROLES["separated_router_stopper"],
        "blocked_pending_authenticated_roster",
    ),
    (
        "solo",
        "protocol_defined_comparator",
        None,
        PROTOCOL_DEFINED_ROLES["solo"],
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
PROVENANCE_CLASSES = (
    "published_method",
    "protocol_defined_comparator",
    "published_method_adaptation",
)
PROTOCOL_REQUIRED_CLAUSES = (
    ("inputs", "inputs"),
    ("action choice", "action_choice"),
    ("stopping", "stopping"),
    ("complete cost", "cost"),
    ("admissibility", "inadmissibility"),
    ("tie", "ties"),
    ("common synthesizer", "synthesis"),
)
NARRATIVE_WEAKENINGS = (
    ("paired direct policy evaluation", "off-policy evaluation"),
    ("score-level orthogonality", "all decision errors are second order"),
    (
        "our first-order action-choice proposition",
        "DML establishes our first-order proposition",
    ),
    ("We claim neither the first graph", "We introduce the first graph"),
)
ORACLE = "retrospective_oracle"
ATTACK_IDS = (
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
SUPPORTING_ROWS = (
    ("B1", "identity"),
    ("B2", "confidence"),
    ("B3", "decision boundary"),
    ("B4", "standard lower-bound boundary"),
    ("B5", "estimator boundary"),
)
KILLED_HEADLINES = (
    "cumulative regret",
    "joint audit/receipt minimax",
    "same-information policy superiority",
)
KILL_SURVIVOR_ROWS = (
    (
        "Architecture",
        "E2 nonpositive, nonestimable, unsupported, or noncompliant",
        "causal mechanism and ICLR-main OACS thesis",
        "JCI descriptive or randomized executed-complete-bundle effect only; never flagship, replication, cross-domain, mechanism-main, or OACS-main",
    ),
    (
        "Architecture",
        "E3 null or parity-invalid after positive E2",
        "OACS method and ICLR-main policy claim",
        "same narrower JCI-only boundary",
    ),
    (
        "JCI",
        "E2 nonpositive, nonestimable, unsupported, or noncompliant",
        "causal mechanism and ICLR-main OACS thesis",
        "Architecture descriptive or randomized executed-complete-bundle effect only; never flagship, replication, cross-domain, mechanism-main, or OACS-main",
    ),
    (
        "JCI",
        "E3 null or parity-invalid after positive E2",
        "OACS method and ICLR-main policy claim",
        "same narrower Architecture-only boundary",
    ),
)
KILL_CHAIN_CLAUSES = (
    "E2 failure in either ontology kills the causal mechanism and ICLR-main thesis.",
    "After positive E2, E3 failure in either ontology kills the OACS method and ICLR-main policy claim.",
    "Only the exact narrower other-ontology descriptive or randomized executed-bundle result may remain, never as a rescued flagship, replication, cross-domain, mechanism, or OACS-main claim.",
)
KILL_CHAIN_SOURCE_CLAUSES = (
    "E2 failure in either ontology kills\nthe causal mechanism and ICLR-main thesis.",
    "After positive E2, E3 failure in\neither ontology kills the OACS method and ICLR-main policy claim.",
    "Only the\nexact narrower other-ontology descriptive or randomized executed-bundle result\nmay remain, never as a rescued flagship, replication, cross-domain, mechanism,\nor OACS-main claim.",
)
KILL_SEMANTIC_MUTATIONS = (
    (
        "Architecture E2 ontology scope",
        0,
        "either ontology",
        "Architecture ontology only",
    ),
    (
        "Architecture E2 required removal",
        0,
        "causal mechanism and ICLR-main thesis",
        "Architecture causal mechanism only",
    ),
    (
        "Architecture E2 survivor expansion",
        2,
        "descriptive or randomized executed-bundle result",
        "descriptive or randomized executed-bundle result or Architecture proxy endpoint",
    ),
    (
        "Architecture E3 ontology scope",
        1,
        "either ontology",
        "Architecture ontology only",
    ),
    (
        "Architecture E3 required removal",
        1,
        "OACS method and ICLR-main policy claim",
        "Architecture OACS method only",
    ),
    (
        "Architecture E3 rescue expansion",
        2,
        "never as a rescued flagship",
        "possibly as a rescued Architecture OACS-main policy claim",
    ),
    ("JCI E2 ontology scope", 0, "either ontology", "JCI ontology only"),
    (
        "JCI E2 required removal",
        0,
        "causal mechanism and ICLR-main thesis",
        "JCI causal mechanism only",
    ),
    (
        "JCI E2 survivor expansion",
        2,
        "descriptive or randomized executed-bundle result",
        "descriptive or randomized executed-bundle result or JCI subgroup",
    ),
    ("JCI E3 ontology scope", 1, "either ontology", "JCI ontology only"),
    (
        "JCI E3 required removal",
        1,
        "OACS method and ICLR-main policy claim",
        "JCI OACS method only",
    ),
    (
        "JCI E3 rescue expansion",
        2,
        "never as a rescued flagship",
        "possibly as a rescued JCI flagship replication claim",
    ),
)

DISPOSITIONS = (
    "iCORE establishes obligation--evidence--responsibility coupling and audit intervention as prior art; our obligation representation is measurement instrumentation, not a first obligation graph.",
    "Eureka establishes dynamic obligation-graph orchestration and acceptance semantics as prior art; our contribution is not obligation-graph construction.",
    "STAR establishes typed execution/failure-state specialist routing as prior art; our contribution is not execution-aware routing.",
    "Set-valued routing establishes fixed-catalog capability coverage and cost-aware selection as prior art; our contribution is not a first set-valued selector.",
    "BRACE is the closest product-bias/compliance prior; B1 is model-specific supporting theory rather than a first orthogonal remainder claim.",
)
METHOD_BOUNDARY = "OACS is the prospective study policy, not the first obligation graph, execution-aware router, or capability-set selector."
FAIL_CLOSED_E2_POLICY = "No required repeat, cell, target, or site may be dropped, replaced, filtered, or analyzed as-treated/per-protocol."
FAIL_CLOSED_E2_POLICY_SOURCE = "No\nrequired repeat, cell, target, or site may be dropped, replaced, filtered,\nor analyzed as-treated/per-protocol."
FORBIDDEN_POSITIVES = (
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
FORBIDDEN_NOVELTY_PHRASES = (
    "latest",
    "first",
    "no prior work",
    "unprecedented",
    "exhaustive",
    "state-of-the-art",
)

RECEIPT_KEYS = (
    "schema_version",
    "status",
    "source_manifest_sha256",
    "source_file_count",
    "primary_source_manifest_sha256",
    "primary_source_keys",
    "primary_source_count",
    "claim_count",
    "blocked_slot_count",
    "policy_count",
    "attack_count",
    "citation_authority_status",
    "pdf_compile_verified",
    "empirical_status",
    "receipt_sha256",
)
PRIMARY_SOURCE_KEYS = tuple(sorted(source[0] for source in PRIMARY_SOURCES))
SOURCE_IDENTITIES = (
    (
        "latex/README.md",
        1518,
        "20DECF93E9AFD5CCC7B1925A383FAC5F691865BD6B99B0F465AB5D62446A4E45",
    ),
    (
        "latex/appendices/appendix_analysis_protocol.tex",
        17157,
        "D5E653A19094C2D0B19475C1FC126308DA1994567C86A2A31D15BC9C36DBC149",
    ),
    (
        "latex/appendices/appendix_claims.tex",
        2449,
        "A61388B1DF0F8665495A892459900915EAD2443E60DED8C632091F72735CFF77",
    ),
    (
        "latex/appendices/appendix_policy_provenance.tex",
        11982,
        "E947C55C6F2C9F18293A163E9C19A0FADD041416B0416A636B92D6F5B72C3D0C",
    ),
    (
        "latex/appendices/appendix_reviewer_attacks.tex",
        2578,
        "1B9DDB20873E16CADFFCF71BBCB9BA538DBB62D16AA25F72C47467CA15E6BE59",
    ),
    (
        "latex/appendices/appendix_theory.tex",
        1790,
        "3AE7B93C307F0FD2B840E9B02315F6733719237668E2AD5A746FBFCB0BC3CE64",
    ),
    (
        "latex/fancyhdr.sty",
        20521,
        "B56EC4434B9F4607529A4B23DC68AD8D4B94F1F631C8CDDAF7DA78140D53A5EA",
    ),
    (
        "latex/iclr2027_conference.bst",
        26973,
        "2D67552DB7ED38CCFCCB5957B52F95656E25C249724761D3CF5F7922AD1844C5",
    ),
    (
        "latex/iclr2027_conference.sty",
        9025,
        "797DEEF41724E93761426AC0CBCCA46279A91CC650DD1F0CE76A4F08D2098EA6",
    ),
    (
        "latex/main.tex",
        2417,
        "010AA6D5DE6B8787470CFE2C58B542A665B409B733C150965DECD026584FD99D",
    ),
    (
        "latex/natbib.sty",
        45154,
        "88BC70C0E48461934CAB5B2ACCEF06B74A8B3AC45AD03CCD3F2A6B7E0D6D530D",
    ),
    (
        "latex/references.bib",
        12287,
        "2A172632CAB4467CB7FEDA55DEBFDC8EB2B6B646333A48A14B6A3E22C8CD8B00",
    ),
    (
        "latex/sections/01_introduction.tex",
        3157,
        "8A7A66623B0BD50D615140EAE4ECC4F82F0B6ED4053B3584BC5481E5F02F0395",
    ),
    (
        "latex/sections/02_related_work.tex",
        4824,
        "2D9971B29924542601DF2F4C9FFCA9A44D798E86F5E4E79B8D7C58FC16B045B3",
    ),
    (
        "latex/sections/03_problem_formulation.tex",
        2703,
        "29E251DE1816A44E98F5DFBAFD302F325F8217BB2C36D4E03DA5519F54AAC28B",
    ),
    (
        "latex/sections/04_method.tex",
        1931,
        "9429D165B37CB751C693706CE2C19041F6AC65FD1FF2709D31132F4F69999D92",
    ),
    (
        "latex/sections/05_supporting_theory.tex",
        1577,
        "87945EF21652F56887EC1C8F4C4050CB8B6CE5FA875CAB3802300438D1DADB81",
    ),
    (
        "latex/sections/06_experimental_design.tex",
        2487,
        "E78F7ADB77675761C986D551D381F82E210CB62DE7C23E96B85655A50790F056",
    ),
    (
        "latex/sections/07_results.tex",
        2085,
        "97B402E82313F8B44B697438D5A61A16DA439C69B602448DED19C2D56EE95D84",
    ),
    (
        "latex/sections/08_limitations.tex",
        1589,
        "A5E17D5EF767CF0AA6F7BBB3419F34DCAC1B38C0EBBEF547F693E04393EE813A",
    ),
    (
        "latex/sections/09_conclusion.tex",
        1406,
        "E3D1F619B544E2DD8EB0181B5C90431D4E1F39A8F604A8072072E8B3EDD76D20",
    ),
    (
        "latex/sections/10_submission_statements.tex",
        1682,
        "B20C836964F08013DCE30467339C0A92D5B3AFE44D187F10566F1E327262A839",
    ),
)
SOURCE_MANIFEST_TEXT = "".join(
    f"{path}\t{length}\t{digest}\n" for path, length, digest in SOURCE_IDENTITIES
)
SOURCE_MANIFEST_SHA256 = (
    "db5b889b10859340e4dc7a835ccf77aaeb3e2a906ed48e52e06615054712d62c"
)
PRIMARY_MANIFEST_SHA256 = (
    "9a84a93002562dfde19008c759c960e809db5cb11cb95cc7ae2790f4a98b7108"
)
EXPECTED_RECEIPT_SHA256 = (
    "5d985080e0a7cd08fa033a6894c71e761d2b8a4df2a829573e604203234611d2"
)
EXPECTED_RECEIPT_JSON = (
    '{"attack_count":24,"blocked_slot_count":9,'
    '"citation_authority_status":"blocked_pending_authenticated_roster",'
    '"claim_count":23,"empirical_status":"no_go_needs_context",'
    '"pdf_compile_verified":false,"policy_count":22,"primary_source_count":10,'
    '"primary_source_keys":["bala2026setvalued","dellapenna2026brace",'
    '"flynn2026sparse","girard2026fast","kallus2018instrument",'
    '"oprescu2025amriv","qin2026oe2d","wong2026eureka","yang2026star",'
    '"zhang2026icore"],"primary_source_manifest_sha256":'
    '"9a84a93002562dfde19008c759c960e809db5cb11cb95cc7ae2790f4a98b7108",'
    '"receipt_sha256":"5d985080e0a7cd08fa033a6894c71e761d2b8a4df2a829573e604203234611d2",'
    '"schema_version":"ace.iclr2027.paper_latex_static.v1","source_file_count":22,'
    '"source_manifest_sha256":"db5b889b10859340e4dc7a835ccf77aaeb3e2a906ed48e52e06615054712d62c",'
    '"status":"literature_corrected_static_ready"}'
)
ACTIVE_PROSE_IDENTITIES = (
    (
        "latex/README.md",
        1508,
        "C6ABE2FEBA78B9BB1AB024B2B0E95ED090088475D1F5280F30ACFA395F8E3FC5",
    ),
    (
        "latex/appendices/appendix_analysis_protocol.tex",
        16567,
        "290ED12641CC8E0241BF5068E3A52229210CC4F45DCCB30955A66E9509CA1427",
    ),
    (
        "latex/appendices/appendix_policy_provenance.tex",
        11956,
        "6F87DDFABED2116FF90BB0CBFA2FF27D1F0BFF44376FAF5636083A45B91CADCD",
    ),
    (
        "latex/appendices/appendix_reviewer_attacks.tex",
        2519,
        "4F43C13DBEAD028ACD1A3C6C77640F0C88B594DCB5185FD4E6498E3008A75B56",
    ),
    (
        "latex/sections/01_introduction.tex",
        3120,
        "7A82A6108F9C13D0DCA3114236FA9F1DE261410F75112CBCA6F0666C7B827E81",
    ),
    (
        "latex/sections/02_related_work.tex",
        4807,
        "1DC86D1706BF17259C1E91CA694FB980CE714F4946B57DB528F05A91AB01CA83",
    ),
    (
        "latex/sections/03_problem_formulation.tex",
        2684,
        "81793744E00FC0D8D9CAEB58D95C474AF7AF4AF0D61C3939C38368AA1C955E36",
    ),
    (
        "latex/sections/04_method.tex",
        1917,
        "07B39518C3684B3D7EEA831BED0F9E4D82AFD6A4239632893B27814483D03008",
    ),
    (
        "latex/sections/09_conclusion.tex",
        1394,
        "8AD2BE06F0F8EC29682AC4D888E1ACA829EC3274568A64CB49EA7CDE5D9E24FF",
    ),
    (
        "latex/sections/10_submission_statements.tex",
        1676,
        "95399F509F392DEB085EF42659EF0549C153361752CC918C7C4E255EA6EF5320",
    ),
)
ACTIVE_PROSE_MANIFEST_SHA256 = (
    "A4EC9DD45C1299AC17891F4A12F16FFEA36A69114C5086F3CE90F05E9D3081CD"
)
CANONICAL_ACTIVE_MAIN_SHA256 = (
    "69DE6587279835C81E7FA2ADB5A3BC440A029E7FCBED5725984830F87556B467"
)
CANONICAL_ACTIVE_STATEMENTS_SHA256 = (
    "B20C836964F08013DCE30467339C0A92D5B3AFE44D187F10566F1E327262A839"
)
CANONICAL_ACTIVE_MANUSCRIPT_TEX_SHA256 = {
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
MAIN_FINAL_CONTROL_MUTATIONS = (
    ("caret-encoded final control", "^^5ciclrfinalcopy"),
    ("csname final control", r"\csname iclrfinalcopy\endcsname"),
    (
        "expanded csname final control",
        r"\expandafter\csname iclrfinalcopy\endcsname",
    ),
    (
        "macro-built final control",
        r"\def\camera{iclrfinalcopy}\csname\camera\endcsname",
    ),
)
MAIN_METADATA_AND_LOADING_MUTATIONS = (
    ("PDF author metadata", r"\hypersetup{pdfauthor={Named Researcher}}"),
    ("PDF creator metadata", r"\hypersetup{pdfcreator={Named Researcher}}"),
    ("primitive PDF author metadata", r"\pdfinfo{/Author (Named Researcher)}"),
    ("primitive PDF creator metadata", r"\pdfinfo{/Creator (Named Researcher)}"),
    ("concealed author identity", r"\def\AuthorIdentity{Named Researcher}"),
    (
        "alternate include",
        r"\include{sections/10_submission_statements}",
    ),
    (
        "conditional input",
        r"\InputIfFileExists{sections/10_submission_statements.tex}{}{}",
    ),
    (
        "include-only load",
        r"\includeonly{sections/10_submission_statements}",
    ),
    (
        "dynamic input",
        r"\csname input\endcsname{sections/10_submission_statements}",
    ),
    (
        "internal input",
        r"\@input{sections/10_submission_statements.tex}",
    ),
    (
        "stream load",
        r"\openin1=sections/10_submission_statements.tex",
    ),
)
MAIN_LAYOUT_TYPOGRAPHY_MUTATIONS = (
    ("paper width", r"\paperwidth=8.5in"),
    ("PDF page width", r"\pdfpagewidth=8.5in"),
    ("horizontal offset", r"\hoffset=-1in"),
    ("vertical offset", r"\voffset=-1in"),
    ("header height", r"\headheight=0pt"),
    ("footer skip", r"\footskip=0pt"),
    ("column separation", r"\columnsep=1pt"),
    ("paragraph spacing", r"\parskip=0pt"),
    ("font size", r"\fontsize{8}{9}\selectfont"),
    ("length alias", r"\setlength{\paperwidth}{8.5in}"),
    ("add-to-length alias", r"\addtolength{\topskip}{-2pt}"),
    (
        "deferred typography",
        r"\AtBeginDocument{\fontsize{8}{9}\selectfont}",
    ),
)
ANONYMITY_CHANNEL_MUTATIONS = (
    ("author metadata", r"\hypersetup{pdfauthor={Named Researcher}}"),
    ("creator metadata", r"\pdfinfo{/Creator (Named Researcher)}"),
    ("stable researcher identifier", "ORCID: 0000-0002-1825-0097"),
    ("affiliation channel", "Affiliation: Example University"),
    ("funding channel", "Funding: Example Grant 1234"),
    (
        "acknowledgment channel",
        r"\section*{Acknowledgments} Named Researcher contributed.",
    ),
    (
        "author-identifying URL",
        "Author profile: https://example.edu/~named-researcher",
    ),
)
INDIRECT_NON_MAIN_METADATA_MUTATIONS = (
    (
        "csname metadata package control",
        r"\csname hypersetup\endcsname{pdfauthor={Named Researcher}}",
    ),
    (
        "expanded document information primitive",
        r"\expandafter\csname pdfinfo\endcsname{/Creator (Named Researcher)}",
    ),
    (
        "macro-built document information primitive",
        r"\def\metadatachannel{pdfinfo}"
        r"\csname\metadatachannel\endcsname{/Author (Named Researcher)}",
    ),
)
STATEMENT_CLOSED_CONTRACT_MUTATIONS = (
    ("direct authorization contradiction", "Submission is hereby authorized."),
    (
        "double-negative execution claim",
        "It is not the case that experimentation did not occur.",
    ),
    ("modal submission claim", "The manuscript may now proceed to review."),
    (
        "reproducibility synonym",
        "The empirical findings can be independently replicated.",
    ),
    (
        "author-review remainder",
        "All author responsibility checks are complete.",
    ),
    ("unresolved-boundary reversal", "No requirement remains unresolved."),
)
ERROR_CODES = (
    "source_identity_invalid",
    "source_bytes_invalid",
    "source_grammar_invalid",
    "scientific_boundary_invalid",
    "primary_source_manifest_invalid",
)
HELP_TEXT = "usage: verify_iclr2027_paper_latex.py [--help]\n"
ERROR_SCHEMA = "ace.iclr2027.paper_latex_static_error.v1"
AUTHORITY_SIBLINGS = (
    "claim_evidence_matrix.md",
    "paper_blueprint.md",
    "reviewer_attack_matrix.md",
    "theory_appendix_map.md",
    "path_b_external_handoff.md",
)
EDITABLE_TEX = (
    "latex/sections/01_introduction.tex",
    "latex/sections/02_related_work.tex",
    "latex/sections/03_problem_formulation.tex",
    "latex/sections/04_method.tex",
    "latex/sections/09_conclusion.tex",
    "latex/appendices/appendix_reviewer_attacks.tex",
    "latex/appendices/appendix_policy_provenance.tex",
)
ROLE_COMMAND_SIGNATURES = {
    "latex/sections/01_introduction.tex": (
        ("begin", "claim", "emph", "end", "section", "structural"),
        ("item",),
    ),
    "latex/sections/02_related_work.tex": (
        ("cite", "citet", "citep", "claim", "section"),
        (),
    ),
    "latex/sections/03_problem_formulation.tex": (
        ("ref", "section"),
        ("in", "lambda", "top"),
    ),
    "latex/sections/04_method.tex": (("section",), ("oacs",)),
    "latex/sections/09_conclusion.tex": (("section",), ()),
    "latex/appendices/appendix_reviewer_attacks.tex": (
        ("begin", "end", "section", "textbf"),
        ("item",),
    ),
    "latex/appendices/appendix_policy_provenance.tex": (
        ("begin", "citep", "end", "section", "textbf", "texttt"),
        ("item", "par", "raggedright", "small"),
    ),
}
COMMAND_SIGNATURE_ORACLE = {
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
CONTROL_SYMBOL_SIGNATURE_ORACLE = {
    "\\": (0, False, {}),
    "_": (0, False, {}),
}
ALLOWED_CONTROL_SYMBOLS = ("\\", "_")
EXCLUDED_CONTROL_SYMBOLS = tuple(
    chr(code)
    for code in range(32, 127)
    if not chr(code).isalpha() and chr(code) not in ALLOWED_CONTROL_SYMBOLS
)
UTF8_AND_NONPRINTING_CONTROL_SYMBOLS = (
    "\x00",
    "\x01",
    "\x1f",
    "\x7f",
    "\u0085",
    "\u00a0",
    "\u200b",
    "\u2028",
    "\ufeff",
    "\u00e9",
    "\ud55c",
    "\U0001f600",
)
ROLE_ENVIRONMENTS = {
    "latex/sections/01_introduction.tex": ("enumerate",),
    "latex/sections/02_related_work.tex": (),
    "latex/sections/03_problem_formulation.tex": (),
    "latex/sections/04_method.tex": (),
    "latex/sections/09_conclusion.tex": (),
    "latex/appendices/appendix_reviewer_attacks.tex": ("enumerate",),
    "latex/appendices/appendix_policy_provenance.tex": ("enumerate",),
}
CANONICAL_NOVELTY_CLAIM_SPANS = (
    "The intended contributions are deliberately conditional. They are "
    "receipt-bound instrumentation rather than first contributions: prior "
    "obligation-state and execution-aware representations are operationalized "
    "here for causal measurement.",
    "We use the reviewed primary roster as a non-exhaustive positioning aid.",
    *DISPOSITIONS,
    "We claim neither the first graph, router, selector, verifier, conformal "
    "stopper, orthogonal score, regret algorithm, nor collaboration framework.",
    "The paper specifies and preregisters a prospective, falsifiable test for "
    "verified executed bundles under a fixed causal and equal-information protocol; "
    "it does not claim that routing, specialization, noncompliance correction, or "
    "orthogonal scores are new in isolation.",
    METHOD_BOUNDARY,
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
    "Novelty (RA-NOV-01 and RA-NOV-02): iCORE removes obligation-graph novelty, "
    "Eureka removes obligation-graph construction novelty, STAR removes "
    "execution-aware-routing novelty, and set-valued routing removes selector "
    "novelty; absent compliant E2/E3 kills ICLR-main novelty. Component prior art "
    "and theorem stitching remove theory-first language.",
    "The standard same-information obstruction and structural estimator separation "
    "remain appendix boundaries, not headline novelty.",
    "It is not a new joint nuisance minimax lower bound.",
    "The scoped literature does not establish a standalone theory-first novelty claim.",
    "The paper tier is evaluation validity with supporting theory only.",
)
CANONICAL_AUTHORIAL_NONCLAIM_SPANS = (
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
AUTHORIAL_CLAIM_SUBJECT = re.compile(
    r"^(?:OACS\b|We\b|Our\b|This (?:approach|contribution|manuscript|method|paper|"
    r"representation|router|scaffold|selector|study|system|work)\b|The (?:approach|"
    r"contribution|method|novelty|originality|paper|representation|router|selector|"
    r"study|system|work)\b)",
    re.IGNORECASE,
)
PATH_AND_LOADER_CAPABILITY_ATTRIBUTES = frozenset(
    {
        "__spec__",
        "absolute",
        "anchor",
        "as_posix",
        "as_uri",
        "cached",
        "chmod",
        "create_module",
        "cwd",
        "drive",
        "exec_module",
        "exists",
        "expanduser",
        "find_spec",
        "get_code",
        "get_data",
        "get_filename",
        "get_resource_reader",
        "get_source",
        "glob",
        "group",
        "hardlink_to",
        "home",
        "is_absolute",
        "is_block_device",
        "is_char_device",
        "is_dir",
        "is_fifo",
        "is_file",
        "is_junction",
        "is_mount",
        "is_package",
        "is_relative_to",
        "is_reserved",
        "is_socket",
        "is_symlink",
        "iterdir",
        "joinpath",
        "lchmod",
        "link_to",
        "load_module",
        "loader",
        "lstat",
        "match",
        "mkdir",
        "module_from_spec",
        "module_repr",
        "name",
        "open",
        "origin",
        "owner",
        "parent",
        "parents",
        "parts",
        "read_bytes",
        "read_text",
        "readlink",
        "relative_to",
        "rename",
        "replace",
        "resolve",
        "rglob",
        "rmdir",
        "root",
        "samefile",
        "spec_from_file_location",
        "stat",
        "stem",
        "submodule_search_locations",
        "suffix",
        "suffixes",
        "symlink_to",
        "touch",
        "unlink",
        "walk",
        "with_name",
        "with_segments",
        "with_stem",
        "with_suffix",
        "write_bytes",
        "write_text",
    }
)
PRODUCTION_ALLOWED_CAPABILITY_REFERENCES = (
    (
        "_contains_unapproved_authorial_claim",
        "replace",
        "call",
        "remainder.replace(span, '', expected_count)",
    ),
    ("_entry_map", "name", "reference", "entry.name"),
    (
        "_estimand_receipt_title",
        "replace",
        "call",
        "titles[0].replace('\\\\\\\\', ' ')",
    ),
    ("_extract_literal_arguments", "group", "call", "match.group(1)"),
    (
        "_extract_normalized_manuscript_title",
        "replace",
        "call",
        "titles[0].replace(_TITLE_LINE_BREAK, ' ')",
    ),
    ("_from_dict", "name", "reference", "field.name"),
    ("_normalize_active", "replace", "call", "active.replace('\\\\%', ' ')"),
    ("_parse_bibtex", "group", "call", "match.group(0)"),
    ("_parse_bibtex", "group", "call", "match.group(2)"),
    (
        "_parse_policy_provenance_registry",
        "replace",
        "call",
        "value.replace('\\\\_', '_')",
    ),
    (
        "_rendered_boundary_text",
        "replace",
        "call",
        "active.replace(_TITLE_LINE_BREAK, ' ')",
    ),
    (
        "_validate_manuscript_anonymity",
        "replace",
        "call",
        "active.replace(anonymous_author, '', 1)",
    ),
    ("_validate_relative_source_path", "as_posix", "call", "path.as_posix()"),
    ("_validate_relative_source_path", "is_absolute", "call", "path.is_absolute()"),
    ("_validate_relative_source_path", "parts", "reference", "path.parts"),
    ("_validate_relative_source_path", "parts", "reference", "path.parts"),
    (
        "_validate_tex_bibliography_and_science",
        "replace",
        "call",
        "' '.join((active[relative] for relative in _MANUSCRIPT_SOURCE_PATHS if relative not in {'latex/appendices/appendix_analysis_protocol.tex', 'latex/appendices/appendix_policy_provenance.tex', 'latex/references.bib'})).replace('\\\\_', '_')",
    ),
    (
        "_validate_tex_bibliography_and_science",
        "replace",
        "call",
        "active['latex/sections/03_problem_formulation.tex'].replace('No required repeat, cell, target, or site may be dropped, replaced, filtered, or analyzed as-treated/per-protocol.', '', 1)",
    ),
    (
        "_validate_tex_bibliography_and_science",
        "replace",
        "call",
        "closure.replace(_METHOD_BOUNDARY, '', 2)",
    ),
    (
        "_validate_tex_bibliography_and_science",
        "replace",
        "call",
        "closure.replace(sentence, '', 1)",
    ),
    (
        "_validate_tex_bibliography_and_science",
        "replace",
        "call",
        "editable_novelty.replace('It does not establish our first-order action-choice proposition for generated features or execution-map errors.', '', 1)",
    ),
    (
        "_validate_tex_bibliography_and_science",
        "replace",
        "call",
        "editable_novelty.replace(span, '', expected_count)",
    ),
    (
        "_validate_tex_bibliography_and_science",
        "replace",
        "call",
        "related.replace(_NOVELTY_BOUNDARY, '', 1)",
    ),
    (
        "_validate_tex_bibliography_and_science",
        "replace",
        "call",
        "related_novelty.replace('We claim neither the first graph, router, selector, verifier, conformal stopper, orthogonal score, regret algorithm, nor collaboration framework.', '', 1)",
    ),
    (
        "_validate_tex_bibliography_and_science",
        "replace",
        "call",
        "related_novelty.replace('We claim neither the first graph, router, selector, verifier, conformal stopper, orthogonal score, regret algorithm, nor collaboration framework.', '', 1).replace('It does not establish our first-order action-choice proposition for generated features or execution-map errors.', '', 1)",
    ),
    (
        "_validate_tex_bibliography_and_science",
        "replace",
        "call",
        "related_novelty.replace(_METHOD_BOUNDARY, '', 1)",
    ),
    (
        "_validate_tex_bibliography_and_science",
        "replace",
        "call",
        "related_novelty.replace(sentence, '', 1)",
    ),
    (
        "_validate_tex_bibliography_and_science",
        "replace",
        "call",
        "token.replace('\\\\_', '_')",
    ),
    (
        "_verify_static_paper_latex_at",
        "read_bytes",
        "call",
        "tree.read_bytes('literature_primary_source_manifest.md', label='primary-source manifest')",
    ),
    (
        "_verify_static_paper_latex_at",
        "read_bytes",
        "call",
        "tree.read_bytes(relative, label=relative)",
    ),
    (
        "verify_estimand_receipt_manuscript",
        "parents",
        "reference",
        "Path(__file__).resolve().parents",
    ),
    (
        "verify_estimand_receipt_manuscript",
        "resolve",
        "call",
        "Path(__file__).resolve()",
    ),
    (
        "verify_estimand_receipt_manuscript_at",
        "is_file",
        "call",
        "path.is_file()",
    ),
    (
        "verify_estimand_receipt_manuscript_at",
        "is_symlink",
        "call",
        "path.is_symlink()",
    ),
    (
        "verify_estimand_receipt_manuscript_at",
        "read_bytes",
        "call",
        "path.read_bytes()",
    ),
    (
        "verify_static_paper_latex",
        "parents",
        "reference",
        "Path(__file__).resolve().parents",
    ),
    ("verify_static_paper_latex", "resolve", "call", "Path(__file__).resolve()"),
)
PRODUCTION_ALLOWED_CAPABILITY_NAMES = (
    ("<module>", "Path", "call", "Path('docs/paper/iclr2027_oacs')"),
    ("_validate_relative_source_path", "Path", "call", "Path(relative)"),
    (
        "_verify_static_paper_latex_at",
        "AuthenticatedTree",
        "call",
        "AuthenticatedTree(paper_root, label='ICLR 2027 paper root', read_observer=read_observer, post_file_validation_hook=post_file_validation_hook, directory_validation_hook=directory_validation_hook, name_observer=name_observer)",
    ),
    ("_verify_static_paper_latex_at", "Path", "annotation", "repository_root"),
    (
        "_verify_static_paper_latex_at",
        "Path",
        "type_check",
        "isinstance(repository_root, Path)",
    ),
    ("from_dict", "Path", "annotation", "repository_root"),
    ("from_json", "Path", "annotation", "repository_root"),
    (
        "verify_estimand_receipt_manuscript",
        "Path",
        "call",
        "Path(__file__)",
    ),
    (
        "verify_estimand_receipt_manuscript_at",
        "Path",
        "annotation",
        "repository_root",
    ),
    (
        "verify_estimand_receipt_manuscript_at",
        "Path",
        "type_check",
        "isinstance(repository_root, Path)",
    ),
    ("verify_static_paper_latex", "Path", "call", "Path(__file__)"),
)
PRODUCTION_AST_STRUCTURE_SHA256 = (
    "860F620FE3A9F2F5CB5F9AE474E128A194546DFA4967117230941A0C057DDC9B"
)
CLI_AST_STRUCTURE_SHA256 = (
    "2645AD8276A116E25DBB8CB0DCC8F4557F03D2654996B8D7B7CD12E5F963B883"
)


def _strip_tex_comments(text: str) -> str:
    lines = []
    for line in text.splitlines():
        for index, character in enumerate(line):
            if character == "%":
                slash_count = 0
                cursor = index - 1
                while cursor >= 0 and line[cursor] == "\\":
                    slash_count += 1
                    cursor -= 1
                if slash_count % 2 == 0:
                    line = line[:index]
                    break
        lines.append(line)
    return "\n".join(lines)


def _test_owned_normalized_manuscript_title(text: str) -> str:
    active = _strip_tex_comments(text)
    titles = tuple(re.findall(r"\\title\s*\{([^{}]*)\}", active, re.DOTALL))
    if len(titles) != 1:
        raise AssertionError("manuscript title grammar drift")
    semantic = titles[0].replace(r"\\", " ")
    return re.sub(r"\s+", " ", semantic).strip()


def _parse_policy_registry_for_test(
    text: str,
) -> tuple[tuple[str, str, str | None, str, str], ...]:
    active = _strip_tex_comments(text)
    begin = r"\begin{enumerate}"
    end = r"\end{enumerate}"
    if active.count(begin) != 1 or active.count(end) != 1:
        raise AssertionError("policy registry environment drift")
    begin_index = active.index(begin)
    end_index = active.index(end)
    if end_index < begin_index:
        raise AssertionError("policy registry environment drift")
    suffix = active[end_index + len(end) :]
    item_command = re.compile(r"\\item(?![A-Za-z])")
    if item_command.search(active[:begin_index]) or item_command.search(suffix):
        raise AssertionError("policy registry item outside enumerate")
    body = active[begin_index + len(begin) : end_index]
    expected_layout_prefix = "\n" + UNDERFULL_POLICY_REGISTRY_PREFIX
    if not body.startswith(expected_layout_prefix):
        raise AssertionError("policy registry layout scope drift")
    body = body[len(expected_layout_prefix) :]
    if suffix.strip():
        raise AssertionError("policy registry environment drift")
    item_parts = body.split(r"\item")
    if item_parts[0].strip():
        raise AssertionError("policy registry row grammar drift")
    items = item_parts[1:]
    rows = []
    pattern = re.compile(
        r"^\s*\\texttt\{(?P<policy>[^{}]+)\}\.\s*"
        r"\\textbf\{provenance\\_class\}=\\texttt\{(?P<kind>[^{}]+)\};\s*"
        r"\\textbf\{public\\_reference\}=(?P<reference>.*?);\s*"
        r"\\textbf\{protocol\\_role\}=(?P<role>.*?);\s*"
        r"\\textbf\{implementation\\_authentication\\_status\}="
        r"\\texttt\{(?P<status>[^{}]+)\}\.\s*$",
        re.S,
    )
    for item in items:
        if re.search(r"(?<!\\)_", item):
            raise AssertionError("policy registry row grammar drift")
        match = pattern.fullmatch(item.strip())
        if match is None:
            raise AssertionError("policy registry row grammar drift")
        reference_text = match.group("reference").strip()
        cite = re.fullmatch(r"\\citep\{([a-z0-9]+)\}", reference_text)
        if reference_text == r"\texttt{none}":
            reference = None
        elif cite is not None:
            reference = cite.group(1)
        else:
            raise AssertionError("policy registry reference drift")
        rows.append(
            (
                match.group("policy").replace(r"\_", "_"),
                match.group("kind").replace(r"\_", "_"),
                reference,
                re.sub(r"\s+", " ", match.group("role")).strip().replace(r"\_", "_"),
                match.group("status").replace(r"\_", "_"),
            )
        )
    return tuple(rows)


def _assert_optioned_xcolor_precedes_official_style(text: str) -> None:
    """Reject an optioned xcolor reload after the official style is active."""
    active = _strip_tex_comments(text)
    package_calls = tuple(
        (
            match.start(),
            (match.group(1) or "").strip(),
            tuple(
                package.strip()
                for package in match.group(2).split(",")
                if package.strip()
            ),
        )
        for match in re.finditer(
            r"\\usepackage\s*(?:\[([^\]]*)\])?\s*\{([^{}]+)\}",
            active,
        )
    )
    official_positions = tuple(
        position
        for position, _options, packages in package_calls
        if "iclr2027_conference" in packages
    )
    if len(official_positions) != 1:
        raise AssertionError("official style load is not unique")
    official_position = official_positions[0]
    optioned_xcolor_positions = tuple(
        position
        for position, options, packages in package_calls
        if "xcolor" in packages and options
    )
    if not optioned_xcolor_positions:
        raise AssertionError("optioned xcolor load is missing")
    if any(position > official_position for position in optioned_xcolor_positions):
        raise AssertionError("optioned xcolor load follows official style")


def _assert_official_font_encoding_preamble(text: str) -> None:
    """Require the portable T1/Times preamble without font/layout substitutes."""
    active = _strip_tex_comments(text)
    active_lines = tuple(line.strip() for line in active.splitlines() if line.strip())
    documentclass = r"\documentclass{article}"
    if active_lines.count(documentclass) != 1:
        raise AssertionError("article documentclass is not unique")
    if active_lines.count(T1_FONT_ENCODING_INVOCATION) != 1:
        raise AssertionError("exact T1 fontenc load is not unique")
    if active_lines.count(OFFICIAL_PACKAGE_INVOCATION) != 1:
        raise AssertionError("official style load is not unique")
    documentclass_index = active_lines.index(documentclass)
    fontenc_index = active_lines.index(T1_FONT_ENCODING_INVOCATION)
    official_index = active_lines.index(OFFICIAL_PACKAGE_INVOCATION)
    if fontenc_index != documentclass_index + 1:
        raise AssertionError("T1 fontenc is not immediately after documentclass")
    if not documentclass_index < fontenc_index < official_index:
        raise AssertionError("T1 fontenc does not precede official Times style")
    fontenc_calls = tuple(
        match.group(0)
        for match in re.finditer(
            r"\\usepackage\s*(?:\[[^\]]*\])?\s*\{fontenc\}",
            active,
        )
    )
    if fontenc_calls != (T1_FONT_ENCODING_INVOCATION,):
        raise AssertionError("fontenc encoding or multiplicity drift")
    if active.count(r"\author{Anonymous Authors}") != 1:
        raise AssertionError("anonymous author declaration drift")
    forbidden = (
        r"\\iclrfinalcopy\b",
        r"\\usepackage\s*(?:\[[^\]]*\])?\s*\{fontspec\}",
        r"\\setmainfont\b",
        r"\\(?:renewcommand|def)\s*\{?\\rmdefault\}?",
        r"\\(?:ifxetex|ifluatex|ifpdftex)\b",
        r"\\fontsize\b",
        r"\\(?:geometry|textwidth|textheight|oddsidemargin|evensidemargin|"
        r"topmargin|baselinestretch|linespread)\b",
    )
    if any(re.search(pattern, active, re.IGNORECASE) for pattern in forbidden):
        raise AssertionError("font, anonymity, or layout override introduced")


def _assert_sap_e3_aligned_layout_preserves_science(text: str) -> None:
    """Check reviewed E3 row layout against test-owned mathematical content."""
    active = _test_owned_lossless_active_tex(text)
    start_marker = r"\item[E3 estimand and parity.]"
    end_marker = r"\item[Policy eligibility and oracle.]"
    if active.count(start_marker) != 1 or active.count(end_marker) != 1:
        raise AssertionError("E3 SAP item boundary drift")
    start = active.index(start_marker) + len(start_marker)
    end = active.index(end_marker, start)
    item = active[start:end]
    displays = tuple(
        match.group(1).strip()
        for match in re.finditer(r"\\\[\s*(.*?)\s*\\\]", item, re.DOTALL)
    )
    if len(displays) != 2:
        raise AssertionError("E3 paired-display count drift")

    observed_science_rows = []
    for display in displays:
        semantic = display.replace(r"\begin{aligned}", "")
        semantic = semantic.replace(r"\end{aligned}", "")
        semantic = semantic.replace(r"\qquad", r"\\")
        rows = tuple(
            re.sub(r"[\s&]+", "", row) for row in semantic.split(r"\\") if row.strip()
        )
        observed_science_rows.append(rows)
    if tuple(observed_science_rows) != SAP_E3_EXPECTED_SCIENCE_ROWS:
        raise AssertionError("E3 mathematical token sequence drift")
    if displays != SAP_E3_EXPECTED_ALIGNED_DISPLAYS:
        raise AssertionError("E3 definitions are not the exact aligned row pairs")
    if any(display.count(r"\begin{aligned}") != 1 for display in displays):
        raise AssertionError("E3 aligned environment count drift")
    if any(display.count(r"\\") != 1 for display in displays):
        raise AssertionError("E3 definition-row count drift")
    if any(r"\qquad" in display for display in displays):
        raise AssertionError("E3 paired display retains same-row spacing")


def _underfull_expected_wrapper(contract) -> str:
    _label, _relative, _before, opening, inner, closing = contract
    return opening + inner + closing


def _assert_one_underfull_scope_wrapper(text: str, contract) -> None:
    label, _relative, before, opening, inner, closing = contract
    wrapper = opening + inner + closing
    if text.count(wrapper) != 1:
        raise AssertionError(f"underfull scope wrapper drift: {label}")
    if before and text.count(before + wrapper) != 1:
        raise AssertionError(f"underfull scope placement drift: {label}")
    if not before and not text.startswith(wrapper):
        raise AssertionError(f"underfull scope placement drift: {label}")


def _assert_no_underfull_layout_escape(source_text: dict[str, str]) -> None:
    active = "\n".join(
        _test_owned_lossless_active_tex(source_text[relative])
        for relative in MANUSCRIPT_SOURCE_CLOSURE
        if relative.endswith(".tex")
    )
    for pattern in UNDERFULL_FORBIDDEN_LAYOUT_PATTERNS:
        if re.search(pattern, active, re.IGNORECASE):
            raise AssertionError(f"underfull layout escape: {pattern}")


def _assert_underfull_source_contract(source_text: dict[str, str]) -> None:
    tex_paths = tuple(
        relative for relative in MANUSCRIPT_SOURCE_CLOSURE if relative.endswith(".tex")
    )
    if tuple(UNDERFULL_TEX_RAGGEDRIGHT_COUNTS) != tex_paths:
        raise AssertionError("underfull TeX count closure drift")
    for relative, expected in UNDERFULL_TEX_RAGGEDRIGHT_COUNTS.items():
        active = _test_owned_lossless_active_tex(source_text[relative])
        if active.count(r"\raggedright") != expected:
            raise AssertionError(f"underfull ragged-right count drift: {relative}")
    reconstructed = {
        relative: source_text[relative]
        for relative, _length, _digest in UNDERFULL_PRE_FIX_SOURCE_IDENTITIES
    }
    for contract in UNDERFULL_SCOPE_CONTRACTS:
        _assert_one_underfull_scope_wrapper(
            source_text[contract[1]],
            contract,
        )
        wrapper = _underfull_expected_wrapper(contract)
        relative = contract[1]
        reconstructed[relative] = reconstructed[relative].replace(
            wrapper,
            contract[4],
            1,
        )
    policy_registry = reconstructed[POLICY_PROVENANCE_RELATIVE]
    reviewed_prefix = "\\begin{enumerate}\n" + UNDERFULL_POLICY_REGISTRY_PREFIX
    if policy_registry.count(reviewed_prefix) != 1:
        raise AssertionError("policy registry list layout scope drift")
    reconstructed[POLICY_PROVENANCE_RELATIVE] = policy_registry.replace(
        reviewed_prefix,
        "\\begin{enumerate}\n",
        1,
    )
    for (
        relative,
        expected_length,
        expected_digest,
    ) in UNDERFULL_PRE_FIX_SOURCE_IDENTITIES:
        raw = reconstructed[relative].encode("utf-8")
        if len(raw) != expected_length:
            raise AssertionError(f"underfull semantic length drift: {relative}")
        if hashlib.sha256(raw).hexdigest().upper() != expected_digest:
            raise AssertionError(f"underfull semantic byte drift: {relative}")
    _assert_no_underfull_layout_escape(source_text)


def _underfull_scope_mutations(text: str, contract):
    label, _relative, before, opening, inner, closing = contract
    wrapper = opening + inner + closing
    expected_placement = before + wrapper
    if text.count(expected_placement) != 1:
        raise AssertionError(f"underfull mutation fixture drift: {label}")
    if before:
        broadened = text.replace(
            expected_placement,
            opening + before + inner + closing,
            1,
        )
    else:
        broadened = text.replace(wrapper, "broadened layout scope\n" + wrapper, 1)
    return (
        ("missing", text.replace(wrapper, inner, 1)),
        ("broadened", broadened),
        ("duplicated", text.replace(wrapper, wrapper + wrapper, 1)),
        ("misplaced after owning text", text.replace(wrapper, inner + wrapper, 1)),
    )


def _policy_registry_prefix_mutations(text: str):
    before = "\\begin{enumerate}\n"
    prefix = UNDERFULL_POLICY_REGISTRY_PREFIX
    expected = before + prefix
    if text.count(expected) != 1:
        raise AssertionError("policy registry prefix mutation fixture drift")
    return (
        ("missing", text.replace(expected, before, 1)),
        ("duplicated", text.replace(expected, expected + prefix, 1)),
        ("misplaced", text.replace(expected, prefix + before, 1)),
    )


def _test_owned_lossless_active_tex(text: str) -> str:
    """Strip true TeX comments without normalizing remaining active bytes."""
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
        raise AssertionError("active TeX caret encoding")
    return active


def _test_owned_lossless_active_tex_sha256(text: str) -> str:
    active = _test_owned_lossless_active_tex(text)
    return hashlib.sha256(active.encode("utf-8")).hexdigest().upper()


def _patch_active_tex_identities_for_downstream(
    changed_tex: dict[str, str],
):
    """Let legacy tests reach predicates downstream of the closed identity."""
    unexpected = set(changed_tex) - set(CANONICAL_ACTIVE_MANUSCRIPT_TEX_SHA256)
    if unexpected:
        raise AssertionError(f"non-manuscript-TeX identity patch: {unexpected}")
    identities = dict(CANONICAL_ACTIVE_MANUSCRIPT_TEX_SHA256)
    for relative, text in changed_tex.items():
        identities[relative] = _test_owned_lossless_active_tex_sha256(text)
    return mock.patch.object(
        _paper_verification,
        "_CANONICAL_ACTIVE_MANUSCRIPT_TEX_SHA256",
        identities,
    )


def _active(text: str) -> str:
    """Remove TeX/HTML comments and normalize ASCII whitespace for prose checks."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    return re.sub(r"[ \t\r\n\f\v]+", " ", _strip_tex_comments(text)).strip()


def _parse_analysis_protocol_items(text: str) -> tuple[tuple[str, str], ...]:
    """Return each labeled SAP item and its own active body."""
    active = _active(text)
    matches = tuple(re.finditer(r"\\item\[([^]]+)\]", active))
    return tuple(
        (
            match.group(1),
            active[match.end() : matches[index + 1].start()].strip()
            if index + 1 < len(matches)
            else active[match.end() :].strip(),
        )
        for index, match in enumerate(matches)
    )


def _assert_analysis_protocol_contract(text: str) -> None:
    """Independently enforce the frozen Task-5 SAP semantics."""
    active = _active(text)
    labels = tuple(re.findall(r"\\item\[([^]]+)\]", active))
    if labels != SAP_ITEM_LABELS:
        raise AssertionError("analysis-protocol item labels drift")
    for span in SAP_REQUIRED_ACTIVE_SPANS:
        if active.count(span) != 1:
            raise AssertionError(f"analysis-protocol span drift: {span}")
    observed_policies = tuple(
        token.replace(r"\_", "_")
        for token in re.findall(r"\\texttt\{([^{}]+)\}", active)
    )
    if observed_policies != POLICY_IDS:
        raise AssertionError("analysis-protocol policy roster drift")
    for marker in SAP_BLOCKED_MARKERS:
        if active.count(marker) != 1:
            raise AssertionError(f"analysis-protocol blocked marker drift: {marker}")
    if active.count("status=BLOCKED; values=UNPOPULATED") != 8:
        raise AssertionError("analysis-protocol result shells are not empty")
    parity_match = re.search(
        r"Both views are complete bijections over exactly 15 canonical parent "
        r"payload fields: ([^.]+)\.",
        active,
    )
    if (
        parity_match is None
        or tuple(parity_match.group(1).replace(r"\_", "_").split(", "))
        != SAP_PARITY_PARENT_FIELDS
    ):
        raise AssertionError("analysis-protocol parity parent drift")
    shared_match = re.search(
        r"The seven opportunity objects are byte-identical: ([^.]+)\.",
        active,
    )
    if (
        shared_match is None
        or tuple(shared_match.group(1).replace(r"\_", "_").split(", "))
        != SAP_SHARED_OPPORTUNITY_FIELDS
    ):
        raise AssertionError("analysis-protocol shared opportunity drift")
    for phrase in SAP_FORBIDDEN_POSITIVE_CLAIMS:
        if phrase in active:
            raise AssertionError(f"forbidden positive SAP claim: {phrase}")


def _independent_active_prose(text: str, relative: str) -> str:
    """Test-owned role-aware active prose normalization."""
    active = (
        re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
        if relative.endswith(".md")
        else _strip_tex_comments(text)
    )
    if relative.endswith(".tex"):
        active = active.replace(r"\%", " ")
    active = re.sub(r"[ \t\r\n\f\v]+", " ", active).strip()
    if relative.endswith(".tex"):
        active = re.sub(r"(\\[A-Za-z]+) +(?=\{)", r"\1", active)
        active = re.sub(r"([\{\[]) +", r"\1", active)
        active = re.sub(r" +([\}\]])", r"\1", active)
    return active


def _independent_active_prose_manifest(
    source_text: dict[str, str],
) -> tuple[tuple[tuple[str, int, str], ...], str]:
    identities = []
    lines = []
    for relative, _length, _digest in ACTIVE_PROSE_IDENTITIES:
        active_bytes = _independent_active_prose(
            source_text[relative],
            relative,
        ).encode("utf-8")
        digest = hashlib.sha256(active_bytes).hexdigest().upper()
        identity = (relative, len(active_bytes), digest)
        identities.append(identity)
        lines.append(f"{relative}\t{len(active_bytes)}\t{digest}\n")
    manifest = "".join(lines)
    return tuple(identities), hashlib.sha256(
        manifest.encode("utf-8")
    ).hexdigest().upper()


def _with_extra_group_after_first_argument(
    text: str,
    command: str,
    separator: str,
) -> str:
    match = re.search(r"\\" + re.escape(command) + r"\s*\{", text)
    if match is None:
        raise AssertionError(f"missing command fixture: {command}")
    cursor = match.end()
    argument_start = cursor
    depth = 1
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
        raise AssertionError(f"unbalanced command fixture: {command}")
    argument = text[argument_start : cursor - 1]
    suffix = COMMAND_SIGNATURE_ORACLE[command][2].get(argument)
    if suffix is not None and text.startswith(suffix, cursor):
        cursor += len(suffix)
    return text[:cursor] + separator + "{extra}" + text[cursor:]


def _rendered_boundary_text(text: str, relative: str) -> str:
    """Test-owned rendering of the reviewed TeX grouping/control subset."""
    active = (
        re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
        if relative.endswith(".md")
        else _strip_tex_comments(text)
    )
    rendered = []
    cursor = 0
    while cursor < len(active):
        character = active[cursor]
        if character == "\\" and cursor + 1 < len(active):
            next_character = active[cursor + 1]
            if next_character.isalpha():
                cursor += 2
                while cursor < len(active) and active[cursor].isalpha():
                    cursor += 1
                continue
            if next_character == "_":
                rendered.append("_")
            else:
                rendered.append(" ")
            cursor += 2
            continue
        if character not in "{}[]":
            rendered.append(character)
        cursor += 1
    return re.sub(r"[ \t\r\n\f\v]+", " ", "".join(rendered)).strip()


def _test_owned_provenance_assignment(rendered: str) -> bool:
    """Recognize attribution structure without consulting polarity or a subject list."""
    attribute = (
        r"(?:attribution|authentication|bibliograph\w*|certification|citation\w*|"
        r"doi|origin|provenance|reference|release|revision|roster|source\w*|"
        r"version\w*)"
    )
    possession = re.compile(
        rf"\b(?:carries|carry|has|have)\b(?:\s+\S+){{0,4}}\s+\b{attribute}\b",
        re.IGNORECASE,
    )
    passive = re.compile(
        rf"\b(?:is|are)\b(?:\s+\S+){{0,3}}\s+\b(?:assigned|attributed|"
        rf"authenticated|certified|cited|documented|registered|sourced|verified)\b"
        rf"(?:\s+\S+){{0,4}}\s+\b{attribute}\b|"
        rf"\b{attribute}\b(?:\s+\S+){{0,4}}\s+\b(?:is|are)\b(?:\s+\S+){{0,2}}"
        rf"\b(?:assigned|attributed|authenticated|certified|cited|complete|current|"
        rf"documented|official|registered|sourced|verified)\b",
        re.IGNORECASE,
    )
    return any(
        possession.search(clause) or passive.search(clause)
        for clause in re.split(r"(?<=[.!?])\s+", rendered)
    )


def _test_owned_unapproved_authorial_claim(rendered_closure: str) -> bool:
    """Apply the independent exact-span/authorial-claim model."""
    remainder = rendered_closure
    for span in (*CANONICAL_NOVELTY_CLAIM_SPANS, *CANONICAL_AUTHORIAL_NONCLAIM_SPANS):
        rendered_span = _rendered_boundary_text(span, ".tex")
        expected_count = 2 if span == METHOD_BOUNDARY else 1
        if remainder.count(rendered_span) != expected_count:
            raise AssertionError(f"canonical claim-bearing span drift: {span}")
        remainder = remainder.replace(rendered_span, "", expected_count)
    return any(
        AUTHORIAL_CLAIM_SUBJECT.match(sentence.strip())
        for sentence in re.split(r"(?<=[.!?])\s+", remainder)
        if sentence.strip()
    )


def _read(root: Path, relative: str) -> str:
    return (root / PAPER / relative).read_text(encoding="utf-8")


def _copy_permitted_fixture_source(source: Path, destination: Path) -> None:
    """Copy one explicit fixture input after a lexical allowlist check."""
    try:
        relative = source.relative_to(REPOSITORY / PAPER).as_posix()
    except ValueError as error:
        raise AssertionError("fixture source is outside the paper root") from error
    permitted = {*SOURCE_CLOSURE, "literature_primary_source_manifest.md"}
    if relative not in permitted:
        raise AssertionError("fixture source is outside the permitted closure")
    shutil.copyfile(source, destination)


def _new_source_closure_repository():
    """Construct a paper root from permitted sources and empty metadata names."""
    temporary = tempfile.TemporaryDirectory()
    root = Path(temporary.name) / "repository"
    paper_root = root / PAPER
    try:
        paper_root.mkdir(parents=True)
        for relative in SOURCE_CLOSURE:
            destination = paper_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            _copy_permitted_fixture_source(
                REPOSITORY / PAPER / relative,
                destination,
            )
        _copy_permitted_fixture_source(
            PRIMARY_MANIFEST,
            paper_root / "literature_primary_source_manifest.md",
        )
        for sibling in AUTHORITY_SIBLINGS:
            (paper_root / sibling).touch()
    except Exception:
        temporary.cleanup()
        raise
    return temporary, root


def _policy_registry_items(text: str) -> tuple[str, str, list[str], str]:
    """Split the one reviewed enumerate while preserving every source byte."""
    begin = r"\begin{enumerate}"
    end = r"\end{enumerate}"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise AssertionError("policy-registry enumerate fixture drift")
    body_start = text.index(begin) + len(begin)
    body_end = text.index(end, body_start)
    pieces = text[body_start:body_end].split(r"\item")
    expected_pre_item_space = "\n" + UNDERFULL_POLICY_REGISTRY_PREFIX
    if (
        pieces[0] != expected_pre_item_space
        or len(pieces) != len(POLICY_PROVENANCE_ROWS) + 1
    ):
        raise AssertionError("policy-registry item fixture drift")
    items = [r"\item" + piece for piece in pieces[1:]]
    return text[:body_start], pieces[0], items, text[body_end:]


def _rebuild_policy_registry(
    prefix: str,
    pre_item_space: str,
    items: list[str],
    suffix: str,
) -> str:
    return prefix + pre_item_space + "".join(items) + suffix


@contextlib.contextmanager
def _repatch_semantic_integrity(
    root: Path,
    relative: str,
    changed_text: str,
):
    """Bypass only raw/aggregate pins so semantic validators see an attack."""
    changed_bytes = changed_text.encode("utf-8")
    pinned = dict(_paper_verification._PINNED_SOURCE_SHA256)
    if relative in pinned:
        pinned[relative] = hashlib.sha256(changed_bytes).hexdigest().upper()

    canonical_active = dict(_paper_verification._CANONICAL_ACTIVE_MANUSCRIPT_TEX_SHA256)
    if relative.endswith(".tex"):
        canonical_active[relative] = _test_owned_lossless_active_tex_sha256(
            changed_text
        )

    source_text = {
        source_relative: _read(root, source_relative)
        for source_relative in MANUSCRIPT_SOURCE_CLOSURE
    }
    source_text[relative] = changed_text
    _identities, active_manifest = _independent_active_prose_manifest(source_text)

    with contextlib.ExitStack() as stack:
        stack.enter_context(
            mock.patch.object(
                _paper_verification,
                "_PINNED_SOURCE_SHA256",
                pinned,
            )
        )
        stack.enter_context(
            mock.patch.object(
                _paper_verification,
                "_CANONICAL_ACTIVE_MANUSCRIPT_TEX_SHA256",
                canonical_active,
            )
        )
        stack.enter_context(
            mock.patch.object(
                _paper_verification,
                "_ACTIVE_PROSE_MANIFEST_SHA256",
                active_manifest.lower(),
            )
        )
        yield


def _parse_bibtex(
    text: str,
) -> tuple[tuple[str, str, tuple[tuple[str, str], ...]], ...]:
    """Small test-owned balanced-brace BibTeX parser for the reviewed subset."""
    text = _strip_tex_comments(text)
    found = []
    cursor = 0
    while True:
        match = re.search(r"@(\w+)\{([^,]+),", text[cursor:])
        if match is None:
            break
        entry_type, key = match.group(1), match.group(2)
        start = cursor + match.end()
        depth, end = 1, start
        while end < len(text) and depth:
            if text[end] == "{":
                depth += 1
            elif text[end] == "}":
                depth -= 1
            end += 1
        if depth:
            raise AssertionError("unbalanced bibliography entry")
        body = text[start : end - 1]
        fields = []
        position = 0
        while position < len(body):
            field = re.match(r"\s*([a-z]+)\s*=\s*\{", body[position:])
            if field is None:
                if body[position:].strip():
                    raise AssertionError("invalid bibliography field")
                break
            name = field.group(1)
            value_start = position + field.end()
            depth, value_end = 1, value_start
            while value_end < len(body) and depth:
                if body[value_end] == "{":
                    depth += 1
                elif body[value_end] == "}":
                    depth -= 1
                value_end += 1
            if depth:
                raise AssertionError("unbalanced bibliography field")
            fields.append((name, body[value_start : value_end - 1]))
            position = value_end
            comma = re.match(r"\s*,", body[position:])
            if comma:
                position += comma.end()
        found.append((key, entry_type, tuple(fields)))
        cursor = end
    return tuple(found)


def _project_task3_review_status(
    entry_type: str,
    fields: tuple[tuple[str, str], ...],
) -> str:
    """Project Task-1 review status from parsed, live BibTeX bytes."""
    field_names = tuple(name for name, _value in fields)
    if len(field_names) != len(set(field_names)):
        raise AssertionError("duplicate Task-3 bibliography field")
    field_map = dict(fields)
    howpublished = field_map.get("howpublished")
    journal = field_map.get("journal")
    booktitle = field_map.get("booktitle")

    if howpublished == "arXiv" or journal == "arXiv" or booktitle == "arXiv":
        if (
            entry_type != "misc"
            or howpublished != "arXiv"
            or not re.fullmatch(r"[0-9]{4}\.[0-9]{5}", field_map.get("eprint", ""))
            or not re.fullmatch(r"arXiv v[1-9][0-9]*", field_map.get("note", ""))
        ):
            raise AssertionError("invalid public-preprint status carrier")
        return "public_preprint"

    if booktitle is not None and "workshop" in booktitle.casefold():
        if (
            entry_type != "inproceedings"
            or "workshop" not in field_map.get("note", "").casefold()
        ):
            raise AssertionError("invalid peer-reviewed-workshop status carrier")
        return "peer_reviewed_workshop"

    if entry_type == "article" and journal is not None:
        return "peer_reviewed"
    if entry_type == "inproceedings" and booktitle is not None:
        return "peer_reviewed"
    raise AssertionError("unrecognized Task-3 review-status carrier")


def _assert_task3_bibliography_authority(
    parsed: tuple[tuple[str, str, tuple[tuple[str, str], ...]], ...],
) -> None:
    """Validate the 21-row Task-3 census without production-derived fixtures."""
    parsed_by_key = {key: (entry_type, fields) for key, entry_type, fields in parsed}
    for (
        key,
        expected_type,
        expected_status,
        expected_fields,
    ) in TASK3_BIBLIOGRAPHY_AUTHORITY:
        if key not in parsed_by_key:
            raise AssertionError(f"missing Task-3 bibliography row: {key}")
        actual_type, actual_fields = parsed_by_key[key]
        actual_status = _project_task3_review_status(actual_type, actual_fields)
        if actual_status != expected_status:
            raise AssertionError(
                f"Task-3 review-status mismatch for {key}: "
                f"{actual_status} != {expected_status}"
            )
        if actual_type != expected_type or actual_fields != expected_fields:
            raise AssertionError(f"Task-3 bibliography semantics drift: {key}")


def _parse_manifest(text: str) -> tuple[tuple[str, ...], tuple[tuple[str, ...], ...]]:
    lines = text.splitlines()
    expected_prefix = (
        "# Task 11 Primary-Source Manifest Transcription",
        "",
        "schema_version: ace.iclr2027.primary_source_manifest_transcription.v1",
        f"reviewed_spec_sha256: {SPEC_SHA256}",
        "network_reads: 0",
        "authority: non_authoritative_transcription",
        "exhaustive: false",
        "",
        "| key | title | authors | year | url | doi | disposition |",
        "|---|---|---|---:|---|---|---|",
    )
    if tuple(lines[:10]) != expected_prefix or len(lines) != 20:
        raise AssertionError("primary manifest grammar or metadata drift")
    if "<!--" in text or any(
        not line.startswith("| ") or not line.endswith(" |") for line in lines[10:]
    ):
        raise AssertionError("primary manifest table framing/comment drift")
    rows = tuple(
        tuple(cell.strip() for cell in line.split("|")[1:-1]) for line in lines[10:]
    )
    if any(len(row) != 7 for row in rows):
        raise AssertionError("primary manifest row grammar drift")
    return expected_prefix, rows


def _expected_bibliography_suffix() -> str:
    entries = []
    for key, entry_type, fields in BIBLIOGRAPHY_ENTRIES:
        lines = [f"@{entry_type}{{{key},"]
        for index, (field, value) in enumerate(fields):
            lines.append(
                f"  {field} = {{{value}}}{',' if index + 1 < len(fields) else ''}"
            )
        lines.append("}")
        entries.append("\n".join(lines))
    return "\n" + "\n\n".join(entries) + "\n"


def _expected_bibliography_entry(
    key: str, entry_type: str, fields: tuple[tuple[str, str], ...]
) -> str:
    lines = [f"@{entry_type}{{{key},"]
    for index, (field, value) in enumerate(fields):
        lines.append(f"  {field} = {{{value}}}{',' if index + 1 < len(fields) else ''}")
    return "\n".join((*lines, "}"))


def _citation_keys(text: str) -> tuple[str, ...]:
    keys = []
    for match in re.finditer(
        r"\\(?:cite|citet|citep)\{([^{}]+)\}", _strip_tex_comments(text)
    ):
        keys.extend(key.strip() for key in match.group(1).split(","))
    return tuple(keys)


def _citation_scan_call_label(
    text: str,
    manuscript_text_digest_to_relative: dict[str, str],
) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest().upper()
    return manuscript_text_digest_to_relative.get(digest, f"UNKNOWN:{digest}")


def _policy_registry_scanner_fragment_labels(text: str) -> dict[str, str]:
    """Own only the 22 exact authenticated row fragments scanned by production."""
    active = _test_owned_lossless_active_tex(text)
    active_digest = hashlib.sha256(active.encode("utf-8")).hexdigest().upper()
    if (
        active_digest
        != CANONICAL_ACTIVE_MANUSCRIPT_TEX_SHA256[POLICY_PROVENANCE_RELATIVE]
    ):
        raise AssertionError("policy-registry active identity drift")
    if _parse_policy_registry_for_test(active) != POLICY_PROVENANCE_ROWS:
        raise AssertionError("policy-registry semantic fixture drift")
    _prefix, _pre_item_space, items, _suffix = _policy_registry_items(active)
    fragments = tuple(item[len(r"\item") :].strip() for item in items)
    labels = {
        hashlib.sha256(fragment.encode("utf-8")).hexdigest().upper(): (
            f"{POLICY_PROVENANCE_RELATIVE}#row:{index:02d}"
        )
        for index, fragment in enumerate(fragments, start=1)
    }
    if len(fragments) != 22 or len(labels) != 22:
        raise AssertionError("policy-registry scanner-fragment closure drift")
    return labels


def _assert_exact_citation_scan_calls(observed: tuple[str, ...]) -> None:
    expected = Counter(
        {
            relative: (
                2
                if relative
                in {
                    "latex/main.tex",
                    POLICY_PROVENANCE_RELATIVE,
                    "latex/sections/02_related_work.tex",
                }
                else 1
            )
            for relative in MANUSCRIPT_SOURCE_CLOSURE
            if relative.endswith(".tex")
        }
    )
    expected.update(
        {
            f"{POLICY_PROVENANCE_RELATIVE}#row:{index:02d}": 1
            for index in range(1, len(POLICY_PROVENANCE_ROWS) + 1)
        }
    )
    if any(call.startswith("UNKNOWN:") for call in observed):
        raise AssertionError("unknown citation/science scan call")
    if len(observed) != 41 or Counter(observed) != expected:
        raise AssertionError("citation/science scan call Counter drift")


def _swap_once(text: str, left: str, right: str) -> str:
    marker = "__TASK11_LITERAL_SWAP_MARKER__"
    if left not in text or right not in text:
        raise AssertionError("mutation literal missing")
    return (
        text.replace(left, marker, 1).replace(right, left, 1).replace(marker, right, 1)
    )


def _swap_claim_columns(
    text: str,
    left: tuple[str, str, str],
    right: tuple[str, str, str],
    roles_only: bool = False,
) -> str:
    left_literal = f"\\claim{{{left[0]}}} & {left[1]} & {left[2]}"
    right_literal = f"\\claim{{{right[0]}}} & {right[1]} & {right[2]}"
    if left_literal not in text or right_literal not in text:
        raise AssertionError("claim row mutation literal missing")
    left_changed = (
        f"\\claim{{{left[0]}}} & {left[1] if roles_only else right[1]} & {right[2]}"
    )
    right_changed = (
        f"\\claim{{{right[0]}}} & {right[1] if roles_only else left[1]} & {left[2]}"
    )
    return text.replace(left_literal, left_changed, 1).replace(
        right_literal, right_changed, 1
    )


def _parse_kill_survivor_semantics(
    claims: str,
) -> tuple[tuple[str, str, str, str], ...]:
    """Interpret the complete active kill-chain paragraph without expected rows."""
    marker = "The symmetric kill chain is load-bearing."
    if claims.count(marker) != 1:
        return ()
    evidence = claims.partition(marker)[2].strip()
    parsed_evidence = re.fullmatch(
        r"E2 failure in (?P<e2_scope>.+?) kills the (?P<e2_removal>.+?)\. "
        r"After positive E2, E3 failure in (?P<e3_scope>.+?) kills the (?P<e3_removal>.+?)\. "
        r"Only the exact narrower (?P<survivor_scope>\S+) (?P<survivor_result>.+?) "
        r"may remain, (?P<rescue_boundary>.+?)\.",
        evidence,
    )
    if parsed_evidence is None:
        return ()

    scope_ontologies = {
        "either ontology": ("Architecture", "JCI"),
        "Architecture ontology only": ("Architecture",),
        "JCI ontology only": ("JCI",),
    }
    endpoint_rules = {
        "E2": (
            scope_ontologies.get(parsed_evidence["e2_scope"], ()),
            "E2 nonpositive, nonestimable, unsupported, or noncompliant",
            parsed_evidence["e2_removal"].replace(
                "ICLR-main thesis", "ICLR-main OACS thesis"
            ),
        ),
        "E3": (
            scope_ontologies.get(parsed_evidence["e3_scope"], ()),
            "E3 null or parity-invalid after positive E2",
            parsed_evidence["e3_removal"],
        ),
    }
    exact_survivor_evidence = (
        parsed_evidence["survivor_scope"] == "other-ontology"
        and parsed_evidence["survivor_result"]
        == "descriptive or randomized executed-bundle result"
        and parsed_evidence["rescue_boundary"]
        == "never as a rescued flagship, replication, cross-domain, mechanism, or OACS-main claim"
    )
    other_ontology = {"Architecture": "JCI", "JCI": "Architecture"}
    parsed_rows = []
    for ontology in ("Architecture", "JCI"):
        for endpoint in ("E2", "E3"):
            ontologies, trigger, removal = endpoint_rules[endpoint]
            if ontology not in ontologies:
                continue
            if exact_survivor_evidence and endpoint == "E2":
                survivor = (
                    f"{other_ontology[ontology]} descriptive or randomized "
                    "executed-complete-bundle effect only; never flagship, replication, "
                    "cross-domain, mechanism-main, or OACS-main"
                )
            elif exact_survivor_evidence:
                survivor = f"same narrower {other_ontology[ontology]}-only boundary"
            else:
                survivor = (
                    f"{parsed_evidence['survivor_scope']} {parsed_evidence['survivor_result']}; "
                    f"{parsed_evidence['rescue_boundary']}"
                )
            parsed_rows.append((ontology, trigger, removal, survivor))
    return tuple(parsed_rows)


def _replace_manifest_cell(text: str, key: str, column: int, replacement: str) -> str:
    lines = text.splitlines()
    matches = [
        index
        for index, line in enumerate(lines)
        if line.startswith("| ")
        and tuple(cell.strip() for cell in line.split("|")[1:-1])[0] == key
    ]
    if len(matches) != 1:
        raise AssertionError("exact manifest row not found")
    line_index = matches[0]
    cells = [cell.strip() for cell in lines[line_index].split("|")[1:-1]]
    original_key, original_value = cells[0], cells[column]
    if original_key != key or original_value == replacement:
        raise AssertionError("wrong manifest mutation target")
    cells[column] = replacement
    if cells[0] != key or cells[column] == original_value:
        raise AssertionError("manifest mutation did not preserve key/change cell")
    lines[line_index] = "| " + " | ".join(cells) + " |"
    return "\n".join(lines) + "\n"


def _replace_bib_field(text: str, key: str, field: str, replacement: str) -> str:
    header = re.search(r"@(\w+)\{" + re.escape(key) + r",", text)
    if header is None:
        raise AssertionError("exact bibliography entry not found")
    depth, entry_end = 1, header.end()
    while entry_end < len(text) and depth:
        if text[entry_end] == "{":
            depth += 1
        elif text[entry_end] == "}":
            depth -= 1
        entry_end += 1
    entry = text[header.start() : entry_end]
    field_match = re.search(r"(?m)^  " + re.escape(field) + r" = \{", entry)
    if field_match is None:
        raise AssertionError("exact bibliography field not found")
    value_start = field_match.end()
    depth, value_end = 1, value_start
    while value_end < len(entry) and depth:
        if entry[value_end] == "{":
            depth += 1
        elif entry[value_end] == "}":
            depth -= 1
        value_end += 1
    original_value = entry[value_start : value_end - 1]
    if original_value == replacement:
        raise AssertionError("bibliography mutation did not change field")
    changed_entry = entry[:value_start] + replacement + entry[value_end - 1 :]
    if (
        not changed_entry.startswith(header.group(0))
        or key not in changed_entry[: header.end() - header.start()]
    ):
        raise AssertionError("bibliography mutation changed key")
    return text[: header.start()] + changed_entry + text[entry_end:]


def _mutate_task3_review_status_carrier(
    text: str,
    key: str,
    review_status: str,
    fields: tuple[tuple[str, str], ...],
) -> str:
    """Change the live venue carrier to a different Task-1 status class."""
    field_map = dict(fields)
    if review_status == "public_preprint":
        if field_map.get("howpublished") != "arXiv":
            raise AssertionError("public-preprint carrier fixture drift")
        return _replace_bib_field(
            text,
            key,
            "howpublished",
            "International Conference on Learning Representations",
        )
    venue_field = "journal" if "journal" in field_map else "booktitle"
    if venue_field not in field_map:
        raise AssertionError("reviewed venue carrier fixture drift")
    replacement = (
        "International Conference on Learning Representations"
        if review_status == "peer_reviewed_workshop"
        else "arXiv"
    )
    return _replace_bib_field(text, key, venue_field, replacement)


class AnalysisProtocolAppendixContractTests(unittest.TestCase):
    maxDiff = None

    def _source(self) -> str:
        path = REPOSITORY / PAPER / SAP_RELATIVE
        self.assertTrue(path.is_file(), "analysis-protocol appendix is missing")
        return path.read_text(encoding="utf-8")

    def test_sap_is_a_locked_input_between_theory_and_claims(self):
        self.assertEqual(len(SAP_EXPECTED_SOURCE_CLOSURE), 22)
        self.assertEqual(
            SAP_EXPECTED_SOURCE_CLOSURE,
            tuple(
                sorted(
                    SAP_EXPECTED_SOURCE_CLOSURE, key=lambda path: path.encode("utf-8")
                )
            ),
        )
        source = self._source()
        self.assertTrue(source.endswith("\n"))
        main = _read(REPOSITORY, "latex/main.tex")
        observed_inputs = _paper_verification._extract_literal_arguments(
            main, ("input",)
        )["input"]
        self.assertEqual(observed_inputs, SAP_EXPECTED_INPUTS)
        self.assertIn(SAP_RELATIVE, _paper_verification._PINNED_SOURCE_SHA256)
        self.assertIn(SAP_RELATIVE, _paper_verification._ACTIVE_PROSE_PATHS)
        self.assertNotIn(SAP_RELATIVE, _paper_verification._EDITABLE_ROLES)

    def test_sap_freezes_the_complete_task5_scientific_contract(self):
        _assert_analysis_protocol_contract(self._source())

    def test_sap_e3_displays_use_semantic_preserving_aligned_rows(self):
        _assert_sap_e3_aligned_layout_preserves_science(self._source())

    def test_science_review_support_stop_falsification_and_case_reporting_are_exact(
        self,
    ):
        active = _active(self._source())
        for span in SAP_REVIEW_FIX_SPANS:
            self.assertEqual(active.count(span), 1, span)
        for label, span, old, new in SAP_REVIEW_FIX_MUTATIONS:
            with self.subTest(label=label):
                self.assertEqual(span.count(old), 1)
                changed_span = span.replace(old, new, 1)
                changed = active.replace(span, changed_span, 1)
                self.assertNotEqual(changed, active)
                with self.assertRaises(AssertionError):
                    _assert_analysis_protocol_contract(changed)

    def test_e1_failure_boundary_is_unique_inside_multiplicity_kill_chain(self):
        source = self._source()
        active = _active(source)
        items = _parse_analysis_protocol_items(source)
        self.assertEqual(tuple(label for label, _body in items), SAP_ITEM_LABELS)
        kill_chain = dict(items)["Multiplicity and kill chain."]
        self.assertEqual(kill_chain.count(SAP_REVIEW_E1_FAILURE_SPAN), 1)
        self.assertEqual(active.count(SAP_REVIEW_E1_FAILURE_SPAN), 1)
        outside = " ".join(
            body for label, body in items if label != "Multiplicity and kill chain."
        )
        self.assertNotIn(SAP_REVIEW_E1_FAILURE_SPAN, outside)

    def test_each_sap_boundary_is_independently_mutation_sensitive(self):
        active = _active(self._source())
        for span in SAP_REQUIRED_ACTIVE_SPANS:
            with self.subTest(span=span[:100]):
                self.assertEqual(active.count(span), 1)
                with self.assertRaises(AssertionError):
                    _assert_analysis_protocol_contract(active.replace(span, "", 1))
        for marker in SAP_BLOCKED_MARKERS:
            with self.subTest(marker=marker):
                with self.assertRaises(AssertionError):
                    _assert_analysis_protocol_contract(active.replace(marker, "", 1))
        policy_literals = tuple(
            r"\texttt{" + policy.replace("_", r"\_") + "}" for policy in POLICY_IDS
        )
        policy_mutations = (
            ("missing", active.replace(policy_literals[0] + ", ", "", 1)),
            (
                "duplicate",
                active.replace(
                    policy_literals[0],
                    policy_literals[0] + ", " + policy_literals[0],
                    1,
                ),
            ),
            ("reordered", _swap_once(active, policy_literals[0], policy_literals[1])),
            (
                "extra",
                active.replace(
                    policy_literals[-1],
                    policy_literals[-1] + r", \texttt{extra_policy}",
                    1,
                ),
            ),
        )
        for label, changed in policy_mutations:
            with self.subTest(policy_roster=label):
                self.assertNotEqual(changed, active)
                with self.assertRaises(AssertionError):
                    _assert_analysis_protocol_contract(changed)
        for phrase in SAP_FORBIDDEN_POSITIVE_CLAIMS:
            with self.subTest(forbidden=phrase):
                with self.assertRaises(AssertionError):
                    _assert_analysis_protocol_contract(active + " " + phrase)

    def test_production_sap_policy_exception_is_exact_and_nonexportable(self):
        source_text = {
            relative: _read(REPOSITORY, relative)
            for relative in MANUSCRIPT_SOURCE_CLOSURE
        }
        source_bytes = {
            relative: (REPOSITORY / PAPER / relative).read_bytes()
            for relative in MANUSCRIPT_SOURCE_CLOSURE
        }
        policy_literals = tuple(
            r"\texttt{" + policy.replace("_", r"\_") + "}" for policy in POLICY_IDS
        )
        mutations = (
            (
                "missing",
                SAP_RELATIVE,
                lambda text: text.replace(policy_literals[0] + ", ", "", 1),
            ),
            (
                "duplicate",
                SAP_RELATIVE,
                lambda text: text.replace(
                    policy_literals[0],
                    policy_literals[0] + ", " + policy_literals[0],
                    1,
                ),
            ),
            (
                "reordered",
                SAP_RELATIVE,
                lambda text: _swap_once(text, policy_literals[0], policy_literals[1]),
            ),
            (
                "extra",
                SAP_RELATIVE,
                lambda text: text.replace(
                    policy_literals[-1],
                    policy_literals[-1] + r", \texttt{extra_policy}",
                    1,
                ),
            ),
            ("elsewhere", "latex/README.md", lambda text: text + "\nagentprune\n"),
        )
        for label, relative, transform in mutations:
            with self.subTest(label=label):
                changed = dict(source_text)
                changed[relative] = transform(changed[relative])
                self.assertNotEqual(changed[relative], source_text[relative])
                _identities, active_digest = _independent_active_prose_manifest(changed)
                changed_tex = (
                    {relative: changed[relative]} if relative.endswith(".tex") else {}
                )
                with (
                    mock.patch.object(
                        _paper_verification,
                        "_ACTIVE_PROSE_MANIFEST_SHA256",
                        active_digest.lower(),
                    ),
                    _patch_active_tex_identities_for_downstream(changed_tex),
                ):
                    with self.assertRaises(PaperLatexVerificationError) as caught:
                        _paper_verification._validate_tex_bibliography_and_science(
                            changed,
                            source_bytes,
                        )
                self.assertEqual(
                    caught.exception.reason_code,
                    "scientific_boundary_invalid",
                )

    def test_sap_closure_receipt_and_observer_require_all_sources(self):
        self._source()
        reads = []
        receipt = _paper_verification._verify_static_paper_latex_at(
            REPOSITORY,
            read_observer=reads.append,
        )
        observed = tuple(
            sorted(
                path.relative_to(REPOSITORY / PAPER).as_posix()
                for path in reads
                if path.name != "literature_primary_source_manifest.md"
            )
        )
        self.assertEqual(observed, SAP_EXPECTED_SOURCE_CLOSURE)
        self.assertEqual(receipt.source_file_count, 22)
        self.assertEqual(
            receipt.citation_authority_status,
            "blocked_pending_authenticated_roster",
        )
        self.assertIs(receipt.pdf_compile_verified, False)
        self.assertEqual(receipt.empirical_status, "no_go_needs_context")


class PolicyProvenanceRegistryContractTests(unittest.TestCase):
    def _assert_copied_root_semantic_rejection(
        self,
        root: Path,
        original: str,
        changed: str,
        expected_codes: tuple[str, ...],
    ) -> None:
        self.assertNotEqual(changed, original)
        path = root / PAPER / POLICY_PROVENANCE_RELATIVE
        path.write_text(changed, encoding="utf-8", newline="\n")
        try:
            with _repatch_semantic_integrity(
                root,
                POLICY_PROVENANCE_RELATIVE,
                changed,
            ):
                with self.assertRaises(PaperLatexVerificationError) as caught:
                    _paper_verification._verify_static_paper_latex_at(root)
            self.assertIn(caught.exception.reason_code, expected_codes)
            self.assertNotIn(
                caught.exception.reason_code,
                {"source_bytes_invalid", "source_identity_invalid"},
            )
        finally:
            path.write_text(original, encoding="utf-8", newline="\n")

    def test_registry_is_exact_and_source_authentication_is_split(self):
        appendix = _read(REPOSITORY, "latex/appendices/appendix_policy_provenance.tex")
        self.assertEqual(
            _parse_policy_registry_for_test(appendix), POLICY_PROVENANCE_ROWS
        )
        self.assertEqual(appendix.count("bibliographic\\_provenance\\_status="), 1)
        self.assertEqual(appendix.count("implementation\\_authentication\\_status="), 1)

    def test_related_work_uses_direct_evaluation_and_scopes_dml(self):
        related = _active(_read(REPOSITORY, "latex/sections/02_related_work.tex"))
        self.assertEqual(related.lower().count("off-policy"), 2)
        self.assertIn(
            "the present paper performs neither direct nor logged off-policy evaluation",
            related.lower(),
        )
        self.assertIn(
            "any future off-policy comparison is protocol-only",
            related.lower(),
        )
        self.assertIn("paired direct policy evaluation", related.lower())
        self.assertIn("score-level orthogonality", related.lower())
        self.assertIn("our first-order action-choice proposition", related.lower())

    def test_public_keys_resolve_and_protocol_defined_rows_have_no_citation(self):
        bibliography = dict(
            (key, (kind, fields))
            for key, kind, fields in _parse_bibtex(
                _read(REPOSITORY, "latex/references.bib")
            )
        )
        for policy, kind, reference, role, status in POLICY_PROVENANCE_ROWS:
            self.assertEqual(status, "blocked_pending_authenticated_roster")
            self.assertTrue(role)
            if kind == "protocol_defined_comparator":
                self.assertIsNone(reference, policy)
            else:
                self.assertIn(reference, bibliography, policy)

    def test_every_row_rejects_order_and_class_mutations_after_pin_bypass(self):
        temporary, root = _new_source_closure_repository()
        try:
            baseline = _paper_verification._verify_static_paper_latex_at(root)
            self.assertEqual(baseline.policy_count, 22)
            original = _read(root, POLICY_PROVENANCE_RELATIVE)
            prefix, spacing, original_items, suffix = _policy_registry_items(original)
            for index, row in enumerate(POLICY_PROVENANCE_ROWS):
                policy, provenance_class, _reference, _role, _status = row
                order_attacks = (
                    (
                        "delete",
                        original_items[:index] + original_items[index + 1 :],
                        ("source_grammar_invalid",),
                    ),
                    (
                        "duplicate",
                        original_items[: index + 1]
                        + [original_items[index]]
                        + original_items[index + 1 :],
                        ("source_grammar_invalid",),
                    ),
                )
                swapped = list(original_items)
                next_index = (index + 1) % len(swapped)
                swapped[index], swapped[next_index] = (
                    swapped[next_index],
                    swapped[index],
                )
                order_attacks += (
                    ("adjacent swap", swapped, ("scientific_boundary_invalid",)),
                )
                for attack, items, expected_codes in order_attacks:
                    with self.subTest(policy=policy, attack=attack):
                        self._assert_copied_root_semantic_rejection(
                            root,
                            original,
                            _rebuild_policy_registry(prefix, spacing, items, suffix),
                            expected_codes,
                        )

                source_class = provenance_class.replace("_", r"\_")
                for replacement in PROVENANCE_CLASSES:
                    if replacement == provenance_class:
                        continue
                    escaped_replacement = replacement.replace("_", r"\_")
                    changed_item = original_items[index].replace(
                        rf"\texttt{{{source_class}}}",
                        rf"\texttt{{{escaped_replacement}}}",
                        1,
                    )
                    with self.subTest(
                        policy=policy,
                        attack="class substitution",
                        replacement=replacement,
                    ):
                        changed_items = list(original_items)
                        changed_items[index] = changed_item
                        self._assert_copied_root_semantic_rejection(
                            root,
                            original,
                            _rebuild_policy_registry(
                                prefix, spacing, changed_items, suffix
                            ),
                            ("scientific_boundary_invalid",),
                        )
        finally:
            temporary.cleanup()

    def test_every_published_row_rejects_reference_and_status_mutations(self):
        temporary, root = _new_source_closure_repository()
        try:
            _paper_verification._verify_static_paper_latex_at(root)
            original = _read(root, POLICY_PROVENANCE_RELATIVE)
            prefix, spacing, original_items, suffix = _policy_registry_items(original)
            published = tuple(
                (index, row)
                for index, row in enumerate(POLICY_PROVENANCE_ROWS)
                if row[1] != "protocol_defined_comparator"
            )
            public_keys = tuple(row[2] for _index, row in published)
            for published_index, (row_index, row) in enumerate(published):
                policy, _kind, reference, _role, status = row
                self.assertIsNotNone(reference, policy)
                reference_attacks = (
                    (
                        "missing citation",
                        original_items[row_index].replace(
                            rf"\citep{{{reference}}}",
                            r"\texttt{none}",
                            1,
                        ),
                    ),
                    (
                        "next public key",
                        original_items[row_index].replace(
                            rf"\citep{{{reference}}}",
                            rf"\citep{{{public_keys[(published_index + 1) % len(public_keys)]}}}",
                            1,
                        ),
                    ),
                )
                for attack, changed_item in reference_attacks:
                    with self.subTest(policy=policy, attack=attack):
                        changed_items = list(original_items)
                        changed_items[row_index] = changed_item
                        self._assert_copied_root_semantic_rejection(
                            root,
                            original,
                            _rebuild_policy_registry(
                                prefix, spacing, changed_items, suffix
                            ),
                            ("scientific_boundary_invalid",),
                        )
                source_status = status.replace("_", r"\_")
                for replacement in ("verified", "authenticated", "ready", "v1"):
                    with self.subTest(
                        policy=policy,
                        attack="status promotion",
                        replacement=replacement,
                    ):
                        changed_items = list(original_items)
                        changed_items[row_index] = original_items[row_index].replace(
                            rf"\texttt{{{source_status}}}.",
                            rf"\texttt{{{replacement}}}.",
                            1,
                        )
                        self._assert_copied_root_semantic_rejection(
                            root,
                            original,
                            _rebuild_policy_registry(
                                prefix, spacing, changed_items, suffix
                            ),
                            ("scientific_boundary_invalid",),
                        )
        finally:
            temporary.cleanup()

    def test_every_protocol_row_rejects_each_required_clause_removal(self):
        temporary, root = _new_source_closure_repository()
        try:
            _paper_verification._verify_static_paper_latex_at(root)
            original = _read(root, POLICY_PROVENANCE_RELATIVE)
            prefix, spacing, original_items, suffix = _policy_registry_items(original)
            for row_index, row in enumerate(POLICY_PROVENANCE_ROWS):
                policy, provenance_class, _reference, _role, _status = row
                if provenance_class != "protocol_defined_comparator":
                    continue
                for clause, source_label in PROTOCOL_REQUIRED_CLAUSES:
                    label = source_label.replace("_", r"\_")
                    changed_item, substitutions = re.subn(
                        re.escape(label) + r"=.*?;",
                        "",
                        original_items[row_index],
                        count=1,
                        flags=re.DOTALL,
                    )
                    self.assertEqual(substitutions, 1, (policy, clause))
                    with self.subTest(
                        policy=policy,
                        attack="remove protocol clause",
                        clause=clause,
                    ):
                        changed_items = list(original_items)
                        changed_items[row_index] = changed_item
                        self._assert_copied_root_semantic_rejection(
                            root,
                            original,
                            _rebuild_policy_registry(
                                prefix, spacing, changed_items, suffix
                            ),
                            ("scientific_boundary_invalid",),
                        )
        finally:
            temporary.cleanup()


class ManuscriptScientificBoundaryTests(unittest.TestCase):
    maxDiff = None

    def test_exact_title_claim_mapping_and_evaluation_validity_narrative(self):
        self._root_check(REPOSITORY)

    def test_title_has_exact_semantics_and_one_intended_raw_line_break(self):
        main = _strip_tex_comments(_read(REPOSITORY, "latex/main.tex"))
        self.assertEqual(
            main.count(rf"\title{{{EXPECTED_RAW_MANUSCRIPT_TITLE}}}"),
            1,
        )
        self.assertEqual(
            _test_owned_normalized_manuscript_title(main),
            EXPECTED_MANUSCRIPT_TITLE,
        )
        self.assertEqual(
            _paper_verification._extract_normalized_manuscript_title(main),
            EXPECTED_MANUSCRIPT_TITLE,
        )
        self.assertEqual(
            tuple(re.findall(r"\\hyphenation\s*\{[^{}]*\}", main)),
            (),
        )

    def test_della_penna_family_encoding_preserves_official_author_identity(self):
        bibliography = _parse_bibtex(_read(REPOSITORY, "latex/references.bib"))
        entry_type, fields = {
            key: (kind, dict(entry_fields)) for key, kind, entry_fields in bibliography
        }["dellapenna2026brace"]
        self.assertEqual(entry_type, "misc")
        self.assertEqual(fields["author"], "{Della Penna}, Nicolás")
        manifest = (
            REPOSITORY / PAPER / "literature_primary_source_manifest.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "| dellapenna2026brace | What Do We Care About in Bandits with "
            "Noncompliance? BRACE: Bandits with Recommendations, Abstention, and "
            "Certified Effects | Nicolás Della Penna | 2026 |",
            manifest,
        )

    def _root_check(
        self,
        root: Path,
        *,
        bypass_bibliography_integrity: bool = False,
    ) -> None:
        main = _active(_read(root, "latex/main.tex"))
        self.assertEqual(
            main.count(rf"\title{{{EXPECTED_RAW_MANUSCRIPT_TITLE}}}"),
            1,
        )
        manifest = root / PAPER / "literature_primary_source_manifest.md"
        self.assertTrue(manifest.exists(), "primary-source manifest missing")
        _, manifest_rows = _parse_manifest(manifest.read_text(encoding="utf-8"))
        expected_rows = tuple(
            (key, title, "; ".join(authors), year, url, doi or "--", disposition)
            for key, title, authors, year, url, doi, disposition in sorted(
                PRIMARY_SOURCES
            )
        )
        self.assertEqual(manifest_rows, expected_rows)
        bibliography = _read(root, "latex/references.bib")
        if not bypass_bibliography_integrity:
            self.assertEqual(
                hashlib.sha256(bibliography.encode("utf-8")[:1202]).hexdigest(),
                PREFIX_BIB_SHA256,
            )
            self.assertEqual(
                hashlib.sha256(bibliography.encode("utf-8")).hexdigest().upper(),
                "2A172632CAB4467CB7FEDA55DEBFDC8EB2B6B646333A48A14B6A3E22C8CD8B00",
            )
        parsed_bibliography = _parse_bibtex(bibliography)
        self.assertEqual(len(parsed_bibliography), 29)
        self.assertEqual(
            tuple(key for key, _kind, _fields in parsed_bibliography),
            ALL_BIBLIOGRAPHY_KEYS,
        )
        _assert_task3_bibliography_authority(parsed_bibliography)
        cited_keys = {
            key
            for relative in MANUSCRIPT_SOURCE_CLOSURE
            if relative.endswith(".tex")
            for key in _citation_keys(_read(root, relative))
        }
        self.assertEqual(set(ALL_BIBLIOGRAPHY_KEYS) - cited_keys, set())
        related = _active(_read(root, "latex/sections/02_related_work.tex"))
        actual_primary_citations = tuple(
            key
            for key in _citation_keys(_read(root, "latex/sections/02_related_work.tex"))
            if key in PRIMARY_SOURCE_KEYS
        )
        self.assertEqual(actual_primary_citations, RELATED_PRIMARY_CITATIONS)
        for sentence in DISPOSITIONS:
            self.assertEqual(related.count(sentence), 1, sentence)
        self.assertIn(
            "citation\\_authority\\_status=blocked\\_pending\\_authenticated\\_roster.",
            related,
        )
        self.assertNotRegex(related, r"\b(?:source|version|verified|cited)=")
        intro = _active(_read(root, "latex/sections/01_introduction.tex"))
        self.assertIn("instrumentation rather than first contributions", intro)
        for identity in EXPECTED_EVALUATION_IDENTITIES:
            self.assertIn(identity, main)
            self.assertIn(identity, intro)
        problem = _active(_read(root, "latex/sections/03_problem_formulation.tex"))
        self.assertIn("$Z_{it}$ the pre-outcome randomized bundle assignment", problem)
        self.assertIn("$E_{it}$ the verified realized execution", problem)
        self.assertIn(
            "entire ontology-specific confirmatory E2 estimand nonestimable and every confirmatory numeric field None",
            problem,
        )
        self.assertEqual(problem.count(FAIL_CLOSED_E2_POLICY), 1)
        problem_without_fail_closed_policy = problem.replace(FAIL_CLOSED_E2_POLICY, "")
        for prohibited in (
            "as-treated",
            "per-protocol",
            "dropped",
            "replaced",
            "filtered",
        ):
            self.assertNotIn(prohibited, problem_without_fail_closed_policy)
        method = _active(_read(root, "latex/sections/04_method.tex"))
        self.assertIn("Study Policy: Obligation-Aware Coordination", method)
        self.assertEqual(method.count(METHOD_BOUNDARY), 1)
        conclusion = _active(_read(root, "latex/sections/09_conclusion.tex"))
        self.assertIn(
            "receipt-verified evaluability is a prerequisite for, not evidence of, coordination value",
            conclusion,
        )
        attacks = _active(_read(root, "latex/appendices/appendix_reviewer_attacks.tex"))
        self.assertIn("RA-NOV-01", attacks)
        for phrase in (
            "iCORE",
            "Eureka",
            "STAR",
            "set-valued routing",
            "ICLR-main novelty",
        ):
            self.assertIn(phrase, attacks)
        claims = _active(_read(root, "latex/appendices/appendix_claims.tex"))
        actual_claim_rows = tuple(
            (key, state, role.strip())
            for key, state, role in re.findall(
                r"\\claim\{([^}]+)\}\s*&\s*([^&]+?)\s*&\s*([^\\]+?)\\\\", claims
            )
        )
        self.assertEqual(actual_claim_rows, CLAIM_ROWS)
        actual_claim_map = {
            key: (state, role) for key, state, role in actual_claim_rows
        }
        self.assertEqual(
            {key: actual_claim_map[key] for key in EXPECTED_CLAIM_UPDATES},
            EXPECTED_CLAIM_UPDATES,
        )
        self.assertNotIn("C-ACCEPTANCE", actual_claim_map)
        self.assertEqual(
            tuple(key for key, state, _ in actual_claim_rows if state == "blocked"),
            BLOCKED_STATE_IDS,
        )
        theory = _active(_read(root, "latex/appendices/appendix_theory.tex"))
        theory_rows = []
        for identifier, label in re.findall(r"\\item\[(B[1-5]): ([^.]+)\.", theory):
            theory_rows.append(
                (identifier, "standard " + label if identifier == "B4" else label)
            )
        self.assertEqual(tuple(theory_rows), SUPPORTING_ROWS)
        self.assertIn("A standard same-information two-law test", theory)
        results = _read(root, "latex/sections/07_results.tex")
        active_results = _active(results)
        self.assertEqual(active_results.count(FROZEN_DIAGNOSTIC_PARAGRAPH), 1)
        self.assertEqual(
            tuple(re.findall(r"\\blocked\{([^}]+)\}", results)), RESULTS_SLOT_IDS
        )
        registry_text = _read(root, POLICY_PROVENANCE_RELATIVE)
        registry_rows = _parse_policy_registry_for_test(registry_text)
        self.assertEqual(registry_rows, POLICY_PROVENANCE_ROWS)
        policy_text = related
        policy_tokens = tuple(
            token.replace("\\_", "_")
            for token in re.findall(r"\\texttt\{([^}]+)\}", policy_text)
        )
        self.assertEqual(policy_tokens, ())
        normalized_related = policy_text.replace(r"\_", "_")
        for policy in POLICY_IDS:
            self.assertIsNone(
                re.search(
                    r"(?<![A-Za-z0-9_])" + re.escape(policy) + r"(?![A-Za-z0-9_])",
                    normalized_related,
                ),
                policy,
            )
        sap_text = _active(_read(root, SAP_RELATIVE))
        sap_policy_tokens = tuple(
            token.replace("\\_", "_")
            for token in re.findall(r"\\texttt\{([^}]+)\}", sap_text)
        )
        self.assertEqual(sap_policy_tokens, POLICY_IDS)
        self.assertEqual(tuple(row[0] for row in registry_rows), POLICY_IDS)
        self.assertNotIn(ORACLE, policy_text)
        self.assertIn("retrospective oracle is not a 23rd policy", policy_text)
        self.assertEqual(tuple(re.findall(r"RA-[A-Z]+-\d\d", attacks)), ATTACK_IDS)
        self.assertEqual(
            tuple(row for row in actual_claim_rows if row[1] == "killed"),
            CLAIM_ROWS[16:19],
        )
        self.assertIn("The symmetric kill chain is load-bearing.", claims)
        self.assertEqual(_parse_kill_survivor_semantics(claims), KILL_SURVIVOR_ROWS)
        for clause in KILL_CHAIN_CLAUSES:
            self.assertIn(clause, claims)
        closure = " ".join(
            _active(_read(root, relative)) for relative in MANUSCRIPT_SOURCE_CLOSURE
        )
        for span in REQUIRED_EVALUATION_VALIDITY_SPANS:
            self.assertIn(span, closure)
        for attack in FORBIDDEN_EVALUATION_VALIDITY_ATTACKS:
            self.assertNotIn(attack, closure)
        for sentence in DISPOSITIONS:
            closure = closure.replace(sentence, "", 1)
        self.assertEqual(closure.count(METHOD_BOUNDARY), 2)
        closure = closure.replace(METHOD_BOUNDARY, "", 2)
        for phrase in FORBIDDEN_POSITIVES:
            self.assertNotIn(phrase, closure)
        for headline in KILLED_HEADLINES:
            self.assertNotIn(f"{headline} established", closure)

    def _mutation_rejected(self, relative: str, old: str, new: str) -> None:
        self._transform_rejected(relative, lambda text: text.replace(old, new, 1))

    def _transform_rejected(self, relative: str, transform) -> None:
        temporary, root = _new_source_closure_repository()
        try:
            self._root_check(
                root
            )  # Every attack starts from an independently passing copy.
            path = root / relative
            text = path.read_text(encoding="utf-8")
            changed = transform(text)
            self.assertNotEqual(changed, text)
            path.write_text(changed, encoding="utf-8", newline="\n")
            with self.assertRaises(AssertionError):
                self._root_check(root)
        finally:
            temporary.cleanup()

    def _assert_independent_semantic_rejection(
        self,
        root: Path,
        relative: str,
        original: str,
        changed: str,
    ) -> None:
        self.assertNotEqual(changed, original)
        path = root / PAPER / relative
        path.write_text(changed, encoding="utf-8", newline="\n")
        try:
            with self.assertRaises(AssertionError):
                self._root_check(
                    root,
                    bypass_bibliography_integrity=True,
                )
        finally:
            path.write_text(original, encoding="utf-8", newline="\n")

    def _assert_production_semantic_rejection(
        self,
        root: Path,
        relative: str,
        original: str,
        changed: str,
    ) -> None:
        self.assertNotEqual(changed, original)
        path = root / PAPER / relative
        path.write_text(changed, encoding="utf-8", newline="\n")
        try:
            with _repatch_semantic_integrity(root, relative, changed):
                with self.assertRaises(PaperLatexVerificationError) as caught:
                    _paper_verification._verify_static_paper_latex_at(root)
            self.assertEqual(
                caught.exception.reason_code,
                "scientific_boundary_invalid",
            )
        finally:
            path.write_text(original, encoding="utf-8", newline="\n")

    def _assert_production_semantic_acceptance(
        self,
        root: Path,
        relative: str,
        original: str,
        changed: str,
    ) -> None:
        self.assertNotEqual(changed, original)
        path = root / PAPER / relative
        path.write_text(changed, encoding="utf-8", newline="\n")
        try:
            try:
                with _repatch_semantic_integrity(root, relative, changed):
                    receipt = _paper_verification._verify_static_paper_latex_at(root)
            except PaperLatexVerificationError as caught:
                self.fail(
                    f"legitimate high-risk sentence rejected: {caught.reason_code}"
                )
            self.assertEqual(receipt.status, "literature_corrected_static_ready")
        finally:
            path.write_text(original, encoding="utf-8", newline="\n")

    def test_exact_narrative_weakenings_reject_after_integrity_bypass(self):
        temporary, root = _new_source_closure_repository()
        try:
            _paper_verification._verify_static_paper_latex_at(root)
            relative = "latex/sections/02_related_work.tex"
            original = _read(root, relative)
            for old, new in NARRATIVE_WEAKENINGS:
                with self.subTest(old=old, new=new):
                    self.assertEqual(original.count(old), 1, old)
                    self._assert_production_semantic_rejection(
                        root,
                        relative,
                        original,
                        original.replace(old, new, 1),
                    )
        finally:
            temporary.cleanup()

    def test_forbidden_evaluation_validity_attacks_reject_after_full_reseal(self):
        temporary, root = _new_source_closure_repository()
        try:
            _paper_verification._verify_static_paper_latex_at(root)
            relative = "latex/sections/01_introduction.tex"
            original = _read(root, relative)
            insertion_point = r"\section{Introduction}"
            self.assertEqual(original.count(insertion_point), 1)
            for attack in FORBIDDEN_EVALUATION_VALIDITY_ATTACKS:
                with self.subTest(attack=attack):
                    changed = original.replace(
                        insertion_point,
                        insertion_point + "\n" + attack + ".",
                        1,
                    )
                    self._assert_production_semantic_rejection(
                        root,
                        relative,
                        original,
                        changed,
                    )
        finally:
            temporary.cleanup()

    def test_compositional_evaluation_validity_attacks_reject_after_full_reseal(
        self,
    ):
        temporary, root = _new_source_closure_repository()
        try:
            _paper_verification._verify_static_paper_latex_at(root)
            relative = "latex/sections/01_introduction.tex"
            original = _read(root, relative)
            insertion_point = r"\section{Introduction}"
            self.assertEqual(original.count(insertion_point), 1)
            for family, attack in COMPOSITIONAL_EVALUATION_VALIDITY_ATTACKS:
                with self.subTest(family=family, attack=attack):
                    changed = original.replace(
                        insertion_point,
                        insertion_point + "\n" + attack,
                        1,
                    )
                    self._assert_production_semantic_rejection(
                        root,
                        relative,
                        original,
                        changed,
                    )
        finally:
            temporary.cleanup()

    def test_high_risk_authorial_assertions_reject_after_full_reseal(self):
        temporary, root = _new_source_closure_repository()
        try:
            _paper_verification._verify_static_paper_latex_at(root)
            relative = "latex/sections/01_introduction.tex"
            original = _read(root, relative)
            insertion_point = r"\section{Introduction}"
            self.assertEqual(original.count(insertion_point), 1)
            for family, attack in HIGH_RISK_AUTHORIAL_SENTENCE_ATTACKS:
                with self.subTest(family=family, attack=attack):
                    changed = original.replace(
                        insertion_point,
                        insertion_point + "\n" + attack,
                        1,
                    )
                    self._assert_production_semantic_rejection(
                        root,
                        relative,
                        original,
                        changed,
                    )
        finally:
            temporary.cleanup()

    def test_synonym_only_assertions_avoid_legacy_topics_and_reject_after_full_reseal(
        self,
    ):
        temporary, root = _new_source_closure_repository()
        try:
            _paper_verification._verify_static_paper_latex_at(root)
            relative = "latex/sections/01_introduction.tex"
            original = _read(root, relative)
            insertion_point = r"\section{Introduction}"
            self.assertEqual(original.count(insertion_point), 1)
            for family, attack in SYNONYM_ONLY_AUTHORIAL_SENTENCE_ATTACKS:
                with self.subTest(family=family, attack=attack):
                    self.assertIsNone(
                        LEGACY_HIGH_RISK_EVALUATION_TOPIC.search(attack),
                        "synonym witness still contains a legacy protected topic",
                    )
                    changed = original.replace(
                        insertion_point,
                        insertion_point + "\n" + attack,
                        1,
                    )
                    self.assertEqual(changed.replace("\n" + attack, "", 1), original)
                    self._assert_production_semantic_rejection(
                        root,
                        relative,
                        original,
                        changed,
                    )
        finally:
            temporary.cleanup()

    def test_high_risk_explicit_negation_and_attack_framing_accept_after_full_reseal(
        self,
    ):
        temporary, root = _new_source_closure_repository()
        try:
            _paper_verification._verify_static_paper_latex_at(root)
            relative = "latex/sections/01_introduction.tex"
            original = _read(root, relative)
            insertion_point = r"\section{Introduction}"
            self.assertEqual(original.count(insertion_point), 1)
            for family, nonclaim in HIGH_RISK_AUTHORIAL_SENTENCE_NONCLAIMS:
                with self.subTest(family=family, nonclaim=nonclaim):
                    changed = original.replace(
                        insertion_point,
                        insertion_point + "\n" + nonclaim,
                        1,
                    )
                    self._assert_production_semantic_acceptance(
                        root,
                        relative,
                        original,
                        changed,
                    )
        finally:
            temporary.cleanup()

    def test_new_bibtex_attack_families_reject_after_raw_hash_bypass(self):
        temporary, root = _new_source_closure_repository()
        try:
            self._root_check(root)
            bibliography_relative = "latex/references.bib"
            bibliography = _read(root, bibliography_relative)
            self.assertEqual(len(TASK3_BIBLIOGRAPHY_AUTHORITY), 21)
            self.assertEqual(
                Counter(
                    review_status
                    for _key, _entry_type, review_status, _fields in TASK3_BIBLIOGRAPHY_AUTHORITY
                ),
                Counter(
                    {
                        "peer_reviewed": 17,
                        "public_preprint": 3,
                        "peer_reviewed_workshop": 1,
                    }
                ),
            )
            assigned_doi_keys = tuple(
                key
                for key, _entry_type, _review_status, fields in TASK3_BIBLIOGRAPHY_AUTHORITY
                if any(field == "doi" for field, _value in fields)
            )
            self.assertEqual(
                assigned_doi_keys,
                (
                    "aggarwal2024automix",
                    "auer2002finite",
                    "chernozhukov2018double",
                    "keyu2026bicsrouter",
                    "kim2026outgrow",
                    "lu2024zooter",
                    "xu2026verimap",
                    "yue2025masrouter",
                ),
            )
            self.assertEqual(
                len(TASK3_BIBLIOGRAPHY_AUTHORITY) * 5 + len(assigned_doi_keys) + 1,
                114,
            )
            doi_attack_count = 0
            for key, entry_type, review_status, fields in TASK3_BIBLIOGRAPHY_AUTHORITY:
                entry = _expected_bibliography_entry(key, entry_type, fields)
                self.assertEqual(bibliography.count(entry), 1, key)
                wrong_type = (
                    "misc" if entry_type == "inproceedings" else "inproceedings"
                )
                with self.subTest(key=key, attack="wrong entry type"):
                    self._assert_independent_semantic_rejection(
                        root,
                        bibliography_relative,
                        bibliography,
                        bibliography.replace(
                            f"@{entry_type}{{{key},",
                            f"@{wrong_type}{{{key},",
                            1,
                        ),
                    )

                doi_fields = tuple(value for field, value in fields if field == "doi")
                for doi in doi_fields:
                    doi_attack_count += 1
                    with self.subTest(key=key, attack="removed assigned DOI"):
                        doi_line = f"  doi = {{{doi}}},\n"
                        self.assertIn(doi_line, bibliography)
                        self._assert_independent_semantic_rejection(
                            root,
                            bibliography_relative,
                            bibliography,
                            bibliography.replace(doi_line, "", 1),
                        )

                with self.subTest(
                    key=key,
                    attack="wrong review status carrier",
                    expected_status=review_status,
                ):
                    self._assert_independent_semantic_rejection(
                        root,
                        bibliography_relative,
                        bibliography,
                        _mutate_task3_review_status_carrier(
                            bibliography,
                            key,
                            review_status,
                            fields,
                        ),
                    )

                with self.subTest(key=key, attack="duplicated field"):
                    self._assert_independent_semantic_rejection(
                        root,
                        bibliography_relative,
                        bibliography,
                        bibliography.replace(
                            f"@{entry_type}{{{key},\n",
                            f"@{entry_type}{{{key},\n  title = {{Duplicate}},\n",
                            1,
                        ),
                    )

                with self.subTest(key=key, attack="case-colliding key"):
                    collision = entry.replace(
                        f"{{{key},",
                        f"{{{key.upper()},",
                        1,
                    )
                    self._assert_independent_semantic_rejection(
                        root,
                        bibliography_relative,
                        bibliography,
                        bibliography + "\n" + collision + "\n",
                    )

                with self.subTest(key=key, attack="comment-hidden fake entry"):
                    hidden = "% " + entry.replace("\n", "\n% ")
                    self._assert_independent_semantic_rejection(
                        root,
                        bibliography_relative,
                        bibliography,
                        bibliography.replace(entry, hidden, 1),
                    )

            self.assertEqual(doi_attack_count, 8)
            with self.subTest(attack="uncited extra entry"):
                self._assert_independent_semantic_rejection(
                    root,
                    bibliography_relative,
                    bibliography,
                    bibliography
                    + "\n@misc{task5uncitedextra,\n"
                    + "  title = {Uncited extra entry},\n"
                    + "  author = {Mutation Fixture},\n"
                    + "  year = {2026}\n"
                    + "}\n",
                )
        finally:
            temporary.cleanup()

    def test_primary_metadata_bibtex_manifest_and_citations_are_bijective(self):
        self._root_check(REPOSITORY)
        manifest_path = "docs/paper/iclr2027_oacs/literature_primary_source_manifest.md"
        for key, title, authors, year, url, doi, _ in PRIMARY_SOURCES:
            disposition = next(
                source[6] for source in PRIMARY_SOURCES if source[0] == key
            )
            fields = [
                (1, title),
                (2, "; ".join(authors)),
                (3, year),
                (4, url),
                (6, disposition),
            ]
            if doi:
                fields.append((5, doi))
            for column, value in fields:
                self._transform_rejected(
                    manifest_path,
                    lambda text,
                    key=key,
                    column=column,
                    value=value: _replace_manifest_cell(
                        text, key, column, value + " wrong"
                    ),
                )
        for key, entry_type, fields in BIBLIOGRAPHY_ENTRIES:
            if key not in ALL_BIBLIOGRAPHY_KEYS:
                continue
            for field, value in fields:
                self._transform_rejected(
                    "docs/paper/iclr2027_oacs/latex/references.bib",
                    lambda text, key=key, field=field, value=value: _replace_bib_field(
                        text, key, field, value + " wrong"
                    ),
                )
            if entry_type == "inproceedings":
                self._mutation_rejected(
                    "docs/paper/iclr2027_oacs/latex/references.bib",
                    f"@inproceedings{{{key},",
                    f"@misc{{{key},",
                )
        ordered_sources = tuple(sorted(PRIMARY_SOURCES))
        for index, (key, *_rest) in enumerate(ordered_sources):
            alternate_key = ordered_sources[(index + 1) % len(ordered_sources)][0]
            self._mutation_rejected(
                "docs/paper/iclr2027_oacs/literature_primary_source_manifest.md",
                f"| {key} |",
                f"| missing-{key} |",
            )
            self._mutation_rejected(
                "docs/paper/iclr2027_oacs/literature_primary_source_manifest.md",
                f"| {key} |",
                f"| {alternate_key} |",
            )
        for index, (key, entry_type, _fields) in enumerate(BIBLIOGRAPHY_ENTRIES):
            if key not in ALL_BIBLIOGRAPHY_KEYS:
                continue
            alternate_key = BIBLIOGRAPHY_ENTRIES[
                (index + 1) % len(BIBLIOGRAPHY_ENTRIES)
            ][0]
            header = f"@{entry_type}{{{key},"
            self._mutation_rejected(
                "docs/paper/iclr2027_oacs/latex/references.bib",
                header,
                f"@{entry_type}{{missing{key},",
            )
            self._mutation_rejected(
                "docs/paper/iclr2027_oacs/latex/references.bib",
                header,
                f"@{entry_type}{{{alternate_key},",
            )
        self._mutation_rejected(
            "docs/paper/iclr2027_oacs/literature_primary_source_manifest.md",
            "| bala2026setvalued",
            "<!-- | bala2026setvalued",
        )
        self._mutation_rejected(
            "docs/paper/iclr2027_oacs/latex/references.bib",
            "@misc{bala2026setvalued,",
            "@misc{bala2026setvalued,\n% @misc{bala2026setvalued,",
        )
        for key, title, authors, year, url, doi, disposition in sorted(PRIMARY_SOURCES):
            row = f"| {key} | {title} | {'; '.join(authors)} | {year} | {url} | {doi or '--'} | {disposition} |"
            self._transform_rejected(
                manifest_path, lambda text, row=row: text.replace(row + "\n", "", 1)
            )
            self._transform_rejected(
                manifest_path,
                lambda text, row=row: text.replace(row, row + "\n" + row, 1),
            )
            self._transform_rejected(
                manifest_path,
                lambda text, row=row: text.replace(row, "<!-- " + row + " -->", 1),
            )
            self._transform_rejected(
                manifest_path, lambda text, row=row: text + row + "\n"
            )
        for left, right in zip(
            tuple(sorted(PRIMARY_SOURCES)), tuple(sorted(PRIMARY_SOURCES))[1:]
        ):
            left_row = f"| {left[0]} | {left[1]} | {'; '.join(left[2])} | {left[3]} | {left[4]} | {left[5] or '--'} | {left[6]} |"
            right_row = f"| {right[0]} | {right[1]} | {'; '.join(right[2])} | {right[3]} | {right[4]} | {right[5] or '--'} | {right[6]} |"
            self._transform_rejected(
                manifest_path,
                lambda text, left_row=left_row, right_row=right_row: text.replace(
                    left_row + "\n" + right_row, right_row + "\n" + left_row, 1
                ),
            )
        bibliography_path = "docs/paper/iclr2027_oacs/latex/references.bib"
        for key in ALL_BIBLIOGRAPHY_KEYS:
            self._transform_rejected(
                bibliography_path,
                lambda text, key=key: re.sub(
                    r"(?m)^(@[A-Za-z]+\{)" + re.escape(key) + r",",
                    lambda match: match.group(1) + "missing-" + key + ",",
                    text,
                    count=1,
                ),
            )
        for left, right in zip(ALL_BIBLIOGRAPHY_KEYS, ALL_BIBLIOGRAPHY_KEYS[1:]):
            self._transform_rejected(
                bibliography_path,
                lambda text, left=left, right=right: _swap_once(
                    text, "{" + left + ",", "{" + right + ","
                ),
            )
        self._transform_rejected(
            bibliography_path,
            lambda text: text + "\n@misc{extra2026row,\n  title = {extra}\n}\n",
        )
        self._transform_rejected(
            "docs/paper/iclr2027_oacs/latex/sections/02_related_work.tex",
            lambda text: text.replace("\\citep{zhang2026icore}", "zhang2026icore", 1),
        )

    def test_each_direct_competitor_has_its_exact_component_demotion(self):
        self.assertIn(
            DISPOSITIONS[0],
            _active(_read(REPOSITORY, "latex/sections/02_related_work.tex")),
        )
        source_dispositions = (
            *DISPOSITIONS[:4],
            "BRACE is the closest\n"
            "product-bias/compliance prior; B1 is model-specific supporting theory rather\n"
            "than a first orthogonal remainder claim.",
        )
        for sentence in source_dispositions:
            self._mutation_rejected(
                "docs/paper/iclr2027_oacs/latex/sections/02_related_work.tex",
                sentence,
                "Our contribution is first and novel.",
            )
        self._mutation_rejected(
            "docs/paper/iclr2027_oacs/latex/sections/02_related_work.tex",
            DISPOSITIONS[0],
            "% " + DISPOSITIONS[0],
        )

    def test_intro_method_and_conclusion_each_keep_their_own_novelty_boundary(self):
        self.assertIn(
            "instrumentation rather than first contributions",
            _active(_read(REPOSITORY, "latex/sections/01_introduction.tex")),
        )
        self._mutation_rejected(
            "docs/paper/iclr2027_oacs/latex/sections/01_introduction.tex",
            "instrumentation rather than first contributions",
            "first contributions",
        )
        self._mutation_rejected(
            "docs/paper/iclr2027_oacs/latex/sections/04_method.tex",
            METHOD_BOUNDARY,
            "OACS is a novel obligation graph.",
        )
        self._mutation_rejected(
            "docs/paper/iclr2027_oacs/latex/sections/09_conclusion.tex",
            "receipt-verified evaluability is a prerequisite for, not\n"
            "evidence of, coordination value",
            "receipt-verified evaluability proves coordination value",
        )

    def test_assignment_execution_and_ontology_wide_nonestimability_are_exact(self):
        self.assertIn(
            "Z_{it}",
            _active(_read(REPOSITORY, "latex/sections/03_problem_formulation.tex")),
        )
        for old, new in (
            ("Z_{it}", "A_{it}"),
            ("E_{it}", "Z_{it}"),
            (
                "entire ontology-specific\nconfirmatory E2 estimand",
                "cell-specific E2 estimand",
            ),
        ):
            self._mutation_rejected(
                "docs/paper/iclr2027_oacs/latex/sections/03_problem_formulation.tex",
                old,
                new,
            )
        for word in (
            "repeat",
            "cell",
            "target",
            "site",
            "dropped",
            "replaced",
            "filtered",
            "as-treated",
            "per-protocol",
        ):
            self._mutation_rejected(
                "docs/paper/iclr2027_oacs/latex/sections/03_problem_formulation.tex",
                FAIL_CLOSED_E2_POLICY_SOURCE,
                FAIL_CLOSED_E2_POLICY_SOURCE.replace(word, word + "_mutated"),
            )

    def test_as_treated_per_protocol_and_selective_drop_language_is_forbidden(self):
        self.assertIn(
            FAIL_CLOSED_E2_POLICY,
            _active(_read(REPOSITORY, "latex/sections/03_problem_formulation.tex")),
        )
        for phrase in ("as-treated", "per-protocol", "dropped", "replaced", "filtered"):
            self._mutation_rejected(
                "docs/paper/iclr2027_oacs/latex/sections/03_problem_formulation.tex",
                phrase,
                "not-" + phrase,
            )
        for conflict in (
            "One repeat may be dropped.",
            "One cell may be dropped.",
            "One site may be dropped.",
            "A required target may be replaced.",
            "A required target may be filtered.",
            "Results may be analyzed as-treated.",
            "Results may be analyzed per-protocol.",
        ):
            self._transform_rejected(
                "docs/paper/iclr2027_oacs/latex/sections/03_problem_formulation.tex",
                lambda text, conflict=conflict: text + "\n" + conflict + "\n",
            )

    def test_policy_source_version_authority_remains_blocked(self):
        self.assertIn(
            "citation\\_authority\\_status=blocked\\_pending\\_authenticated\\_roster.",
            _active(_read(REPOSITORY, "latex/sections/02_related_work.tex")),
        )
        self._mutation_rejected(
            "docs/paper/iclr2027_oacs/latex/sections/02_related_work.tex",
            "citation\\_authority\\_status=blocked\\_pending\\_authenticated\\_roster",
            "citation\\_authority\\_status=verified",
        )
        self._mutation_rejected(
            "docs/paper/iclr2027_oacs/latex/sections/02_related_work.tex",
            "Self-resource allocation",
            "agentprune source=v1 verified cited; Self-resource allocation",
        )

    def test_exact_claim_policy_oracle_attack_and_kill_objects_do_not_drift(self):
        self.assertIn(
            "C-THEORY-JOINT-MINIMAX",
            _active(_read(REPOSITORY, "latex/appendices/appendix_claims.tex")),
        )
        claim_path = "docs/paper/iclr2027_oacs/latex/appendices/appendix_claims.tex"
        self._transform_rejected(
            claim_path,
            lambda text: text
            + "\nArchitecture E2 failure is scoped to Architecture only; "
            "JCI may rescue the ICLR-main OACS thesis.\n",
        )
        for left_index, left in enumerate(CLAIM_ROWS):
            for right in CLAIM_ROWS[left_index + 1 :]:
                self._transform_rejected(
                    claim_path,
                    lambda text, left=left, right=right: _swap_claim_columns(
                        text, left, right
                    ),
                )
        self._transform_rejected(
            claim_path,
            lambda text: _swap_claim_columns(
                text, CLAIM_ROWS[4], CLAIM_ROWS[5], roles_only=True
            ),
        )
        policy_path = (
            "docs/paper/iclr2027_oacs/latex/appendices/appendix_analysis_protocol.tex"
        )
        policy_literals = tuple(
            "\\texttt{" + policy.replace("_", "\\_") + "}" for policy in POLICY_IDS
        )
        for left_index, left in enumerate(policy_literals):
            for right in policy_literals[left_index + 1 :]:
                self._transform_rejected(
                    policy_path,
                    lambda text, left=left, right=right: _swap_once(text, left, right),
                )
        attack_path = (
            "docs/paper/iclr2027_oacs/latex/appendices/appendix_reviewer_attacks.tex"
        )
        for left_index, left in enumerate(ATTACK_IDS):
            for right in ATTACK_IDS[left_index + 1 :]:
                self._transform_rejected(
                    attack_path,
                    lambda text, left=left, right=right: _swap_once(text, left, right),
                )
        self._mutation_rejected(
            "docs/paper/iclr2027_oacs/latex/sections/02_related_work.tex",
            "The retrospective oracle is not a 23rd policy",
            "The retrospective_oracle is a 23rd policy",
        )
        self._transform_rejected(
            policy_path,
            lambda text: text.replace(
                "\\texttt{zooter\\_adaptation}",
                "\\texttt{retrospective_oracle}, \\texttt{zooter\\_adaptation}",
                1,
            ),
        )
        for label, clause_index, old, new in KILL_SEMANTIC_MUTATIONS:
            source_clause = KILL_CHAIN_SOURCE_CLAUSES[clause_index]
            self.assertEqual(source_clause.count(old), 1, label)
            mutated_clause = source_clause.replace(old, new, 1)
            self._mutation_rejected(claim_path, source_clause, mutated_clause)
        for headline in KILLED_HEADLINES:
            self._transform_rejected(
                claim_path,
                lambda text, headline=headline: text + f"\n{headline} established\n",
            )

    def test_positive_result_authority_novelty_and_submission_claims_are_forbidden(
        self,
    ):
        self.assertIn(
            "reviewed primary roster",
            _active(_read(REPOSITORY, "latex/sections/02_related_work.tex")),
        )
        for phrase in FORBIDDEN_POSITIVES:
            self._mutation_rejected(
                "docs/paper/iclr2027_oacs/latex/sections/01_introduction.tex",
                "\\section{Introduction}",
                f"\\section{{Introduction}}\n{phrase}",
            )


def _error_json(reason_code: str) -> str:
    return (
        json.dumps(
            {
                "reason_code": reason_code,
                "schema_version": ERROR_SCHEMA,
                "status": "error",
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )


def _receipt_hash(payload: dict[str, object]) -> str:
    unhashed = {key: payload[key] for key in RECEIPT_KEYS[:-1]}
    canonical = json.dumps(unhashed, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalized_ast_sha256(source: str) -> str:
    normalized = ast.dump(
        ast.parse(source),
        annotate_fields=True,
        include_attributes=False,
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest().upper()


def _assert_no_repository_paper_copytree(source: str) -> None:
    """Reject test fixtures that copy the repository paper/docs tree."""
    tree = ast.parse(source)
    parents = {
        id(child): parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }

    def scope(node: ast.AST):
        cursor = node
        while id(cursor) in parents:
            cursor = parents[id(cursor)]
            if isinstance(cursor, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                return cursor
        return None

    assignments: dict[tuple[int | None, str], list[tuple[ast.AST, object]]] = {}
    for assignment in ast.walk(tree):
        if not isinstance(assignment, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
            continue
        targets = (
            assignment.targets
            if isinstance(assignment, ast.Assign)
            else (assignment.target,)
        )
        assignment_scope = scope(assignment)
        scope_key = None if assignment_scope is None else id(assignment_scope)
        for target in targets:
            for child in ast.walk(target):
                if isinstance(child, ast.Name):
                    assignments.setdefault((scope_key, child.id), []).append(
                        (assignment.value, assignment_scope)
                    )

    def repository_dependent(
        expression: ast.AST,
        expression_scope,
        seen: frozenset[tuple[int | None, str]] = frozenset(),
    ) -> bool:
        names = {
            child.id for child in ast.walk(expression) if isinstance(child, ast.Name)
        }
        if "REPOSITORY" in names:
            return True
        scope_key = None if expression_scope is None else id(expression_scope)
        for name in names:
            key = (scope_key, name)
            fallback = (None, name)
            lookup = key if key in assignments else fallback
            if lookup in seen:
                continue
            for value, value_scope in assignments.get(lookup, ()):
                if repository_dependent(value, value_scope, seen | {lookup}):
                    return True
        return False

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if not (
            isinstance(function, ast.Attribute)
            and function.attr == "copytree"
            or isinstance(function, ast.Name)
            and function.id == "copytree"
        ):
            continue
        if not node.args:
            continue
        if repository_dependent(node.args[0], scope(node)):
            raise AssertionError("repository paper/docs copytree fixture")


def _assert_safe_ast(source: str, *, cli: bool) -> None:
    tree = ast.parse(source)
    observed_structure_sha256 = _normalized_ast_sha256(source)
    observed_imports = []
    parents = {
        id(child): parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    forbidden_roots = {
        "http",
        "importlib",
        "multiprocessing",
        "requests",
        "socket",
        "subprocess",
        "urllib",
    }
    forbidden_calls = {
        "__import__",
        "chmod",
        "compile",
        "delattr",
        "eval",
        "exec",
        "getattr",
        "globals",
        "link",
        "locals",
        "mkdir",
        "open",
        "remove",
        "rename",
        "rmdir",
        "setattr",
        "symlink",
        "touch",
        "unlink",
        "vars",
        "call",
        "check_call",
        "check_output",
        "exec_module",
        "load_module",
        "Popen",
        "run",
        "spawnl",
        "spawnle",
        "spawnlp",
        "spawnlpe",
        "spawnv",
        "spawnve",
        "spawnvp",
        "spawnvpe",
        "system",
        "write_bytes",
        "write_text",
    }
    capability_references = []
    capability_names = []
    unsafe_call = False

    def owner(node: ast.AST) -> str:
        cursor = node
        while id(cursor) in parents:
            cursor = parents[id(cursor)]
            if isinstance(cursor, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return cursor.name
        return "<module>"

    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in {
            "AuthenticatedTree",
            "Path",
            "__loader__",
            "__spec__",
        }:
            parent = parents.get(id(node))
            if isinstance(parent, ast.Call) and parent.func is node:
                kind = "call"
                expression = ast.unparse(parent)
            elif isinstance(parent, ast.arg) and parent.annotation is node:
                kind = "annotation"
                expression = parent.arg
            elif (
                isinstance(parent, ast.Call)
                and isinstance(parent.func, ast.Name)
                and parent.func.id == "isinstance"
                and node in parent.args[1:]
            ):
                kind = "type_check"
                expression = ast.unparse(parent)
            else:
                kind = "reference"
                expression = ast.unparse(node)
            capability_names.append((owner(node), node.id, kind, expression))
        if (
            isinstance(node, ast.Attribute)
            and node.attr in PATH_AND_LOADER_CAPABILITY_ATTRIBUTES
        ):
            parent = parents.get(id(node))
            is_call = isinstance(parent, ast.Call) and parent.func is node
            target = parent if is_call else node
            capability_references.append(
                (
                    owner(node),
                    node.attr,
                    "call" if is_call else "reference",
                    ast.unparse(target),
                )
            )
        if isinstance(node, ast.Import):
            for alias in node.names:
                observed_imports.append(("import", alias.name, alias.asname))
                if alias.name.split(".")[0] in forbidden_roots:
                    raise AssertionError("forbidden import")
        elif isinstance(node, ast.ImportFrom):
            names = tuple((alias.name, alias.asname) for alias in node.names)
            observed_imports.append(("from", node.module, names, node.level))
            if node.module is None or node.module.split(".")[0] in forbidden_roots:
                raise AssertionError("forbidden import")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called = node.func.id
                if called in forbidden_calls:
                    unsafe_call = True
            elif isinstance(node.func, ast.Attribute):
                called = node.func.attr
            else:
                unsafe_call = True
                continue
            if called in forbidden_calls - {"compile"}:
                unsafe_call = True
    expected_capability_references = (
        () if cli else PRODUCTION_ALLOWED_CAPABILITY_REFERENCES
    )
    if tuple(sorted(capability_references)) != expected_capability_references:
        raise AssertionError("capability reference drift")
    expected_capability_names = () if cli else PRODUCTION_ALLOWED_CAPABILITY_NAMES
    if tuple(sorted(capability_names)) != expected_capability_names:
        raise AssertionError("capability name drift")
    if unsafe_call:
        raise AssertionError("forbidden or dynamic call")
    expected = (
        (
            ("import", "sys", None),
            (
                "from",
                "iclr2027.paper_latex_verification",
                (
                    ("PaperLatexVerificationError", None),
                    ("PaperStaticReceipt", None),
                    ("verify_static_paper_latex", None),
                ),
                0,
            ),
        )
        if cli
        else (
            ("from", "__future__", (("annotations", None),), 0),
            ("from", "dataclasses", (("dataclass", None), ("fields", None)), 0),
            ("import", "hashlib", None),
            ("import", "json", None),
            ("from", "pathlib", (("Path", None),), 0),
            ("import", "re", None),
            (
                "from",
                "iclr2027.secure_files",
                (("AuthenticatedTree", None),),
                0,
            ),
        )
    )
    if tuple(observed_imports) != expected:
        raise AssertionError("import allowlist drift")
    expected_structure_sha256 = (
        CLI_AST_STRUCTURE_SHA256 if cli else PRODUCTION_AST_STRUCTURE_SHA256
    )
    if observed_structure_sha256 != expected_structure_sha256:
        raise AssertionError("AST structural digest drift")


class VenueOverlaySecurityFixTests(unittest.TestCase):
    @staticmethod
    def _source_text(root: Path) -> dict[str, str]:
        return {
            relative: _read(root, relative) for relative in MANUSCRIPT_SOURCE_CLOSURE
        }

    def _assert_main_mutations_reject(self, mutations) -> None:
        temporary, root = _new_source_closure_repository()
        try:
            source_text = self._source_text(root)
            main = source_text["latex/main.tex"]
            self.assertEqual(
                _test_owned_lossless_active_tex_sha256(main),
                CANONICAL_ACTIVE_MAIN_SHA256,
            )
            _paper_verification._validate_iclr2027_venue_overlay(source_text)
            for label, insertion in mutations:
                with self.subTest(label=label):
                    changed = dict(source_text)
                    changed["latex/main.tex"] = main.replace(
                        r"\begin{document}",
                        insertion + "\n" + r"\begin{document}",
                        1,
                    )
                    with self.assertRaises(PaperLatexVerificationError) as caught:
                        _paper_verification._validate_iclr2027_venue_overlay(changed)
                    self.assertEqual(
                        caught.exception.reason_code,
                        "source_grammar_invalid",
                    )
        finally:
            temporary.cleanup()

    def test_fixtures_never_copy_the_repository_paper_or_docs_tree(self):
        source = Path(__file__).read_text(encoding="utf-8")
        _assert_no_repository_paper_copytree(source)
        attacks = (
            "\nshutil.copytree(REPOSITORY / PAPER, REPOSITORY / 'copy')\n",
            (
                "\npaper_source = REPOSITORY / PAPER\n"
                "source_alias = paper_source\n"
                "shutil.copytree(source_alias, REPOSITORY / 'copy')\n"
            ),
        )
        for attack in attacks:
            with self.subTest(attack=attack.strip()):
                with self.assertRaisesRegex(
                    AssertionError,
                    "repository paper/docs copytree fixture",
                ):
                    _assert_no_repository_paper_copytree(source + attack)

    def test_safe_fixture_copies_only_permitted_sources_and_empty_metadata(self):
        copied_sources = []
        opened_sources = []
        original_copyfile = shutil.copyfile
        original_open = builtins.open

        def copyfile_spy(source, destination, *args, **kwargs):
            source_path = Path(source)
            if source_path.is_relative_to(REPOSITORY / PAPER):
                relative = source_path.relative_to(REPOSITORY / PAPER).as_posix()
                if relative in AUTHORITY_SIBLINGS:
                    raise AssertionError("authority sibling copy attempted")
                copied_sources.append(relative)
            return original_copyfile(source, destination, *args, **kwargs)

        def open_spy(file, *args, **kwargs):
            try:
                source_path = Path(file)
            except TypeError:
                return original_open(file, *args, **kwargs)
            if source_path.is_relative_to(REPOSITORY / PAPER):
                relative = source_path.relative_to(REPOSITORY / PAPER).as_posix()
                if relative in AUTHORITY_SIBLINGS:
                    raise AssertionError("authority sibling open attempted")
                opened_sources.append(relative)
            return original_open(file, *args, **kwargs)

        with mock.patch.object(
            shutil,
            "copyfile",
            side_effect=AssertionError("copy delegated"),
        ) as delegated:
            with self.assertRaisesRegex(
                AssertionError,
                "fixture source is outside the permitted closure",
            ):
                _copy_permitted_fixture_source(
                    REPOSITORY / PAPER / AUTHORITY_SIBLINGS[-1],
                    Path(tempfile.gettempdir()) / "must-not-exist",
                )
            delegated.assert_not_called()

        temporary = None
        try:
            with (
                mock.patch.object(
                    shutil,
                    "copyfile",
                    side_effect=copyfile_spy,
                ),
                mock.patch.object(
                    shutil,
                    "copytree",
                    side_effect=AssertionError("broad copytree"),
                ),
                mock.patch.object(
                    builtins,
                    "open",
                    side_effect=open_spy,
                ),
            ):
                temporary, root = _new_source_closure_repository()
            expected_inputs = (
                *SOURCE_CLOSURE,
                "literature_primary_source_manifest.md",
            )
            self.assertEqual(tuple(copied_sources), expected_inputs)
            self.assertEqual(Counter(opened_sources), Counter(expected_inputs))
            paper_root = root / PAPER
            for sibling in AUTHORITY_SIBLINGS:
                placeholder = paper_root / sibling
                self.assertTrue(placeholder.is_file())
                self.assertFalse(placeholder.is_symlink())
                self.assertEqual(placeholder.stat().st_size, 0)
            reads = []
            receipt = _paper_verification._verify_static_paper_latex_at(
                root,
                read_observer=reads.append,
            )
            self.assertEqual(
                {path.relative_to(paper_root).as_posix() for path in reads},
                {*SOURCE_CLOSURE, "literature_primary_source_manifest.md"},
            )
            self.assertEqual(
                receipt.status,
                "literature_corrected_static_ready",
            )
        finally:
            if temporary is not None:
                temporary.cleanup()

    def test_closed_main_rejects_alternate_and_dynamic_final_controls(self):
        self._assert_main_mutations_reject(MAIN_FINAL_CONTROL_MUTATIONS)
        temporary, root = _new_source_closure_repository()
        try:
            source_text = self._source_text(root)
            source_text["latex/main.tex"] += "% \\iclrfinalcopy is inactive\n"
            _paper_verification._validate_iclr2027_venue_overlay(source_text)
        finally:
            temporary.cleanup()

    def test_closed_main_rejects_metadata_and_alternate_loading_controls(self):
        self._assert_main_mutations_reject(MAIN_METADATA_AND_LOADING_MUTATIONS)

    def test_closed_main_rejects_layout_and_typography_override_families(self):
        self._assert_main_mutations_reject(MAIN_LAYOUT_TYPOGRAPHY_MUTATIONS)

    def test_anonymity_channels_reject_across_every_manuscript_tex_source(self):
        temporary, root = _new_source_closure_repository()
        try:
            source_text = self._source_text(root)
            tex_paths = tuple(
                relative
                for relative in MANUSCRIPT_SOURCE_CLOSURE
                if relative.endswith(".tex")
            )
            self.assertEqual(len(tex_paths), 16)
            for index, relative in enumerate(tex_paths):
                label, payload = ANONYMITY_CHANNEL_MUTATIONS[
                    index % len(ANONYMITY_CHANNEL_MUTATIONS)
                ]
                with self.subTest(relative=relative, channel=label):
                    changed = dict(source_text)
                    changed[relative] += "\n" + payload + "\n"
                    with self.assertRaises(PaperLatexVerificationError) as caught:
                        _paper_verification._validate_iclr2027_venue_overlay(changed)
                    self.assertEqual(
                        caught.exception.reason_code,
                        "source_grammar_invalid",
                    )
            outside_main = "latex/sections/01_introduction.tex"
            for label, payload in ANONYMITY_CHANNEL_MUTATIONS:
                with self.subTest(relative=outside_main, channel=label):
                    changed = dict(source_text)
                    changed[outside_main] += "\n" + payload + "\n"
                    with self.assertRaises(PaperLatexVerificationError) as caught:
                        _paper_verification._validate_iclr2027_venue_overlay(changed)
                    self.assertEqual(
                        caught.exception.reason_code,
                        "source_grammar_invalid",
                    )
            bibliography_only = dict(source_text)
            bibliography_only["latex/references.bib"] += (
                "\n% Third-Party Author, https://example.org/publication\n"
            )
            _paper_verification._validate_iclr2027_venue_overlay(bibliography_only)
        finally:
            temporary.cleanup()

    def test_closed_non_main_tex_rejects_indirect_metadata_per_path(self):
        temporary, root = _new_source_closure_repository()
        try:
            source_text = self._source_text(root)
            tex_paths = tuple(
                relative
                for relative in MANUSCRIPT_SOURCE_CLOSURE
                if relative.endswith(".tex")
            )
            self.assertEqual(len(tex_paths), 16)
            self.assertEqual(
                tuple(CANONICAL_ACTIVE_MANUSCRIPT_TEX_SHA256),
                tex_paths,
            )
            for (
                relative,
                expected_digest,
            ) in CANONICAL_ACTIVE_MANUSCRIPT_TEX_SHA256.items():
                self.assertEqual(
                    _test_owned_lossless_active_tex_sha256(source_text[relative]),
                    expected_digest,
                )

            non_main_paths = tuple(
                relative for relative in tex_paths if relative != "latex/main.tex"
            )
            self.assertEqual(len(non_main_paths), 15)
            for relative in non_main_paths:
                for label, payload in INDIRECT_NON_MAIN_METADATA_MUTATIONS:
                    with self.subTest(
                        relative=relative,
                        family=label,
                        active=True,
                    ):
                        changed = dict(source_text)
                        changed[relative] += "\n" + payload + "\n"
                        _paper_verification._validate_manuscript_anonymity(changed)
                        with self.assertRaises(PaperLatexVerificationError) as caught:
                            _paper_verification._validate_iclr2027_venue_overlay(
                                changed
                            )
                        self.assertEqual(
                            caught.exception.reason_code,
                            "source_grammar_invalid",
                        )

                    with self.subTest(
                        relative=relative,
                        family=label,
                        active=False,
                    ):
                        comment_only = dict(source_text)
                        comment_only[relative] += "% " + payload + "\n"
                        _paper_verification._validate_iclr2027_venue_overlay(
                            comment_only
                        )
        finally:
            temporary.cleanup()

    def test_closed_statements_reject_contradictions_modals_and_remainder(self):
        temporary, root = _new_source_closure_repository()
        try:
            source_text = self._source_text(root)
            relative = SUBMISSION_STATEMENTS_RELATIVE
            statements = source_text[relative]
            self.assertEqual(
                _test_owned_lossless_active_tex_sha256(statements),
                CANONICAL_ACTIVE_STATEMENTS_SHA256,
            )
            for label, remainder in STATEMENT_CLOSED_CONTRACT_MUTATIONS:
                with self.subTest(label=label):
                    changed = dict(source_text)
                    changed[relative] = statements + "\n" + remainder + "\n"
                    with self.assertRaises(PaperLatexVerificationError) as caught:
                        _paper_verification._validate_iclr2027_venue_overlay(changed)
                    self.assertEqual(
                        caught.exception.reason_code,
                        "scientific_boundary_invalid",
                    )
            comment_only = dict(source_text)
            comment_only[relative] += "% Submission is authorized.\n"
            _paper_verification._validate_iclr2027_venue_overlay(comment_only)
        finally:
            temporary.cleanup()

    def test_receipt_source_independent_deserialization_is_deauthorized(self):
        receipt = _paper_verification._make_receipt(
            SOURCE_MANIFEST_SHA256,
            PRIMARY_MANIFEST_SHA256,
        )
        cases = (
            (PaperStaticReceipt.from_dict, receipt.to_dict()),
            (PaperStaticReceipt.from_json, receipt.canonical_json()),
        )
        for parser, value in cases:
            with self.subTest(parser=parser.__name__):
                with self.assertRaises(TypeError):
                    parser(value)

    def test_receipt_recomputed_manifest_substitution_rejects_supplied_root(self):
        receipt = _paper_verification._make_receipt(
            SOURCE_MANIFEST_SHA256,
            PRIMARY_MANIFEST_SHA256,
        )
        forged = receipt.to_dict()
        forged["source_manifest_sha256"] = "1" * 64
        forged["primary_source_manifest_sha256"] = "2" * 64
        forged["receipt_sha256"] = _receipt_hash(forged)
        forged_json = json.dumps(forged, sort_keys=True, separators=(",", ":"))
        temporary, root = _new_source_closure_repository()
        try:
            cases = (
                (PaperStaticReceipt.from_dict, forged),
                (PaperStaticReceipt.from_json, forged_json),
            )
            for parser, value in cases:
                with self.subTest(parser=parser.__name__):
                    try:
                        with self.assertRaises(PaperLatexVerificationError):
                            parser(value, repository_root=root)
                    except TypeError as error:
                        self.fail(f"explicit repository_root API missing: {error}")
        finally:
            temporary.cleanup()

    def test_receipt_round_trip_is_bound_to_the_same_verified_source_root(self):
        first_temporary, first_root = _new_source_closure_repository()
        second_temporary, second_root = _new_source_closure_repository()
        try:
            introduction = first_root / PAPER / "latex/sections/01_introduction.tex"
            introduction.write_bytes(
                introduction.read_bytes() + b"% permitted source-manifest-only drift\n"
            )
            receipt = _paper_verification._verify_static_paper_latex_at(first_root)
            self.assertNotEqual(
                receipt.source_manifest_sha256,
                SOURCE_MANIFEST_SHA256,
            )
            try:
                restored_dict = PaperStaticReceipt.from_dict(
                    receipt.to_dict(),
                    repository_root=first_root,
                )
                restored_json = PaperStaticReceipt.from_json(
                    receipt.canonical_json(),
                    repository_root=first_root,
                )
            except TypeError as error:
                self.fail(f"explicit repository_root API missing: {error}")
            self.assertEqual(restored_dict, receipt)
            self.assertEqual(restored_json, receipt)
            with self.assertRaises(PaperLatexVerificationError):
                PaperStaticReceipt.from_json(
                    receipt.canonical_json(),
                    repository_root=second_root,
                )
        finally:
            first_temporary.cleanup()
            second_temporary.cleanup()


class VenueOverlayContractTests(unittest.TestCase):
    def test_official_vendor_assets_are_exact_and_separate(self):
        self.assertEqual(len(VENDOR_SOURCE_IDENTITIES), 4)
        self.assertEqual(len(MANUSCRIPT_SOURCE_CLOSURE), 18)
        self.assertEqual(len(VENDOR_SOURCE_CLOSURE), 4)
        self.assertEqual(len(VENUE_SOURCE_CLOSURE), 22)
        self.assertEqual(len(SOURCE_CLOSURE), 22)
        self.assertIn(POLICY_PROVENANCE_RELATIVE, SOURCE_CLOSURE)
        self.assertEqual(len(ACTIVE_PROSE_IDENTITIES), 10)
        self.assertIn(
            POLICY_PROVENANCE_RELATIVE,
            tuple(path for path, _length, _digest in ACTIVE_PROSE_IDENTITIES),
        )
        self.assertEqual(
            tuple(
                sorted(VENUE_SOURCE_CLOSURE, key=lambda value: value.encode("utf-8"))
            ),
            VENUE_SOURCE_CLOSURE,
        )
        for relative, length, digest in VENDOR_SOURCE_IDENTITIES:
            path = REPOSITORY / PAPER / relative
            self.assertTrue(
                path.is_file(), f"official vendor asset is missing: {relative}"
            )
            raw = path.read_bytes()
            self.assertEqual(len(raw), length)
            self.assertEqual(hashlib.sha256(raw).hexdigest().upper(), digest)
            self.assertNotIn(
                relative,
                tuple(path for path, _length, _digest in ACTIVE_PROSE_IDENTITIES),
            )
        latex_root = REPOSITORY / PAPER / "latex"
        selected_vendor_names = {
            Path(relative).name
            for relative, _length, _digest in VENDOR_SOURCE_IDENTITIES
        }
        observed_vendor_names = {
            path.name
            for path in latex_root.iterdir()
            if path.is_file() and path.suffix.lower() in {".sty", ".bst", ".cls"}
        }
        self.assertEqual(observed_vendor_names, selected_vendor_names)

    def test_production_freezes_complete_official_archive_contract(self):
        latex_root = REPOSITORY / PAPER / "latex"
        for member in OMITTED_ARCHIVE_MEMBERS:
            self.assertFalse((latex_root / Path(member).name).exists(), member)
        expected = {
            "_OFFICIAL_STYLE_ARCHIVE_URL": OFFICIAL_STYLE_ARCHIVE_URL,
            "_OFFICIAL_STYLE_ARCHIVE_LENGTH": OFFICIAL_STYLE_ARCHIVE_LENGTH,
            "_OFFICIAL_STYLE_ARCHIVE_SHA256": OFFICIAL_STYLE_ARCHIVE_SHA256,
            "_VENDOR_SOURCE_IDENTITIES": VENDOR_SOURCE_IDENTITIES,
            "_OMITTED_ARCHIVE_MEMBERS": OMITTED_ARCHIVE_MEMBERS,
        }
        observed = {name: getattr(_paper_verification, name, None) for name in expected}
        self.assertEqual(observed, expected)

    def test_policy_registry_source_is_closed_active_and_owned_by_one_role(self):
        self.assertEqual(
            _paper_verification._MANUSCRIPT_SOURCE_PATHS,
            MANUSCRIPT_SOURCE_CLOSURE,
        )
        self.assertEqual(
            _paper_verification._SOURCE_PATHS,
            SOURCE_CLOSURE,
        )
        self.assertEqual(
            _paper_verification._ACTIVE_PROSE_PATHS,
            tuple(path for path, _length, _digest in ACTIVE_PROSE_IDENTITIES),
        )
        self.assertEqual(
            _paper_verification._APPENDIX_ENTRIES,
            {
                "appendix_analysis_protocol.tex": False,
                "appendix_claims.tex": False,
                "appendix_policy_provenance.tex": False,
                "appendix_reviewer_attacks.tex": False,
                "appendix_theory.tex": False,
            },
        )
        self.assertEqual(
            _paper_verification._EDITABLE_ROLES[POLICY_PROVENANCE_RELATIVE],
            (
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
        )
        self.assertEqual(_paper_verification._MAIN_INPUTS, SAP_EXPECTED_INPUTS)
        self.assertEqual(
            SAP_EXPECTED_INPUTS.index(POLICY_PROVENANCE_INPUT),
            SAP_EXPECTED_INPUTS.index(SAP_INPUT) + 1,
        )
        self.assertEqual(
            SAP_EXPECTED_INPUTS.index("appendices/appendix_claims"),
            SAP_EXPECTED_INPUTS.index(POLICY_PROVENANCE_INPUT) + 1,
        )

    def test_main_uses_official_anonymous_review_overlay(self):
        main = (REPOSITORY / PAPER / "latex/main.tex").read_text(encoding="utf-8")
        active = _strip_tex_comments(main)
        self.assertEqual(active.count(OFFICIAL_PACKAGE_INVOCATION), 1)
        self.assertEqual(active.count(OFFICIAL_BIBLIOGRAPHY_STYLE), 1)
        self.assertEqual(active.count(SUBMISSION_STATEMENTS_INPUT), 1)
        conclusion_input = r"\input{sections/09_conclusion}"
        bibliography_input = r"\bibliography{references}"
        appendix_input = r"\appendix"
        for literal in (
            conclusion_input,
            SUBMISSION_STATEMENTS_INPUT,
            bibliography_input,
            appendix_input,
        ):
            self.assertEqual(active.count(literal), 1)
        self.assertLess(
            active.index(conclusion_input), active.index(SUBMISSION_STATEMENTS_INPUT)
        )
        self.assertLess(
            active.index(SUBMISSION_STATEMENTS_INPUT), active.index(bibliography_input)
        )
        self.assertLess(active.index(bibliography_input), active.index(appendix_input))
        self.assertNotIn(r"\iclrfinalcopy", active)
        self.assertNotIn("{geometry}", active)
        self.assertNotIn(r"\bibliographystyle{plainnat}", active)

    def test_optioned_xcolor_precedes_official_style_and_late_reload_rejects(self):
        main = (REPOSITORY / PAPER / "latex/main.tex").read_text(encoding="utf-8")
        _assert_optioned_xcolor_precedes_official_style(main)
        xcolor_load = r"\usepackage[dvipsnames]{xcolor}"
        without_xcolor = main.replace(xcolor_load + "\n", "", 1)
        self.assertNotEqual(without_xcolor, main)
        conflicting = without_xcolor.replace(
            r"\usepackage{amsmath,amssymb,booktabs,microtype}",
            r"\usepackage{amsmath,amssymb,booktabs,microtype}" + "\n" + xcolor_load,
            1,
        )
        self.assertNotEqual(conflicting, without_xcolor)
        with self.assertRaisesRegex(
            AssertionError,
            "optioned xcolor load follows official style",
        ):
            _assert_optioned_xcolor_precedes_official_style(conflicting)

    def test_official_font_encoding_preamble_is_exact_and_mutation_closed(self):
        main = (REPOSITORY / PAPER / "latex/main.tex").read_text(encoding="utf-8")
        _assert_official_font_encoding_preamble(main)
        missing = main.replace(T1_FONT_ENCODING_INVOCATION + "\n", "", 1)
        late = missing.replace(
            OFFICIAL_PACKAGE_INVOCATION,
            OFFICIAL_PACKAGE_INVOCATION + "\n" + T1_FONT_ENCODING_INVOCATION,
            1,
        )
        wrong_encoding = main.replace(
            T1_FONT_ENCODING_INVOCATION,
            r"\usepackage[OT1]{fontenc}",
            1,
        )
        duplicate = main.replace(
            T1_FONT_ENCODING_INVOCATION,
            T1_FONT_ENCODING_INVOCATION + "\n" + T1_FONT_ENCODING_INVOCATION,
            1,
        )
        substitutions = (
            r"\usepackage{fontspec}",
            r"\setmainfont{Times New Roman}",
            r"\renewcommand{\rmdefault}{ptm}",
            r"\ifxetex\setmainfont{Times New Roman}\fi",
            r"\fontsize{8}{9}\selectfont",
            r"\textwidth=7in",
            r"\iclrfinalcopy",
        )
        mutations = [
            ("missing", missing),
            ("late", late),
            ("wrong encoding", wrong_encoding),
            ("duplicate", duplicate),
        ]
        mutations.extend(
            (
                label,
                main.replace(
                    r"\begin{document}",
                    payload + "\n" + r"\begin{document}",
                    1,
                ),
            )
            for label, payload in (
                ("fontspec", substitutions[0]),
                ("setmainfont", substitutions[1]),
                ("rmdefault", substitutions[2]),
                ("engine branch", substitutions[3]),
                ("font size", substitutions[4]),
                ("layout override", substitutions[5]),
                ("final mode", substitutions[6]),
            )
        )
        for label, changed in mutations:
            with self.subTest(label=label):
                self.assertNotEqual(changed, main)
                with self.assertRaises(AssertionError):
                    _assert_official_font_encoding_preamble(changed)

    def test_submission_statements_are_exact_and_precede_references(self):
        path = REPOSITORY / PAPER / SUBMISSION_STATEMENTS_RELATIVE
        self.assertTrue(path.is_file(), "submission-statements source is missing")
        text = path.read_text(encoding="utf-8")
        self.assertEqual(text.count(r"\section*{AI Use Statement}"), 1)
        self.assertEqual(text.count(r"\section*{Reproducibility Statement}"), 1)
        for span in (*AI_USE_REQUIRED_SPANS, *REPRODUCIBILITY_REQUIRED_SPANS):
            self.assertEqual(text.count(span), 1)


class Task5UnderfullScopeContractTests(unittest.TestCase):
    @staticmethod
    def _source_text() -> dict[str, str]:
        return {
            relative: _read(REPOSITORY, relative)
            for relative in MANUSCRIPT_SOURCE_CLOSURE
        }

    def test_exact_eight_local_underfull_wrappers_are_owned(self):
        source_text = self._source_text()
        self.assertEqual(len(UNDERFULL_SCOPE_CONTRACTS), 8)
        related = source_text["latex/sections/02_related_work.tex"]
        self.assertEqual(related.count(RELATED_WORK_STATUS_BLOCK), 1)
        self.assertEqual(
            related.count("workshop paper.\n" + RELATED_WORK_STATUS_BLOCK),
            1,
        )
        for contract in UNDERFULL_SCOPE_CONTRACTS:
            with self.subTest(scope=contract[0]):
                _assert_one_underfull_scope_wrapper(
                    source_text[contract[1]],
                    contract,
                )
        registry = source_text[POLICY_PROVENANCE_RELATIVE]
        self.assertEqual(
            registry.count("\\begin{enumerate}\n" + UNDERFULL_POLICY_REGISTRY_PREFIX),
            1,
        )

    def test_scoped_wrappers_are_byte_token_equivalent_and_mutation_closed(self):
        source_text = self._source_text()
        _assert_underfull_source_contract(source_text)
        _paper_verification._validate_underfull_layout_scopes(source_text)
        for contract in UNDERFULL_SCOPE_CONTRACTS:
            for mutation, changed_text in _underfull_scope_mutations(
                source_text[contract[1]],
                contract,
            ):
                with self.subTest(scope=contract[0], mutation=mutation):
                    changed = dict(source_text)
                    changed[contract[1]] = changed_text
                    with self.assertRaises(AssertionError):
                        _assert_underfull_source_contract(changed)
                    with self.assertRaises(PaperLatexVerificationError) as caught:
                        _paper_verification._validate_underfull_layout_scopes(changed)
                    self.assertEqual(
                        caught.exception.reason_code,
                        "source_grammar_invalid",
                    )
        registry = source_text[POLICY_PROVENANCE_RELATIVE]
        for mutation, changed_text in _policy_registry_prefix_mutations(registry):
            with self.subTest(scope="policy registry list", mutation=mutation):
                changed = dict(source_text)
                changed[POLICY_PROVENANCE_RELATIVE] = changed_text
                with self.assertRaises(AssertionError):
                    _assert_underfull_source_contract(changed)
                with self.assertRaises(PaperLatexVerificationError) as caught:
                    _paper_verification._validate_underfull_layout_scopes(changed)
                self.assertEqual(
                    caught.exception.reason_code,
                    "source_grammar_invalid",
                )

    def test_global_warning_masking_and_layout_escapes_are_rejected(self):
        source_text = self._source_text()
        _assert_no_underfull_layout_escape(source_text)
        target = "latex/sections/01_introduction.tex"
        for label, payload in UNDERFULL_LAYOUT_ESCAPE_MUTATIONS:
            with self.subTest(label=label):
                changed = dict(source_text)
                changed[target] += "\n" + payload + "\n"
                with self.assertRaises(AssertionError):
                    _assert_no_underfull_layout_escape(changed)
                with self.assertRaises(PaperLatexVerificationError) as caught:
                    _paper_verification._validate_underfull_layout_scopes(changed)
                self.assertEqual(
                    caught.exception.reason_code,
                    "source_grammar_invalid",
                )

    def test_all_eleven_nonowners_reject_an_unreviewed_scope(self):
        source_text = self._source_text()
        nonowners = tuple(
            relative
            for relative, count in UNDERFULL_TEX_RAGGEDRIGHT_COUNTS.items()
            if count == 0
        )
        self.assertEqual(
            nonowners,
            (
                "latex/appendices/appendix_claims.tex",
                "latex/appendices/appendix_reviewer_attacks.tex",
                "latex/appendices/appendix_theory.tex",
                "latex/sections/01_introduction.tex",
                "latex/sections/02_related_work.tex",
                "latex/sections/03_problem_formulation.tex",
                "latex/sections/04_method.tex",
                "latex/sections/07_results.tex",
                "latex/sections/08_limitations.tex",
                "latex/sections/09_conclusion.tex",
                "latex/sections/10_submission_statements.tex",
            ),
        )
        unreviewed_scope = "\n{\\raggedright unreviewed scope\\par}\n"
        for relative in nonowners:
            with self.subTest(relative=relative):
                changed = dict(source_text)
                changed[relative] += unreviewed_scope
                oracle_rejected = False
                try:
                    _assert_underfull_source_contract(changed)
                except AssertionError:
                    oracle_rejected = True
                production_reason = None
                try:
                    _paper_verification._validate_underfull_layout_scopes(changed)
                except PaperLatexVerificationError as error:
                    production_reason = error.reason_code
                self.assertEqual(
                    (oracle_rejected, production_reason),
                    (True, "source_grammar_invalid"),
                )


class VenueOverlayAdversarialMutationTests(unittest.TestCase):
    @contextlib.contextmanager
    def _passing_copy(self):
        temporary, root = _new_source_closure_repository()
        try:
            baseline = _paper_verification._verify_static_paper_latex_at(root)
            self.assertEqual(
                baseline.status,
                "literature_corrected_static_ready",
            )
            yield root
        finally:
            temporary.cleanup()

    @staticmethod
    def _move_before(text: str, literal: str, anchor: str) -> str:
        if text.count(literal) != 1 or text.count(anchor) != 1:
            raise AssertionError("reorder fixture is not unique")
        without = text.replace(literal, "", 1)
        return without.replace(anchor, literal + "\n" + anchor, 1)

    @staticmethod
    def _move_after(text: str, literal: str, anchor: str) -> str:
        if text.count(literal) != 1 or text.count(anchor) != 1:
            raise AssertionError("reorder fixture is not unique")
        without = text.replace(literal, "", 1)
        return without.replace(anchor, anchor + "\n" + literal, 1)

    def _assert_main_semantic_rejection(self, transform) -> None:
        with self._passing_copy() as root:
            path = root / PAPER / "latex/main.tex"
            original = path.read_text(encoding="utf-8")
            changed = transform(original)
            self.assertNotEqual(changed, original)
            path.write_text(changed, encoding="utf-8", newline="\n")
            pins = dict(_paper_verification._PINNED_SOURCE_SHA256)
            pins["latex/main.tex"] = (
                hashlib.sha256(changed.encode("utf-8")).hexdigest().upper()
            )
            with mock.patch.object(
                _paper_verification,
                "_PINNED_SOURCE_SHA256",
                pins,
            ):
                with self.assertRaises(PaperLatexVerificationError) as caught:
                    _paper_verification._verify_static_paper_latex_at(root)
            self.assertEqual(caught.exception.reason_code, "source_grammar_invalid")

    def _assert_full_root_text_rejection(
        self,
        relative: str,
        transform,
        expected_code: str,
    ) -> None:
        with self._passing_copy() as root:
            path = root / PAPER / relative
            original = path.read_text(encoding="utf-8")
            changed = transform(original)
            self.assertNotEqual(changed, original)
            path.write_text(changed, encoding="utf-8", newline="\n")
            with self.assertRaises(PaperLatexVerificationError) as caught:
                _paper_verification._verify_static_paper_latex_at(root)
            self.assertEqual(caught.exception.reason_code, expected_code)

    def _assert_direct_dict_rejection(
        self,
        root: Path,
        relative: str,
        transform,
        expected_code: str,
    ) -> None:
        source_text = {path: _read(root, path) for path in MANUSCRIPT_SOURCE_CLOSURE}
        source_bytes = {
            path: (root / PAPER / path).read_bytes()
            for path in MANUSCRIPT_SOURCE_CLOSURE
        }
        original = source_text[relative]
        changed = transform(original)
        self.assertNotEqual(changed, original)
        source_text[relative] = changed
        source_bytes[relative] = changed.encode("utf-8")
        _identities, active_digest = _independent_active_prose_manifest(source_text)
        with mock.patch.object(
            _paper_verification,
            "_ACTIVE_PROSE_MANIFEST_SHA256",
            active_digest.lower(),
        ):
            with self.assertRaises(PaperLatexVerificationError) as caught:
                _paper_verification._validate_tex_bibliography_and_science(
                    source_text,
                    source_bytes,
                )
        self.assertEqual(caught.exception.reason_code, expected_code)

    @staticmethod
    def _statement_semantic_cases():
        cases = [
            (
                label,
                lambda text, old=old, new=new: text.replace(old, new, 1),
            )
            for label, old, new in STATEMENT_TRUTH_MUTATIONS
        ]
        pending_boundary = (
            "Submission remains blocked until all authors review the\nAI-assisted "
            "text, claims, code, citations, and artifacts and accept\nresponsibility "
            "for the final content."
        )
        cases.append(
            (
                "pending all-author review boundary removed",
                lambda text: text.replace(pending_boundary, "", 1),
            )
        )
        for heading in (
            r"\section*{AI Use Statement}",
            r"\section*{Reproducibility Statement}",
        ):
            cases.append(
                (
                    f"duplicate {heading}",
                    lambda text, heading=heading: text + heading + "\n",
                )
            )
        for phrase in VENUE_FORBIDDEN_POSITIVE_PHRASES:
            cases.append(
                (
                    f"forbidden positive: {phrase}",
                    lambda text, phrase=phrase: text + phrase + "\n",
                )
            )
        return tuple(cases)

    def test_each_vendor_rejects_delete_change_rename_and_extra_sibling(self):
        for relative, _length, _digest in VENDOR_SOURCE_IDENTITIES:
            for attack in ("delete", "one-byte change", "rename", "extra sibling"):
                with self.subTest(relative=relative, attack=attack):
                    with self._passing_copy() as root:
                        path = root / PAPER / relative
                        if attack == "delete":
                            path.unlink()
                            expected_code = "source_identity_invalid"
                        elif attack == "one-byte change":
                            data = path.read_bytes()
                            path.write_bytes(bytes((data[0] ^ 1,)) + data[1:])
                            expected_code = "source_bytes_invalid"
                        elif attack == "rename":
                            path.rename(path.with_name("renamed-" + path.name))
                            expected_code = "source_identity_invalid"
                        else:
                            path.with_name("extra-" + path.name).write_bytes(
                                path.read_bytes()
                            )
                            expected_code = "source_identity_invalid"
                        with self.assertRaises(PaperLatexVerificationError) as caught:
                            _paper_verification._verify_static_paper_latex_at(root)
                        self.assertEqual(caught.exception.reason_code, expected_code)

    def test_each_omitted_official_sample_rejects_as_an_extra(self):
        for member in OMITTED_ARCHIVE_MEMBERS:
            with self.subTest(member=member):
                with self._passing_copy() as root:
                    extra = root / PAPER / "latex" / Path(member).name
                    extra.write_bytes(b"omitted official sample\n")
                    with self.assertRaises(PaperLatexVerificationError) as caught:
                        _paper_verification._verify_static_paper_latex_at(root)
                    self.assertEqual(
                        caught.exception.reason_code,
                        "source_identity_invalid",
                    )

    def test_main_overlay_injections_reach_the_venue_predicate_and_reject(self):
        begin_document = r"\begin{document}"
        insertions = (
            ("final copy", r"\iclrfinalcopy"),
            ("geometry package", r"\usepackage[margin=1in]{geometry}"),
            ("geometry command", r"\geometry{margin=1in}"),
            ("plainnat style", r"\bibliographystyle{plainnat}"),
            ("thanks", r"\thanks{funding}"),
            ("text width", r"\textwidth=7in"),
        )
        for label, insertion in insertions:
            with self.subTest(label=label):
                self._assert_main_semantic_rejection(
                    lambda text, insertion=insertion: text.replace(
                        begin_document,
                        insertion + "\n" + begin_document,
                        1,
                    )
                )
        with self.subTest(label="named author"):
            self._assert_main_semantic_rejection(
                lambda text: text.replace(
                    r"\author{Anonymous Authors}",
                    r"\author{Named Author}",
                    1,
                )
            )

    def test_main_overlay_deletions_and_reorders_reach_production_and_reject(self):
        package = OFFICIAL_PACKAGE_INVOCATION
        statement = SUBMISSION_STATEMENTS_INPUT
        bibliography = r"\bibliography{references}"
        appendix = r"\appendix"
        appendix_inputs = (
            r"\input{appendices/appendix_theory}",
            r"\input{appendices/appendix_analysis_protocol}",
            r"\input{appendices/appendix_policy_provenance}",
            r"\input{appendices/appendix_claims}",
            r"\input{appendices/appendix_reviewer_attacks}",
        )
        for literal in (package, statement, bibliography, appendix, *appendix_inputs):
            with self.subTest(attack="delete", literal=literal):
                self._assert_main_semantic_rejection(
                    lambda text, literal=literal: text.replace(literal, "", 1)
                )
        reorder_cases = (
            (
                "official package before documentclass",
                lambda text: self._move_before(
                    text,
                    package,
                    r"\documentclass{article}",
                ),
            ),
            (
                "statement after bibliography",
                lambda text: self._move_after(text, statement, bibliography),
            ),
            (
                "bibliography after appendix",
                lambda text: self._move_after(text, bibliography, appendix),
            ),
            (
                "appendix before bibliography",
                lambda text: self._move_before(text, appendix, bibliography),
            ),
            *(
                (
                    f"{literal} before appendix",
                    lambda text, literal=literal: self._move_before(
                        text,
                        literal,
                        appendix,
                    ),
                )
                for literal in appendix_inputs
            ),
        )
        for label, transform in reorder_cases:
            with self.subTest(attack="reorder", label=label):
                self._assert_main_semantic_rejection(transform)

    def test_statement_semantics_reject_direct_dict_mutations_beyond_raw_pins(self):
        with self._passing_copy() as root:
            for label, transform in self._statement_semantic_cases():
                with self.subTest(label=label):
                    self._assert_direct_dict_rejection(
                        root,
                        SUBMISSION_STATEMENTS_RELATIVE,
                        transform,
                        "scientific_boundary_invalid",
                    )
            with self.subTest(label="statement relocated after references"):
                self._assert_direct_dict_rejection(
                    root,
                    "latex/main.tex",
                    lambda text: self._move_after(
                        text,
                        SUBMISSION_STATEMENTS_INPUT,
                        r"\bibliography{references}",
                    ),
                    "source_grammar_invalid",
                )

    def test_statement_semantics_reject_at_the_full_root_boundary(self):
        for label, transform in self._statement_semantic_cases():
            with self.subTest(label=label):
                self._assert_full_root_text_rejection(
                    SUBMISSION_STATEMENTS_RELATIVE,
                    transform,
                    "source_bytes_invalid",
                )
        with self.subTest(label="statement relocated after references"):
            self._assert_full_root_text_rejection(
                "latex/main.tex",
                lambda text: self._move_after(
                    text,
                    SUBMISSION_STATEMENTS_INPUT,
                    r"\bibliography{references}",
                ),
                "source_bytes_invalid",
            )

    def test_counted_manuscript_vendor_scanner_and_manifest_separation(self):
        with self._passing_copy() as root:
            raw_by_relative = {
                relative: (root / PAPER / relative).read_bytes()
                for relative in SOURCE_CLOSURE
            }
            digest_to_relative = {
                hashlib.sha256(data).hexdigest(): relative
                for relative, data in raw_by_relative.items()
            }
            text_digest_to_relative = {
                hashlib.sha256(_read(root, relative).encode("utf-8"))
                .hexdigest()
                .upper(): relative
                for relative in MANUSCRIPT_SOURCE_CLOSURE
            }
            text_digest_to_relative.update(
                _policy_registry_scanner_fragment_labels(
                    _read(root, POLICY_PROVENANCE_RELATIVE)
                )
            )
            decoded = []
            normalized = []
            citation_scanned = []
            science_calls = []
            reads = []
            original_validated_text = _paper_verification._validated_text
            original_normalize_active = _paper_verification._normalize_active
            original_extract_arguments = _paper_verification._extract_literal_arguments
            original_science_validator = (
                _paper_verification._validate_tex_bibliography_and_science
            )

            def validated_text_spy(data, *, primary_manifest=False):
                decoded.append(
                    "literature_primary_source_manifest.md"
                    if primary_manifest
                    else digest_to_relative[hashlib.sha256(data).hexdigest()]
                )
                return original_validated_text(
                    data,
                    primary_manifest=primary_manifest,
                )

            def normalize_active_spy(text, relative):
                normalized.append(relative)
                return original_normalize_active(text, relative)

            def extract_arguments_spy(text, commands):
                citation_scanned.append(
                    _citation_scan_call_label(
                        text,
                        text_digest_to_relative,
                    )
                )
                return original_extract_arguments(text, commands)

            def science_validator_spy(source_text, source_bytes):
                science_calls.append(
                    (tuple(sorted(source_text)), tuple(sorted(source_bytes)))
                )
                return original_science_validator(source_text, source_bytes)

            with (
                mock.patch.object(
                    _paper_verification,
                    "_validated_text",
                    side_effect=validated_text_spy,
                ),
                mock.patch.object(
                    _paper_verification,
                    "_normalize_active",
                    side_effect=normalize_active_spy,
                ),
                mock.patch.object(
                    _paper_verification,
                    "_extract_literal_arguments",
                    side_effect=extract_arguments_spy,
                ),
                mock.patch.object(
                    _paper_verification,
                    "_validate_tex_bibliography_and_science",
                    side_effect=science_validator_spy,
                ),
            ):
                receipt = _paper_verification._verify_static_paper_latex_at(
                    root,
                    read_observer=reads.append,
                )

            decoded_manuscripts = tuple(
                relative
                for relative in decoded
                if relative in MANUSCRIPT_SOURCE_CLOSURE
            )
            self.assertEqual(len(decoded_manuscripts), 18)
            self.assertEqual(set(decoded_manuscripts), set(MANUSCRIPT_SOURCE_CLOSURE))
            self.assertEqual(decoded.count("literature_primary_source_manifest.md"), 1)
            self.assertTrue(set(VENDOR_SOURCE_CLOSURE).isdisjoint(decoded))

            self.assertEqual(len(normalized), 53)
            for relative in MANUSCRIPT_SOURCE_CLOSURE:
                self.assertEqual(
                    normalized.count(relative),
                    2 if relative == "latex/references.bib" else 3,
                )
            self.assertTrue(set(VENDOR_SOURCE_CLOSURE).isdisjoint(normalized))

            _assert_exact_citation_scan_calls(tuple(citation_scanned))
            self.assertEqual(len(citation_scanned), 41)
            policy_fragment_labels = tuple(
                _policy_registry_scanner_fragment_labels(
                    _read(root, POLICY_PROVENANCE_RELATIVE)
                ).values()
            )
            self.assertEqual(len(policy_fragment_labels), 22)
            duplicated_fragment_calls = list(citation_scanned)
            omitted_fragment_index = duplicated_fragment_calls.index(
                policy_fragment_labels[1]
            )
            duplicated_fragment_calls[omitted_fragment_index] = policy_fragment_labels[
                0
            ]
            with self.assertRaisesRegex(
                AssertionError,
                "citation/science scan call Counter drift",
            ):
                _assert_exact_citation_scan_calls(tuple(duplicated_fragment_calls))
            self.assertTrue(set(VENDOR_SOURCE_CLOSURE).isdisjoint(citation_scanned))
            vendor_like_call = _citation_scan_call_label(
                r"\ProvidesPackage{vendor_like}\RequirePackage{opaque}",
                text_digest_to_relative,
            )
            self.assertRegex(vendor_like_call, r"^UNKNOWN:[0-9A-F]{64}$")
            with self.assertRaisesRegex(
                AssertionError,
                "unknown citation/science scan call",
            ):
                _assert_exact_citation_scan_calls((*citation_scanned, vendor_like_call))
            self.assertEqual(len(science_calls), 1)
            science_text_paths, science_byte_paths = science_calls[0]
            self.assertEqual(set(science_text_paths), set(MANUSCRIPT_SOURCE_CLOSURE))
            self.assertEqual(set(science_byte_paths), set(SOURCE_CLOSURE))
            self.assertTrue(set(VENDOR_SOURCE_CLOSURE).isdisjoint(science_text_paths))

            observed_reads = {
                path.relative_to(root / PAPER).as_posix() for path in reads
            }
            self.assertTrue(set(VENDOR_SOURCE_CLOSURE) <= observed_reads)
            manifest_paths = {
                line.split("\t", 1)[0] for line in SOURCE_MANIFEST_TEXT.splitlines()
            }
            self.assertTrue(set(VENDOR_SOURCE_CLOSURE) <= manifest_paths)
            self.assertEqual(receipt.source_manifest_sha256, SOURCE_MANIFEST_SHA256)


class PaperStaticReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary, cls.repository_root = _new_source_closure_repository()
        cls.receipt = _paper_verification._make_receipt(
            SOURCE_MANIFEST_SHA256,
            PRIMARY_MANIFEST_SHA256,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_public_api_and_receipt_are_exactly_sealed(self):
        self.assertEqual(
            _paper_verification.__all__,
            (
                "PaperLatexVerificationError",
                "PaperStaticReceipt",
                "verify_static_paper_latex",
            ),
        )
        self.assertEqual(
            tuple(
                field.name
                for field in __import__("dataclasses").fields(PaperStaticReceipt)
            ),
            RECEIPT_KEYS,
        )
        self.assertFalse(hasattr(self.receipt, "__dict__"))
        with self.assertRaises((AttributeError, TypeError)):
            self.receipt.status = "changed"
        with self.assertRaises(TypeError):
            PaperStaticReceipt()
        with self.assertRaises(TypeError):

            class _ReceiptSubclass(PaperStaticReceipt):
                pass

    def test_verified_receipt_has_exact_constants_and_independent_hashes(self):
        payload = self.receipt.to_dict()
        self.assertEqual(tuple(payload), RECEIPT_KEYS)
        self.assertEqual(
            payload["schema_version"], "ace.iclr2027.paper_latex_static.v1"
        )
        self.assertEqual(payload["status"], "literature_corrected_static_ready")
        self.assertEqual(payload["source_manifest_sha256"], SOURCE_MANIFEST_SHA256)
        self.assertEqual(payload["source_file_count"], 22)
        self.assertEqual(
            payload["primary_source_manifest_sha256"], PRIMARY_MANIFEST_SHA256
        )
        self.assertEqual(payload["primary_source_keys"], list(PRIMARY_SOURCE_KEYS))
        self.assertEqual(payload["primary_source_count"], 10)
        self.assertEqual(payload["claim_count"], 23)
        self.assertEqual(payload["blocked_slot_count"], 9)
        self.assertEqual(payload["policy_count"], 22)
        self.assertEqual(payload["attack_count"], 24)
        self.assertEqual(
            payload["citation_authority_status"], "blocked_pending_authenticated_roster"
        )
        self.assertIs(payload["pdf_compile_verified"], False)
        self.assertEqual(payload["empirical_status"], "no_go_needs_context")
        self.assertEqual(payload["receipt_sha256"], _receipt_hash(payload))
        self.assertEqual(payload["receipt_sha256"], EXPECTED_RECEIPT_SHA256)
        self.assertEqual(self.receipt.canonical_json(), EXPECTED_RECEIPT_JSON)
        for key in (
            "source_manifest_sha256",
            "primary_source_manifest_sha256",
            "receipt_sha256",
        ):
            self.assertRegex(payload[key], r"^[0-9a-f]{64}$")

    def test_direct_dict_and_json_round_trips_restore_an_exact_tuple(self):
        payload = self.receipt.to_dict()
        restored_dict = PaperStaticReceipt.from_dict(
            payload,
            repository_root=self.repository_root,
        )
        restored_json = PaperStaticReceipt.from_json(
            self.receipt.canonical_json(),
            repository_root=self.repository_root,
        )
        self.assertEqual(restored_dict, self.receipt)
        self.assertEqual(restored_json, self.receipt)
        self.assertIs(type(restored_dict.primary_source_keys), tuple)
        self.assertEqual(restored_json.canonical_json(), self.receipt.canonical_json())

    def test_dict_parser_rejects_shape_type_constant_and_integrity_forgery(self):
        valid = self.receipt.to_dict()
        mutations = []
        for key in RECEIPT_KEYS:
            mutations.append((f"missing {key}", lambda data, key=key: data.pop(key)))
        mutations.extend(
            (
                ("extra key", lambda data: data.update(extra=True)),
                (
                    "tuple at JSON boundary",
                    lambda data: data.update(
                        primary_source_keys=tuple(PRIMARY_SOURCE_KEYS)
                    ),
                ),
                (
                    "digest uppercase",
                    lambda data: data.update(
                        source_manifest_sha256=SOURCE_MANIFEST_SHA256.upper()
                    ),
                ),
                (
                    "digest nonhex",
                    lambda data: data.update(primary_source_manifest_sha256="g" * 64),
                ),
                ("float count", lambda data: data.update(source_file_count=22.0)),
                ("boolean count", lambda data: data.update(source_file_count=True)),
                ("negative count", lambda data: data.update(source_file_count=-1)),
                ("wrong schema", lambda data: data.update(schema_version="wrong")),
                (
                    "positive empirical",
                    lambda data: data.update(empirical_status="complete"),
                ),
                ("positive PDF", lambda data: data.update(pdf_compile_verified=True)),
                ("status forgery", lambda data: data.update(status="ready")),
                ("count forgery", lambda data: data.update(policy_count=23)),
                (
                    "list member type",
                    lambda data: data.update(
                        primary_source_keys=[*PRIMARY_SOURCE_KEYS[:-1], 3]
                    ),
                ),
                (
                    "self hash forgery",
                    lambda data: data.update(receipt_sha256="0" * 64),
                ),
            )
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                payload = dict(valid)
                payload["primary_source_keys"] = list(valid["primary_source_keys"])
                mutate(payload)
                if all(key in payload for key in RECEIPT_KEYS) and label not in {
                    "self hash forgery"
                }:
                    payload["receipt_sha256"] = _receipt_hash(payload)
                with self.assertRaises(PaperLatexVerificationError):
                    PaperStaticReceipt.from_dict(
                        payload,
                        repository_root=self.repository_root,
                    )

    def test_json_parser_rejects_duplicate_noncanonical_float_nan_and_negative_zero(
        self,
    ):
        canonical = self.receipt.canonical_json()
        attacks = (
            canonical.replace("{", '{"status":"literature_corrected_static_ready",', 1),
            canonical.replace(":", ": ", 1),
            canonical.replace('"source_file_count":22', '"source_file_count":22.0'),
            canonical.replace('"source_file_count":22', '"source_file_count":NaN'),
            canonical.replace('"source_file_count":22', '"source_file_count":-0'),
        )
        for attack in attacks:
            with self.subTest(attack=attack[:80]):
                with self.assertRaises(PaperLatexVerificationError):
                    PaperStaticReceipt.from_json(
                        attack,
                        repository_root=self.repository_root,
                    )

    def test_low_level_receipt_forgery_cannot_serialize_or_cross_json_boundary(self):
        attacks = (
            ("status", "forged_ready"),
            ("pdf_compile_verified", True),
            ("empirical_status", "complete"),
            ("policy_count", 23),
        )
        for key, value in attacks:
            with self.subTest(key=key):
                payload = self.receipt.to_dict()
                payload[key] = value
                payload["receipt_sha256"] = _receipt_hash(payload)
                forged = object.__new__(PaperStaticReceipt)
                for field in RECEIPT_KEYS:
                    stored = (
                        tuple(payload[field])
                        if field == "primary_source_keys"
                        else payload[field]
                    )
                    object.__setattr__(forged, field, stored)
                with self.assertRaises(PaperLatexVerificationError):
                    forged.to_dict()
                with self.assertRaises(PaperLatexVerificationError):
                    forged.canonical_json()
                forged_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
                with self.assertRaises(PaperLatexVerificationError):
                    PaperStaticReceipt.from_json(
                        forged_json,
                        repository_root=self.repository_root,
                    )


class StaticPaperVerifierTests(unittest.TestCase):
    def _temporary_repository(self):
        return _new_source_closure_repository()

    def _mutate(self, relative: str, transform, expected_code: str) -> None:
        temporary, root = self._temporary_repository()
        try:
            baseline = _paper_verification._verify_static_paper_latex_at(root)
            self.assertEqual(baseline.status, "literature_corrected_static_ready")
            path = root / PAPER / relative
            original = path.read_bytes()
            changed = transform(original)
            self.assertNotEqual(changed, original)
            path.write_bytes(changed)
            changed_tex = (
                {relative: changed.decode("utf-8")}
                if expected_code == "scientific_boundary_invalid"
                and relative in CANONICAL_ACTIVE_MANUSCRIPT_TEX_SHA256
                else {}
            )
            with _patch_active_tex_identities_for_downstream(changed_tex):
                with self.assertRaises(PaperLatexVerificationError) as caught:
                    _paper_verification._verify_static_paper_latex_at(root)
            self.assertEqual(caught.exception.reason_code, expected_code)
        finally:
            temporary.cleanup()

    def test_exact_source_manifest_and_metadata_only_authority_siblings(self):
        reads = []
        names = []
        receipt = _paper_verification._verify_static_paper_latex_at(
            REPOSITORY,
            read_observer=reads.append,
            name_observer=lambda directory, name: names.append((directory, name)),
        )
        self.assertEqual(receipt.source_manifest_sha256, SOURCE_MANIFEST_SHA256)
        self.assertEqual(
            receipt.primary_source_manifest_sha256, PRIMARY_MANIFEST_SHA256
        )
        self.assertEqual(
            {path.relative_to(REPOSITORY / PAPER).as_posix() for path in reads},
            {*SOURCE_CLOSURE, "literature_primary_source_manifest.md"},
        )
        self.assertTrue(all(path.is_relative_to(REPOSITORY / PAPER) for path in reads))
        self.assertTrue(
            all(
                not path.name.endswith(".md") or path.name not in AUTHORITY_SIBLINGS
                for path in reads
            )
        )
        self.assertNotIn("path_b_external_handoff.md", {path.name for path in reads})
        root_names = {
            name for directory, name in names if directory == REPOSITORY / PAPER
        }
        self.assertEqual(
            root_names,
            {"latex", "literature_primary_source_manifest.md", *AUTHORITY_SIBLINGS},
        )

    def test_manifest_preimage_is_byte_sorted_and_valid_edits_cannot_reuse_stale_digest(
        self,
    ):
        paths = tuple(path for path, _length, _digest in SOURCE_IDENTITIES)
        self.assertEqual(
            paths, tuple(sorted(paths, key=lambda path: path.encode("utf-8")))
        )
        self.assertEqual(
            hashlib.sha256(SOURCE_MANIFEST_TEXT.encode("utf-8")).hexdigest(),
            SOURCE_MANIFEST_SHA256,
        )
        temporary, root = self._temporary_repository()
        try:
            baseline = _paper_verification._verify_static_paper_latex_at(root)
            introduction = root / PAPER / "latex/sections/01_introduction.tex"
            introduction.write_bytes(
                introduction.read_bytes() + b"% valid digest-change comment\n"
            )
            changed = _paper_verification._verify_static_paper_latex_at(root)
            self.assertNotEqual(
                changed.source_manifest_sha256, baseline.source_manifest_sha256
            )
            independent_lines = []
            for relative in paths:
                data = (root / PAPER / relative).read_bytes()
                independent_lines.append(
                    f"{relative}\t{len(data)}\t{hashlib.sha256(data).hexdigest().upper()}\n"
                )
            expected_changed = hashlib.sha256(
                "".join(independent_lines).encode("utf-8")
            ).hexdigest()
            self.assertEqual(changed.source_manifest_sha256, expected_changed)
            stale = changed.to_dict()
            stale["source_manifest_sha256"] = baseline.source_manifest_sha256
            with self.assertRaises(PaperLatexVerificationError):
                PaperStaticReceipt.from_dict(
                    stale,
                    repository_root=root,
                )
        finally:
            temporary.cleanup()

    def test_independent_active_prose_manifest_and_direct_dict_boundary(self):
        source_text = {
            relative: _read(REPOSITORY, relative)
            for relative in MANUSCRIPT_SOURCE_CLOSURE
        }
        source_bytes = {
            relative: (REPOSITORY / PAPER / relative).read_bytes()
            for relative in MANUSCRIPT_SOURCE_CLOSURE
        }
        identities, manifest_sha256 = _independent_active_prose_manifest(source_text)
        self.assertEqual(identities, ACTIVE_PROSE_IDENTITIES)
        self.assertEqual(manifest_sha256, ACTIVE_PROSE_MANIFEST_SHA256)
        _paper_verification._validate_tex_bibliography_and_science(
            source_text,
            source_bytes,
        )

        comment_only = dict(source_text)
        comment_only["latex/sections/01_introduction.tex"] += (
            "% active prose digest must ignore this comment\n"
        )
        self.assertEqual(
            _independent_active_prose_manifest(comment_only),
            (ACTIVE_PROSE_IDENTITIES, ACTIVE_PROSE_MANIFEST_SHA256),
        )
        _paper_verification._validate_tex_bibliography_and_science(
            comment_only,
            source_bytes,
        )

        format_only = dict(source_text)
        format_only["latex/sections/02_related_work.tex"] = format_only[
            "latex/sections/02_related_work.tex"
        ].replace(
            r"\citep{zhang2026icore}",
            "\\citep{\nzhang2026icore\n}",
            1,
        )
        self.assertEqual(
            _independent_active_prose_manifest(format_only),
            (ACTIVE_PROSE_IDENTITIES, ACTIVE_PROSE_MANIFEST_SHA256),
        )
        with self.assertRaises(PaperLatexVerificationError) as caught:
            _paper_verification._validate_tex_bibliography_and_science(
                format_only,
                source_bytes,
            )
        self.assertEqual(caught.exception.reason_code, "source_grammar_invalid")

        active_changes = (
            (
                "latex/sections/01_introduction.tex",
                "The candidate's catalog entry resolves to arXiv record 2601.0042.",
            ),
            (
                "latex/sections/02_related_work.tex",
                "A bibliographic coordinate maps the candidate to archive record 2601.0042.",
            ),
            (
                "latex/sections/03_problem_formulation.tex",
                "Researchers may view the design as transformative.",
            ),
            (
                "latex/README.md",
                "A watershed advance emerges from this scaffold.",
            ),
        )
        for relative, addition in active_changes:
            with self.subTest(relative=relative, addition=addition):
                changed = dict(source_text)
                changed[relative] += addition + "\n"
                changed_identities, changed_digest = _independent_active_prose_manifest(
                    changed
                )
                self.assertNotEqual(changed_identities, ACTIVE_PROSE_IDENTITIES)
                self.assertNotEqual(changed_digest, ACTIVE_PROSE_MANIFEST_SHA256)
                changed_tex = (
                    {relative: changed[relative]} if relative.endswith(".tex") else {}
                )
                with _patch_active_tex_identities_for_downstream(changed_tex):
                    with self.assertRaises(PaperLatexVerificationError) as caught:
                        _paper_verification._validate_tex_bibliography_and_science(
                            changed,
                            source_bytes,
                        )
                self.assertEqual(
                    caught.exception.reason_code,
                    "scientific_boundary_invalid",
                )

        grammar_first = dict(source_text)
        grammar_first["latex/sections/04_method.tex"] += (
            "Unpinned active drift.\\unknown{still grammar first}\n"
        )
        with self.assertRaises(PaperLatexVerificationError) as caught:
            _paper_verification._validate_tex_bibliography_and_science(
                grammar_first,
                source_bytes,
            )
        self.assertEqual(caught.exception.reason_code, "source_grammar_invalid")

    def test_active_prose_pin_rejects_previously_accepted_full_root_changes(self):
        active_changes = (
            (
                "latex/sections/01_introduction.tex",
                "The candidate's catalog entry resolves to arXiv record 2601.0042.",
            ),
            (
                "latex/sections/02_related_work.tex",
                "A bibliographic coordinate maps the candidate to archive record 2601.0042.",
            ),
            (
                "latex/sections/03_problem_formulation.tex",
                "Researchers may view the design as transformative.",
            ),
            (
                "latex/README.md",
                "A watershed advance emerges from this scaffold.",
            ),
        )
        for relative, addition in active_changes:
            with self.subTest(relative=relative, addition=addition):
                self._mutate(
                    relative,
                    lambda data, addition=addition: data
                    + (addition + "\n").encode("utf-8"),
                    "scientific_boundary_invalid",
                )

    def test_closure_rejects_missing_extra_type_symlink_hardlink_and_escape(self):
        cases = []
        cases.append(
            ("missing", lambda root: (root / PAPER / "latex/README.md").unlink())
        )
        cases.append(
            (
                "extra",
                lambda root: (root / PAPER / "latex/extra.tex").write_text(
                    "extra\n", encoding="utf-8"
                ),
            )
        )
        cases.append(
            (
                "type drift",
                lambda root: (
                    (root / PAPER / "claim_evidence_matrix.md").unlink(),
                    (root / PAPER / "claim_evidence_matrix.md").mkdir(),
                ),
            )
        )
        for label, mutate in cases:
            with self.subTest(label=label):
                temporary, root = self._temporary_repository()
                try:
                    _paper_verification._verify_static_paper_latex_at(root)
                    mutate(root)
                    with self.assertRaises(PaperLatexVerificationError) as caught:
                        _paper_verification._verify_static_paper_latex_at(root)
                    self.assertEqual(
                        caught.exception.reason_code, "source_identity_invalid"
                    )
                finally:
                    temporary.cleanup()

        temporary, root = self._temporary_repository()
        try:
            _paper_verification._verify_static_paper_latex_at(root)
            victim = root / PAPER / "latex/README.md"
            outside = root / "outside.md"
            outside.write_bytes(victim.read_bytes())
            victim.unlink()
            os.link(outside, victim)
            with self.assertRaises(PaperLatexVerificationError):
                _paper_verification._verify_static_paper_latex_at(root)
        finally:
            temporary.cleanup()

        temporary, root = self._temporary_repository()
        try:
            _paper_verification._verify_static_paper_latex_at(root)
            victim = root / PAPER / "latex/README.md"
            outside = root / "outside.md"
            outside.write_bytes(victim.read_bytes())
            victim.unlink()
            try:
                victim.symlink_to(outside)
            except OSError as error:
                self.skipTest(f"symlink creation unavailable: {error}")
            with self.assertRaises(PaperLatexVerificationError):
                _paper_verification._verify_static_paper_latex_at(root)
        finally:
            temporary.cleanup()

        for attack in ("../outside", "/absolute", "latex/../outside", "latex/\\macro"):
            with self.subTest(path=attack):
                with self.assertRaises(PaperLatexVerificationError):
                    _paper_verification._validate_relative_source_path(attack)

    def test_retained_handles_reject_directory_swap_and_ignore_file_swap(self):
        temporary, root = self._temporary_repository()
        try:
            _paper_verification._verify_static_paper_latex_at(root)
            swapped = False

            def swap_directory(path: Path) -> None:
                nonlocal swapped
                if swapped or path.name != "latex":
                    return
                swapped = True
                replacement = path.with_name("latex_replacement")
                shutil.copytree(path, replacement)
                path.rename(path.with_name("latex_original"))
                replacement.rename(path)

            with self.assertRaises(PaperLatexVerificationError):
                _paper_verification._verify_static_paper_latex_at(
                    root,
                    directory_validation_hook=swap_directory,
                )
        finally:
            temporary.cleanup()

        temporary, root = self._temporary_repository()
        try:
            swapped = False

            def swap_file(path: Path) -> None:
                nonlocal swapped
                if swapped or path.name != "01_introduction.tex":
                    return
                swapped = True
                path.rename(path.with_suffix(".original"))
                path.write_text(
                    "\\section{Introduction}\nPDF verified\n", encoding="utf-8"
                )

            try:
                receipt = _paper_verification._verify_static_paper_latex_at(
                    root,
                    post_file_validation_hook=swap_file,
                )
            except PaperLatexVerificationError as error:
                self.assertEqual(error.reason_code, "source_identity_invalid")
                self.assertEqual(os.name, "nt")
            else:
                self.assertEqual(receipt.source_manifest_sha256, SOURCE_MANIFEST_SHA256)
        finally:
            temporary.cleanup()

    def test_source_bytes_fail_closed(self):
        path = "latex/sections/01_introduction.tex"
        transforms = (
            lambda data: b"\xef\xbb\xbf" + data,
            lambda data: data.replace(b"\n", b"\r\n", 1),
            lambda data: data[:-1],
            lambda data: data[:-1] + b"\x00\n",
            lambda data: data[:-1] + b"\xff\n",
        )
        for transform in transforms:
            self._mutate(path, transform, "source_bytes_invalid")
        for pinned in (
            "latex/main.tex",
            "latex/sections/05_supporting_theory.tex",
            "latex/sections/06_experimental_design.tex",
            "latex/sections/07_results.tex",
            "latex/sections/08_limitations.tex",
            "latex/appendices/appendix_analysis_protocol.tex",
            "latex/appendices/appendix_claims.tex",
            "latex/appendices/appendix_theory.tex",
        ):
            self._mutate(
                pinned,
                lambda data: data + b"% immutable mutation\n",
                "source_bytes_invalid",
            )

    def test_main_inputs_bibliography_and_manifest_exact_objects_reject_drift(self):
        main = (REPOSITORY / PAPER / "latex/main.tex").read_text(encoding="utf-8")
        observed_inputs = _paper_verification._extract_literal_arguments(
            main, ("input",)
        )["input"]
        self.assertEqual(observed_inputs, SAP_EXPECTED_INPUTS)
        self._mutate(
            "latex/main.tex",
            lambda data: data.replace(
                b"sections/01_introduction", b"sections/missing", 1
            ),
            "source_bytes_invalid",
        )
        for key, _entry_type, fields in BIBLIOGRAPHY_ENTRIES:
            if key not in ALL_BIBLIOGRAPHY_KEYS:
                continue
            for field, value in fields:
                self._mutate(
                    "latex/references.bib",
                    lambda data, key=key, field=field, value=value: _replace_bib_field(
                        data.decode("utf-8"), key, field, value + " wrong"
                    ).encode("utf-8"),
                    "source_grammar_invalid",
                )
        self._mutate(
            "latex/references.bib",
            lambda data: data.replace(
                b"  title = {Multi-Agent",
                b"  title = {Duplicate},\n  title = {Multi-Agent",
                1,
            ),
            "source_grammar_invalid",
        )
        manifest_attacks = (
            lambda data: data.replace(b"schema_version:", b"schema_drift:", 1),
            lambda data: data.replace(
                b"authority: non_authoritative_transcription",
                b"authority: authoritative",
                1,
            ),
            lambda data: b"\n".join(data.split(b"\n")[:-2]) + b"\n",
            lambda data: data
            + b"| extra | extra | extra | 2026 | url | -- | extra |\n",
        )
        for attack in manifest_attacks:
            self._mutate(
                "literature_primary_source_manifest.md",
                attack,
                "primary_source_manifest_invalid",
            )

    def test_production_policy_registry_parser_is_exact_and_independent(self):
        appendix = _read(REPOSITORY, POLICY_PROVENANCE_RELATIVE)
        self.assertEqual(
            _paper_verification._parse_policy_provenance_registry(appendix),
            POLICY_PROVENANCE_ROWS,
        )
        self.assertEqual(
            _paper_verification._POLICY_PROVENANCE_ROWS,
            POLICY_PROVENANCE_ROWS,
        )
        self.assertEqual(
            _paper_verification._BIBLIOGRAPHIC_PROVENANCE_STATUS,
            "bibliographic\\_provenance\\_status="
            "public\\_source\\_mapped\\_or\\_protocol\\_defined.",
        )
        self.assertEqual(
            _paper_verification._IMPLEMENTATION_AUTHENTICATION_STATUS,
            "implementation\\_authentication\\_status="
            "blocked\\_pending\\_authenticated\\_roster.",
        )

    def test_policy_registry_source_grammar_and_semantic_error_families_are_separate(
        self,
    ):
        appendix = _read(REPOSITORY, POLICY_PROVENANCE_RELATIVE)
        source_attacks = (
            appendix.replace(r"action\_choice", "action_choice", 1),
            appendix.replace(
                r"\textbf{provenance\_class}", r"\emph{provenance\_class}", 1
            ),
            appendix.replace(r"\end{enumerate}", "", 1),
            appendix.replace(
                r"\item \texttt{agentprune}", r"\item[wrong] \texttt{agentprune}", 1
            ),
        )
        for attacked in source_attacks:
            with self.subTest(attacked=attacked[:100]):
                with self.assertRaises(PaperLatexVerificationError) as caught:
                    _paper_verification._parse_policy_provenance_registry(attacked)
                self.assertEqual(caught.exception.reason_code, "source_grammar_invalid")

        begin = r"\begin{enumerate}"
        orphan = r"\item \texttt{orphan}."
        outside_item_attacks = (
            ("pre-enumerate", appendix.replace(begin, orphan + "\n" + begin, 1)),
            ("post-enumerate", appendix + "\n" + orphan + "\n"),
        )
        for label, attacked in outside_item_attacks:
            with self.subTest(outside_item=label):
                with self.assertRaises(AssertionError):
                    _parse_policy_registry_for_test(attacked)
                with self.assertRaises(PaperLatexVerificationError) as caught:
                    _paper_verification._parse_policy_provenance_registry(attacked)
                self.assertEqual(caught.exception.reason_code, "source_grammar_invalid")

        reference = r"\citep{zhang2025agentprune}"
        reference_grammar_attacks = (
            ("nested group", r"\citep{{zhang2025agentprune}}"),
            ("whitespace", r"\citep{zhang2025 agentprune}"),
            ("multiple keys", r"\citep{zhang2025agentprune,aggarwal2024automix}"),
        )
        for label, replacement in reference_grammar_attacks:
            attacked = appendix.replace(reference, replacement, 1)
            with self.subTest(reference_grammar=label):
                with self.assertRaises(AssertionError):
                    _parse_policy_registry_for_test(attacked)
                with self.assertRaises(PaperLatexVerificationError) as caught:
                    _paper_verification._parse_policy_provenance_registry(attacked)
                self.assertEqual(caught.exception.reason_code, "source_grammar_invalid")

        valid_wrong_reference = appendix.replace(
            reference,
            r"\citep{zhang2025agentprunex}",
            1,
        )
        self.assertEqual(
            _parse_policy_registry_for_test(valid_wrong_reference)[0][2],
            "zhang2025agentprunex",
        )
        with self.assertRaises(PaperLatexVerificationError) as caught:
            _paper_verification._parse_policy_provenance_registry(valid_wrong_reference)
        self.assertEqual(caught.exception.reason_code, "scientific_boundary_invalid")

        first_start = appendix.index(r"\item \texttt{agentprune}")
        second_start = appendix.index(r"\item \texttt{agora}")
        third_start = appendix.index(r"\item \texttt{always\_all\_specialists}")
        reordered = (
            appendix[:first_start]
            + appendix[second_start:third_start]
            + appendix[first_start:second_start]
            + appendix[third_start:]
        )
        semantic_attacks = (
            appendix.replace(r"\texttt{agentprune}", r"\texttt{agentprunex}", 1),
            reordered,
            appendix.replace(
                r"\texttt{published\_method}",
                r"\texttt{published\_method\_adaptation}",
                1,
            ),
            appendix.replace("zhang2025agentprune", "aggarwal2024automix", 1),
            appendix.replace("AgentPrune / Cut the Crap", "AgentPrune altered", 1),
            appendix.replace(
                r"blocked\_pending\_authenticated\_roster", r"authenticated", 1
            ),
        )
        for attacked in semantic_attacks:
            with self.subTest(attacked=attacked[:100]):
                with self.assertRaises(PaperLatexVerificationError) as caught:
                    _paper_verification._parse_policy_provenance_registry(attacked)
                self.assertEqual(
                    caught.exception.reason_code, "scientific_boundary_invalid"
                )

    def test_policy_registry_public_references_and_related_narrative_are_exact(self):
        appendix = _read(REPOSITORY, POLICY_PROVENANCE_RELATIVE)
        related = _active(_read(REPOSITORY, "latex/sections/02_related_work.tex"))
        bibliography_keys = tuple(
            key
            for key, _kind, _fields in _parse_bibtex(
                _read(REPOSITORY, "latex/references.bib")
            )
        )
        self.assertEqual(bibliography_keys, ALL_BIBLIOGRAPHY_KEYS)
        self.assertEqual(
            _paper_verification._ALL_BIBLIOGRAPHY_KEYS, ALL_BIBLIOGRAPHY_KEYS
        )
        self.assertEqual(
            tuple(
                key
                for key in _citation_keys(
                    _read(REPOSITORY, "latex/sections/02_related_work.tex")
                )
                if key in PRIMARY_SOURCE_KEYS
            ),
            RELATED_PRIMARY_CITATIONS,
        )
        rows = _parse_policy_registry_for_test(appendix)
        self.assertEqual(rows, POLICY_PROVENANCE_ROWS)
        for policy, kind, reference, role, status in rows:
            self.assertTrue(role, policy)
            self.assertEqual(status, "blocked_pending_authenticated_roster", policy)
            if kind == "protocol_defined_comparator":
                self.assertIsNone(reference, policy)
            else:
                self.assertIn(reference, bibliography_keys, policy)
        self.assertEqual(related.casefold().count("off-policy"), 2)
        self.assertIn(
            "the present paper performs neither direct nor logged off-policy evaluation",
            related.casefold(),
        )
        self.assertIn(
            "any future off-policy comparison is protocol-only",
            related.casefold(),
        )
        self.assertEqual(related.count("paired direct policy evaluation"), 1)
        self.assertEqual(related.count("score-level orthogonality"), 1)
        self.assertEqual(related.count("our first-order action-choice proposition"), 1)
        for policy in POLICY_IDS:
            self.assertIsNone(
                re.search(
                    r"(?<![A-Za-z0-9_])" + re.escape(policy) + r"(?![A-Za-z0-9_])",
                    related.replace(r"\_", "_"),
                ),
                policy,
            )
        for promotion in (
            "adapter authenticated",
            "implementation verified",
            "version verified",
            "roster authenticated",
            "roster verified",
            "policy ready",
        ):
            self.assertNotIn(promotion, related.casefold())

    def test_comment_multiline_and_task1_scientific_families_reach_production(self):
        self._mutate(
            "latex/sections/02_related_work.tex",
            lambda data: data.replace(
                b"\\citep{zhang2026icore}", b"% \\citep{zhang2026icore}", 1
            ),
            "source_grammar_invalid",
        )
        temporary, root = self._temporary_repository()
        try:
            _paper_verification._verify_static_paper_latex_at(root)
            related = root / PAPER / "latex/sections/02_related_work.tex"
            related.write_text(
                related.read_text(encoding="utf-8").replace(
                    "\\citep{zhang2026icore}", "\\citep{\nzhang2026icore\n}", 1
                ),
                encoding="utf-8",
                newline="\n",
            )
            with self.assertRaises(PaperLatexVerificationError) as caught:
                _paper_verification._verify_static_paper_latex_at(root)
            self.assertEqual(
                caught.exception.reason_code,
                "source_grammar_invalid",
            )
        finally:
            temporary.cleanup()

        temporary, root = self._temporary_repository()
        try:
            _paper_verification._verify_static_paper_latex_at(root)
            readme = root / PAPER / "latex/README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8")
                + "<!-- E2 causal mechanism established -->\n",
                encoding="utf-8",
                newline="\n",
            )
            self.assertEqual(
                _paper_verification._verify_static_paper_latex_at(root).status,
                "literature_corrected_static_ready",
            )
        finally:
            temporary.cleanup()

        self._mutate(
            "latex/sections/02_related_work.tex",
            lambda data: _swap_once(
                data.decode("utf-8"),
                "\\citep{zhang2026icore}",
                "\\citep{wong2026eureka}",
            ).encode("utf-8"),
            "scientific_boundary_invalid",
        )
        science_attacks = (
            (
                "latex/sections/02_related_work.tex",
                b"Self-resource allocation",
                b"agentprune source=v1 verified=true; Self-resource allocation",
            ),
            (
                "latex/sections/04_method.tex",
                b"Study Policy: Obligation-Aware Coordination",
                b"Novel OACS Method",
            ),
            (
                "latex/sections/09_conclusion.tex",
                b"The present contributions are a receipt-bound evaluation contract, the\n",
                b"The present contributions establish coordination value, and the\n",
            ),
            (
                "latex/sections/03_problem_formulation.tex",
                b"No selective-analysis alternative is permitted.",
                b"No selective-analysis alternative is permitted. One target may be dropped.",
            ),
        )
        for relative, old, new in science_attacks:
            self._mutate(
                relative,
                lambda data, old=old, new=new: data.replace(old, new, 1),
                "scientific_boundary_invalid",
            )
        for phrase in FORBIDDEN_POSITIVES:
            self._mutate(
                "latex/sections/01_introduction.tex",
                lambda data, phrase=phrase: data + phrase.encode("utf-8") + b"\n",
                "scientific_boundary_invalid",
            )

    def test_comment_parity_multiline_arguments_and_environment_stack(self):
        stripped = _paper_verification._strip_tex_comments(
            "kept \\% value % removed\nnext\\\\% gone"
        )
        self.assertEqual(stripped, "kept \\% value \nnext\\\\")
        scanned = _paper_verification._scan_tex_document(
            "\\citep{alpha,\n beta}\n\\input{sections/\npart}\n",
            allowed_commands={"citep", "input"},
            allowed_environments=(),
        )
        self.assertEqual(scanned["citep"], ("alpha,\n beta",))
        self.assertEqual(scanned["input"], ("sections/\npart",))
        for old, new in (
            (b"\\begin{enumerate}", b"\\begin{quote}"),
            (b"\\end{enumerate}", b"\\end{quote}"),
            (b"\\end{enumerate}", b"\\end{quote}\\end{enumerate}"),
            (b"\\section{Introduction}", b"\\section{Introduction"),
        ):
            self._mutate(
                "latex/sections/01_introduction.tex",
                lambda data, old=old, new=new: data.replace(old, new, 1),
                "source_grammar_invalid",
            )

    def test_every_role_enforces_exact_command_arity_and_control_symbols(self):
        for relative, (
            required_arguments,
            zero_arguments,
        ) in ROLE_COMMAND_SIGNATURES.items():
            expected_code = (
                "source_bytes_invalid"
                if relative == POLICY_PROVENANCE_RELATIVE
                else "source_grammar_invalid"
            )
            for command in required_arguments:
                with self.subTest(relative=relative, bare=command):
                    self._mutate(
                        relative,
                        lambda data, command=command: data + f"\\{command}\n".encode(),
                        expected_code,
                    )
            for command in zero_arguments:
                with self.subTest(relative=relative, unexpected_argument=command):
                    self._mutate(
                        relative,
                        lambda data, command=command: data
                        + f"\\{command}{{attack}}\n".encode(),
                        expected_code,
                    )
            with self.subTest(relative=relative, excluded_symbol="%"):
                self._mutate(
                    relative,
                    lambda data: data + b"\\%\n",
                    expected_code,
                )
        for symbol in ALLOWED_CONTROL_SYMBOLS:
            _paper_verification._scan_tex_document(
                "\\" + symbol + "\n",
                allowed_commands=set(),
                allowed_environments=(),
            )
            with self.subTest(allowed_symbol_with_argument=symbol):
                with self.assertRaises(PaperLatexVerificationError):
                    _paper_verification._scan_tex_document(
                        "\\" + symbol + "{attack}\n",
                        allowed_commands=set(),
                        allowed_environments=(),
                    )
        for symbol in EXCLUDED_CONTROL_SYMBOLS:
            with self.subTest(excluded_symbol=symbol):
                with self.assertRaises(PaperLatexVerificationError):
                    _paper_verification._scan_tex_document(
                        "\\" + symbol + "\n",
                        allowed_commands=set(),
                        allowed_environments=(),
                    )
        for relative in EDITABLE_TEX:
            expected_code = (
                "source_bytes_invalid"
                if relative == POLICY_PROVENANCE_RELATIVE
                else "source_grammar_invalid"
            )
            self._mutate(
                relative,
                lambda data: data + b"\\begin{foreign}x\\end{foreign}\n",
                expected_code,
            )

    def test_every_one_argument_signature_rejects_an_adjacent_extra_group(self):
        preservation_cases = (
            (
                "reviewed begin suffix",
                "\\begin{enumerate}[leftmargin=*]x\\end{enumerate}\n",
                {"begin", "end"},
                ("enumerate",),
            ),
            ("empty oacs delimiter", "\\oacs{}\n", {"oacs"}, ()),
            (
                "zero-arity delimiter then prose group",
                "\\oacs{} ordinary prose {grouped}\n",
                {"oacs"},
                (),
            ),
            (
                "one-argument command then prose group",
                "\\emph{value} ordinary prose {grouped}\n",
                {"emph"},
                (),
            ),
            (
                "nested declared argument",
                "\\emph{value {nested}}\n",
                {"emph"},
                (),
            ),
            (
                "next command on following line",
                "\\section{A}\n\\section{B}\n",
                {"section"},
                (),
            ),
        )
        for label, text, allowed, environments in preservation_cases:
            with self.subTest(preservation=label):
                _paper_verification._scan_tex_document(
                    text,
                    allowed_commands=allowed,
                    allowed_environments=environments,
                )

        separators = (("space", " "), ("tab", "\t"), ("newline", "\n"))
        for command, (
            arity,
            _permits_empty,
            _suffixes,
        ) in COMMAND_SIGNATURE_ORACLE.items():
            if arity != 1:
                continue
            if command in {"begin", "end"}:
                base = "\\begin{enumerate}[leftmargin=*]x\\end{enumerate}\n"
                allowed = {"begin", "end"}
                environments = ("enumerate",)
            else:
                base = f"\\{command}{{value}}\n"
                allowed = {command}
                environments = ()
            _paper_verification._scan_tex_document(
                base,
                allowed_commands=allowed,
                allowed_environments=environments,
            )
            for separator_name, separator in separators:
                attack = _with_extra_group_after_first_argument(
                    base,
                    command,
                    separator,
                )
                with self.subTest(command=command, separator=separator_name):
                    with self.assertRaises(PaperLatexVerificationError) as caught:
                        _paper_verification._scan_tex_document(
                            attack,
                            allowed_commands=allowed,
                            allowed_environments=environments,
                        )
                    self.assertEqual(
                        caught.exception.reason_code,
                        "source_grammar_invalid",
                    )

    def test_each_editable_role_rejects_an_extra_group_on_a_live_command(self):
        representatives = (
            ("latex/sections/01_introduction.tex", "claim"),
            ("latex/sections/02_related_work.tex", "citep"),
            ("latex/sections/03_problem_formulation.tex", "section"),
            ("latex/sections/04_method.tex", "section"),
            ("latex/sections/09_conclusion.tex", "section"),
            ("latex/appendices/appendix_reviewer_attacks.tex", "textbf"),
        )
        for relative, command in representatives:
            required_arguments, zero_arguments = ROLE_COMMAND_SIGNATURES[relative]
            base = _read(REPOSITORY, relative)
            allowed = set(required_arguments) | set(zero_arguments)
            environments = ROLE_ENVIRONMENTS[relative]
            _paper_verification._scan_tex_document(
                base,
                allowed_commands=allowed,
                allowed_environments=environments,
            )
            for separator_name, separator in (
                ("space", " "),
                ("tab", "\t"),
                ("newline", "\n"),
            ):
                attack = _with_extra_group_after_first_argument(
                    base,
                    command,
                    separator,
                )
                with self.subTest(
                    relative=relative,
                    command=command,
                    separator=separator_name,
                ):
                    with self.assertRaises(PaperLatexVerificationError) as caught:
                        _paper_verification._scan_tex_document(
                            attack,
                            allowed_commands=allowed,
                            allowed_environments=environments,
                        )
                    self.assertEqual(
                        caught.exception.reason_code,
                        "source_grammar_invalid",
                    )

    def test_every_role_rejects_unapproved_command_and_symbol_modifiers(self):
        for relative, (
            required_arguments,
            zero_arguments,
        ) in ROLE_COMMAND_SIGNATURES.items():
            base = _read(REPOSITORY, relative)
            allowed = set(required_arguments) | set(zero_arguments)
            environments = ROLE_ENVIRONMENTS[relative]
            _paper_verification._scan_tex_document(
                base,
                allowed_commands=allowed,
                allowed_environments=environments,
            )
            for command in required_arguments:
                for attack in (
                    f"\\{command}*{{attack}}\n",
                    f"\\{command}[attack]{{attack}}\n",
                    f"\\{command}{{attack}}*\n",
                    f"\\{command}{{attack}}[attack]\n",
                ):
                    with self.subTest(
                        relative=relative, command=command, attack=attack
                    ):
                        with self.assertRaises(PaperLatexVerificationError):
                            _paper_verification._scan_tex_document(
                                base + attack,
                                allowed_commands=allowed,
                                allowed_environments=environments,
                            )
            for command in zero_arguments:
                attacks = (f"\\{command}*\n", f"\\{command}[attack]\n")
                if command != "oacs":
                    attacks += (f"\\{command}{{}}\n",)
                for attack in attacks:
                    with self.subTest(
                        relative=relative, command=command, attack=attack
                    ):
                        with self.assertRaises(PaperLatexVerificationError):
                            _paper_verification._scan_tex_document(
                                base + attack,
                                allowed_commands=allowed,
                                allowed_environments=environments,
                            )
            for symbol in ALLOWED_CONTROL_SYMBOLS:
                for modifier in ("*", "[1ex]", "{}"):
                    with self.subTest(
                        relative=relative, symbol=symbol, modifier=modifier
                    ):
                        with self.assertRaises(PaperLatexVerificationError):
                            _paper_verification._scan_tex_document(
                                base + "\\" + symbol + modifier + "\n",
                                allowed_commands=allowed,
                                allowed_environments=environments,
                            )
            if "enumerate" in environments:
                if "\\begin{enumerate}[leftmargin=*]" in base:
                    drift = base.replace(
                        "\\begin{enumerate}[leftmargin=*]",
                        "\\begin{enumerate}[unapproved=*]",
                        1,
                    )
                else:
                    drift = base.replace(
                        "\\begin{enumerate}",
                        "\\begin{enumerate}[unapproved=*]",
                        1,
                    )
                self.assertNotEqual(drift, base)
                with self.assertRaises(PaperLatexVerificationError):
                    _paper_verification._scan_tex_document(
                        drift,
                        allowed_commands=allowed,
                        allowed_environments=environments,
                    )

    def test_tex_scanner_rejects_unescaped_top_level_underscore_outside_math(self):
        with self.assertRaises(PaperLatexVerificationError):
            _paper_verification._scan_tex_document(
                "citation_authority_status=blocked\n",
                allowed_commands=set(),
                allowed_environments=(),
            )

        _paper_verification._scan_tex_document(
            "$Z_{it}$ and $Y_{it}$.\n",
            allowed_commands=set(),
            allowed_environments=(),
        )
        _paper_verification._scan_tex_document(
            "\\texttt{citation\\_authority\\_status=blocked}.\n",
            allowed_commands={"texttt"},
            allowed_environments=(),
        )

    def test_related_work_authority_status_is_renderable_tex(self):
        related = _read(REPOSITORY, "latex/sections/02_related_work.tex")
        self.assertIn(
            "citation\\_authority\\_status=blocked\\_pending\\_authenticated\\_roster.",
            related,
        )

    def test_reviewed_layout_guards_avoid_known_overfull_rows(self):
        related = _read(REPOSITORY, "latex/sections/02_related_work.tex")
        self.assertNotIn(r"\begin{quote}", related)
        self.assertNotIn(r"\raggedright", related)
        registry = _read(REPOSITORY, POLICY_PROVENANCE_RELATIVE)
        self.assertEqual(registry.count(r"\begin{enumerate}"), 1)
        self.assertEqual(registry.count(r"\end{enumerate}"), 1)

        design = _read(REPOSITORY, "latex/sections/06_experimental_design.tex")
        self.assertIn(
            "The Architecture policy claim is \\claim{C-E3-ARCH-POLICY}.\n"
            "The JCI policy claim is \\claim{C-E3-JCI-POLICY}.",
            design,
        )

        theory = _read(REPOSITORY, "latex/sections/05_supporting_theory.tex")
        self.assertIn(
            "theorem (\\claim{C-THEORY-REGRET}).  It does not support a joint\n"
            "audit/receipt minimax theorem (\\claim{C-THEORY-JOINT-MINIMAX}).\n"
            "It also does not support a same-information policy-superiority\n"
            "theorem (\\claim{C-THEORY-POLICY-SUPERIOR}).}",
            theory,
        )
        self.assertNotIn(
            "citation_authority_status=blocked_pending_authenticated_roster",
            related,
        )

    def test_test_owned_exact_signatures_reject_escaped_suffix_modifiers_and_unicode_symbols(
        self,
    ):
        required = {
            command
            for required_arguments, _zero_arguments in ROLE_COMMAND_SIGNATURES.values()
            for command in required_arguments
        }
        zero = {
            command
            for _required_arguments, zero_arguments in ROLE_COMMAND_SIGNATURES.values()
            for command in zero_arguments
        }
        self.assertTrue(required | zero <= set(COMMAND_SIGNATURE_ORACLE))
        self.assertTrue(
            all(COMMAND_SIGNATURE_ORACLE[command][0] == 1 for command in required)
        )
        self.assertTrue(
            all(COMMAND_SIGNATURE_ORACLE[command][0] == 0 for command in zero)
        )
        self.assertEqual(
            CONTROL_SYMBOL_SIGNATURE_ORACLE,
            {"\\": (0, False, {}), "_": (0, False, {})},
        )

        _paper_verification._scan_tex_document(
            "\\begin{enumerate}[leftmargin=*]\n\\end{enumerate}\n",
            allowed_commands={"begin", "end"},
            allowed_environments=("enumerate",),
        )
        _paper_verification._scan_tex_document(
            "\\in[0,1]\n",
            allowed_commands={"in"},
            allowed_environments=(),
        )
        escaped_suffix_modifiers = (
            (
                "\\begin{enumerate}[leftmargin=*]\\_\n\\end{enumerate}\n",
                {"begin", "end"},
                ("enumerate",),
            ),
            ("\\in[0,1]\\_\n", {"in"}, ()),
            ("\\in[0,1]\\\\\n", {"in"}, ()),
        )
        for attack, allowed, environments in escaped_suffix_modifiers:
            with self.subTest(escaped_suffix_modifier=repr(attack)):
                with self.assertRaises(PaperLatexVerificationError):
                    _paper_verification._scan_tex_document(
                        attack,
                        allowed_commands=allowed,
                        allowed_environments=environments,
                    )
        for symbol in UTF8_AND_NONPRINTING_CONTROL_SYMBOLS:
            with self.subTest(non_ascii_or_nonprinting=repr(symbol)):
                with self.assertRaises(PaperLatexVerificationError):
                    _paper_verification._scan_tex_document(
                        "\\" + symbol + "\n",
                        allowed_commands=set(),
                        allowed_environments=(),
                    )

    def test_exact_control_symbol_complement_rejects_in_every_editable_role(self):
        for relative, (
            required_arguments,
            zero_arguments,
        ) in ROLE_COMMAND_SIGNATURES.items():
            base = _read(REPOSITORY, relative)
            allowed = set(required_arguments) | set(zero_arguments)
            environments = ROLE_ENVIRONMENTS[relative]
            _paper_verification._scan_tex_document(
                base,
                allowed_commands=allowed,
                allowed_environments=environments,
            )
            for symbol in EXCLUDED_CONTROL_SYMBOLS:
                with self.subTest(relative=relative, symbol=repr(symbol)):
                    with self.assertRaises(PaperLatexVerificationError):
                        _paper_verification._scan_tex_document(
                            base + "\\" + symbol + "\n",
                            allowed_commands=allowed,
                            allowed_environments=environments,
                        )

    def test_unknown_and_dynamic_tex_controls_all_reject(self):
        controls = (
            "unknown",
            "include",
            "InputIfFileExists",
            "includegraphics",
            "verbatiminput",
            "csname",
            "endinput",
            "iftrue",
            "fi",
            "let",
            "expandafter",
            "scantokens",
            "openin",
            "read",
            "openout",
            "write",
            "special",
            "pdfximage",
            "write18",
            "def",
            "edef",
            "gdef",
            "xdef",
            "catcode",
        )
        for relative in EDITABLE_TEX:
            expected_code = (
                "source_bytes_invalid"
                if relative == POLICY_PROVENANCE_RELATIVE
                else "source_grammar_invalid"
            )
            for control in controls:
                self._mutate(
                    relative,
                    lambda data, control=control: data
                    + f"\\{control}{{attack}}\n".encode(),
                    expected_code,
                )
        for attack in (
            b"\\input{/absolute}\n",
            b"\\input{../escape}\n",
            b"\\input{\\macro}\n",
            b"\\input{|pipe}\n",
            b"\\end{document}\n",
        ):
            self._mutate(
                "latex/sections/04_method.tex",
                lambda data, attack=attack: data + attack,
                "source_grammar_invalid",
            )

    def test_tex_caret_decoding_cannot_hide_controls_or_traversal(self):
        attacks = (b"^^5cwrite18{attack}\n", b"^^5cinput{../escape}\n")
        for attack in attacks:
            with self.subTest(attack=attack):
                self._mutate(
                    "latex/sections/04_method.tex",
                    lambda data, attack=attack: data + attack,
                    "source_grammar_invalid",
                )

    def test_active_comment_forms_and_section_controls_fail_closed(self):
        science_attacks = (
            ("latex/sections/04_method.tex", b"<!-- PDF verified -->\n"),
            ("latex/README.md", b"% PDF verified\n"),
        )
        for relative, attack in science_attacks:
            with self.subTest(relative=relative, attack=attack):
                self._mutate(
                    relative,
                    lambda data, attack=attack: data + attack,
                    "scientific_boundary_invalid",
                )
        self._mutate(
            "latex/sections/04_method.tex",
            lambda data: data + b"PDF \\% verified\n",
            "source_grammar_invalid",
        )
        for attack in (b"\\section\n", b"\\section*{Attack}\n"):
            with self.subTest(attack=attack):
                self._mutate(
                    "latex/sections/04_method.tex",
                    lambda data, attack=attack: data + attack,
                    "source_grammar_invalid",
                )

    def test_full_binding_novelty_boundary_rejects_retained_disclaimer_attacks(self):
        for phrase in FORBIDDEN_NOVELTY_PHRASES:
            with self.subTest(phrase=phrase):
                self._mutate(
                    "latex/sections/02_related_work.tex",
                    lambda data, phrase=phrase: data.replace(
                        b"non-exhaustive positioning aid",
                        phrase.encode("utf-8") + b" positioning aid",
                        1,
                    ),
                    "scientific_boundary_invalid",
                )

    def test_retained_valid_novelty_boundary_rejects_appended_forbidden_phrases(self):
        for phrase in FORBIDDEN_NOVELTY_PHRASES:
            with self.subTest(phrase=phrase):
                self._mutate(
                    "latex/sections/02_related_work.tex",
                    lambda data, phrase=phrase: data
                    + (f"The reviewed roster proves our method is {phrase}.\n").encode(
                        "utf-8"
                    ),
                    "scientific_boundary_invalid",
                )

    def test_retained_provenance_boundary_rejects_contradictory_remainder(self):
        contradictions = (
            "Every policy has an assigned source.",
            "All policy versions are current.",
            "Policy citations are verified.",
            "The external roster verification is complete.",
            "Every policy is verified against the roster.",
        )
        for contradiction in contradictions:
            with self.subTest(contradiction=contradiction):
                self._mutate(
                    "latex/sections/02_related_work.tex",
                    lambda data, contradiction=contradiction: data
                    + ("\n" + contradiction + "\n").encode("utf-8"),
                    "scientific_boundary_invalid",
                )

    def test_registry_and_sap_are_the_exact_two_policy_roster_owners(self):
        appendix = _read(REPOSITORY, POLICY_PROVENANCE_RELATIVE)
        self.assertEqual(
            _paper_verification._parse_policy_provenance_registry(appendix),
            POLICY_PROVENANCE_ROWS,
        )
        self._mutate(
            "latex/sections/02_related_work.tex",
            lambda data: data.replace(
                b"the two exact roster owners",
                b"three exact roster owners",
                1,
            ),
            "scientific_boundary_invalid",
        )
        assignments = (
            (
                "latex/sections/01_introduction.tex",
                "agentprune has DOI 10.5555/assigned.",
            ),
            (
                "latex/sections/02_related_work.tex",
                "agora has an official bibliographic origin.",
            ),
            (
                "latex/sections/03_problem_formulation.tex",
                "automix carries release revision v2.",
            ),
            (
                "latex/sections/04_method.tex",
                "bicsrouter has completed authentication.",
            ),
            (
                "latex/sections/09_conclusion.tex",
                "masrouter now has authoritative attribution.",
            ),
            (
                "latex/appendices/appendix_reviewer_attacks.tex",
                "routellm is documented by a roster reference.",
            ),
        )
        for relative, assignment in assignments:
            with self.subTest(relative=relative, assignment=assignment):
                self._mutate(
                    relative,
                    lambda data, assignment=assignment: data
                    + ("\n" + assignment + "\n").encode("utf-8"),
                    "scientific_boundary_invalid",
                )

    def test_forbidden_authentication_promotions_reject_across_active_roles(self):
        attacks = (
            ("latex/sections/01_introduction.tex", "The adapter authenticated."),
            ("latex/sections/02_related_work.tex", "The implementation verified."),
            ("latex/sections/03_problem_formulation.tex", "The version verified."),
            ("latex/sections/04_method.tex", "The roster authenticated."),
            ("latex/sections/09_conclusion.tex", "The roster verified."),
            ("latex/appendices/appendix_reviewer_attacks.tex", "The policy ready."),
        )
        for relative, attack in attacks:
            with self.subTest(relative=relative, attack=attack):
                if relative in ROLE_COMMAND_SIGNATURES:
                    required_arguments, zero_arguments = ROLE_COMMAND_SIGNATURES[
                        relative
                    ]
                    _paper_verification._scan_tex_document(
                        _read(REPOSITORY, relative) + "\n" + attack + "\n",
                        allowed_commands=set(required_arguments) | set(zero_arguments),
                        allowed_environments=ROLE_ENVIRONMENTS[relative],
                    )
                self._mutate(
                    relative,
                    lambda data, attack=attack: data
                    + ("\n" + attack + "\n").encode("utf-8"),
                    "scientific_boundary_invalid",
                )

    def test_retained_ra_nov_01_item_rejects_opposing_novelty_remainder(self):
        contradictions = (
            "OACS has unprecedented novelty.",
            "Our routing contribution is original.",
            "We introduce a new selector.",
            "The obligation representation is novel in this work.",
        )
        for contradiction in contradictions:
            with self.subTest(contradiction=contradiction):
                self._mutate(
                    "latex/appendices/appendix_reviewer_attacks.tex",
                    lambda data, contradiction=contradiction: data
                    + ("\n" + contradiction + "\n").encode("utf-8"),
                    "scientific_boundary_invalid",
                )

    def test_retained_ra_item_rejects_morphological_and_cross_role_reversals(self):
        reversals = (
            (
                "latex/sections/01_introduction.tex",
                "Our representation claims originality.",
            ),
            ("latex/sections/02_related_work.tex", "Our selector is innovative."),
            (
                "latex/sections/03_problem_formulation.tex",
                "We originate a routing method.",
            ),
            ("latex/sections/04_method.tex", "OACS is pioneering."),
            (
                "latex/sections/09_conclusion.tex",
                "This is a breakthrough contribution.",
            ),
            (
                "latex/appendices/appendix_reviewer_attacks.tex",
                "OACS newly introduces the selector.",
            ),
        )
        for relative, reversal in reversals:
            with self.subTest(relative=relative, reversal=reversal):
                self._mutate(
                    relative,
                    lambda data, reversal=reversal: data
                    + ("\n" + reversal + "\n").encode("utf-8"),
                    "scientific_boundary_invalid",
                )

    def test_exact_rendered_claim_spans_reject_grouped_synonyms_and_readme_claims(self):
        rendered_closure = " ".join(
            _rendered_boundary_text(_read(REPOSITORY, relative), relative)
            for relative in MANUSCRIPT_SOURCE_CLOSURE
        )
        self.assertFalse(_test_owned_unapproved_authorial_claim(rendered_closure))
        attacks = (
            (
                "latex/sections/01_introduction.tex",
                "Our selector claims orig{in}ality.",
            ),
            ("latex/sections/02_related_work.tex", "OACS is pathbreaking."),
            (
                "latex/sections/03_problem_formulation.tex",
                "Our approach is trailblazing.",
            ),
            ("latex/sections/04_method.tex", "This method is field-leading."),
            ("latex/sections/09_conclusion.tex", "Our study is paradigm-shifting."),
            (
                "latex/appendices/appendix_reviewer_attacks.tex",
                "This work is landmark-defining.",
            ),
            ("latex/README.md", "OACS offers an unmatched advance."),
        )
        for relative, attack in attacks:
            with self.subTest(relative=relative, attack=attack):
                attacked_closure = (
                    rendered_closure + ". " + _rendered_boundary_text(attack, relative)
                )
                self.assertTrue(
                    _test_owned_unapproved_authorial_claim(attacked_closure)
                )
                if relative in ROLE_COMMAND_SIGNATURES:
                    required_arguments, zero_arguments = ROLE_COMMAND_SIGNATURES[
                        relative
                    ]
                    _paper_verification._scan_tex_document(
                        _read(REPOSITORY, relative) + "\n" + attack + "\n",
                        allowed_commands=set(required_arguments) | set(zero_arguments),
                        allowed_environments=ROLE_ENVIRONMENTS[relative],
                    )
                self._mutate(
                    relative,
                    lambda data, attack=attack: data
                    + ("\n" + attack + "\n").encode("utf-8"),
                    "scientific_boundary_invalid",
                )

    def test_implementation_block_and_ra_nov_01_demotions_cannot_reverse(self):
        attacks = (
            (
                "latex/sections/02_related_work.tex",
                b"implementation authentication remains blocked pending\nthe authenticated external roster",
                b"implementation verified against\nthe authenticated external roster",
            ),
            (
                "latex/appendices/appendix_reviewer_attacks.tex",
                b"iCORE removes obligation-graph\n  novelty",
                b"iCORE establishes our obligation-graph\n  novelty",
            ),
        )
        for relative, old, new in attacks:
            with self.subTest(relative=relative):
                self._mutate(
                    relative,
                    lambda data, old=old, new=new: data.replace(old, new, 1),
                    "scientific_boundary_invalid",
                )

    def test_unresolved_references_citations_and_bibliography_drift_reject(self):
        attacks = (
            b"\\citep{missing2026}\n",
            b"\\ref{missing-label}\n",
            b"\\label{duplicate-label}\\label{duplicate-label}\n",
        )
        for attack in attacks:
            self._mutate(
                "latex/sections/02_related_work.tex",
                lambda data, attack=attack: data + attack,
                "source_grammar_invalid",
            )
        for marker in (
            b"@string",
            b"@preamble",
            b"@comment",
            b" # macro",
            b"@misc{extra",
        ):
            self._mutate(
                "latex/references.bib",
                lambda data, marker=marker: data + marker + b"\n",
                "source_grammar_invalid",
            )
        self._mutate(
            "latex/references.bib",
            lambda data: data.replace(
                b"@misc{bala2026setvalued", b"@misc{BALA2026SETVALUED", 1
            ),
            "source_grammar_invalid",
        )
        self._mutate(
            "latex/references.bib",
            lambda data: data.replace(
                b"  title = {Multi-Agent", b"  title = {Wrong Multi-Agent", 1
            ),
            "source_grammar_invalid",
        )

    def test_primary_manifest_and_scientific_mutations_reject(self):
        manifest_mutations = (
            lambda data: b"% comment\n" + data,
            lambda data: b"<!-- comment -->\n" + data,
            lambda data: data.replace(b"network_reads: 0", b"network_reads: 1", 1),
            lambda data: data.replace(b"exhaustive: false", b"exhaustive: true", 1),
            lambda data: data.replace(SPEC_SHA256.encode(), b"0" * 64, 1),
            lambda data: data.replace(b"2026", b"2025", 1),
            lambda data: data + data.splitlines(keepends=True)[-1],
        )
        for mutate in manifest_mutations:
            self._mutate(
                "literature_primary_source_manifest.md",
                mutate,
                "primary_source_manifest_invalid",
            )
        scientific = (
            (
                "latex/sections/01_introduction.tex",
                b"\\section{Introduction}",
                b"\\section{Introduction}\nPDF verified",
            ),
            ("latex/sections/03_problem_formulation.tex", b"$Z_{it}$", b"$A_{it}$"),
            (
                "latex/sections/04_method.tex",
                METHOD_BOUNDARY.encode(),
                b"OACS is novel.",
            ),
            (
                "latex/sections/09_conclusion.tex",
                b"receipt-bound evaluation contract",
                b"coordination-value result",
            ),
            (
                "latex/appendices/appendix_reviewer_attacks.tex",
                b"RA-NOV-01",
                b"RA-NOV-99",
            ),
        )
        for relative, old, new in scientific:
            self._mutate(
                relative,
                lambda data, old=old, new=new: data.replace(old, new, 1),
                "scientific_boundary_invalid",
            )
        self._mutate(
            "latex/sections/02_related_work.tex",
            lambda data: data.replace(
                DISPOSITIONS[0].encode(),
                b"% " + DISPOSITIONS[0].encode() + b"\n",
                1,
            ),
            "scientific_boundary_invalid",
        )


class StaticVerifierSourcePolicyTests(unittest.TestCase):
    def test_high_risk_grammar_does_not_enumerate_assertion_vocabulary(self):
        production = (REPOSITORY / "iclr2027/paper_latex_verification.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("_EVALUATION_VALIDITY_INTERPRETATION_RULES", production)
        self.assertNotIn("_HIGH_RISK_EVALUATION_TOPIC", production)
        for review_witness_verb in (
            "fixes",
            "indicates",
            "reveals",
            "serves",
            "warrants",
            "done",
            "approved",
        ):
            with self.subTest(review_witness_verb=review_witness_verb):
                self.assertNotRegex(
                    production,
                    rf"(?i)\b{re.escape(review_witness_verb)}\b",
                )

    def test_source_structure_semantics_and_identity_have_fixed_precedence(self):
        source_text = {
            relative: _read(REPOSITORY, relative)
            for relative in MANUSCRIPT_SOURCE_CLOSURE
        }
        relative = "latex/sections/01_introduction.tex"
        original = source_text[relative]
        insertion_point = r"\section{Introduction}"
        self.assertEqual(original.count(insertion_point), 1)

        def insert(payload: str) -> str:
            return original.replace(
                insertion_point,
                insertion_point + "\n" + payload,
                1,
            )

        witnesses = (
            (
                "closed source command grammar before semantics",
                insert(
                    r"\unknowncommand{masked}"
                    "\nThe amended evaluator rehabilitates the frozen result."
                ),
                "source_grammar_invalid",
            ),
            (
                "metadata grammar before semantics",
                insert(
                    r"\csname hypersetup\endcsname{pdfauthor={Named Researcher}}"
                    "\nThe amended evaluator rehabilitates the frozen result."
                ),
                "source_grammar_invalid",
            ),
            (
                "closed semantics before canonical identity",
                insert("The amended evaluator rehabilitates the frozen result."),
                "scientific_boundary_invalid",
            ),
            (
                "canonical identity after valid structure and semantics",
                original.replace("None of the four", "None  of the four", 1),
                "source_grammar_invalid",
            ),
        )
        for label, changed_text, expected_reason in witnesses:
            with self.subTest(label=label):
                changed = dict(source_text)
                changed[relative] = changed_text
                self.assertNotEqual(changed_text, original)
                with self.assertRaises(PaperLatexVerificationError) as caught:
                    _paper_verification._validate_iclr2027_venue_overlay(changed)
                self.assertEqual(caught.exception.reason_code, expected_reason)

        main_relative = "latex/main.tex"
        main = source_text[main_relative]
        begin_document = r"\begin{document}"
        self.assertEqual(main.count(begin_document), 1)
        main_witnesses = (
            (
                "closed main loading grammar before semantics",
                main.replace(
                    begin_document,
                    r"\include{sections/10_submission_statements}"
                    "\nThe amended evaluator rehabilitates the frozen result."
                    "\n" + begin_document,
                    1,
                ),
                "source_grammar_invalid",
            ),
            (
                "closed main semantics before canonical identity",
                main.replace(
                    begin_document,
                    begin_document
                    + "\nThe amended evaluator rehabilitates the frozen result.",
                    1,
                ),
                "scientific_boundary_invalid",
            ),
            (
                "closed main canonical identity after valid structure and semantics",
                main.replace(
                    rf"\title{{{EXPECTED_RAW_MANUSCRIPT_TITLE}}}" + "\n",
                    rf"\title{{{EXPECTED_RAW_MANUSCRIPT_TITLE}}}" + "\n ",
                    1,
                ),
                "source_grammar_invalid",
            ),
        )
        for label, changed_main, expected_reason in main_witnesses:
            with self.subTest(label=label):
                changed = dict(source_text)
                changed[main_relative] = changed_main
                self.assertNotEqual(changed_main, main)
                with self.assertRaises(PaperLatexVerificationError) as caught:
                    _paper_verification._validate_iclr2027_venue_overlay(changed)
                self.assertEqual(caught.exception.reason_code, expected_reason)

        temporary, root = _new_source_closure_repository()
        try:
            introduction_path = root / PAPER / relative
            introduction_path.write_text(
                insert("The amended evaluator rehabilitates the frozen result."),
                encoding="utf-8",
                newline="\n",
            )
            policy_path = root / PAPER / POLICY_PROVENANCE_RELATIVE
            policy = policy_path.read_text(encoding="utf-8")
            _prefix, _spacing, items, _suffix = _policy_registry_items(policy)
            self.assertGreater(len(items), 1)
            changed_policy = policy.replace(items[0], "", 1)
            policy_path.write_text(
                changed_policy,
                encoding="utf-8",
                newline="\n",
            )
            pinned_source_sha256 = dict(_paper_verification._PINNED_SOURCE_SHA256)
            pinned_source_sha256[POLICY_PROVENANCE_RELATIVE] = (
                hashlib.sha256(changed_policy.encode("utf-8")).hexdigest().upper()
            )
            with mock.patch.object(
                _paper_verification,
                "_PINNED_SOURCE_SHA256",
                pinned_source_sha256,
            ):
                with self.assertRaises(PaperLatexVerificationError) as caught:
                    _paper_verification._verify_static_paper_latex_at(root)
            self.assertEqual(caught.exception.reason_code, "source_grammar_invalid")
        finally:
            temporary.cleanup()

    def test_production_and_cli_ast_allowlists_and_mutation_sensitivity(self):
        production = (REPOSITORY / "iclr2027/paper_latex_verification.py").read_text(
            encoding="utf-8"
        )
        cli = (REPOSITORY / "verify_iclr2027_paper_latex.py").read_text(
            encoding="utf-8"
        )
        _assert_safe_ast(production, cli=False)
        _assert_safe_ast(cli, cli=True)
        attacks = (
            "\nimport subprocess\n",
            "\nimport socket\n",
            "\nimport http.client\n",
            "\nimport urllib.request\n",
            "\nimport importlib\n",
            "\n__import__('os')\n",
            "\ngetattr(object, 'x')\n",
            "\nsetattr(object, 'x', 1)\n",
            "\ndelattr(object, 'x')\n",
            "\nglobals()\n",
            "\nlocals()\n",
            "\nvars()\n",
            "\neval('1')\n",
            "\nexec('x=1')\n",
            "\ncompile('1', 'x', 'eval')\n",
            "\nopen('x', 'w')\n",
            "\nopen('x', 'a')\n",
            "\nopen('x', 'x')\n",
            "\nopen('x', 'r+')\n",
            "\nPath('x').write_text('x')\n",
            "\nPath('x').write_bytes(b'x')\n",
            "\nPath('x').unlink()\n",
            "\nPath('x').mkdir()\n",
            "\nPath('x').rmdir()\n",
            "\nPath('x').touch()\n",
            "\nPath('x').rename('y')\n",
            "\nPath('x').replace('y')\n",
            "\nPath('x').chmod(0o600)\n",
            "\nPath('x').read_text()\n",
            "\n__loader__.load_module('subprocess').run(['x'])\n",
            "\nAlias = Path\nAlias('x').replace('y')\n",
            "\nPath.cwd().joinpath('x').read_text()\n",
            "\nreader = Path('x').read_text\nreader()\n",
            "\nAlias: object = Path\nAlias('x').replace('y')\n",
            "\nmutate = Path('x').unlink\nmutate()\n",
            "\n__spec__.loader.get_data('x')\n",
            "\npath: Path = Path('x')\npath.replace('y')\n",
            "\n(Path('x') / 'child').replace('y')\n",
            "\n(path := Path('x')).replace('y')\n",
            "\nPath('x').stat()\n",
            "\nmutate = Path('x').replace\nmutate('y')\n",
        )
        for source, is_cli in ((production, False), (cli, True)):
            for attack in attacks:
                with self.subTest(cli=is_cli, attack=attack.strip()):
                    with self.assertRaises(AssertionError):
                        _assert_safe_ast(source + attack, cli=is_cli)
        import_drifts = (
            production.replace("import hashlib", "import hashlib as digest", 1),
            production.replace(
                "from dataclasses import dataclass, fields",
                "from dataclasses import fields, dataclass",
                1,
            ),
            production.replace(
                "import hashlib\nimport json", "import json\nimport hashlib", 1
            ),
            cli.replace("import sys", "import sys as system", 1),
            cli.replace(
                "PaperLatexVerificationError,\n    PaperStaticReceipt,",
                "PaperStaticReceipt,\n    PaperLatexVerificationError,",
                1,
            ),
        )
        for index, drift in enumerate(import_drifts):
            with self.subTest(import_drift=index):
                with self.assertRaises(AssertionError):
                    _assert_safe_ast(drift, cli=index >= 3)

    def test_exact_capability_reference_policy_rejects_existing_expression_escapes(
        self,
    ):
        production = (REPOSITORY / "iclr2027/paper_latex_verification.py").read_text(
            encoding="utf-8"
        )
        cli = (REPOSITORY / "verify_iclr2027_paper_latex.py").read_text(
            encoding="utf-8"
        )
        _assert_safe_ast(production, cli=False)
        _assert_safe_ast(cli, cli=True)
        production_attacks = (
            "\n(_PAPER_RELATIVE / 'child').replace(_PAPER_RELATIVE)\n",
            "\ncandidate: object = _PAPER_RELATIVE\ncandidate.replace(_PAPER_RELATIVE)\n",
            "\n(candidate := _PAPER_RELATIVE).replace(_PAPER_RELATIVE)\n",
            "\n_PAPER_RELATIVE.with_suffix('.tmp').replace(_PAPER_RELATIVE)\n",
            "\nmutate = _PAPER_RELATIVE.symlink_to\nmutate(_PAPER_RELATIVE)\n",
            "\nreader = _PAPER_RELATIVE.resolve\nreader()\n",
            "\nhashlib.__spec__.loader.get_filename('x')\n",
        )
        for attack in production_attacks:
            with self.subTest(file="production", attack=attack.strip()):
                with self.assertRaisesRegex(
                    AssertionError, "capability reference drift"
                ):
                    _assert_safe_ast(production + attack, cli=False)
        with self.subTest(file="cli", attack="attribute module-spec loader"):
            with self.assertRaisesRegex(AssertionError, "capability reference drift"):
                _assert_safe_ast(
                    cli + "\nsys.__spec__.loader.get_filename('x')\n",
                    cli=True,
                )

    def test_exact_ast_structure_rejects_indirect_capabilities_and_any_added_node(self):
        production = (REPOSITORY / "iclr2027/paper_latex_verification.py").read_text(
            encoding="utf-8"
        )
        cli = (REPOSITORY / "verify_iclr2027_paper_latex.py").read_text(
            encoding="utf-8"
        )
        self.assertEqual(
            _normalized_ast_sha256(production),
            PRODUCTION_AST_STRUCTURE_SHA256,
        )
        self.assertEqual(_normalized_ast_sha256(cli), CLI_AST_STRUCTURE_SHA256)
        _assert_safe_ast(production, cli=False)
        _assert_safe_ast(cli, cli=True)

        indirect_attacks = (
            (
                production,
                False,
                "\nreader = type(_PAPER_RELATIVE).__dict__['read_text']\n",
            ),
            (
                production,
                False,
                "\nreader = object.__getattribute__(_PAPER_RELATIVE, 'resolve')\n",
            ),
            (
                production,
                False,
                "\nreader = _PAPER_RELATIVE.__class__.__dict__['write_text']\n",
            ),
            (
                cli,
                True,
                "\nloader = object.__getattribute__(sys, '__spec__')\n",
            ),
        )
        for source, is_cli, attack in indirect_attacks:
            with self.subTest(cli=is_cli, indirect=attack.strip()):
                self.assertNotEqual(
                    _normalized_ast_sha256(source + attack),
                    CLI_AST_STRUCTURE_SHA256
                    if is_cli
                    else PRODUCTION_AST_STRUCTURE_SHA256,
                )
                with self.assertRaisesRegex(
                    AssertionError,
                    "AST structural digest drift",
                ):
                    _assert_safe_ast(source + attack, cli=is_cli)

        node_drifts = (
            (production, False, "\nmarker = 1\n"),
            (production, False, "\nvalue = hashlib.sha256\n"),
            (production, False, "\nlen(())\n"),
            (production, False, "\nimport math\n"),
            (cli, True, "\nmarker = 1\n"),
        )
        for source, is_cli, addition in node_drifts:
            with self.subTest(cli=is_cli, added_node=addition.strip()):
                with self.assertRaises(AssertionError):
                    _assert_safe_ast(source + addition, cli=is_cli)

    def test_runtime_default_verifier_has_no_write_process_or_network_effect(self):
        original_open = os.open

        def observed_open(path, flags, *args, **kwargs):
            forbidden = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
            if flags & forbidden:
                raise AssertionError("write-capable open")
            return original_open(path, flags, *args, **kwargs)

        with (
            mock.patch.object(os, "open", side_effect=observed_open),
            mock.patch.object(
                builtins, "open", side_effect=AssertionError("builtin open")
            ),
            mock.patch.object(
                subprocess, "Popen", side_effect=AssertionError("process")
            ),
            mock.patch.object(socket, "socket", side_effect=AssertionError("network")),
        ):
            self.assertEqual(
                verify_static_paper_latex().status, "literature_corrected_static_ready"
            )


class StaticVerifierCliTests(unittest.TestCase):
    class _WindowsTranslatedCapture:
        def __init__(self) -> None:
            self.buffer = io.BytesIO()

        def write(self, value: str) -> int:
            self.buffer.write(value.replace("\n", "\r\n").encode("utf-8"))
            return len(value)

        def flush(self) -> None:
            return None

    def _run(self, argv: list[str]):
        stdout = self._WindowsTranslatedCapture()
        stderr = self._WindowsTranslatedCapture()
        with (
            mock.patch.object(_paper_cli.sys, "stdout", stdout),
            mock.patch.object(_paper_cli.sys, "stderr", stderr),
        ):
            code = _paper_cli.main(argv)
        return (
            code,
            stdout.buffer.getvalue().decode("utf-8"),
            stderr.buffer.getvalue().decode("utf-8"),
        )

    def _run_raw(self, argv: list[str]):
        stdout = self._WindowsTranslatedCapture()
        stderr = self._WindowsTranslatedCapture()
        with (
            mock.patch.object(_paper_cli.sys, "stdout", stdout),
            mock.patch.object(_paper_cli.sys, "stderr", stderr),
        ):
            code = _paper_cli.main(argv)
        return code, stdout.buffer.getvalue(), stderr.buffer.getvalue()

    def test_every_cli_path_emits_exact_lf_only_bytes(self):
        self.assertEqual(self._run_raw(["--help"]), (0, HELP_TEXT.encode("utf-8"), b""))
        self.assertEqual(
            self._run_raw(["--unknown"]),
            (2, b"", _error_json("invalid_cli_argument").encode("utf-8")),
        )
        code, stdout, stderr = self._run_raw([])
        self.assertEqual(code, 0)
        self.assertEqual(stderr, b"")
        self.assertEqual(stdout, EXPECTED_RECEIPT_JSON.encode("utf-8") + b"\n")
        for reason_code in ERROR_CODES:
            with self.subTest(reason_code=reason_code):
                with mock.patch.object(
                    _paper_cli,
                    "verify_static_paper_latex",
                    side_effect=PaperLatexVerificationError(reason_code),
                ):
                    self.assertEqual(
                        self._run_raw([]),
                        (1, b"", _error_json(reason_code).encode("utf-8")),
                    )

    def test_help_unknown_success_and_validation_failure_bytes_are_exact(self):
        self.assertEqual(self._run(["--help"]), (0, HELP_TEXT, ""))
        self.assertEqual(
            self._run(["--unknown"]), (2, "", _error_json("invalid_cli_argument"))
        )
        code, stdout, stderr = self._run([])
        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(stdout, EXPECTED_RECEIPT_JSON + "\n")
        for reason_code in ERROR_CODES:
            with self.subTest(reason_code=reason_code):
                with mock.patch.object(
                    _paper_cli,
                    "verify_static_paper_latex",
                    side_effect=PaperLatexVerificationError(reason_code),
                ):
                    self.assertEqual(self._run([]), (1, "", _error_json(reason_code)))

    def test_cli_paths_are_deterministic_and_do_not_write_spawn_or_network(self):
        cases = (
            ([], None),
            (["--help"], None),
            (["--unknown"], None),
            ([], "source_grammar_invalid"),
        )
        for argv, failure in cases:
            with self.subTest(argv=argv, failure=failure):
                failure_context = (
                    mock.patch.object(
                        _paper_cli,
                        "verify_static_paper_latex",
                        side_effect=PaperLatexVerificationError(failure),
                    )
                    if failure is not None
                    else contextlib.nullcontext()
                )
                with (
                    failure_context,
                    mock.patch.object(
                        builtins, "open", side_effect=AssertionError("write")
                    ),
                    mock.patch.object(
                        subprocess, "Popen", side_effect=AssertionError("process")
                    ),
                    mock.patch.object(
                        socket, "socket", side_effect=AssertionError("network")
                    ),
                ):
                    first = self._run(argv)
                    second = self._run(argv)
                self.assertEqual(first, second)
