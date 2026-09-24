from __future__ import annotations

import ast
from contextlib import redirect_stderr, redirect_stdout
import ctypes
from ctypes import wintypes
from dataclasses import replace
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.request

import build_iclr2027_oacs_preoutcome as build_cli
from build_iclr2027_oacs_preoutcome import main as build_main

from iclr2027.capability_binding import (
    CapabilityPacketManifest,
    CapabilityProfile,
    build_controller_catalog,
    build_crossover_plan,
)
from iclr2027.obligation_oracle import (
    BaselinePreOutcomeReadinessAuthority,
    MandatoryBaselineRoster,
    MandatoryBaselineRosterEntry,
)
from iclr2027.oacs_backend_audit import (
    ApprovalTrustRootV1,
    BackendAuditConfigV1,
    QuotaAssumptionV1,
    UsageAccountingV1,
    approval_digest,
    audit_backend,
)
from iclr2027.oacs_claim_ledger import (
    ClaimLedgerV1,
    ClaimRecordV1,
    claim_ledger_bytes,
)
from iclr2027.oacs_domain_census import (
    DomainCensusV1,
    DomainUnitV1,
    domain_census_bytes,
)
from iclr2027.oacs_power import DomainPowerPlanV1, domain_power_plan_bytes
from iclr2027.oacs_preflight import (
    OacsPreflightInputsV1,
    PreflightError,
    evaluate_preflight,
    preflight_receipt_bytes,
    validate_preflight_receipt_bytes,
    verify_preflight_receipt_bytes,
)
from iclr2027.oacs_review_harness import (
    FindingV1,
    build_review_package,
    lock_review_record,
    locked_review_bytes,
    review_package_bytes,
)
from iclr2027.oacs_study_contract import (
    OacsStudyContractV1,
    TreatmentSpecV1,
    study_contract_bytes,
)
import validate_iclr2027_oacs_preflight as validate_cli
from validate_iclr2027_oacs_preflight import main as validate_main


def _digest(label: str) -> str:
    return sha256(label.encode("utf-8")).hexdigest()


def _canonical(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def _windows_open_directory(path: Path, desired: int) -> object:
    handle = build_cli._secure_files._kernel32.CreateFileW(
        str(path),
        desired,
        0x0001 | 0x0002,
        None,
        build_cli._secure_files._OPEN_EXISTING,
        build_cli._secure_files._FILE_FLAG_BACKUP_SEMANTICS
        | build_cli._secure_files._FILE_FLAG_OPEN_REPARSE_POINT,
        None,
    )
    if handle == build_cli._secure_files._INVALID_HANDLE_VALUE:
        raise PermissionError(ctypes.get_last_error(), "directory access denied")
    return handle


def _windows_owner_reset_insert_restore(directory: Path, inserted: Path) -> bool:
    try:
        handle = _windows_open_directory(directory, 0x00020000 | 0x00040000)
    except PermissionError:
        return True
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    get_security = advapi32.GetSecurityInfo
    get_security.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.LPVOID,
        ctypes.POINTER(wintypes.LPVOID),
        wintypes.LPVOID,
        ctypes.POINTER(wintypes.LPVOID),
    )
    get_security.restype = wintypes.DWORD
    set_security = advapi32.SetSecurityInfo
    set_security.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.LPVOID,
        wintypes.LPVOID,
        wintypes.LPVOID,
    )
    set_security.restype = wintypes.DWORD
    local_free = build_cli._secure_files._kernel32.LocalFree
    local_free.argtypes = (wintypes.HLOCAL,)
    local_free.restype = wintypes.HLOCAL
    dacl = wintypes.LPVOID()
    descriptor = wintypes.LPVOID()
    try:
        result = get_security(
            handle,
            1,
            0x00000004,
            None,
            None,
            ctypes.byref(dacl),
            None,
            ctypes.byref(descriptor),
        )
        if result != 0:
            raise OSError(result, "cannot save directory DACL")
        result = set_security(handle, 1, 0x00000004, None, None, None, None)
        if result != 0:
            raise OSError(result, "cannot install permissive directory DACL")
        inserted.write_bytes(b"{}\n")
        result = set_security(
            handle,
            1,
            0x00000004 | 0x80000000,
            None,
            None,
            dacl,
            None,
        )
        if result != 0:
            raise OSError(result, "cannot restore directory DACL")
        return False
    finally:
        if descriptor:
            local_free(descriptor)
        build_cli._close_handle(handle)


def _windows_install_allow_before_deny(handle: object) -> None:
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    create_world_sid = advapi32.CreateWellKnownSid
    create_world_sid.argtypes = (
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.LPVOID,
        ctypes.POINTER(wintypes.DWORD),
    )
    create_world_sid.restype = wintypes.BOOL
    initialize_acl = advapi32.InitializeAcl
    initialize_acl.argtypes = (wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD)
    initialize_acl.restype = wintypes.BOOL
    add_allowed_ace = advapi32.AddAccessAllowedAceEx
    add_allowed_ace.argtypes = (
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
    )
    add_allowed_ace.restype = wintypes.BOOL
    add_denied_ace = advapi32.AddAccessDeniedAceEx
    add_denied_ace.argtypes = add_allowed_ace.argtypes
    add_denied_ace.restype = wintypes.BOOL
    set_security = advapi32.SetSecurityInfo
    set_security.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.LPVOID,
        wintypes.LPVOID,
        wintypes.LPVOID,
    )
    set_security.restype = wintypes.DWORD
    sid_length = wintypes.DWORD(68)
    world_sid = ctypes.create_string_buffer(sid_length.value)
    if not create_world_sid(1, None, world_sid, ctypes.byref(sid_length)):
        raise OSError("cannot construct world SID")
    acl_length = 8 + 2 * (8 + sid_length.value)
    dacl = ctypes.create_string_buffer(acl_length)
    if not initialize_acl(dacl, acl_length, 2):
        raise OSError("cannot initialize attack DACL")
    allowed = 0x00000006 | 0x00010000 | 0x00020000 | 0x00040000 | 0x001000A1
    if not add_allowed_ace(dacl, 2, 0, allowed, world_sid):
        raise OSError("cannot add attack allow ACE")
    if not add_denied_ace(dacl, 2, 0, 0x00000006, world_sid):
        raise OSError("cannot add trailing attack deny ACE")
    result = set_security(
        handle,
        1,
        0x00000004 | 0x80000000,
        None,
        None,
        dacl,
        None,
    )
    if result != 0:
        raise OSError(result, "cannot install attack DACL")


def _windows_security_descriptor_bytes(path: Path) -> bytes:
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    get_file_security = advapi32.GetFileSecurityW
    get_file_security.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    )
    get_file_security.restype = wintypes.BOOL
    required = wintypes.DWORD()
    get_file_security(
        str(path),
        0x00000001 | 0x00000004,
        None,
        0,
        ctypes.byref(required),
    )
    if required.value == 0:
        raise OSError(ctypes.get_last_error(), "security descriptor size unavailable")
    descriptor = ctypes.create_string_buffer(required.value)
    if not get_file_security(
        str(path),
        0x00000001 | 0x00000004,
        descriptor,
        len(descriptor),
        ctypes.byref(required),
    ):
        raise OSError(ctypes.get_last_error(), "security descriptor unavailable")
    return descriptor.raw[: required.value]


def _windows_create_mutable_directory_relative(
    parent_handle: object,
    name: str,
    expected: Path,
) -> object:
    encoded = name.encode("utf-16-le")
    buffer = ctypes.create_unicode_buffer(name)
    unicode_name = build_cli._secure_files._UnicodeString(
        len(encoded),
        len(encoded) + 2,
        ctypes.cast(buffer, wintypes.LPWSTR),
    )
    attributes = build_cli._secure_files._ObjectAttributes(
        ctypes.sizeof(build_cli._secure_files._ObjectAttributes),
        parent_handle,
        ctypes.pointer(unicode_name),
        build_cli._secure_files._OBJ_CASE_INSENSITIVE,
        None,
        None,
    )
    io_status = build_cli._secure_files._IoStatusBlock()
    handle = wintypes.HANDLE()
    status = build_cli._secure_files._ntdll.NtCreateFile(
        ctypes.byref(handle),
        0x00000001 | 0x00000080 | 0x00020000 | 0x00040000 | 0x00080000 | 0x00100000,
        ctypes.byref(attributes),
        ctypes.byref(io_status),
        None,
        0,
        build_cli._secure_files._FILE_SHARE_READ,
        2,
        build_cli._secure_files._FILE_DIRECTORY_FILE
        | build_cli._secure_files._FILE_SYNCHRONOUS_IO_NONALERT
        | build_cli._secure_files._FILE_FLAG_OPEN_REPARSE_POINT,
        None,
        0,
    )
    if status < 0:
        error = build_cli._secure_files._ntdll.RtlNtStatusToDosError(status)
        raise OSError(error, "cannot create mutable test directory")
    build_cli.AuthenticatedTree._validate_handle(
        handle,
        expected=expected,
        directory=True,
        label="mutable test directory",
    )
    return handle


