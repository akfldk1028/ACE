"""Behavioral contract for the registered estimand-receipt manuscript."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import shutil
import tempfile
import unittest

from iclr2027.paper_latex_verification import (
    PaperLatexVerificationError,
    verify_estimand_receipt_manuscript_at,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT_AUXILIARY_FILES = (
    "iclr2027_conference.sty",
    "iclr2027_conference.bst",
)
PRIMARY_CITATIONS = (
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


class EstimandReceiptManuscriptContractTests(unittest.TestCase):
    """Exercise the verifier at the manuscript boundary, including mutations."""

    def _verify_mutation(
        self,
        relative: str,
        mutate: Callable[[str], str],
        expected_reason: str,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            latex = root / "latex"
            latex.mkdir()
            for name in ("main.tex", "references.bib"):
                shutil.copyfile(REPOSITORY_ROOT / "latex" / name, latex / name)
            for name in MANUSCRIPT_AUXILIARY_FILES:
                source = REPOSITORY_ROOT / "latex" / name
                if source.is_file():
                    shutil.copyfile(source, latex / name)
            target = root / relative
            original = target.read_text(encoding="utf-8")
            changed = mutate(original)
            self.assertNotEqual(changed, original)
            target.write_text(changed, encoding="utf-8", newline="\n")
            with self.assertRaises(PaperLatexVerificationError) as raised:
                verify_estimand_receipt_manuscript_at(root)
            self.assertEqual(raised.exception.reason_code, expected_reason)

    def _verification_outcome(self, main_source: str) -> str:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            latex = root / "latex"
            latex.mkdir()
            (latex / "main.tex").write_text(main_source, encoding="utf-8", newline="\n")
            shutil.copyfile(
                REPOSITORY_ROOT / "latex" / "references.bib",
                latex / "references.bib",
            )
            for name in MANUSCRIPT_AUXILIARY_FILES:
                source = REPOSITORY_ROOT / "latex" / name
                if source.is_file():
                    shutil.copyfile(source, latex / name)
            try:
                return verify_estimand_receipt_manuscript_at(root).status
            except PaperLatexVerificationError as error:
                return error.reason_code

    @staticmethod
    def _replace_once(old: str, new: str) -> Callable[[str], str]:
        def mutate(source: str) -> str:
            if source.count(old) != 1:
                raise AssertionError(f"expected one mutation witness: {old!r}")
            return source.replace(old, new, 1)

        return mutate

    def test_registered_story_and_three_evidence_objects_verify(self) -> None:
        receipt = verify_estimand_receipt_manuscript_at(REPOSITORY_ROOT)
        self.assertEqual(receipt.status, "verified")
        self.assertEqual(
            receipt.title,
            "When Is Planned Coordination Evaluable? Estimand-Specific "
            "Receipts for Randomized Multi-Agent Experiments",
        )
        self.assertEqual(
            receipt.evidence_objects,
            (
                "fig:estimand-support-lattice",
                "fig:inference-consequence",
                "tab:evaluator-comparison",
            ),
        )
        self.assertEqual(receipt.format_status, "official-iclr2027-submission")
        self.assertEqual(receipt.source_file_count, 4)

    def test_official_iclr_style_is_closed_and_colm_is_rejected(self) -> None:
        receipt = verify_estimand_receipt_manuscript_at(REPOSITORY_ROOT)
        self.assertEqual(receipt.format_status, "official-iclr2027-submission")
        main = (REPOSITORY_ROOT / "latex" / "main.tex").read_text(encoding="utf-8")
        self.assertEqual(main.count("\\usepackage{iclr2027_conference}"), 1)
        self.assertEqual(main.count("\\bibliographystyle{iclr2027_conference}"), 1)
        self.assertNotIn("colm", main.casefold())
        for filename in MANUSCRIPT_AUXILIARY_FILES:
            with self.subTest(filename=filename):
                self.assertTrue((REPOSITORY_ROOT / "latex" / filename).is_file())
        self._verify_mutation(
            "latex/main.tex",
            self._replace_once(
                "\\usepackage{iclr2027_conference}",
                "\\usepackage[submission]{colm2026_conference}",
            ),
            "source_grammar_invalid",
        )

    def test_t1_font_encoding_is_unique_canonical_and_mutation_closed(self) -> None:
        documentclass = "\\documentclass{article}"
        font_encoding = "\\usepackage[T1]{fontenc}"
        conference_style = "\\usepackage{iclr2027_conference}"
        current = (REPOSITORY_ROOT / "latex" / "main.tex").read_text(encoding="utf-8")
        canonical_prefix = documentclass + "\n" + font_encoding + "\n"
        canonical = (
            current
            if current.startswith(canonical_prefix)
            else current.replace(documentclass + "\n", canonical_prefix, 1)
        )
        removal = canonical.replace(font_encoding + "\n", "", 1)
        misordered = canonical.replace(font_encoding + "\n", "", 1).replace(
            conference_style + "\n",
            conference_style + "\n" + font_encoding + "\n",
            1,
        )
        duplicate = canonical.replace(
            font_encoding + "\n",
            font_encoding + "\n" + font_encoding + "\n",
            1,
        )
        expectations = (
            ("canonical", canonical, "verified"),
            ("removal", removal, "source_grammar_invalid"),
            ("misordered", misordered, "source_grammar_invalid"),
            ("duplicate", duplicate, "source_grammar_invalid"),
        )
        for name, source, expected in expectations:
            with self.subTest(name=name):
                self.assertEqual(self._verification_outcome(source), expected)

    def test_status_macros_and_title_are_spacing_safe_and_mutation_closed(self) -> None:
        main = (REPOSITORY_ROOT / "latex" / "main.tex").read_text(encoding="utf-8")
        raw_title = (
            "\\title{When Is Planned Coordination Evaluable?\\\\\n"
            "Estimand-Specific Receipts for Randomized\\\\\n"
            "Multi-Agent Experiments}"
        )
        self.assertEqual(main.count(raw_title), 1)
        self.assertNotIn("\\hyphenation{Experiments}", main)
        self.assertEqual(main.count("\\usepackage{xspace}"), 1)
        for macro in ("cert", "bounded", "notcert"):
            with self.subTest(macro=macro):
                declaration = f"\\newcommand{{\\{macro}}}"
                line = next(line for line in main.splitlines() if declaration in line)
                self.assertTrue(line.endswith("\\xspace}"))
        receipt = verify_estimand_receipt_manuscript_at(REPOSITORY_ROOT)
        self.assertEqual(
            receipt.title,
            "When Is Planned Coordination Evaluable? Estimand-Specific "
            "Receipts for Randomized Multi-Agent Experiments",
        )
        self._verify_mutation(
            "latex/main.tex",
            self._replace_once(
                "\\newcommand{\\notcert}{\\textsc{Not-Certified}\\xspace}",
                "\\newcommand{\\notcert}{\\textsc{Not-Certified}}",
            ),
            "source_grammar_invalid",
        )

    def test_internal_task_labels_are_absent_and_mutation_closed(self) -> None:
        main = (REPOSITORY_ROOT / "latex" / "main.tex").read_text(encoding="utf-8")
        self.assertNotIn("Task 7", main)
        self.assertNotIn("Task 11", main)
        self._verify_mutation(
            "latex/main.tex",
            self._replace_once(
                "\\subsection{Public artifact and external transport evidence}",
                "\\subsection{Task 7 evidence and external transport}",
            ),
            "scientific_boundary_invalid",
        )
        self._verify_mutation(
            "latex/main.tex",
            self._replace_once(
                "the frozen retained-results report",
                "the frozen Task 11 report",
            ),
            "scientific_boundary_invalid",
        )

    def test_narrow_novelty_and_synthetic_boundary_are_mutation_closed(self) -> None:
        self._verify_mutation(
            "latex/main.tex",
            self._replace_once(
                "We specialize existing support-identifiability principles to "
                "randomized multi-agent experiments.",
                "We introduce the first general support-identifiability theorem "
                "for agent systems.",
            ),
            "scientific_boundary_invalid",
        )
        self._verify_mutation(
            "latex/main.tex",
            self._replace_once(
                "The benchmark is synthetic and provides no causal result about "
                "real buildings or evidence about a sampled Architecture "
                "population.",
                "The benchmark establishes causal gains for real Architecture "
                "workflows.",
            ),
            "scientific_boundary_invalid",
        )

    def test_point_metrics_and_two_clean_denominators_are_exact(self) -> None:
        main = (REPOSITORY_ROOT / "latex" / "main.tex").read_text(encoding="utf-8")
        for forbidden in (
            "Clopper--Pearson",
            "[0, 0.00000261898]",
            "[0.9999901231,1]",
            "[0.9486606790, 0.9500696340]",
            "[0.0485384137, 0.0514015660]",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, main)
        mutations = (
            ("1,408,516", "1,408,515"),
            ("373,484/373,484", "373,483/373,484"),
            (
                "354{,}574/373{,}484=0.9493686477",
                "354{,}574/373{,}484=0.9493686476",
            ),
            ("4,479/89,660", "4,478/89,660"),
            (
                "4,479/89,660, namely $0.0499553870$",
                "4,479/89,660, namely $0.0499553869$",
            ),
            ("0/54,000", "0/12,000"),
            ("389/12,000", "0/54,000"),
        )
        for old, new in mutations:
            with self.subTest(old=old):
                self._verify_mutation(
                    "latex/main.tex",
                    self._replace_once(old, new),
                    "scientific_boundary_invalid",
                )

        self._verify_mutation(
            "latex/main.tex",
            self._replace_once(
                "Fatal-fault false reportability was $0/1{,}408{,}516=0$.",
                "Fatal-fault false reportability was "
                "$0/1{,}408{,}516=0$ with an exact 95\\% "
                "Clopper--Pearson interval.",
            ),
            "scientific_boundary_invalid",
        )

    def test_frozen_claim_is_synthetic_consistency_not_comparative_validity(
        self,
    ) -> None:
        main = (REPOSITORY_ROOT / "latex" / "main.tex").read_text(encoding="utf-8")
        narrow_claim = (
            "The frozen evidence establishes a target-specific structural "
            "separation against the co-designed oracle in this synthetic fault "
            "census: the corresponding one-component ablation falsely reported "
            "every unsupported case in each relevant one-family row, whereas "
            "the full gate reported none. It does not establish independent "
            "empirical validity, general fault-diagnosis ability, causal "
            "recovery, or comparative inferential improvement."
        )
        self.assertEqual(main.count(narrow_claim), 1)
        self._verify_mutation(
            "latex/main.tex",
            self._replace_once(
                narrow_claim,
                "The full gate establishes superior fault diagnosis and "
                "inferential validity over all listed comparators.",
            ),
            "scientific_boundary_invalid",
        )

    def test_expectation_measure_is_explicit_and_mutation_closed(self) -> None:
        main = (REPOSITORY_ROOT / "latex" / "main.tex").read_text(encoding="utf-8")
        measure = (
            "For each simulated replicate, $U$ is uniform over its fixed "
            "64-position synthetic roster, and $\\E$ in the three estimands is "
            "the finite-roster mean conditional on that replicate's generated "
            "potential outcomes and retained design objects. Monte Carlo "
            "performance summaries, unlike the estimands, additionally average "
            "over the declared site, outcome, balanced-assignment, and "
            "fault-selection streams across 2,000 replicates. Neither measure "
            "averages over real Architecture projects or deployed agents."
        )
        self.assertEqual(main.count(measure), 1)
        self._verify_mutation(
            "latex/main.tex",
            self._replace_once(
                measure,
                "$\\E$ denotes an expectation over Architecture projects in general.",
            ),
            "scientific_boundary_invalid",
        )

    def test_posthoc_family_comparison_is_exact_and_provenance_bounded(self) -> None:
        main = (REPOSITORY_ROOT / "latex" / "main.tex").read_text(encoding="utf-8")
        rows = (
            "E & $\\tau_{\\mathrm{CB}}$ & 0/20{,}653 & "
            "20{,}653/24{,}000 & 20{,}653/20{,}653",
            "B & All three & 0/20{,}636 & 20{,}636/24{,}000 & 20{,}636/20{,}636",
            "T & All three & 0/20{,}565 & 20{,}565/24{,}000 & 20{,}565/20{,}565",
            "S & All three & 0/20{,}619 & 20{,}619/24{,}000 & 20{,}619/20{,}619",
            "G & All three & 0/20{,}600 & 20{,}600/24{,}000 & 20{,}600/20{,}600",
            "P & $\\Psi_N$ & 0/20{,}579 & 20{,}579/24{,}000 & 20{,}579/20{,}579",
        )
        for row in rows:
            with self.subTest(row=row):
                self.assertEqual(main.count(row), 1)
        provenance = (
            "This table is a post-hoc descriptive extraction from the "
            "pre-specified frozen configurations, not a confirmatory comparison "
            "backed by an external time-stamped commitment."
        )
        macro_boundary = (
            "The strongest independent held-out/external macro comparison was "
            "not preserved in the frozen payload, so we make no claim that its "
            "pre-specified margin criterion was met."
        )
        uncertainty = (
            "No defensible pooled Monte Carlo standard error is recoverable "
            "because replicate-level joint sufficient statistics and "
            "cross-estimand and cross-configuration covariance were not "
            "persisted."
        )
        for required in (provenance, macro_boundary, uncertainty):
            with self.subTest(required=required):
                self.assertEqual(main.count(required), 1)
        self._verify_mutation(
            "latex/main.tex",
            self._replace_once("20{,}653/20{,}653", "20{,}652/20{,}653"),
            "scientific_boundary_invalid",
        )
        self._verify_mutation(
            "latex/main.tex",
            self._replace_once(
                macro_boundary,
                "The independent held-out/external macro criterion was met.",
            ),
            "scientific_boundary_invalid",
        )

    def test_exact_witness_scope_is_narrow_and_mutation_closed(self) -> None:
        main = (REPOSITORY_ROOT / "latex" / "main.tex").read_text(encoding="utf-8")
        witness_scope = (
            "The eight finite witnesses cover one declared component--target "
            "example for each of $Z,A,E,B,T,S,G,P$; they do not cover every "
            "required component--target pair."
        )
        self.assertEqual(main.count(witness_scope), 1)
        self._verify_mutation(
            "latex/main.tex",
            self._replace_once(
                witness_scope,
                "The witnesses cover every required component and target.",
            ),
            "scientific_boundary_invalid",
        )

    def test_appendix_contains_reviewable_assumptions_and_proofs(self) -> None:
        main = (REPOSITORY_ROOT / "latex" / "main.tex").read_text(encoding="utf-8")
        bibliography = main.index("\\bibliography{references}")
        appendix = main.index("\\appendix")
        self.assertLess(bibliography, appendix)
        for required in (
            "\\section{Mathematical Details and Assumptions}",
            "\\label{app:mathematical-details}",
            "\\subsection{Assumptions and support lattice}",
            "\\subsection{Component-relative nonidentification}",
            "\\subsection{Overlap-aware bounded contrast error}",
            "\\subsection{Terminal misclassification and selection}",
            "\\paragraph{Proof.}",
        ):
            with self.subTest(required=required):
                self.assertIn(required, main[appendix:])
        self.assertGreaterEqual(main[appendix:].count("\\paragraph{Proof.}"), 3)
        self._verify_mutation(
            "latex/main.tex",
            self._replace_once(
                "\\subsection{Overlap-aware bounded contrast error}",
                "\\subsection{Unproved bound}",
            ),
            "scientific_boundary_invalid",
        )

    def test_commitment_wording_and_synthetic_architecture_are_exact(self) -> None:
        main = (REPOSITORY_ROOT / "latex" / "main.tex").read_text(encoding="utf-8")
        self.assertNotIn("preregistered", main.casefold())
        self.assertNotIn("registered thresholds", main.casefold())
        wording = "pre-specified in the retained design narrative"
        self.assertEqual(main.count(wording), 1)
        self.assertIn("synthetic Architecture stress vocabulary", main)
        self._verify_mutation(
            "latex/main.tex",
            self._replace_once(wording, "preregistered before any result existed"),
            "scientific_boundary_invalid",
        )

    def test_task7_transport_and_custody_disclosures_cannot_be_promoted(self) -> None:
        mutations = (
            (
                "The original V2 held-out run was an invalid harness, not a "
                "case-level result; V3 was a vocabulary-only technical rerun.",
                "The V2 failure was rescued by V3.",
            ),
            (
                "The external AgentTelemetry check tests schema-identity "
                "transport only; it is not causal evidence and does not validate "
                "the synthetic Architecture setting.",
                "The external AgentTelemetry check causally validates the "
                "Architecture setting.",
            ),
            (
                "Two matching roots are retained, but the post-hoc custody "
                "correction cannot cryptographically prove the historical "
                "absence of a deleted third execution.",
                "Two retained roots cryptographically prove that no third "
                "execution ever existed.",
            ),
        )
        for old, new in mutations:
            with self.subTest(old=old):
                self._verify_mutation(
                    "latex/main.tex",
                    self._replace_once(old, new),
                    "scientific_boundary_invalid",
                )

    def test_ai_use_statement_and_primary_citations_are_required(self) -> None:
        self._verify_mutation(
            "latex/main.tex",
            self._replace_once(
                "Humans remain responsible for every claim, source, proof, "
                "implementation decision, result interpretation, and the final "
                "text.",
                "The AI system is responsible for the scientific claims.",
            ),
            "scientific_boundary_invalid",
        )
        main = (REPOSITORY_ROOT / "latex" / "main.tex").read_text(encoding="utf-8")
        self.assertIn(
            "These foundations supply identification tools; they are not "
            "contributions of this paper.",
            main,
        )
        self.assertIn(
            "None of the trace or telemetry studies establishes our synthetic "
            "outcome model or comparative evaluator performance.",
            main,
        )
        for citation in PRIMARY_CITATIONS:
            with self.subTest(citation=citation):
                self._verify_mutation(
                    "latex/references.bib",
                    lambda source, key=citation: source.replace(
                        f"{{{key},", f"{{removed{key},", 1
                    ),
                    "scientific_boundary_invalid",
                )

    def test_structure_rejects_legacy_or_extra_evidence_objects(self) -> None:
        self._verify_mutation(
            "latex/main.tex",
            lambda source: source.replace(
                "\\end{document}",
                "\\begin{figure}Legacy termination plot.\\end{figure}\n\\end{document}",
                1,
            ),
            "source_grammar_invalid",
        )
        self._verify_mutation(
            "latex/main.tex",
            self._replace_once(
                "\\usepackage{iclr2027_conference}",
                "\\usepackage[submission]{colm2026_conference}",
            ),
            "source_grammar_invalid",
        )


if __name__ == "__main__":
    unittest.main()
