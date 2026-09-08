"""Recoverable twelve-stage cycle. Exit 75 requests external work, never completion."""
import argparse
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[3]
# Sibling modules (lineage) must import whether this file runs as a script
# or is loaded from its path by the tests.
SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


class CycleError(RuntimeError):
    pass


class Pending(Exception):
    pass


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def digest(path):
    path = Path(path)
    if not path.is_file() or not path.stat().st_size:
        raise CycleError(f"missing or empty prerequisite artifact: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_asset(directory, reference):
    """Delivery assets must remain valid inside an immutable directory snapshot."""
    parsed = urlsplit(str(reference))
    relative = Path(unquote(parsed.path))
    path = (directory / relative).resolve()
    if (parsed.scheme or parsed.netloc or relative.is_absolute()
            or not path.is_relative_to(directory.resolve()) or not path.is_file()):
        raise CycleError(f'delivery asset is missing or outside its snapshot: {reference}')
    return path


def delivery_files(directory, study=False):
    """Freeze the whole delivery tree, including machine-readable evidence."""
    directory = Path(directory).resolve()
    required = ['study.html', 'study.json'] if study else ['board.html', 'board-key.json']
    for name in required:
        digest(directory / name)
    files = sorted(p for p in directory.rglob('*') if p.is_file())
    for path in files:
        if not path.resolve().is_relative_to(directory):
            raise CycleError(f'delivery asset escapes snapshot: {path}')

    class Assets(HTMLParser):
        def handle_starttag(self, tag, attrs):
            for key, value in attrs:
                if key in ('src', 'href') and value and not value.startswith(('data:', '#')):
                    local_asset(self.directory, value)
            if tag == 'base':
                raise CycleError('delivery asset base URLs are not supported')

    for path in files:
        if path.suffix.lower() == '.html':
            parser = Assets()
            parser.directory = path.parent
            parser.feed(path.read_text(encoding='utf-8'))
    if study:
        for row in read(directory / 'study.json')['alternatives']:
            for key in ('tile', 'drawings', 'sequence', 'parking_plan'):
                if row.get(key):
                    local_asset(directory, row[key])
    return files


def pair_votes(paths, expected):
    if len(paths) != 3 or len({Path(p).resolve() for p in paths}) != 3 or not expected:
        raise CycleError("pair jury requires three distinct complete ballots and at least one pair")
    result = {p: [] for p in expected}
    for path in paths:
        votes = re.findall(r"^PAIR\s+(p\d+):\s*([AB])\b", Path(path).read_text(encoding="utf-8"), re.M)
        if len(votes) != len(expected) or {p for p, _ in votes} != expected:
            raise CycleError(f"incomplete, duplicate or unknown pair ballot: {path}")
        for p, vote in votes:
            result[p].append(vote)
    return result


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("round")
    p.add_argument("count", nargs="?", type=int, default=18)
    p.add_argument("--from", dest="from_step", type=int, choices=range(1, 13), default=1)
    p.add_argument("--agent-mode", choices=("external", "internal"), default="external")
    p.add_argument("--author-model", default=os.environ.get("AUTHOR_MODEL"))
    p.add_argument("--book-count", type=int, default=int(os.environ.get("BOOK_COUNT", "120")))
    p.add_argument("--book-payload", type=Path)
    p.add_argument("--develop-count", type=int, default=6)
    p.add_argument("--new-era", metavar="REASON")
    p.add_argument("--baseline", type=Path, help="preserved artifact directory with manifest.json")
    p.add_argument("--repair-inputs", action="store_true", help="accept repaired input only before its successful generation")
    p.add_argument("--restage-unscored", metavar="REASON",
                   help="preserve an unscored stage, rebuild both tracks and require fresh jurors")
    return p


class Cycle:
    def __init__(self, args):
        self.args = args
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", args.round):
            raise CycleError("round must contain only letters, digits, underscore or hyphen")
        if min(args.count, args.book_count, args.develop_count) < 1:
            raise CycleError("counts must be positive")
        self.ws = Path(os.environ["MASSV2_WS"]).resolve()
        self.backend = Path(os.environ["ARR_BACKEND"]).resolve()
        self.home = self.ws / "runs" / f"cycle-{args.round}"
        self.home.mkdir(parents=True, exist_ok=True)
        self.state_path = self.home / "state.json"
        self.book_run = f"book-{args.round}"
        self.corpus = self.ws / "inputs" / f"gen-{args.round}.json"
        self.book_payload = (args.book_payload or self.ws / "inputs" / f"book-{args.round}.json").resolve()
        config = {"round": args.round, "count": args.count, "book_count": args.book_count,
                  "develop_count": args.develop_count, "book_payload": str(self.book_payload),
                  "pnu": os.environ.get("PNU"), "track": os.environ.get("TRACK"),
                  "building_type": os.environ.get("BUILDING_TYPE")}
        config.update(new_era=args.new_era, baseline=str(args.baseline.resolve()) if args.baseline else None)
        if args.new_era and not args.baseline:
            raise CycleError("--new-era requires --baseline with the preserved pre-change artifacts")
        self.state = read(self.state_path) if self.state_path.exists() else {
            "schema": 2, "config": config, "actions": {}, "steps": [], "status": "running"}
        if self.state["config"] != config:
            raise CycleError("resume configuration changed; use original arguments or a new round")
        self.step = 0

    def save(self):
        write(self.state_path, self.state)

    def command(self, argv, cwd=None, env=None):
        log = self.home / "workers.log"
        with log.open("a", encoding="utf-8") as f:
            f.write("\n" + json.dumps([str(a) for a in argv], ensure_ascii=False) + "\n")
            f.flush()
            proc = subprocess.run([str(a) for a in argv], cwd=cwd or self.ws,
                                  env={**os.environ, **(env or {})}, stdout=f, stderr=f)
        if proc.returncode:
            raise CycleError(f"worker exited {proc.returncode}: {argv[1:3]}; see {log}")

    def py(self, tool, *args):
        self.command([sys.executable, "-X", "utf8", self.ws / "tools" / tool, *args])

    def helper(self, *args):
        self.command([sys.executable, "-X", "utf8", ROOT / "skills/mass-cycle/scripts/bridge.py", *args])

    def shell(self, skill, script, *args, env=None):
        self.command([os.environ.get("MASS_BASH") or shutil.which("bash"),
                      ROOT / "skills" / skill / "scripts" / script, *args], cwd=ROOT, env=env)

    def action(self, name, worker, outputs):
        prior = self.state["actions"].get(name)
        if prior is not None:
            for path, sha in prior["outputs"].items():
                if digest(path) != sha:
                    raise CycleError(f"completed artifact changed: {path}; use a new round")
            return
        worker()
        paths = outputs() if callable(outputs) else outputs
        self.state["actions"][name] = {"outputs": {str(path): digest(path) for path in paths}}
        self.save()

    def attempt(self, name, directory):
        """Preserve a failed worker's partial directory before retrying it."""
        directory = Path(directory).resolve()
        allowed = (self.ws / "runs", self.backend / "tmp_mass_check/c260-book")
        if not any(directory.is_relative_to(root.resolve()) and directory != root.resolve() for root in allowed):
            raise CycleError(f"worker output is outside its workspace: {directory}")
        attempts = self.state.setdefault("attempts", {})
        previous = attempts.get(name, 0)
        if directory.exists() and any(directory.iterdir()):
            if not previous:
                raise CycleError(f"untracked existing output: {directory}; use a new round")
            archive = directory.with_name(f"{directory.name}.failed-{previous}")
            if archive.exists():
                raise CycleError(f"retry archive already exists: {archive}")
            directory.rename(archive)
        attempts[name] = previous + 1
        self.save()

    def pending(self, kind, **details):
        data = {"status": "pending", "exit_code": 75, "round": self.args.round,
                "step": self.step, "kind": kind, "agent_mode": self.args.agent_mode,
                "resume": "rerun the identical cycle.sh command", **details}
        self.state["status"] = "pending"
        self.save()
        write(self.home / "pending.json", data)
        print(json.dumps(data, ensure_ascii=False), flush=True)
        raise Pending()

    def payload(self, path, role, count):
        if role == 'book-author' and 'book-author-contract' in self.state['actions']:
            self.action('book-author-contract', lambda: None, [])
        if not path.exists():
            book_inputs = None
            if role == 'book-author':
                directory = self.home / 'book-author'
                book_inputs = {key: str(directory / name) for key, name in (
                    ('prompt', 'PROMPT.txt'), ('schema', 'schema.json'), ('context', 'context.json'))}
                book_inputs['project_brief'] = str(self.home / 'brief.md')
                self.action('book-author-contract',
                            lambda: self.helper('book-author-contract', directory, count, self.book_run),
                            [Path(value) for value in book_inputs.values()])
            if self.args.agent_mode == "internal":
                if not self.args.author_model:
                    raise CycleError("internal author requires --author-model or AUTHOR_MODEL")
                agent_role = "developer" if role == "parti-developer" else role
                development_contract = (
                    f"Read {self.home / 'development-parent.json'} and resolve its exact source. "
                    f"Authored development requires parent, parent_shape_id and exactly {count} complete child schemes. "
                    if role == "parti-developer" else
                    f"Read {self.home / 'development-parent.json'} and {self.home / 'book-development-parent-contract.json'}. "
                    "Use mode exact-authored-development, inherit_parent_dimensions true, matching parent, parent_shape_id, parent_program_hash and complete geometry_programs. "
                    "Read site_feedback in the frozen parent contract. Address measured repair_requests while preserving the spatial principle and dimensional contract; explain each child's response and unresolved conflicts. Delivered children are remeasured against their own shape and certificate; visual preference does not certify parking. "
                    if role == "developer" else "")
                self.command(["node", ROOT / "dist/index.js", "--dir", ROOT / "agents" / agent_role,
                              "--model", self.args.author_model,
                              "--prompt", (f"Read {book_inputs['prompt']}, {book_inputs['schema']} and {book_inputs['context']} and your role contract. "
                                           f"Read {book_inputs['project_brief']} for project facts and design policy only; the BOOK schema takes precedence over any parti output instructions. "
                                           if book_inputs else f"Read {self.ws / 'brief.md'} and your role contract. ") +
                              development_contract +
                              f"Author {count} candidates to {path}. Run no pipeline stages."],
                             env={"GITAGENT_AUTH_FILE": str(ROOT / "auth.json")})
            else:
                if book_inputs:
                    self.pending(role, output=str(path), count=count, **book_inputs,
                                 contract='Use project_brief for project facts and design policy only. The live BOOK schema takes precedence over parti output instructions. Return its JSON object, not parti schemes.')
                self.pending(role, output=str(path), count=count,
                             brief=str(self.home / "brief.md"),
                             contract=("parti object with nonempty schemes" if role in ("parti-author", "parti-developer")
                                       else "BOOK payload for creative_program_author.authored_programs_from_payload; geometry_programs preferred"))
        value = read(path)
        if not isinstance(value, dict):
            raise CycleError(f"payload must be an object: {path}")
        if role in ("parti-author", "parti-developer"):
            if not isinstance(value.get("schemes"), list) or not value["schemes"]:
                raise CycleError(f"parti payload needs nonempty schemes: {path}")
            if len(value["schemes"]) != count:
                raise CycleError(f"parti payload contains {len(value['schemes'])} schemes; expected {count}")
        elif not any(isinstance(value.get(key), list) and value[key]
                     for key in ("geometry_programs", "programs", "candidates", "nodes")):
            raise CycleError(f"BOOK payload has no authored programs: {path}")
        return value

    def stage_files(self, stage, pairs=False):
        images = sorted(stage.glob("p*.png" if pairs else "t*.png"))
        if not images:
            raise CycleError(f"no {'pair' if pairs else 'tile'} images at {stage}")
        return [stage / "PROMPT.txt", *images] + ([] if pairs else [stage / "key.json"])

    def jury(self, stage, name, pairs=False):
        files = self.stage_files(stage, pairs)
        self.action(f"freeze-{name}", lambda: None, files)
        requests, ballots = [], []
        for i in range(1, 4):
            jury_root = self.home / "jury"
            if self.state.get('jury_generation'):
                jury_root /= f"restage-{self.state['jury_generation']:03d}"
            private = jury_root / name / f"juror-r{i}"
            private.mkdir(parents=True, exist_ok=True)
            for source in files:
                if source.name == "key.json":
                    continue
                target = private / source.name
                if target.exists() and digest(target) != digest(source):
                    raise CycleError(f"private jury input changed: {target}")
                if not target.exists():
                    shutil.copyfile(source, target)
            ballot = stage / f"r{i}.txt"
            authored = private / f"r{i}.txt"
            if authored.exists() and f"jury-{name}" not in self.state["actions"]:
                shutil.copyfile(authored, ballot)
            if not ballot.exists() and self.args.agent_mode == "internal":
                model = os.environ.get("JUROR_MODEL")
                if not model:
                    raise CycleError("internal jury requires explicit JUROR_MODEL; no fallback")
                self.command(["node", ROOT / "dist/index.js", "--dir", ROOT / "agents/juror",
                              "--model", model, "--prompt",
                              f"Read only {private}/PROMPT.txt and every image there. Write exactly "
                              f"the requested verdict to {authored}. Do not read other files."],
                             env={"GITAGENT_IO_ROOT": str(private), "GITAGENT_AUTH_FILE": str(ROOT / "auth.json")})
                if authored.exists():
                    shutil.copyfile(authored, ballot)
            if not ballot.exists():
                requests.append({"juror": i, "input_dir": str(private), "output": str(authored)})
            ballots.append(ballot)
        if requests:
            if self.args.agent_mode == "internal":
                raise CycleError("internal juror produced no ballot")
            self.pending("pairwise-jury" if pairs else "round-jury", stage=name, requests=requests,
                         contract="Three independent fresh jurors; only private PROMPT.txt and images")
        def verify():
            if pairs:
                pair_votes(ballots, {p.stem for p in stage.glob("p*.png")})
            else:
                for ballot in ballots:
                    self.py("vlm_shortlist.py", name, "--verify", ballot)
        self.action(f"jury-{name}", verify, ballots)
        return ballots

    def book_generate(self, name, payload, count, carry=True, development_contract=None):
        out = self.backend / "tmp_mass_check/c260-book" / name
        def generate():
            if development_contract is not None:
                self.helper('validate-book-development', payload, count, development_contract)
            else:
                self.helper("validate-book", payload, count)
            self.attempt(f"generate-{name}", out)
            self.command([sys.executable, "-X", "utf8", "manage.py", "generate_maas_creative_100",
                          "--count", count, "--pnu", os.environ["PNU"],
                          "--capacity-ceiling-m2", os.environ["GROUND_CAPACITY_M2"],
                          "--output-root", "tmp_mass_check/c260-book", "--run-id", name,
                          "--author-mode", "payload", "--author-payload", payload,
                          *(['--development-parent-contract', development_contract] if development_contract is not None else [])],
                         cwd=self.backend,
                         # The round salt: a payload reused across rounds meets a
                         # different rotation of the 59 principles each time.
                         env={"MAAS_BOOK_SCHEDULE_SALT": str(name)})
        self.action(f"generate-{name}", generate, [out / "maas-creative-portfolio.json", payload,
                    *([development_contract] if development_contract is not None else [])])
        if carry:
            self.action(f"carry-{name}", lambda: self.helper("carry-book", out),
                        [out / "maas-book-exact-geometry-artifacts.json"])
        stage = self.ws / "runs" / f"vlm-{name}"
        def import_book():
            self.attempt(f"import-{name}", stage)
            self.py("book_import.py", out, name)
        self.action(f"import-{name}", import_book,
                    lambda: self.stage_files(stage) + [self.ws / "runs/books" / f"{name}.json"])
        return out

    def development_parent(self):
        """Select one verified parent without conflating development with ranking."""
        selected = self.home / "development-parent.json"
        # Historical completed selections remain governed by their original receipts.
        if 'development-parent' in self.state['actions']:
            self.action('development-parent', lambda: None, [selected])
            return read(selected)
        board = self.home / 'board-key.json'
        choice = self.home / 'development-choice.json'
        self.action('development-candidates', lambda: None, [board])

        cohort = self.home / 'development-cohort.json'
        def select():
            from lineage import lineage_of, recent_lineages
            rows = read(board)
            eligible = [r for r in rows if re.fullmatch(r'O[1-9][0-9]*', str(r.get('label', '')))]
            if not eligible:
                raise CycleError("no scored overseas board parent available for development")
            # Six cycles developed one curved figure because the rule was the
            # top score and the board re-seated that figure's champions every
            # round. A figure developed in the last three cycles waits its turn
            # while another eligible figure exists; only an exhausted board
            # returns to a recent lineage, and the receipt says so.
            recent = recent_lineages(self.ws, self.args.round)
            fresh = [r for r in eligible if lineage_of(str(r.get('name', '')), self.ws) not in recent]
            pool = fresh or eligible
            if self.args.agent_mode == 'external':
                if not choice.exists():
                    self.pending('development-selector', output=str(choice), candidates=str(board),
                        candidates_sha256=digest(board), count=1,
                        required_fields=['name', 'shape_id', 'certificate_id', 'architectural_reason'],
                        recently_developed_lineages=recent,
                        eligible_names=[r['name'] for r in pool],
                        instruction='Review the frozen O candidates and their delivered geometry. Select one '
                        'parent for architectural development from eligible_names: figures developed in the '
                        'last three cycles (recently_developed_lineages) are excluded while another eligible '
                        'figure exists. Write its exact name, shape_id, certificate_id and a nonempty '
                        'architectural_reason in English. A lower-ranked eligible parent may be chosen; do not '
                        'change scores. Labels alone are not identities.')
                payload = read(choice)
                keys = ('name', 'shape_id', 'certificate_id', 'architectural_reason')
                if not isinstance(payload, dict) or any(
                        not isinstance(payload.get(k), str) or not payload[k].strip() for k in keys):
                    raise CycleError('development choice requires exact identity and architectural_reason')
                matches = [r for r in eligible if all(r.get(k) == payload[k] for k in keys[:3])]
                if len(matches) != 1:
                    raise CycleError('development choice is unknown, stale or ambiguous in frozen O candidates')
                top = matches[0]
                if fresh and top not in fresh:
                    raise CycleError(
                        f"development choice {top['name']} descends from "
                        f"{lineage_of(top['name'], self.ws)}, developed within the last three cycles; "
                        f"{len(fresh)} eligible parents of other lineages remain")
            else:
                top = pool[0]
            write(selected, top)
            write(cohort, {'rule': 'not developed in the last three completed cycles while another '
                                   'eligible figure exists',
                           'recently_developed_lineages': recent,
                           'parent_lineage': lineage_of(str(top.get('name', '')), self.ws),
                           'eligible_names': [r['name'] for r in eligible],
                           'fresh_names': [r['name'] for r in fresh],
                           'cohort_exhausted': not fresh})
        self.action('development-parent', select,
                    [selected, cohort, choice, board] if self.args.agent_mode == 'external'
                    else [selected, cohort, board])
        return read(selected)

    def develop(self):
        top = self.development_parent()
        parent = top["name"]
        out = self.ws / "runs" / f"develop-{self.args.round}"
        if parent.startswith("book:"):
            legacy_pairs = ('development-pairs' in self.state['actions']
                            and (out / 'mutants.json').exists()
                            and any(c.get('pair') for c in read(out / 'mutants.json')['children']))
            if not legacy_pairs:
                contract = self.home / 'book-development-parent-contract.json'
                self.action('book-development-parent-contract',
                    lambda: self.helper('book-development-contract', parent, top.get('shape_id', ''), contract),
                    [contract])
                revision = 1
                while True:
                    suffix = '' if revision == 1 else f'-r{revision}'
                    name = f'book-develop-{self.args.round}{suffix}'
                    action_name = f'development-pairs-book-exact{suffix}'
                    out = self.ws / 'runs' / f'develop-{self.args.round}-book-exact{suffix}'
                    if action_name in self.state['actions']:
                        if any(c.get('pair') for c in read(out / 'mutants.json')['children']):
                            break
                        revision += 1
                        continue
                    # A successful legacy generation freezes its payload too.
                    # Preserve it and use a new revision under the new contract.
                    generated = self.state['actions'].get(f'generate-{name}')
                    registry = self.ws / 'runs/books' / f'{name}.json'
                    legacy_generation = generated and str(contract) not in generated['outputs']
                    empty_import = (generated and registry.exists() and
                                    not read(registry).get('entries'))
                    if legacy_generation or empty_import:
                        revision += 1
                        continue
                    break
                payload = self.ws / 'inputs' / f'book-develop-{self.args.round}{suffix}.json'
                if not payload.exists() and self.args.agent_mode == 'external':
                    self.pending('book-developer', output=str(payload), parent=top,
                                 count=self.args.develop_count, revision=revision,
                                 parent_contract=str(contract),
                                 contract='mode exact-authored-development; exact parent, parent_shape_id, parent_program_hash; inherit_parent_dimensions true; exactly count complete geometry_programs; no automatic BOOK recipe. Read site_feedback in parent_contract and address measured repair_requests; explain each child response and unresolved conflicts. Child parking is remeasured after delivery; visual preference does not certify parking.',
                                 registry=str(self.ws / 'runs/books'))
                self.payload(payload, 'developer', self.args.develop_count)
                self.book_generate(name, payload, self.args.develop_count, carry=False,
                                   development_contract=contract)
                def make_pairs():
                    self.attempt(action_name, out)
                    self.helper('book-pairs', parent, name, out, top.get('shape_id', ''))
                self.action(action_name, make_pairs,
                            lambda: [payload, contract, out / 'mutants.json', *sorted((out / 'pairs').glob('p*.png'))])
        else:
            source_run = str(top.get("round") or self.args.round).removeprefix("vlm-")
            # Already frozen legacy pairs retain their original evidence. A legacy
            # height sweep with zero distinct children can request actual authorship
            # without releasing or overwriting its earlier receipt.
            legacy_pairs = ("development-pairs" in self.state["actions"]
                            and (out / "mutants.json").exists()
                            and any(c.get("pair") for c in read(out / "mutants.json")["children"]))
            if not legacy_pairs:
                revision = 1
                while True:
                    suffix = "" if revision == 1 else f"-r{revision}"
                    action_name = f"development-pairs-authored{suffix}"
                    out = self.ws / "runs" / f"develop-{self.args.round}-authored{suffix}"
                    if action_name not in self.state["actions"]:
                        break
                    if any(child.get("pair") for child in read(out / "mutants.json")["children"]):
                        break
                    revision += 1
                payload = self.ws / "inputs" / f"parti-develop-{self.args.round}{suffix}.json"
                if not payload.exists() and self.args.agent_mode == "external":
                    self.pending("parti-developer", output=str(payload), parent=top,
                                 count=self.args.develop_count, source_run=source_run,
                                 revision=revision,
                                 corpus=str(self.ws / "inputs"),
                                 contract="Object with exact parent variant, parent_shape_id and exactly count complete child schemes; unique child base names; preserve the dominant spatial move and address the jury's visual criticisms")
                self.payload(payload, "parti-developer", self.args.develop_count)
                def make_pairs():
                    self.attempt(action_name, out)
                    self.helper("authored-pairs", parent, source_run, self.args.develop_count,
                                out, top.get("shape_id", ""), payload)
                self.action(action_name, make_pairs,
                            lambda: [payload, out / "mutants.json", *sorted((out / "pairs").glob("p*.png"))])
        record = read(out / "mutants.json")
        if not any(child.get("pair") for child in record["children"]):
            self.pending("development-incomplete", parent=parent,
                         reason="no distinct legal child was delivered; no pairwise verdict possible",
                         artifacts=str(out))
        stage = out / "pairs"
        def prompt():
            (stage / "PROMPT.txt").write_text(
                "Compare every pair image independently. A and B are anonymous massing alternatives. "
                "Prefer coherent architectural composition, legible entry/outdoor spaces, and convincing "
                "roof/section with usable rooms. Read only this prompt and pair images. "
                "PLAN/SECTION panels are cuts of the same delivered sources; do not assume undrawn rooms, doors or stairs. "
                "For every image pNN.png write exactly one line: PAIR pNN: A or PAIR pNN: B, "
                "followed by a short visual reason. Choose A on an indistinguishable tie. Save UTF-8 without BOM.\n", encoding="utf-8")
        self.action("pair-prompt", prompt, [stage / "PROMPT.txt"])
        ballots = self.jury(stage, f"develop-{self.args.round}", pairs=True)
        worker = (lambda: self.helper("score-book", out, *ballots)) if parent.startswith("book:") else (
                  lambda: self.py("develop.py", out.name, "--score", *ballots))
        self.action("development-score", worker, [out / "champion.json"])
        champion = read(out / "champion.json")
        if champion.get("jurors") != 3 or not champion.get("feedback_written"):
            raise CycleError("development score has no complete jury/corpus feedback receipt")
        feedback = self.home / "feedback.json"
        self.action("feedback", lambda: write(feedback, {
            "parent": parent, "champion": champion.get("champion") or parent,
            "source": str(out / "champion.json"), "feedback_written": True}), [feedback])

    def run(self):
        if self.args.repair_inputs:
            self.repair_inputs()
        if self.args.from_step > 1 and any(i not in self.state["steps"] for i in range(1, self.args.from_step)):
            raise CycleError("missing prerequisite step receipts for --from; resume the original cycle or use a new round")
        for receipt in self.state["actions"].values():
            for path, sha in receipt["outputs"].items():
                if digest(path) != sha:
                    raise CycleError(f"completed artifact changed: {path}; use a new round")
        for restage in self.state.get('restages', []):
            archive = Path(restage['archive']).resolve()
            for entry in read(archive / 'manifest.json').values():
                path = archive / entry['archive_path']
                if (not path.resolve().is_relative_to(archive) or not path.is_file()
                        or hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']):
                    raise CycleError(f'preserved restage artifact changed: {path}')
        if self.args.restage_unscored:
            self.restage_unscored()
        if self.state["status"] == "complete":
            if self.state['schema'] >= 2 and 'complete' not in self.state['actions']:
                raise CycleError('missing completion receipt for schema 2 cycle')
            digest(self.home / "complete.json")
            print(json.dumps({"status": "complete", "receipt": str(self.home / "complete.json")}))
            return
        steps = [self.brief, self.author, self.validate, self.generate, self.book,
                 self.stage, self.judge, self.score, self.curate, self.bake, self.sheet, self.develop]
        for number, worker in enumerate(steps, 1):
            self.step = number
            if number < self.args.from_step:
                continue
            print(f"=== {number}. {worker.__name__} ===", flush=True)
            worker()
            if number not in self.state["steps"]:
                self.state["steps"].append(number)
            self.state["status"] = "running"
            self.save()
        completion = {"status": "complete", "round": self.args.round,
              "steps": self.state["steps"], "feedback": read(self.home / "feedback.json"),
              "board": str((self.home / 'board' if self.state['schema'] >= 2
                            else self.ws / 'runs/board') / 'board.html'),
              "sheet": str(self.ws / f"runs/study-{self.args.round}/study.html")}
        if self.state['schema'] >= 2:
            self.action('complete', lambda: write(self.home / 'complete.json', completion),
                        [self.home / 'complete.json'])
        else:
            write(self.home / 'complete.json', completion)
        self.state["status"] = "complete"
        self.save()
        (self.home / "pending.json").unlink(missing_ok=True)
        print(json.dumps({"status": "complete", "receipt": str(self.home / "complete.json")}))

    def restage_unscored(self):
        """Copy all old evidence before releasing only unscored delivery receipts.

        Successful authored/BOOK generation stays immutable. New private jury
        directories cannot inherit a verdict on the previous pictures. Normal
        worker attempts archive the superseded public stages when rebuilding.
        """
        reason = self.args.restage_unscored.strip()
        previous = self.state.get('restages', [])
        if previous and previous[-1]['reason'] == reason:
            return  # Leaving the same flag on a resume must not restage again.
        if not reason or self.args.from_step != 1:
            raise CycleError('--restage-unscored needs a reason and a full cycle resume')
        stages = [self.ws / 'runs' / f'vlm-{name}'
                  for name in (self.args.round, self.book_run)]
        if (any(n >= 8 for n in self.state['steps'])
                or any(n.startswith('score-') for n in self.state['actions'])
                or any((stage / 'vlm-shortlist.json').exists() for stage in stages)):
            raise CycleError('round already scored; preserve its board and use a new era/round')
        if self.state['status'] not in ('pending', 'failed') or 'stage' not in self.state['actions']:
            raise CycleError('--restage-unscored requires a stopped, staged round')
        # Validate every source path before copying, including symlink targets.
        runs = (self.ws / 'runs').resolve()
        sources = [self.state_path, self.home / 'pending.json', self.home / 'jury',
                   *stages, runs / 'books' / f'{self.book_run}.json']
        files = []
        for source in sources:
            if not source.exists():
                continue
            for path in (source.rglob('*') if source.is_dir() else [source]):
                if not path.resolve().is_relative_to(runs):
                    raise CycleError(f'restage source escapes workspace: {path}')
                if path.is_file():
                    files.append(path)
        serial = len(previous) + 1
        archive = self.home / f'restage-evidence-{serial:03d}'
        while archive.exists():  # A failed snapshot leaves original evidence intact.
            serial += 1
            archive = self.home / f'restage-evidence-{serial:03d}'
        if not archive.resolve().is_relative_to(runs):
            raise CycleError('restage archive escapes workspace')
        archive.mkdir()
        manifest = {}
        for source in files:
            target = archive / source.relative_to(runs)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            sha = hashlib.sha256(source.read_bytes()).hexdigest()
            if hashlib.sha256(target.read_bytes()).hexdigest() != sha:
                raise CycleError(f'restage snapshot mismatch: {source}')
            manifest[str(source)] = {'archive_path': str(target.relative_to(archive)), 'sha256': sha}
        write(archive / 'manifest.json', manifest)
        # Commit invalidation only after a complete verified snapshot exists.
        released = {'stage', f'import-{self.book_run}'}
        for name in (self.args.round, self.book_run):
            released.update((f'freeze-{name}', f'jury-{name}'))
        self.state['actions'] = {key: value for key, value in self.state['actions'].items()
                                 if key not in released}
        self.state['actions'][f'restage-evidence-{serial:03d}'] = {
            'outputs': {str(archive / 'manifest.json'): digest(archive / 'manifest.json')}}
        self.state['steps'] = [n for n in self.state['steps'] if n < 5]
        self.state['jury_generation'] = self.state.get('jury_generation', 0) + 1
        self.state['restages'] = [*previous, {'reason': reason, 'archive': str(archive),
                                             'jury_generation': self.state['jury_generation']}]
        self.state['status'] = 'running'
        self.save()

    def repair_inputs(self):
        for path, receipt, generation, step in (
                (self.corpus, "validate", "run", 3),
                (self.book_payload, "book-payload", f"generate-{self.book_run}", 5)):
            record = self.state["actions"].get(receipt)
            if not record or record["outputs"].get(str(path)) == digest(path):
                continue
            if generation in self.state["actions"]:
                raise CycleError(f"cannot repair delivered input {path}; use a new round and jury")
            self.state["actions"].pop(receipt)
            self.state["steps"] = [n for n in self.state["steps"] if n < step]
            self.state["status"] = "running"
            self.save()

    def brief(self):
        if self.args.new_era:
            def era():
                self.helper("new-era", self.args.new_era + " [cycle " + self.args.round + "]", self.args.baseline)
                shutil.copyfile(self.ws / "runs/board/era.json", self.home / "era.json")
            self.action("new-era", era, [self.home / "era.json"])
        def worker():
            self.shell("mass-author", "brief.sh", env={"MASS_AUTHOR_COUNT": str(self.args.count)})
            shutil.copyfile(self.ws / "brief.md", self.home / "brief.md")
        self.action("brief", worker, [self.home / "brief.md"])

    def author(self):
        # The author may repair invalid grammar until validation commits the
        # input digest. A structural check alone must not freeze bad input.
        self.payload(self.corpus, "parti-author", self.args.count)

    def validate(self):
        self.action("validate", lambda: self.shell("mass-validate", "validate.sh", self.corpus), [self.corpus])

    def generate(self):
        def worker():
            self.attempt("run", self.ws / "runs" / self.args.round)
            self.shell("mass-run", "run.sh", self.corpus, self.args.round)
        self.action("run", worker,
                    [self.ws / "runs" / self.args.round / "massv2-summary.json"])

    def book(self):
        def validate_payload():
            self.payload(self.book_payload, "book-author", self.args.book_count)
            self.helper("validate-book", self.book_payload, self.args.book_count)
        self.action("book-payload", validate_payload, [self.book_payload])
        self.book_generate(self.book_run, self.book_payload, self.args.book_count)

    def stage(self):
        stage = self.ws / "runs" / f"vlm-{self.args.round}"
        def worker():
            self.attempt("stage", stage)
            self.shell("mass-judge", "stage.sh", self.args.round, "14")
        self.action("stage", worker,
                    lambda: self.stage_files(stage))

    def judge(self):
        for name in (self.args.round, self.book_run):
            self.jury(self.ws / "runs" / f"vlm-{name}", name)

    def score(self):
        for name in (self.args.round, self.book_run):
            self.action(f"score-{name}", lambda name=name: self.shell("mass-judge", "score.sh", name),
                        [self.ws / "runs" / f"vlm-{name}" / "vlm-shortlist.json"])

    def curate(self):
        def worker():
            self.shell("mass-curate", "curate.sh")
            shutil.copyfile(self.ws / "runs/board/ledger.json", self.home / "ledger.json")
        self.action("curate", worker, [self.home / "ledger.json"])

    def bake(self):
        def worker():
            self.shell("mass-board", "bake.sh")
            shutil.copyfile(self.ws / "runs/board/board-key.json", self.home / "board-key.json")
        self.action("bake", worker, [self.home / "board-key.json"])
        if self.state['schema'] >= 2:
            snapshot = self.home / 'board'
            def board_snapshot():
                source = self.ws / 'runs/board'
                baked_key = digest(self.home / 'board-key.json')
                if digest(source / 'board-key.json') != baked_key:
                    raise CycleError('shared board changed after bake; cannot certify another cycle as this board')
                self.shell('mass-board', 'html.sh')
                files = delivery_files(source)
                self.attempt('board-snapshot', snapshot)
                for path in files:
                    target = snapshot / path.relative_to(source.resolve())
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, target)
                if digest(snapshot / 'board-key.json') != baked_key:
                    raise CycleError('shared board changed during snapshot; use the preserved cycle evidence')
            self.action('board-html', board_snapshot, lambda: delivery_files(snapshot))
        else:
            # Historical receipts retain their original fail-closed semantics.
            # Never copy today's board and certify it as an older cycle's board.
            self.action('board-html', lambda: self.shell('mass-board', 'html.sh'),
                        [self.ws / 'runs/board/board.html'])
        if self.args.baseline:
            self.action("pixel-diff", lambda: self.helper("pixel-diff", self.args.baseline, self.home / "pixel-diff.json"),
                        [self.home / "pixel-diff.json"])

    def sheet(self):
        directory = self.ws / 'runs' / f'study-{self.args.round}'
        self.action("sheet", lambda: self.py("study_sheet.py", self.args.round, f"study-{self.args.round}"),
                    lambda: delivery_files(directory, study=True) if self.state['schema'] >= 2
                    else [directory / 'study.html'])


def main():
    current = None
    try:
        current = Cycle(parser().parse_args())
        current.run()
        return 0
    except Pending:
        return 75
    except (CycleError, OSError, ValueError, KeyError) as exc:
        if current is not None and current.step > 0:
            current.state['status'] = 'failed'
            current.state['last_failure'] = {'step': current.step, 'reason': str(exc)}
            current.save()
        print(json.dumps({"status": "failed", "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