def _start_windows_publication_peer(
    directory: Path,
    inserted: Path,
) -> subprocess.Popen[str]:
    peer_code = r"""
import ctypes
import json
import os
from pathlib import Path
import sys
from ctypes import wintypes

directory = Path(sys.argv[1])
inserted = Path(sys.argv[2])
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
kernel32.CreateFileW.argtypes = (
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.HANDLE,
)
kernel32.CreateFileW.restype = wintypes.HANDLE
kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
kernel32.CloseHandle.restype = wintypes.BOOL
advapi32.SetSecurityInfo.argtypes = (
    wintypes.HANDLE,
    ctypes.c_int,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.LPVOID,
    wintypes.LPVOID,
    wintypes.LPVOID,
)
advapi32.SetSecurityInfo.restype = wintypes.DWORD
invalid = ctypes.c_void_p(-1).value
banked = None


def reply(value):
    print(json.dumps(value, sort_keys=True), flush=True)


def attempt(path, desired, flags):
    ctypes.set_last_error(0)
    handle = kernel32.CreateFileW(
        str(path),
        desired,
        0x00000001 | 0x00000002 | 0x00000004,
        None,
        3,
        flags | 0x00200000,
        None,
    )
    value = handle if isinstance(handle, int) else handle.value
    if value == invalid:
        return {"opened": False, "error": ctypes.get_last_error()}
    kernel32.CloseHandle(handle)
    return {"opened": True, "error": 0}


for request in sys.stdin:
    command = request.strip()
    if command == "bank":
        ctypes.set_last_error(0)
        handle = kernel32.CreateFileW(
            str(directory),
            0x00020000 | 0x00040000,
            0x00000001 | 0x00000002 | 0x00000004,
            None,
            3,
            0x02000000 | 0x00200000,
            None,
        )
        value = handle if isinstance(handle, int) else handle.value
        if value == invalid:
            reply(
                {
                    "banked": False,
                    "error": ctypes.get_last_error(),
                    "visible": os.path.lexists(directory),
                }
            )
        else:
            banked = handle
            reply({"banked": True, "error": 0, "visible": True})
    elif command == "attack":
        if banked is None:
            reply({"inserted": False, "set_security_error": None})
            continue
        result = advapi32.SetSecurityInfo(
            banked,
            1,
            0x00000004,
            None,
            None,
            None,
            None,
        )
        inserted_ok = False
        if result == 0:
            try:
                inserted.write_bytes(b"peer insertion\n")
                inserted_ok = True
            except OSError:
                pass
        reply({"inserted": inserted_ok, "set_security_error": result})
    elif command == "probe_committed":
        try:
            inserted.write_bytes(b"post-commit insertion\n")
            insertion = {"created": True}
        except OSError:
            insertion = {"created": False}
        reply(
            {
                "add": attempt(directory, 0x00000006, 0x02000000),
                "file_write": attempt(
                    directory / "governing-design.md",
                    0x40000000,
                    0,
                ),
                "insertion": insertion,
                "write_dac": attempt(directory, 0x00040000, 0x02000000),
            }
        )
    elif command == "quit":
        break

if banked is not None:
    kernel32.CloseHandle(banked)
"""
    return subprocess.Popen(
        [
            sys.executable,
            "-E",
            "-B",
            "-c",
            peer_code,
            str(directory),
            str(inserted),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _publication_peer_command(
    peer: subprocess.Popen[str],
    command: str,
) -> dict[str, object]:
    assert peer.stdin is not None
    assert peer.stdout is not None
    peer.stdin.write(f"{command}\n")
    peer.stdin.flush()
    response = peer.stdout.readline()
    if not response:
        stderr = "" if peer.stderr is None else peer.stderr.read()
        raise AssertionError(f"publication peer exited without a response: {stderr}")
    value = json.loads(response)
    if type(value) is not dict:
        raise AssertionError("publication peer returned a non-object response")
    return value


class _MetadataProbe:
    def version(self) -> str:
        return "1.2.3"

    def auth_mode(self) -> str:
        return "service_account"

    def quota_mode(self) -> str:
        return "declared"


class _SyntheticPreflight:
    design_bytes = b"# Synthetic MAS/OACS governing design\n"

    def _ledger_bytes(self) -> bytes:
        records = tuple(
            ClaimRecordV1(
                claim_id=f"claim:{position}-{claim_type}",
                exact_span=f"Prospective synthetic {claim_type} claim.",
                claim_type=claim_type,
                status="prospective",
                evidence_sha256=(),
                falsifier=f"Synthetic falsifier {position}.",
                severity_if_wrong="critical" if position == 0 else "important",
            )
            for position, claim_type in enumerate(
                (
                    "problem",
                    "causal_mechanism",
                    "policy_consequence",
                    "domain_scope",
                    "limitation",
                )
            )
        )
        return claim_ledger_bytes(
            ClaimLedgerV1(
                design_sha256=sha256(self.design_bytes).hexdigest(),
                records=records,
            )
        )

    def _unit(
        self,
        domain: str,
        cluster_id: str,
        unit_id: str,
        partition: str,
        families: tuple[str, ...],
        *,
        commitment_label: str = "commitment",
    ) -> DomainUnitV1:
        identity = f"{domain}|{cluster_id}|{unit_id}|{partition}"
        return DomainUnitV1(
            domain=domain,
            cluster_id=cluster_id,
            unit_id=unit_id,
            partition=partition,
            obligation_families=families,
            public_packet_sha256=_digest(f"public|{identity}"),
            evaluator_commitment_sha256=_digest(f"{commitment_label}|{identity}"),
            source_rights_status="unrestricted",
            blind_overlap_sha256=_digest(f"overlap|{identity}"),
        )

    def _architecture_bytes(
        self,
        *,
        sites: int = 8,
        units: int = 64,
        audit_units: int = 24,
        commitment_label: str = "commitment",
    ) -> bytes:
        rows: list[DomainUnitV1] = []
        for position in range(units):
            partition = "audit" if position < audit_units else "focal"
            cluster_number = (
                position % 3 + 1
                if partition == "audit"
                else 4 + ((position - audit_units) % max(1, sites - 3))
            )
            rows.append(
                self._unit(
                    "architecture",
                    f"cluster-{cluster_number:02d}",
                    f"unit-{position:03d}",
                    partition,
                    (f"family-{position % 5}",),
                    commitment_label=commitment_label,
                )
            )
        return domain_census_bytes(
            DomainCensusV1(
                schema="oacs-domain-census/v1",
                units=tuple(
                    sorted(rows, key=lambda row: (row.cluster_id, row.unit_id))
                ),
                source_manifest_sha256=_digest(
                    f"architecture-manifest|{sites}|{units}|{commitment_label}"
                ),
            )
        )

    def _jci_bytes(
        self,
        *,
        repositories: int = 8,
        prefixes: int = 80,
        resource_prefixes: int = 20,
    ) -> bytes:
        rows = tuple(
            self._unit(
                "jci",
                f"cluster-{position % repositories + 1:02d}",
                f"unit-{position:03d}",
                "focal",
                ("resource",) if position < resource_prefixes else ("compatibility",),
            )
            for position in range(prefixes)
        )
        return domain_census_bytes(
            DomainCensusV1(
                schema="oacs-domain-census/v1",
                units=tuple(
                    sorted(rows, key=lambda row: (row.cluster_id, row.unit_id))
                ),
                source_manifest_sha256=_digest(
                    f"jci-manifest|{repositories}|{prefixes}"
                ),
            )
        )

    def _catalog_and_plan(self):
        profiles = (
            CapabilityProfile((("geometry.angle", 0.25),), 1.0),
            CapabilityProfile((("law.use", -0.5),), 1.0),
            CapabilityProfile((("parking.supply", 0.75),), 1.0),
            CapabilityProfile((("program.area", 1.25),), 1.0),
        )
        catalog = build_controller_catalog(
            profiles,
            _digest("catalog-a"),
            _digest("catalog-b"),
            _digest("catalog-c"),
        )
        packets = tuple(
            CapabilityPacketManifest(
                action=action,
                prompt_sha256=_digest(f"{label}-prompt"),
                tool_manifest_sha256=_digest(f"{label}-tool"),
                permission_manifest_sha256=_digest(f"{label}-permission"),
                evidence_scope_sha256=_digest(f"{label}-evidence"),
                budget_contract_sha256=_digest(f"{label}-budget"),
                output_schema_sha256=_digest(f"{label}-output"),
                model_runtime_sha256=_digest(f"{label}-runtime"),
                container_sha256=_digest(f"{label}-container"),
            )
            for action, label in (
                ("ASK_GEOMETRY", "geometry"),
                ("ASK_LAW", "law"),
                ("ASK_PARKING", "parking"),
                ("ASK_PROGRAM", "program"),
            )
        )
        return catalog, build_crossover_plan(catalog, packets, _digest("crossover"))

    def _baseline_roster_and_readiness(self):
        baseline_ids = (
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
        internal = {
            "always_all_specialists",
            "difficulty_confidence",
            "fixed_topology",
            "random_admissible_action",
            "separated_router_stopper",
            "solo",
        }
        entries = []
        readiness = []
        for baseline_id in baseline_ids:
            official = (
                None if baseline_id in internal else _digest(f"{baseline_id}:official")
            )
            version = _digest(f"{baseline_id}:version")
            entries.append(
                MandatoryBaselineRosterEntry.create(
                    baseline_id=baseline_id,
                    official_source_spec_sha256=official,
                    version_sha256=version,
                )
            )
            readiness.append(
                BaselinePreOutcomeReadinessAuthority.create(
                    baseline_id=baseline_id,
                    version_sha256=version,
                    status="unsupported_missing_dependency",
                    reason_code="dependency_unavailable",
                    official_source_spec_sha256=official,
                    executed_method_id=None,
                    adapter_code_sha256=None,
                    dependency_environment_lock_sha256=_digest("environment"),
                    parity_projection_sha256=None,
                    synthetic_faithfulness_test_receipt_sha256=None,
                    reviewer_decision_sha256=_digest("baseline-review"),
                    pre_outcome_amendment_sha256=None,
                )
            )
        return MandatoryBaselineRoster.create(entries=tuple(entries)), tuple(readiness)

    def _study_bytes(self, *, parity_valid: bool = True) -> bytes:
        catalog, crossover = self._catalog_and_plan()
        roster, readiness = self._baseline_roster_and_readiness()
        common = {
            "model_binding_sha256": _digest("model-binding"),
            "public_input_projection_sha256": _digest("public-input"),
            "token_budget": 4096,
            "call_budget": 12,
            "timeout_seconds": 90,
            "retry_policy_sha256": _digest("retry"),
            "common_synthesizer_sha256": _digest("synthesizer"),
            "terminal_evaluator_sha256": _digest("evaluator"),
            "usage_accounting_sha256": _digest("accounting"),
        }
        ids = (
            "solo",
            "rr3",
            "sel3",
            "swm3",
            "refl3",
            "debate3",
            "equal_information_router",
            "oacs",
        )
        treatments = tuple(
            TreatmentSpecV1(
                treatment_id=treatment_id,
                treatment_family=(
                    "oacs_capability" if treatment_id == "oacs" else "core_mas"
                ),
                tool_catalog_sha256=(
                    catalog.sha256()
                    if treatment_id == "oacs"
                    else _digest("non-oacs-tools")
                ),
                **common,
            )
            for treatment_id in ids
        )
        raw = study_contract_bytes(
            OacsStudyContractV1(treatments, catalog, crossover, roster, readiness)
        )
        if parity_valid:
            return raw
        payload = json.loads(raw)
        payload["treatments"][-1]["token_budget"] = 4097
        return _canonical(payload)

    def _approval(self) -> ApprovalTrustRootV1:
        quota = (
            QuotaAssumptionV1(
                scope="requests_per_day", statement="100 requests per day"
            ),
        )
        return ApprovalTrustRootV1(
            executable_sha256=_digest("executable"),
            runtime_version="1.2.3",
            adapter_sha256=_digest("adapter"),
            model_id="provider/model-2026-09-01",
            auth_mode="service_account",
            quota_mode="declared",
            quota_assumptions=quota,
            invoice_approval_id="APR-SYNTHETIC-001",
            maximum_marginal_cost_microunits=1_000_000,
            timeout_seconds=30,
            retry_count=1,
            usage_accounting=UsageAccountingV1.all_accounted(),
            required_evidence_provenance="injected_metadata",
        )

    def _backend_bytes(
        self,
        approval: ApprovalTrustRootV1,
        *,
        ready: bool = True,
    ) -> bytes:
        config = BackendAuditConfigV1(
            executable="oacs-cli",
            executable_sha256=approval.executable_sha256,
            adapter="oacs.adapter.v1",
            adapter_sha256=approval.adapter_sha256,
            model_id=approval.model_id,
            quota_assumptions=approval.quota_assumptions,
            invoice_approval_id=approval.invoice_approval_id,
            maximum_marginal_cost_microunits=(
                approval.maximum_marginal_cost_microunits if ready else 0
            ),
            timeout_seconds=approval.timeout_seconds,
            retry_count=approval.retry_count,
            usage_accounting=approval.usage_accounting,
            evidence_provenance=approval.required_evidence_provenance,
        )
        audit = audit_backend(
            config,
            _MetadataProbe(),
            approval if ready else None,
            approval_digest(approval) if ready else None,
        )
        return audit.canonical_bytes()

    def _power_bytes(
        self,
        domain: str,
        census_bytes: bytes,
        cluster_count: int,
        *,
        powered: bool = True,
    ) -> bytes:
        return domain_power_plan_bytes(
            DomainPowerPlanV1.create(
                domain=domain,
                census_sha256=sha256(census_bytes).hexdigest(),
                direction="one_sided_greater",
                alpha=0.05,
                target_power=0.80,
                cluster_count=cluster_count,
                target_standardized_effect=2.0 if powered else 0.2,
                multiplicity_family=f"{domain}_primary",
            )
        )

    def inputs(
        self,
        *,
        architecture_sites: int = 8,
        jci_repositories: int = 8,
        parity_valid: bool = True,
        backend_ready: bool = True,
        powered: bool = True,
        review_unresolved: bool = False,
        architecture_bytes: bytes | None = None,
        architecture_power_bytes: bytes | None = None,
        backend_bytes: bytes | None = None,
        approval_bytes: bytes | None = None,
        expected_approval_sha256: str | None = None,
        extra_review_source_sha256: str | None = None,
    ) -> OacsPreflightInputsV1:
        ledger = self._ledger_bytes()
        architecture = architecture_bytes or self._architecture_bytes(
            sites=architecture_sites
        )
        jci = self._jci_bytes(repositories=jci_repositories)
        study = self._study_bytes(parity_valid=parity_valid)
        approval = self._approval()
        raw_approval = (
            approval.canonical_bytes() if approval_bytes is None else approval_bytes
        )
        backend = backend_bytes or self._backend_bytes(approval, ready=backend_ready)
        architecture_power = architecture_power_bytes or self._power_bytes(
            "architecture", architecture, architecture_sites, powered=powered
        )
        jci_power = self._power_bytes("jci", jci, jci_repositories, powered=powered)
        source_hash_set = {
            sha256(raw).hexdigest()
            for raw in (
                self.design_bytes,
                architecture,
                jci,
                study,
                backend,
                architecture_power,
                jci_power,
                raw_approval,
            )
        }
        if extra_review_source_sha256 is not None:
            source_hash_set.add(extra_review_source_sha256)
        source_hashes = tuple(sorted(source_hash_set))
        ledger_object = ClaimLedgerV1(
            design_sha256=sha256(self.design_bytes).hexdigest(),
            records=tuple(
                ClaimRecordV1(
                    **{
                        **row,
                        "evidence_sha256": tuple(row["evidence_sha256"]),
                    }
                )
                for row in json.loads(ledger)["records"]
            ),
        )
        package = build_review_package(ledger_object, source_hashes)
        reviews = []
        for assignment in package.assignments:
            findings = ()
            verdict = "ACCEPT"
            if review_unresolved and assignment.role == "causal_statistics":
                findings = (
                    FindingV1(
                        failure_code="synthetic-power-objection",
                        severity="I",
                        claim_id=package.claim_ids[0],
                        evidence_sha256=package.source_sha256[0],
                        falsifier_result="Synthetic objection remains open.",
                        resolved=False,
                    ),
                )
                verdict = "REVISE"
            reviews.append(
                lock_review_record(
                    role=assignment.role,
                    assignment_sha256=assignment.assignment_sha256,
                    verdict=verdict,
                    findings=findings,
                )
            )
        expected = (
            approval_digest(approval)
            if expected_approval_sha256 is None
            else expected_approval_sha256
        )
        return OacsPreflightInputsV1(
            governing_design_bytes=self.design_bytes,
            expected_governing_design_sha256=sha256(self.design_bytes).hexdigest(),
            claim_ledger_bytes=ledger,
            review_package_bytes=review_package_bytes(package),
            locked_review_bytes=tuple(
                locked_review_bytes(review) for review in reviews
            ),
            architecture_census_bytes=architecture,
            jci_census_bytes=jci,
            study_contract_bytes=study,
            backend_audit_bytes=backend,
            approval_trust_root_bytes=raw_approval,
            expected_approval_trust_root_sha256=expected,
            architecture_power_plan_bytes=architecture_power,
            jci_power_plan_bytes=jci_power,
        )


class OacsPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = _SyntheticPreflight()

    def test_all_authorities_are_conjunctive(self) -> None:
        receipt = evaluate_preflight(self.fixture.inputs())
        self.assertEqual(receipt.status, "go_for_separate_execution_plan")
        self.assertEqual(receipt.reason_codes, ())

        mutations = (
            (
                self.fixture.inputs(architecture_sites=7),
                "architecture_census_insufficient",
            ),
            (self.fixture.inputs(jci_repositories=7), "jci_census_insufficient"),
            (self.fixture.inputs(parity_valid=False), "study_parity_invalid"),
            (self.fixture.inputs(backend_ready=False), "backend_not_ready"),
            (
                self.fixture.inputs(powered=False),
                "prospective_power_insufficient",
            ),
            (
                self.fixture.inputs(review_unresolved=True),
                "preoutcome_review_unresolved",
            ),
        )
        for inputs, reason in mutations:
            with self.subTest(reason=reason):
                failed = evaluate_preflight(inputs)
                self.assertEqual(failed.status, "no_go_needs_context")
                self.assertIn(reason, failed.reason_codes)

    def test_all_six_reasons_accumulate_in_closed_byte_order(self) -> None:
        receipt = evaluate_preflight(
            self.fixture.inputs(
                architecture_sites=7,
                jci_repositories=7,
                parity_valid=False,
                backend_ready=False,
                powered=False,
                review_unresolved=True,
            )
        )
        self.assertEqual(
            receipt.reason_codes,
            (
                "architecture_census_insufficient",
                "backend_not_ready",
                "jci_census_insufficient",
                "preoutcome_review_unresolved",
                "prospective_power_insufficient",
                "study_parity_invalid",
            ),
        )

    def test_receipt_binds_raw_component_review_and_approval_identities(self) -> None:
        inputs = self.fixture.inputs()
        receipt = evaluate_preflight(inputs)
        self.assertEqual(
            receipt.governing_design_sha256,
            sha256(inputs.governing_design_bytes).hexdigest(),
        )
        self.assertEqual(
            receipt.component_sha256["claim_ledger"],
            sha256(inputs.claim_ledger_bytes).hexdigest(),
        )
        self.assertEqual(
            receipt.component_sha256["architecture_census"],
            sha256(inputs.architecture_census_bytes).hexdigest(),
        )
        self.assertEqual(
            tuple(receipt.review_sha256.values()),
            tuple(sha256(raw).hexdigest() for raw in inputs.locked_review_bytes),
        )
        self.assertEqual(
            receipt.approval_trust_root_sha256,
            sha256(inputs.approval_trust_root_bytes).hexdigest(),
        )
        self.assertEqual(
            receipt.expected_approval_trust_root_sha256,
            inputs.expected_approval_trust_root_sha256,
        )

    def test_missing_or_mismatched_separately_verified_approval_is_no_go(self) -> None:
        valid = self.fixture.inputs()
        cases = (
            replace(
                valid,
                approval_trust_root_bytes=None,
            ),
            replace(
                valid,
                expected_approval_trust_root_sha256=_digest("wrong-approval"),
            ),
        )
        for inputs in cases:
            with self.subTest(approval=inputs.approval_trust_root_bytes is not None):
                receipt = evaluate_preflight(inputs)
                self.assertEqual(receipt.status, "no_go_needs_context")
                self.assertIn("backend_not_ready", receipt.reason_codes)

    def test_ready_audit_must_match_every_field_of_the_verified_approval_root(
        self,
    ) -> None:
        mismatched_root = replace(
            self.fixture._approval(), model_id="provider/different-model-2026-09-01"
        )
        inputs = self.fixture.inputs(
            backend_bytes=self.fixture._backend_bytes(mismatched_root)
        )
        receipt = evaluate_preflight(inputs)
        self.assertEqual(receipt.status, "no_go_needs_context")
        self.assertIn("backend_not_ready", receipt.reason_codes)

    def test_review_package_may_not_introduce_unverified_source_hashes(self) -> None:
        inputs = self.fixture.inputs(
            extra_review_source_sha256=_digest("unverified-review-source")
        )
        with self.assertRaisesRegex(PreflightError, "review package.*exact"):
            evaluate_preflight(inputs)

    def test_valid_census_substitution_fails_against_frozen_power_binding(self) -> None:
        original = self.fixture.inputs()
        substituted = self.fixture._architecture_bytes(
            commitment_label="substituted-commitment"
        )
        rebuilt = self.fixture.inputs(
            architecture_bytes=substituted,
            architecture_power_bytes=original.architecture_power_plan_bytes,
        )
        with self.assertRaisesRegex(PreflightError, "power.*census|census.*power"):
            evaluate_preflight(rebuilt)

    def test_unresolved_critical_and_important_union_is_preserved(self) -> None:
        receipt = evaluate_preflight(self.fixture.inputs(review_unresolved=True))
        self.assertEqual(len(receipt.unresolved_critical_important), 1)
        finding = receipt.unresolved_critical_important[0]
        self.assertEqual(finding["severity"], "I")
        self.assertEqual(finding["failure_code"], "synthetic-power-objection")

    def test_noncanonical_or_stale_component_bytes_fail_closed(self) -> None:
        valid = self.fixture.inputs()
        attacks = (
            replace(valid, claim_ledger_bytes=b" " + valid.claim_ledger_bytes),
            replace(
                valid,
                expected_governing_design_sha256=_digest("wrong-design"),
            ),
            replace(valid, backend_audit_bytes=valid.backend_audit_bytes + b"\n"),
        )
        for inputs in attacks:
            with self.subTest():
                with self.assertRaises(PreflightError):
                    evaluate_preflight(inputs)

    def test_receipt_is_canonical_self_hashed_and_revalidates_inputs(self) -> None:
        inputs = self.fixture.inputs()
        receipt = evaluate_preflight(inputs)
        raw = preflight_receipt_bytes(receipt)
        self.assertEqual(
            raw, preflight_receipt_bytes(verify_preflight_receipt_bytes(raw))
        )
        self.assertEqual(raw, validate_preflight_receipt_bytes(raw, inputs))
        self.assertTrue(raw.endswith(b"\n"))
        self.assertNotIn(b"\r", raw)

        tampered = json.loads(raw)
        tampered["receipt_sha256"] = _digest("tampered")
        with self.assertRaisesRegex(PreflightError, "self-hash"):
            verify_preflight_receipt_bytes(_canonical(tampered))

    def test_receipt_rejects_duplicate_noncanonical_order_and_native_type_attacks(
        self,
    ) -> None:
        inputs = self.fixture.inputs(review_unresolved=True, powered=False)
        raw = preflight_receipt_bytes(evaluate_preflight(inputs))

        duplicate = raw.replace(
            b'{"approval_trust_root_sha256":',
            b'{"schema":"oacs-preflight-receipt/v1","approval_trust_root_sha256":',
            1,
        )
        with self.assertRaisesRegex(PreflightError, "duplicate JSON key"):
            verify_preflight_receipt_bytes(duplicate)

        with self.assertRaisesRegex(PreflightError, "not canonical"):
            verify_preflight_receipt_bytes(raw.replace(b'":', b'": ', 1))

        unsorted_reasons = json.loads(raw)
        unsorted_reasons["reason_codes"].reverse()
        body = dict(unsorted_reasons)
        body.pop("receipt_sha256")
        unsorted_reasons["receipt_sha256"] = sha256(_canonical(body)).hexdigest()
        with self.assertRaisesRegex(PreflightError, "byte-sorted"):
            verify_preflight_receipt_bytes(_canonical(unsorted_reasons))

        boolean_counter = json.loads(raw)
        boolean_counter["operation_counters"]["network_calls"] = False
        body = dict(boolean_counter)
        body.pop("receipt_sha256")
        boolean_counter["receipt_sha256"] = sha256(_canonical(body)).hexdigest()
        with self.assertRaisesRegex(PreflightError, "native zero integers"):
            verify_preflight_receipt_bytes(_canonical(boolean_counter))

    def test_locked_review_byte_order_is_not_caller_asserted(self) -> None:
        inputs = self.fixture.inputs()
        reviews = list(inputs.locked_review_bytes)
        reviews[0], reviews[1] = reviews[1], reviews[0]
        with self.assertRaisesRegex(PreflightError, "package-bound"):
            evaluate_preflight(replace(inputs, locked_review_bytes=tuple(reviews)))

    def test_reason_deletion_and_operation_counter_drift_fail_closed(self) -> None:
        inputs = self.fixture.inputs(review_unresolved=True, powered=False)
        raw = preflight_receipt_bytes(evaluate_preflight(inputs))
        deleted = json.loads(raw)
        deleted["reason_codes"].remove("prospective_power_insufficient")
        body = dict(deleted)
        body.pop("receipt_sha256")
        deleted["receipt_sha256"] = sha256(_canonical(body)).hexdigest()
        with self.assertRaisesRegex(PreflightError, "does not match.*inputs"):
            validate_preflight_receipt_bytes(_canonical(deleted), inputs)

        drifted = json.loads(raw)
        drifted["operation_counters"]["model_calls"] = 1
        body = dict(drifted)
        body.pop("receipt_sha256")
        drifted["receipt_sha256"] = sha256(_canonical(body)).hexdigest()
        with self.assertRaisesRegex(PreflightError, "operation counters"):
            verify_preflight_receipt_bytes(_canonical(drifted))

    def test_resealed_receipt_cannot_split_design_or_go_approval_identity(self) -> None:
        raw = preflight_receipt_bytes(evaluate_preflight(self.fixture.inputs()))
        split_design = json.loads(raw)
        split_design["component_sha256"]["governing_design"] = _digest(
            "different-design"
        )
        body = dict(split_design)
        body.pop("receipt_sha256")
        split_design["receipt_sha256"] = sha256(_canonical(body)).hexdigest()
        with self.assertRaisesRegex(PreflightError, "governing design"):
            verify_preflight_receipt_bytes(_canonical(split_design))

        split_approval = json.loads(raw)
        split_approval["expected_approval_trust_root_sha256"] = _digest(
            "different-approval"
        )
        body = dict(split_approval)
        body.pop("receipt_sha256")
        split_approval["receipt_sha256"] = sha256(_canonical(body)).hexdigest()
        with self.assertRaisesRegex(PreflightError, "approval.*GO"):
            verify_preflight_receipt_bytes(_canonical(split_approval))

    def test_status_vocabulary_never_authorizes_an_experiment(self) -> None:
        raw = preflight_receipt_bytes(evaluate_preflight(self.fixture.inputs()))
        self.assertNotIn(b"experiment_approved", raw)
        self.assertNotIn(b"paper_ready", raw)
        self.assertNotIn(b"acceptance", raw)

    def test_operation_counters_are_exact_native_zeros_for_every_call_surface(
        self,
    ) -> None:
        receipt = evaluate_preflight(self.fixture.inputs())
        self.assertEqual(
            dict(receipt.operation_counters),
            {
                "api_calls": 0,
                "experiments_started": 0,
                "generation_calls": 0,
                "model_calls": 0,
                "network_calls": 0,
                "provider_calls": 0,
                "subprocess_generation_calls": 0,
            },
        )
        self.assertTrue(
            all(type(value) is int for value in receipt.operation_counters.values())
        )


class OacsPreflightCliTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.fixture = _SyntheticPreflight()
        self.temporary = tempfile.TemporaryDirectory(prefix="oacs-preflight-synthetic-")
        self.root = Path(self.temporary.name).resolve(strict=True)
        self.inputs = self.fixture.inputs()
        self.paths = self._write_inputs(self.inputs)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_inputs(self, inputs: OacsPreflightInputsV1) -> dict[str, Path]:
        rows: dict[str, bytes] = {
            "governing-design.md": inputs.governing_design_bytes,
            "claim-ledger.json": inputs.claim_ledger_bytes,
            "review-package.json": inputs.review_package_bytes,
            "architecture-census.json": inputs.architecture_census_bytes,
            "jci-census.json": inputs.jci_census_bytes,
            "study-contract.json": inputs.study_contract_bytes,
            "backend-audit.json": inputs.backend_audit_bytes,
            "architecture-power-plan.json": inputs.architecture_power_plan_bytes,
            "jci-power-plan.json": inputs.jci_power_plan_bytes,
        }
        rows.update(
            {
                f"review-{role}.json": raw
                for role, raw in zip(
                    (
                        "problem-novelty",
                        "causal-statistics",
                        "experiment-reproducibility",
                        "adversarial-falsifier",
                    ),
                    inputs.locked_review_bytes,
                    strict=True,
                )
            }
        )
        if inputs.approval_trust_root_bytes is not None:
            rows["approval-trust-root.json"] = inputs.approval_trust_root_bytes
        result = {}
        for name, raw in rows.items():
            path = self.root / name
            path.write_bytes(raw)
            result[name] = path
        return result

    def _build_args(self, output_root: Path) -> list[str]:
        return [
            "--governing-design",
            str(self.paths["governing-design.md"]),
            "--governing-design-sha256",
            self.inputs.expected_governing_design_sha256,
            "--claim-ledger",
            str(self.paths["claim-ledger.json"]),
            "--review-package",
            str(self.paths["review-package.json"]),
            "--review-problem-novelty",
            str(self.paths["review-problem-novelty.json"]),
            "--review-causal-statistics",
            str(self.paths["review-causal-statistics.json"]),
            "--review-experiment-reproducibility",
            str(self.paths["review-experiment-reproducibility.json"]),
            "--review-adversarial-falsifier",
            str(self.paths["review-adversarial-falsifier.json"]),
            "--architecture-census",
            str(self.paths["architecture-census.json"]),
            "--jci-census",
            str(self.paths["jci-census.json"]),
            "--study-contract",
            str(self.paths["study-contract.json"]),
            "--backend-audit",
            str(self.paths["backend-audit.json"]),
            "--approval-trust-root",
            str(self.paths["approval-trust-root.json"]),
            "--approval-trust-root-sha256",
            self.inputs.expected_approval_trust_root_sha256,
            "--architecture-power-plan",
            str(self.paths["architecture-power-plan.json"]),
            "--jci-power-plan",
            str(self.paths["jci-power-plan.json"]),
            "--output-root",
            str(output_root),
        ]

    def _validate_args(self, input_root: Path) -> list[str]:
        return [
            "--input-root",
            str(input_root),
            "--governing-design-sha256",
            self.inputs.expected_governing_design_sha256,
            "--approval-trust-root-sha256",
            self.inputs.expected_approval_trust_root_sha256,
        ]

    @staticmethod
    def _replace_option(args: list[str], option: str, value: str) -> list[str]:
        changed = list(args)
        changed[changed.index(option) + 1] = value
        return changed

    def _run_main(self, function, args: list[str]) -> tuple[int, bytes, str]:
        binary = io.BytesIO()

        class _Stdout:
            buffer = binary

            def write(self, value: str) -> int:
                return len(value)

            def flush(self) -> None:
                return None

        errors = io.StringIO()
        with redirect_stdout(_Stdout()), redirect_stderr(errors):
            code = function(args)
        return code, binary.getvalue(), errors.getvalue()

    def test_build_and_validator_emit_identical_canonical_binary_stdout(self) -> None:
        project = Path(__file__).resolve(strict=True).parents[1]
        python = Path(sys.executable).resolve(strict=True)
        build_script = project / "build_iclr2027_oacs_preoutcome.py"
        validate_script = project / "validate_iclr2027_oacs_preflight.py"
        outputs = (self.root / "package-a-final", self.root / "package-b-final")
        build_processes = tuple(
            subprocess.run(
                [str(python), "-E", "-B", str(build_script), *self._build_args(root)],
                check=False,
                capture_output=True,
            )
            for root in outputs
        )
        for process in build_processes:
            self.assertEqual(process.returncode, 0)
            self.assertEqual(process.stderr, b"")
            self.assertTrue(process.stdout.endswith(b"\n"))
            self.assertNotIn(b"\r", process.stdout)
        self.assertEqual(build_processes[0].stdout, build_processes[1].stdout)

        validation_processes = tuple(
            subprocess.run(
                [
                    str(python),
                    "-E",
                    "-B",
                    str(validate_script),
                    *self._validate_args(root),
                ],
                check=False,
                capture_output=True,
            )
            for root in outputs
        )
        for process in validation_processes:
            self.assertEqual(process.returncode, 0)
            self.assertEqual(process.stderr, b"")
        self.assertEqual(validation_processes[0].stdout, build_processes[0].stdout)
        self.assertEqual(validation_processes[0].stdout, validation_processes[1].stdout)

    def test_build_validates_everything_before_creating_output_root(self) -> None:
        self.paths["backend-audit.json"].write_bytes(
            self.inputs.backend_audit_bytes + b"\n"
        )
        output = self.root / "must-not-exist-final"
        code, stdout, _ = self._run_main(build_main, self._build_args(output))
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, b"")
        self.assertFalse(os.path.lexists(output))

    def test_builder_blocks_mutation_after_an_early_member_read(self) -> None:
        output = self.root / "retained-member-final"
        original = build_cli._read_retained_handle
        mutation_blocked = False

        def attack_after_read(handle, *, label):
            nonlocal mutation_blocked
            raw = original(handle, label=label)
            if label == "governing-design.md":
                try:
                    (output / label).write_bytes(b"attacker replacement\n")
                except OSError:
                    mutation_blocked = True
            return raw

        with patch.object(
            build_cli,
            "_read_retained_handle",
            new=attack_after_read,
        ):
            code, stdout, errors = self._run_main(build_main, self._build_args(output))

        self.assertEqual((code, errors), (0, ""))
        self.assertTrue(mutation_blocked)
        self.assertEqual(stdout, (output / "preflight-receipt.json").read_bytes())
        self.assertEqual(
            (output / "governing-design.md").read_bytes(),
            self.inputs.governing_design_bytes,
        )

    def test_builder_fails_closed_on_member_insertion_after_enumeration(self) -> None:
        output = self.root / "inserted-member-final"
        original = build_cli._list_retained_directory
        attacked = False

        def attack_after_enumeration(handle, *, label):
            nonlocal attacked
            entries = original(handle, label=label)
            if label == "new output package" and not attacked:
                attacked = True
                (output / "attacker-extra.json").write_bytes(b"{}\n")
            return entries

        with patch.object(
            build_cli,
            "_list_retained_directory",
            new=attack_after_enumeration,
        ):
            code, stdout, _ = self._run_main(build_main, self._build_args(output))

        self.assertTrue(attacked)
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, b"")

    @unittest.skipUnless(os.name == "nt", "Windows namespace seal contract")
    def test_builder_seals_the_published_directory_member_set(self) -> None:
        output = self.root / "namespace-sealed-final"
        code, _, errors = self._run_main(build_main, self._build_args(output))
        self.assertEqual((code, errors), (0, ""))

        inserted = output / "late-attacker-extra.json"
        try:
            with self.assertRaises(OSError):
                inserted.write_bytes(b"{}\n")
        finally:
            if inserted.exists():
                inserted.unlink()

    @unittest.skipUnless(os.name == "nt", "Windows namespace seal contract")
    def test_validator_rejects_an_unsealed_package_namespace(self) -> None:
        output = self.root / "unsealed-package-final"
        with (
            patch.object(build_cli, "_seal_directory_namespace", return_value=None),
            patch.object(
                build_cli,
                "_require_directory_namespace_sealed",
                return_value=None,
            ),
        ):
            code, _, errors = self._run_main(build_main, self._build_args(output))
        self.assertEqual((code, errors), (0, ""))

        code, stdout, errors = self._run_main(
            validate_main, self._validate_args(output)
        )
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, b"")
        self.assertIn("namespace seal", errors)

    @unittest.skipUnless(os.name == "nt", "Windows member seal contract")
    def test_validator_rejects_a_package_with_unsealed_members(self) -> None:
        output = self.root / "unsealed-members-final"
        with (
            patch.object(build_cli, "_FILE_OWNER_ALLOW_MASK", 0x001301BF),
            patch.object(
                build_cli,
                "_require_file_access_sealed",
                return_value=None,
            ),
        ):
            code, _, errors = self._run_main(build_main, self._build_args(output))
        self.assertEqual((code, errors), (0, ""))

        code, stdout, errors = self._run_main(
            validate_main,
            self._validate_args(output),
        )
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, b"")
        self.assertIn("member seal", errors)

    @unittest.skipUnless(os.name == "nt", "Windows owner-rights contract")
    def test_directories_are_owner_immutable_when_commit_becomes_visible(self) -> None:
        output = self.root / "commit-boundary-final"
        blocked: dict[Path, dict[int, bool]] = {}

        code, stdout, errors = self._run_main(build_main, self._build_args(output))

        self.assertEqual((code, errors), (0, ""))
        for directory in (output, output / "reviews"):
            blocked[directory] = {}
            for desired in (0x00040000, 0x00080000, 0x00000006):
                try:
                    peer_handle = _windows_open_directory(directory, desired)
                except PermissionError:
                    blocked[directory][desired] = True
                else:
                    blocked[directory][desired] = False
                    build_cli._close_handle(peer_handle)
        self.assertEqual(set(blocked), {output, output / "reviews"})
        self.assertTrue(all(all(rights.values()) for rights in blocked.values()))
        self.assertEqual(stdout, (output / "preflight-receipt.json").read_bytes())

    @unittest.skipUnless(os.name == "nt", "Windows transactional publication")
    def test_mutable_tree_is_invisible_to_a_concurrent_same_user_process(self) -> None:
        output = self.root / "transaction-hidden-final"
        inserted = output / "peer-banked-insertion.json"
        peer = _start_windows_publication_peer(output, inserted)
        bank_result: dict[str, object] | None = None
        precommit_bank_result: dict[str, object] | None = None
        attack_result: dict[str, object] | None = None
        committed_result: dict[str, object] | None = None
        precommit_directory_seals: set[str] = set()
        precommit_file_seals: set[str] = set()
        precommit_member_set: set[str] | None = None
        phase = "precommit"
        original_create = build_cli._create_relative
        original_write = build_cli._write_retained_handle
        original_commit = build_cli._WindowsPublicationTransaction.commit
        original_require_directory_sealed = (
            build_cli._require_directory_namespace_sealed
        )
        original_require_file_sealed = build_cli._require_file_access_sealed
        original_verify = build_cli._verify_created_package
        original_stdout = build_cli._write_stdout

        def create_mutable_directory(
            parent_handle,
            name,
            *,
            expected,
            directory,
        ):
            if directory:
                return _windows_create_mutable_directory_relative(
                    parent_handle,
                    name,
                    expected,
                )
            return original_create(
                parent_handle,
                name,
                expected=expected,
                directory=False,
            )

        def bank_authority_before_first_member_write(handle, raw):
            nonlocal bank_result
            if bank_result is None:
                bank_result = _publication_peer_command(peer, "bank")
            return original_write(handle, raw)

        def record_directory_seal(handle, *, label):
            original_require_directory_sealed(handle, label=label)
            if phase == "precommit":
                precommit_directory_seals.add(label)

        def record_file_seal(handle, *, label):
            original_require_file_sealed(handle, label=label)
            if phase == "precommit":
                precommit_file_seals.add(label)

        def record_member_set(package):
            nonlocal precommit_member_set
            original_verify(package)
            if phase == "precommit":
                precommit_member_set = set(package.expected)

        def probe_immediately_before_commit(transaction):
            nonlocal phase, precommit_bank_result
            expected_members = set(build_cli.PACKAGE_MEMBERS.values())
            self.assertEqual(precommit_member_set, expected_members)
            self.assertEqual(
                precommit_directory_seals,
                {"new output package", "new output reviews"},
            )
            self.assertEqual(precommit_file_seals, expected_members)
            precommit_bank_result = _publication_peer_command(peer, "bank")
            original_commit(transaction)
            phase = "committed"

        def attack_immediately_before_stdout(raw):
            nonlocal attack_result
            attack_result = _publication_peer_command(peer, "attack")
            return original_stdout(raw)

        try:
            with (
                patch.object(
                    build_cli,
                    "_create_relative",
                    new=create_mutable_directory,
                ),
                patch.object(
                    build_cli,
                    "_write_retained_handle",
                    new=bank_authority_before_first_member_write,
                ),
                patch.object(
                    build_cli,
                    "_require_directory_namespace_sealed",
                    new=record_directory_seal,
                ),
                patch.object(
                    build_cli,
                    "_require_file_access_sealed",
                    new=record_file_seal,
                ),
                patch.object(
                    build_cli,
                    "_verify_created_package",
                    new=record_member_set,
                ),
                patch.object(
                    build_cli._WindowsPublicationTransaction,
                    "commit",
                    new=probe_immediately_before_commit,
                ),
                patch.object(
                    build_cli,
                    "_write_stdout",
                    new=attack_immediately_before_stdout,
                ),
            ):
                code, stdout, errors = self._run_main(
                    build_main,
                    self._build_args(output),
                )
            committed_result = _publication_peer_command(peer, "probe_committed")
        finally:
            if peer.poll() is None:
                assert peer.stdin is not None
                peer.stdin.write("quit\n")
                peer.stdin.flush()
            _, peer_errors = peer.communicate(timeout=5)

        self.assertEqual(peer_errors, "")
        self.assertEqual((code, errors), (0, ""))
        self.assertEqual(
            bank_result,
            {"banked": False, "error": 2, "visible": False},
        )
        self.assertEqual(
            precommit_bank_result,
            {"banked": False, "error": 2, "visible": False},
        )
        self.assertEqual(
            attack_result,
            {"inserted": False, "set_security_error": None},
        )
        self.assertEqual(
            committed_result,
            {
                "add": {"error": 5, "opened": False},
                "file_write": {"error": 5, "opened": False},
                "insertion": {"created": False},
                "write_dac": {"error": 5, "opened": False},
            },
        )
        self.assertFalse(inserted.exists())
        self.assertEqual(stdout, (output / "preflight-receipt.json").read_bytes())

    @unittest.skipUnless(os.name == "nt", "Windows transactional publication")
    def test_transaction_api_unavailability_fails_before_root_or_stdout(self) -> None:
        output = self.root / "transaction-unavailable-final"
        with (
            patch.object(
                build_cli,
                "_require_safe_windows_privileges",
                return_value=None,
            ),
            patch.object(
                build_cli.ctypes,
                "WinDLL",
                side_effect=OSError("KTM unavailable"),
            ),
        ):
            code, stdout, errors = self._run_main(
                build_main,
                self._build_args(output),
            )

        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, b"")
        self.assertIn("transactional publication APIs are unavailable", errors)
        self.assertFalse(os.path.lexists(output))

    @unittest.skipUnless(os.name == "nt", "Windows transactional validation")
    def test_validator_fails_closed_when_transaction_support_is_unavailable(
        self,
    ) -> None:
        output = self.root / "validator-transaction-unavailable-final"
        code, _, errors = self._run_main(build_main, self._build_args(output))
        self.assertEqual((code, errors), (0, ""))
        original_windll = build_cli.ctypes.WinDLL

        def reject_ktm(name, *args, **kwargs):
            if str(name).casefold() == "ktmw32":
                raise OSError("KTM unavailable")
            return original_windll(name, *args, **kwargs)

        with patch.object(build_cli.ctypes, "WinDLL", new=reject_ktm):
            code, stdout, errors = self._run_main(
                validate_main,
                self._validate_args(output),
            )

        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, b"")
        self.assertIn("transactional publication APIs are unavailable", errors)

    @unittest.skipUnless(os.name == "nt", "Windows transactional publication")
    def test_precommit_failure_rolls_back_without_a_visible_root(self) -> None:
        output = self.root / "transaction-rollback-final"
        failure = build_cli.PreflightCliError("synthetic member seal failure")
        with patch.object(build_cli, "_seal_file_access", side_effect=failure):
            code, stdout, errors = self._run_main(
                build_main,
                self._build_args(output),
            )

        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, b"")
        self.assertIn("synthetic member seal failure", errors)
        self.assertFalse(os.path.lexists(output))

    @unittest.skipUnless(os.name == "nt", "Windows transactional publication")
    def test_commit_failure_rolls_back_without_root_or_stdout(self) -> None:
        class _FakeFunction:
            def __init__(self, callback):
                self.callback = callback
                self.argtypes = None
                self.restype = None

            def __call__(self, *args):
                return self.callback(*args)

        class _FailingCommitKtm:
            def __init__(self, real_ktm):
                self.rollback_calls = 0
                self.CreateTransaction = _FakeFunction(real_ktm.CreateTransaction)
                self.CommitTransaction = _FakeFunction(self._commit)
                self.RollbackTransaction = _FakeFunction(self._rollback)
                self._real_rollback = real_ktm.RollbackTransaction

            @staticmethod
            def _commit(_transaction):
                ctypes.set_last_error(6701)
                return False

            def _rollback(self, transaction):
                self.rollback_calls += 1
                return self._real_rollback(transaction)

        output = self.root / "commit-failure-final"
        original_windll = build_cli.ctypes.WinDLL
        fake_ktm = _FailingCommitKtm(original_windll("KtmW32", use_last_error=True))

        def inject_commit_failure(name, *args, **kwargs):
            if str(name).casefold() == "ktmw32":
                return fake_ktm
            return original_windll(name, *args, **kwargs)

        with patch.object(build_cli.ctypes, "WinDLL", new=inject_commit_failure):
            code, stdout, errors = self._run_main(
                build_main,
                self._build_args(output),
            )

        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, b"")
        self.assertIn("cannot commit (6701)", errors)
        self.assertEqual(fake_ktm.rollback_calls, 1)
        self.assertFalse(os.path.lexists(output))

    @unittest.skipUnless(os.name == "nt", "Windows owner-rights contract")
    def test_owner_cannot_reset_restore_dacl_and_insert_before_stdout(self) -> None:
        output = self.root / "owner-rights-final"
        inserted = output / "owner-inserted-after-final-read.json"
        original = build_cli._require_directory_namespace_sealed
        calls = 0
        reset_blocked = False
        owner_change_blocked = False

        def attack_before_final_seal_check(handle, *, label):
            nonlocal calls, owner_change_blocked, reset_blocked
            calls += 1
            if calls == 3:
                reset_blocked = _windows_owner_reset_insert_restore(output, inserted)
                try:
                    owner_handle = _windows_open_directory(output, 0x00080000)
                except PermissionError:
                    owner_change_blocked = True
                else:
                    build_cli._close_handle(owner_handle)
            return original(handle, label=label)

        with patch.object(
            build_cli,
            "_require_directory_namespace_sealed",
            new=attack_before_final_seal_check,
        ):
            code, stdout, errors = self._run_main(build_main, self._build_args(output))

        self.assertEqual((code, errors), (0, ""))
        self.assertTrue(reset_blocked)
        self.assertTrue(owner_change_blocked)
        self.assertFalse(inserted.exists())
        self.assertEqual(stdout, (output / "preflight-receipt.json").read_bytes())

    @unittest.skipUnless(os.name == "nt", "Windows canonical ACL contract")
    def test_allow_before_deny_descriptor_is_rejected_as_ineffective(self) -> None:
        directory = self.root / "allow-before-deny"
        directory.mkdir()
        handle = _windows_open_directory(
            directory,
            0x00020000 | 0x00040000,
        )
        try:
            _windows_install_allow_before_deny(handle)
            inserted = directory / "insertion-is-effective.json"
            inserted.write_bytes(b"{}\n")
            self.assertTrue(inserted.exists())
            with self.assertRaises(build_cli.PreflightCliError):
                build_cli._require_directory_namespace_sealed(
                    handle,
                    label="allow-before-deny",
                )
        finally:
            build_cli._close_handle(handle)

    @unittest.skipUnless(os.name == "nt", "Windows privilege proof contract")
    def test_effective_thread_and_process_privileges_fail_before_authority_or_stdout(
        self,
    ) -> None:
        class _FakeFunction:
            def __init__(self, callback):
                self.callback = callback
                self.argtypes = None
                self.restype = None

            def __call__(self, *args):
                return self.callback(*args)

        class _FakeAdvapi:
            thread_token = 0x101
            process_token = 0x202

            def __init__(self, enabled_name: str, enabled_token: str):
                self.enabled_name = enabled_name
                self.enabled_token = enabled_token
                self.current_name = ""
                self.OpenThreadToken = _FakeFunction(self._open_thread_token)
                self.OpenProcessToken = _FakeFunction(self._open_process_token)
                self.LookupPrivilegeValueW = _FakeFunction(self._lookup_privilege)
                self.PrivilegeCheck = _FakeFunction(self._privilege_check)

            def _open_thread_token(self, _thread, _access, _as_self, result):
                ctypes.cast(result, ctypes.POINTER(wintypes.HANDLE))[0] = (
                    self.thread_token
                )
                return True

            def _open_process_token(self, _process, _access, result):
                ctypes.cast(result, ctypes.POINTER(wintypes.HANDLE))[0] = (
                    self.process_token
                )
                return True

            def _lookup_privilege(self, _system, name, luid):
                self.current_name = name
                value = ctypes.cast(
                    luid,
                    ctypes.POINTER(build_cli._Luid),
                ).contents
                value.LowPart = 1
                value.HighPart = 0
                return True

            def _privilege_check(self, token, _required, enabled):
                value = token.value if hasattr(token, "value") else token
                ctypes.cast(enabled, ctypes.POINTER(wintypes.BOOL)).contents.value = (
                    value
                    == (
                        self.thread_token
                        if self.enabled_token == "effective thread"
                        else self.process_token
                    )
                    and self.current_name == self.enabled_name
                )
                return True

        for privilege in ("SeTakeOwnershipPrivilege", "SeRestorePrivilege"):
            for token_label in ("effective thread", "process"):
                with self.subTest(privilege=privilege, token=token_label):
                    fake_advapi = _FakeAdvapi(privilege, token_label)
                    output = self.root / (
                        f"{token_label.replace(' ', '-')}-privilege-{privilege}-final"
                    )
                    authority_failure = build_cli.PreflightCliError(
                        "filesystem authority was reached"
                    )
                    with (
                        patch.object(
                            build_cli.ctypes,
                            "WinDLL",
                            return_value=fake_advapi,
                        ),
                        patch.object(build_cli, "_close_handle", return_value=None),
                        patch.object(
                            build_cli,
                            "_new_output_parent",
                            side_effect=authority_failure,
                        ),
                    ):
                        code, stdout, errors = self._run_main(
                            build_main,
                            self._build_args(output),
                        )
                    self.assertNotEqual(code, 0)
                    self.assertEqual(stdout, b"")
                    self.assertIn(f"enabled {privilege}", errors)
                    self.assertIn(f"on {token_label} token", errors)
                    self.assertFalse(output.exists())

                    fake_advapi = _FakeAdvapi(privilege, token_label)
                    with (
                        patch.object(
                            build_cli.ctypes,
                            "WinDLL",
                            return_value=fake_advapi,
                        ),
                        patch.object(build_cli, "_close_handle", return_value=None),
                        patch.object(
                            validate_cli,
                            "read_package_inputs",
                            side_effect=authority_failure,
                        ),
                    ):
                        code, stdout, errors = self._run_main(
                            validate_main,
                            self._validate_args(output),
                        )
                    self.assertNotEqual(code, 0)
                    self.assertEqual(stdout, b"")
                    self.assertIn(f"enabled {privilege}", errors)
                    self.assertIn(f"on {token_label} token", errors)

    @unittest.skipUnless(os.name == "nt", "Windows privilege proof contract")
    def test_enabled_takeover_privilege_fails_closed_before_stdout(self) -> None:
        output = self.root / "privilege-rejected-final"
        failure = build_cli.PreflightCliError(
            "enabled SeRestorePrivilege defeats the publication security proof"
        )
        with patch.object(
            build_cli,
            "_require_safe_windows_privileges",
            side_effect=failure,
        ):
            code, stdout, errors = self._run_main(build_main, self._build_args(output))
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, b"")
        self.assertIn("SeRestorePrivilege", errors)
        self.assertFalse(output.exists())

        code, _, errors = self._run_main(build_main, self._build_args(output))
        self.assertEqual((code, errors), (0, ""))
        with patch.object(
            validate_cli,
            "_require_safe_windows_privileges",
            side_effect=failure,
        ):
            code, stdout, errors = self._run_main(
                validate_main, self._validate_args(output)
            )
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, b"")
        self.assertIn("SeRestorePrivilege", errors)

    def test_builder_retains_parent_authority_during_creation(self) -> None:
        parent = self.root / "publication-parent"
        parent.mkdir()
        displaced = self.root / "publication-parent-displaced"
        output = parent / "parent-bound-final"
        original = build_cli._read_declared_inputs
        substitution_blocked = False

        def attack_after_input_read(namespace):
            nonlocal substitution_blocked
            result = original(namespace)
            try:
                parent.rename(displaced)
                parent.mkdir()
            except OSError:
                substitution_blocked = True
            return result

        with patch.object(
            build_cli,
            "_read_declared_inputs",
            new=attack_after_input_read,
        ):
            code, stdout, errors = self._run_main(build_main, self._build_args(output))

        self.assertEqual((code, errors), (0, ""))
        self.assertTrue(substitution_blocked)
        self.assertEqual(stdout, (output / "preflight-receipt.json").read_bytes())
        self.assertFalse((displaced / output.name).exists())

    def test_both_clis_retain_root_authority_through_stdout(self) -> None:
        output = self.root / "stdout-bound-final"
        displaced_build = self.root / "stdout-bound-build-displaced"
        build_substitution_blocked = False
        original_build_stdout = build_cli._write_stdout

        def attack_build_stdout(raw):
            nonlocal build_substitution_blocked
            try:
                output.rename(displaced_build)
                output.mkdir()
            except OSError:
                build_substitution_blocked = True
            original_build_stdout(raw)

        with patch.object(build_cli, "_write_stdout", new=attack_build_stdout):
            code, stdout, errors = self._run_main(build_main, self._build_args(output))
        self.assertEqual((code, errors), (0, ""))
        self.assertTrue(build_substitution_blocked)
        self.assertEqual(stdout, (output / "preflight-receipt.json").read_bytes())

        displaced_validate = self.root / "stdout-bound-validate-displaced"
        validate_substitution_blocked = False
        original_validate_stdout = validate_cli._write_stdout

        def attack_validate_stdout(raw):
            nonlocal validate_substitution_blocked
            try:
                output.rename(displaced_validate)
                output.mkdir()
            except OSError:
                validate_substitution_blocked = True
            original_validate_stdout(raw)

        with patch.object(
            validate_cli,
            "_write_stdout",
            new=attack_validate_stdout,
        ):
            code, stdout, errors = self._run_main(
                validate_main, self._validate_args(output)
            )
        self.assertEqual((code, errors), (0, ""))
        self.assertTrue(validate_substitution_blocked)
        self.assertEqual(stdout, (output / "preflight-receipt.json").read_bytes())

    def test_validator_retains_declared_parent_through_stdout(self) -> None:
        parent = self.root / "validator-parent"
        parent.mkdir()
        displaced = self.root / "validator-parent-displaced"
        output = parent / "parent-retained-final"
        code, _, errors = self._run_main(build_main, self._build_args(output))
        self.assertEqual((code, errors), (0, ""))
        substitution_blocked = False
        original_stdout = validate_cli._write_stdout

        def attack_parent_before_stdout(raw):
            nonlocal substitution_blocked
            try:
                parent.rename(displaced)
                parent.mkdir()
            except OSError:
                substitution_blocked = True
            original_stdout(raw)

        with patch.object(
            validate_cli,
            "_write_stdout",
            new=attack_parent_before_stdout,
        ):
            code, stdout, errors = self._run_main(
                validate_main,
                self._validate_args(output),
            )

        self.assertEqual((code, errors), (0, ""))
        self.assertTrue(substitution_blocked)
        self.assertEqual(stdout, (output / "preflight-receipt.json").read_bytes())

    def test_existing_output_root_and_duplicate_options_are_rejected(self) -> None:
        output = self.root / "new-package-final"
        code, _, errors = self._run_main(build_main, self._build_args(output))
        self.assertEqual((code, errors), (0, ""))
        code, stdout, errors = self._run_main(build_main, self._build_args(output))
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, b"")
        self.assertIn("already exists", errors)

        duplicate_output = self.root / "duplicate-option-final"
        args = self._build_args(duplicate_output)
        args.extend(("--claim-ledger", str(self.paths["claim-ledger.json"])))
        code, stdout, errors = self._run_main(build_main, args)
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, b"")
        self.assertIn("duplicate option", errors)
        self.assertFalse(os.path.lexists(duplicate_output))

    def test_build_rejects_an_output_root_without_the_final_suffix(self) -> None:
        output = self.root / "synthetic-staging"
        code, stdout, errors = self._run_main(build_main, self._build_args(output))
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, b"")
        self.assertIn("-final", errors)
        self.assertFalse(os.path.lexists(output))

    def test_relative_alias_and_duplicate_input_paths_are_rejected(self) -> None:
        relative_output = self.root / "relative-rejected-final"
        relative_args = self._replace_option(
            self._build_args(relative_output),
            "--claim-ledger",
            "claim-ledger.json",
        )
        code, stdout, errors = self._run_main(build_main, relative_args)
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, b"")
        self.assertIn("absolute", errors)
        self.assertFalse(os.path.lexists(relative_output))

        alias_output = self.root / "alias-rejected-final"
        aliased = f"{self.root}{os.sep}.{os.sep}claim-ledger.json"
        alias_args = self._replace_option(
            self._build_args(alias_output), "--claim-ledger", aliased
        )
        code, stdout, errors = self._run_main(build_main, alias_args)
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, b"")
        self.assertIn("canonical absolute", errors)
        self.assertFalse(os.path.lexists(alias_output))

        duplicate_output = self.root / "duplicate-path-rejected-final"
        duplicate_args = self._replace_option(
            self._build_args(duplicate_output),
            "--jci-census",
            str(self.paths["architecture-census.json"]),
        )
        code, stdout, errors = self._run_main(build_main, duplicate_args)
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, b"")
        self.assertIn("duplicate input path", errors)
        self.assertFalse(os.path.lexists(duplicate_output))

    def test_symlink_or_reparse_input_is_rejected_before_output_creation(self) -> None:
        link = self.root / "claim-link.json"
        try:
            os.symlink(self.paths["claim-ledger.json"], link)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"symlink unavailable: {exc}")
        output = self.root / "link-rejected-final"
        args = self._replace_option(
            self._build_args(output), "--claim-ledger", str(link)
        )
        code, stdout, errors = self._run_main(build_main, args)
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, b"")
        self.assertRegex(errors, "symlink|reparse")
        self.assertFalse(os.path.lexists(output))

    def test_nonregular_and_hardlink_inputs_are_rejected(self) -> None:
        directory_output = self.root / "directory-rejected-final"
        directory_args = self._replace_option(
            self._build_args(directory_output), "--claim-ledger", str(self.root)
        )
        code, stdout, errors = self._run_main(build_main, directory_args)
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, b"")
        self.assertRegex(errors, "regular file|cannot be authenticated")
        self.assertFalse(os.path.lexists(directory_output))

        hardlink = self.root / "claim-hardlink.json"
        try:
            os.link(self.paths["claim-ledger.json"], hardlink)
        except OSError as exc:
            self.skipTest(f"hardlink unavailable: {exc}")
        hardlink_output = self.root / "hardlink-rejected-final"
        hardlink_args = self._replace_option(
            self._build_args(hardlink_output), "--claim-ledger", str(hardlink)
        )
        code, stdout, errors = self._run_main(build_main, hardlink_args)
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, b"")
        self.assertIn("link count", errors)
        self.assertFalse(os.path.lexists(hardlink_output))

    def test_validator_rejects_a_symlink_or_reparse_package_root(self) -> None:
        output = self.root / "real-package-final"
        code, _, errors = self._run_main(build_main, self._build_args(output))
        self.assertEqual((code, errors), (0, ""))
        link = self.root / "package-link-final"
        try:
            os.symlink(output, link, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"directory symlink unavailable: {exc}")
        code, stdout, errors = self._run_main(validate_main, self._validate_args(link))
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, b"")
        self.assertRegex(errors, "symlink|reparse")

    def test_validator_is_read_only_and_rejects_resealed_receipt_reason_deletion(
        self,
    ) -> None:
        negative = self.fixture.inputs(review_unresolved=True, powered=False)
        self.inputs = negative
        self.paths = self._write_inputs(negative)
        output = self.root / "negative-package-final"
        code, _, errors = self._run_main(build_main, self._build_args(output))
        self.assertEqual((code, errors), (0, ""))
        before = {
            str(path.relative_to(output)): sha256(path.read_bytes()).hexdigest()
            for path in output.rglob("*")
            if path.is_file()
        }
        before_security = (
            {
                str(path.relative_to(output)) if path != output else ".": (
                    _windows_security_descriptor_bytes(path)
                )
                for path in (output, *output.rglob("*"))
            }
            if os.name == "nt"
            else None
        )
        code, stdout, errors = self._run_main(
            validate_main, self._validate_args(output)
        )
        self.assertEqual((code, errors), (0, ""))
        self.assertEqual(stdout, (output / "preflight-receipt.json").read_bytes())
        after = {
            str(path.relative_to(output)): sha256(path.read_bytes()).hexdigest()
            for path in output.rglob("*")
            if path.is_file()
        }
        self.assertEqual(after, before)
        after_security = (
            {
                str(path.relative_to(output)) if path != output else ".": (
                    _windows_security_descriptor_bytes(path)
                )
                for path in (output, *output.rglob("*"))
            }
            if os.name == "nt"
            else None
        )
        self.assertEqual(after_security, before_security)

        receipt_path = output / "preflight-receipt.json"
        original_receipt = receipt_path.read_bytes()
        payload = json.loads(original_receipt)
        payload["reason_codes"].remove("prospective_power_insufficient")
        body = dict(payload)
        body.pop("receipt_sha256")
        payload["receipt_sha256"] = sha256(_canonical(body)).hexdigest()
        tampered_receipt = _canonical(payload)
        tampered_output = self.root / "reason-deleted-package-final"
        original_write = build_cli._write_retained_handle

        def substitute_receipt_before_sealing(handle, raw):
            return original_write(
                handle,
                tampered_receipt if raw == original_receipt else raw,
            )

        with (
            patch.object(
                build_cli,
                "_write_retained_handle",
                new=substitute_receipt_before_sealing,
            ),
            patch.object(build_cli, "_verify_created_package", return_value=None),
        ):
            code, _, errors = self._run_main(
                build_main,
                self._build_args(tampered_output),
            )
        self.assertEqual((code, errors), (0, ""))
        code, stdout, errors = self._run_main(
            validate_main,
            self._validate_args(tampered_output),
        )
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, b"")
        self.assertIn("does not match", errors)

    def test_validator_uses_independent_design_and_approval_trust_pins(self) -> None:
        output = self.root / "independent-pins-final"
        code, _, errors = self._run_main(build_main, self._build_args(output))
        self.assertEqual((code, errors), (0, ""))

        code, stdout, _ = self._run_main(validate_main, ["--input-root", str(output)])
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, b"")

        correct = [
            "--input-root",
            str(output),
            "--governing-design-sha256",
            self.inputs.expected_governing_design_sha256,
            "--approval-trust-root-sha256",
            self.inputs.expected_approval_trust_root_sha256,
        ]
        code, stdout, errors = self._run_main(validate_main, correct)
        self.assertEqual((code, errors), (0, ""))
        self.assertEqual(stdout, (output / "preflight-receipt.json").read_bytes())

        wrong = self._replace_option(
            correct,
            "--approval-trust-root-sha256",
            _digest("wrong-independent-approval"),
        )
        code, stdout, _ = self._run_main(validate_main, wrong)
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, b"")

    def test_no_network_provider_model_or_generation_subprocess_capability_is_used(
        self,
    ) -> None:
        output = self.root / "capability-guarded-final"
        failure = AssertionError("forbidden capability called")
        with (
            patch.object(socket, "socket", side_effect=failure),
            patch.object(urllib.request, "urlopen", side_effect=failure),
            patch.object(subprocess, "run", side_effect=failure),
            patch.object(subprocess, "Popen", side_effect=failure),
        ):
            code, _, errors = self._run_main(build_main, self._build_args(output))
            self.assertEqual((code, errors), (0, ""))
            code, _, errors = self._run_main(validate_main, self._validate_args(output))
            self.assertEqual((code, errors), (0, ""))

        project = Path(__file__).resolve(strict=True).parents[1]
        forbidden_imports = {
            "anthropic",
            "autogen",
            "httpx",
            "openai",
            "requests",
            "socket",
            "subprocess",
            "urllib",
        }
        for relative in (
            "iclr2027/oacs_preflight.py",
            "build_iclr2027_oacs_preoutcome.py",
            "validate_iclr2027_oacs_preflight.py",
        ):
            tree = ast.parse((project / relative).read_text(encoding="utf-8"))
            imported = {
                alias.name.split(".")[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            } | {
                node.module.split(".")[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module is not None
            }
            self.assertTrue(forbidden_imports.isdisjoint(imported), relative)


if __name__ == "__main__":
    unittest.main()
