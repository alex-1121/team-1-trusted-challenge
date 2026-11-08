"""The release gate and the signed policy: one test per way a release must be refused, and the verdict over the
committed results. Keys are throwaway ones generated at test time."""
import inspect
import json
import re
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest
from pets_eval.check import scan_path

from pets_transformer import build, cli, contract as ct, policy, protect, redteam, repair, score

ROOT = Path(__file__).parent.parent
SHIPPED = policy.load("HEALTH-S1")
T = SHIPPED["attack_thresholds"]


def clean():
    """Evidence of a release with nothing wrong, as evaluate's keyword arguments."""
    attacks = {
        "order_attack": {"value": 0.0002, "detail": {"best_ordering": "file order"}},
        "news_linkage": {"value": 0.0, "detail": {"clips": 220, "clips_with_date_and_hour": 25}},
        "person_fingerprint": {"value": 0.0, "detail": {"applicable": False, "why": "no person key released", "tables_checked": []}},
        "scorer_linkage_band_aware": {"value": 0.0, "detail": {"specs": [{"adversary": "a", "reidentification_rate": 0.0}]}},
        "plain_hash": {"value": 0.0, "detail": {"hash_like_columns": []}},
    }
    tables = {"visits": {"action": "release", "record_id": "id", "reason": "r"}, "labs": {"action": "release", "record_id": "id", "reason": "r"},
              "notes": {"action": "withhold", "reason": "r"}}
    target = {"table": "visits", "k": 5, "l": 2, "sensitive": "dx", "columns": ["age"], "join_flags": [{"table": "labs", "on": "id"}]}
    joined = {"result": {"min_k": 1}, "for_comparison_k_columns_only": {"min_k": 5},
              "per_join": {"labs": {"result": {"min_k": 1}, "for_comparison_k_columns_only": {"min_k": 5}}}}
    return {
        "policy": {**json.loads(json.dumps(SHIPPED)), "required_tasks": ["U1", "U2"]},
        "contract": {"tables": tables, "k_target": target},
        "report": {"time_column": "ts", "attacks": attacks},
        "card": {"tables": {"visits": {"status": "released", "k_anonymity": {"min_k": 5}}, "labs": {"status": "released"}, "notes": {"status": "withheld"}},
                 "utility": [{"id": "U1", "score": 0.9}, {"id": "U2", "score": 0.5}],
                 "risk_components": {"visits: direct identifiers retained": 0.0, "visits: free-text identifier leakage": 0.0, "visits: records with k<5": 0.2}},
        "check_results": {"informed_attacker.json": {}, "joined_k.json": joined, "l_diversity.json": {"result": {"worst_group": {"distinct": 2}}}},
        "scan": {"totals": {}, "n_files_scanned": 7},
        "csv_files": ["labs.csv", "plan.csv", "rowmap_labs.csv", "rowmap_visits.csv", "visits.csv"],
        "required_tasks": ["U1", "U2"],
    }


def verdict(**changes):
    return redteam.evaluate(**{**clean(), **changes})


def reasons(ev, prefix):
    return [r for r in redteam.evaluate(**ev)["reasons"] if r.startswith(prefix)]


def test_clean_release_passes_and_the_exact_code_join_k_is_not_read():
    v = verdict()
    assert v["gate"] == "pass" and v["reasons"] == [] and v["utility_check"]["pass"] is True


def test_scorer_k_under_the_target_fails():
    ev = clean()
    ev["card"]["tables"]["visits"]["k_anonymity"]["min_k"] = 4
    assert reasons(ev, "k:") == ["k: scorer min k of visits 4 under 5"]


def test_scorer_k_not_measured_fails():
    ev = clean()
    ev["card"]["tables"]["visits"]["k_anonymity"] = {"note": "no catalogued quasi-identifier kept"}
    assert reasons(ev, "k:") == ["k: scorer min k of visits not measured"]


def test_join_k_under_the_target_fails_on_any_join():
    ev = clean()
    ev["check_results"]["joined_k.json"]["per_join"]["other"] = {"for_comparison_k_columns_only": {"min_k": 1}}
    assert reasons(ev, "joined k:") == ["joined k: min k with other 1 under 5"]


def test_a_join_k_result_that_cannot_be_read_fails():
    ev = clean()
    ev["check_results"]["joined_k.json"] = {}
    assert reasons(ev, "joined k:") == ["joined k: min k with the joined tables not measured"]


def test_l_under_the_target_fails_and_l_of_one_is_not_checked():
    ev = clean()
    ev["check_results"]["l_diversity.json"]["result"]["worst_group"]["distinct"] = 1
    assert reasons(ev, "l:") == ["l: fewest distinct values in a group 1 under 2"]
    ev["policy"]["l_min"] = 1
    assert redteam.evaluate(**ev)["gate"] == "pass"


@pytest.mark.parametrize("name", ["informed_attacker.json", "l_diversity.json", "joined_k.json"])
def test_a_check_the_contract_needs_that_did_not_run_fails(name):
    ev = clean()
    del ev["check_results"][name]
    assert reasons(ev, "check did not run") == [f"check did not run: {name}"]


def test_l_above_one_without_a_sensitive_column_cannot_pass_silently():
    ev = clean()
    del ev["contract"]["k_target"]["sensitive"]
    del ev["check_results"]["l_diversity.json"]
    assert reasons(ev, "check did not run") == ["check did not run: l_diversity.json"]


def test_a_contract_without_k_target_needs_no_check():
    ev = clean()
    del ev["contract"]["k_target"]
    ev["policy"].update(k_min=None, l_min=None)
    assert verdict(policy=ev["policy"], contract=ev["contract"], check_results={})["gate"] == "pass"


def test_k_target_without_join_or_sensitive_needs_only_the_informed_attacker():
    ev = clean()
    for key in ("join_flags", "sensitive"):
        del ev["contract"]["k_target"][key]
    ev["policy"]["l_min"] = 1
    assert verdict(policy=ev["policy"], contract=ev["contract"], check_results={"informed_attacker.json": {}})["gate"] == "pass"


def test_stale_check_file_never_satisfies_a_check(tmp_path, monkeypatch):
    stale = tmp_path / "checks"
    stale.mkdir()
    (stale / "l_diversity.json").write_text(json.dumps({"result": {"worst_group": {"distinct": 9}}}))
    (stale / "joined_k.json").write_text("{}")

    def broken(*a):
        raise KeyError("column gone")
    monkeypatch.setattr(build.checks, "run", broken)
    got = build.run_checks({}, tmp_path, tmp_path, tmp_path, [])
    assert got == {} and not (stale / "l_diversity.json").exists() and not (stale / "joined_k.json").exists()
    assert "column gone" in (stale / "not_run.txt").read_text()
    assert len(reasons({**clean(), "check_results": got}, "check did not run")) == 3


def test_stale_not_run_never_fails_a_check(tmp_path, monkeypatch):
    stale = tmp_path / "checks"
    stale.mkdir()
    (stale / "not_run.txt").write_text("Checks not run: an earlier contract.\n")
    fresh = clean()["check_results"]
    monkeypatch.setattr(build.checks, "run", lambda *a: fresh)
    got = build.run_checks({}, tmp_path, tmp_path, tmp_path, [])
    assert got == fresh and not (stale / "not_run.txt").exists()
    assert verdict(check_results=got)["gate"] == "pass"


@pytest.mark.parametrize("name, attack, time_col, why", [
    ("order_attack", {"value": 0.0, "detail": {"applicable": False, "why": "no hour-only column in the release"}}, None, "no hour-only column"),
    ("news_linkage", {"value": None, "detail": None}, None, "no hour-only column"),
    ("news_linkage", {"value": None, "detail": {"applicable": False, "why": "other data"}}, "ts", "other data"),
    ("person_fingerprint", {"value": 0.0, "detail": {"applicable": False, "why": "no person key released", "tables_checked": []}}, "ts", "no person key"),
    ("person_fingerprint", {"value": 0.0, "detail": {"applicable": False, "why": "no quasi-identifier", "tables_checked": [{"applicable": False}]}}, "ts", "no quasi-identifier"),
    ("scorer_linkage_band_aware", {"value": 0.0, "detail": {"specs": [{"evaluated": False, "reason": redteam.NO_QI}]}}, "ts", redteam.NO_QI),
    ("scorer_linkage_band_aware", {"value": 0.0, "detail": {"specs": []}}, "ts", "no attack spec"),
])
def test_attack_with_nothing_to_work_on_is_not_applicable_with_a_reason(name, attack, time_col, why):
    status, reason = redteam.attack_status(name, attack, time_col, T)
    assert status == "not_applicable" and why in reason


@pytest.mark.parametrize("name, attack, why", [
    ("order_attack", {"value": 0.0, "detail": {"applicable": False, "why": "original time column has no dates"}}, "no dates"),
    ("order_attack", {"value": None, "detail": {}}, "did not run"),
    ("order_attack", {"value": 0.0002, "detail": {"columns_checked": [{"applicable": None}, {"applicable": False, "why": "no dates"}]}}, "no dates"),
    ("order_attack", {"value": 0.06, "detail": {}}, "over the threshold"),
    ("news_linkage", {"value": None, "detail": None}, "could not run"),
    ("news_linkage", {"value": 0.0, "detail": {"clips": 0, "clips_with_date_and_hour": 0}}, "could not run"),
    ("person_fingerprint", {"value": 0.0, "detail": {}}, "did not run"),
    ("person_fingerprint", {"value": 0.2935, "detail": {"applicable": False, "why": "x", "tables_checked": [{"applicable": False}, {"applicable": True}]}}, "over the threshold"),
    ("scorer_linkage_band_aware", {"value": None, "detail": None}, "could not run"),
    ("scorer_linkage_band_aware", {"value": 0.0, "detail": {"specs": [{"adversary": "a", "evaluated": False, "reason": "input files missing: a.csv"}]}}, "a.csv"),
    ("scorer_linkage_band_aware", {"value": 0.0, "detail": {"specs": [{"adversary": "a", "reidentification_rate": 0.0}, {"adversary": "b"}]}}, "no rate measured"),
    ("plain_hash", {"value": float("nan"), "detail": {}}, "did not run"),
])
def test_attack_that_should_have_run_fails(name, attack, why):
    status, reason = redteam.attack_status(name, attack, "ts", T)
    assert status == "fail" and why in reason


def test_measured_zero_on_a_real_attack_is_a_pass():
    assert redteam.attack_status("news_linkage", {"value": 0.0, "detail": {"clips_with_date_and_hour": 25}}, "ts", T) == ("pass", None)
    ran = {"value": 0.01, "detail": {"applicable": False, "why": "x", "tables_checked": [{"applicable": True}]}}
    assert redteam.attack_status("person_fingerprint", ran, "ts", T) == ("pass", None)


def test_an_attack_missing_from_the_report_fails():
    ev = clean()
    del ev["report"]["attacks"]["plain_hash"]
    assert reasons(ev, "attack") == ["attack plain_hash: did not run"]


def toy_policy(contract_bytes, **changes):
    return {**json.loads(json.dumps(SHIPPED)), "scenario": "TOY-S1", "k_min": None, "l_min": None, "no_k_target": "no group to count",
            "required_tasks": ["U1"], "allowed_contracts": {"default": policy.sha256(contract_bytes)}, **changes}


def _toy(tmp_path, folder, ts_rule):
    """A real small release through protect: 40 rows, one record key, a colour, and a time column under ts_rule."""
    original = tmp_path / folder
    original.mkdir()
    n = 40
    pd.DataFrame({"rec": [f"R-{i:03d}" for i in range(n)], "colour": ["red", "blue"] * (n // 2),
                  "ts": [f"2025-01-{1 + i // 8:02d} {3 * (i % 8):02d}:15:00" for i in range(n)]}).to_csv(original / "t.csv", index=False)
    c = {"scenario": "TOY-S1", "recipient": "r", "purpose": "p", "trust_level": "t", "threat_model": "m", "required_tasks": ["U1"],
         "tables": {"t": {"action": "release", "record_id": "rec", "reason": "r"}},
         "columns": {"t": {"rec": {"pet": "token", "params": {"prefix": "T"}, "reason": "r"}, "colour": {"pet": "keep", "reason": "r"}, "ts": {**ts_rule, "reason": "r"}}}}
    labels = pd.DataFrame({"table": ["t"] * 3, "column": ["rec", "colour", "ts"], "privacy_role": ["record_key", "non_sensitive", "quasi_identifier"]})
    protect.protect_folder(c, original, tmp_path / "out", b"k" * 32, labels, seed=1)
    specs, truth, adversary = tmp_path / "specs.json", tmp_path / "truth", tmp_path / "adversary"
    specs.write_text(json.dumps({"attacks": []}))
    truth.mkdir(), adversary.mkdir()
    return c, original, tmp_path / "out", specs, truth, adversary


def test_hour_column_with_the_adversary_file_missing_fails(tmp_path):
    c, original, prot, specs, truth, adversary = _toy(tmp_path, "health", {"pet": "hour_of_day"})
    rep = redteam.run(prot, original, c, tmp_path, T, truth, adversary, specs_path=specs)
    news = rep["attacks"]["news_linkage"]
    assert news["status"] == "fail" and news["pass"] is False and news["value"] is None and rep["gate"] == "fail"
    assert "news clips" in news["reason"] and rep["attacks"]["order_attack"]["status"] in ("pass", "fail")


def test_scorer_linkage_with_its_adversary_file_missing_fails_and_does_not_crash(tmp_path):
    c, original, prot, specs, truth, adversary = _toy(tmp_path, "health", {"pet": "hour_of_day"})
    specs.write_text(json.dumps({"attacks": [{"dataset": "health", "table": "t", "adversary": "gone",
                                              "qis": [{"kind": "exact", "adversary": ["x"], "protected": ["colour"]}]}]}))
    a = redteam.run(prot, original, c, tmp_path, T, truth, adversary, specs_path=specs)["attacks"]["scorer_linkage_band_aware"]
    assert a["status"] == "fail" and "gone.csv" in a["reason"]


def test_attacks_without_their_inputs_fail(tmp_path):
    c, original, prot, *_ = _toy(tmp_path, "health", {"pet": "hour_of_day"})
    a = redteam.run(prot, original, c, tmp_path, T)["attacks"]
    assert a["news_linkage"]["status"] == a["scorer_linkage_band_aware"]["status"] == "fail"


def test_health_clips_are_not_applicable_to_other_data_even_with_an_hour_column(tmp_path):
    c, original, prot, specs, truth, adversary = _toy(tmp_path, "toy", {"pet": "hour_of_day"})
    a = redteam.run(prot, original, c, tmp_path, T, truth, adversary, specs_path=specs)["attacks"]["news_linkage"]
    assert a["status"] == "not_applicable" and "health" in a["reason"]


def test_not_applicable_reads_as_not_applicable_in_json_and_on_screen(tmp_path, capsys, monkeypatch):
    c, original, prot, specs, truth, adversary = _toy(tmp_path, "toy", {"pet": "month"})
    cpath, out, pdir = tmp_path / "c.json", tmp_path / "redteam.json", tmp_path / "policies"
    cpath.write_text(json.dumps(c))
    pdir.mkdir()
    (pdir / "TOY-S1.policy.json").write_text(json.dumps(toy_policy(cpath.read_bytes())))
    monkeypatch.setattr(policy, "POLICY_DIR", pdir)
    cli.main(["redteam", "--protected", str(prot), "--original", str(original), "--contract", str(cpath), "--out", str(out),
              "--truth", str(truth), "--adversary", str(adversary), "--attack-specs", str(specs)])
    printed = capsys.readouterr().out
    rep = json.loads(out.read_text())
    assert rep["gate"] == "pass" and rep["attacks"]["plain_hash"]["status"] == "pass"
    for name in ("order_attack", "news_linkage", "person_fingerprint", "scorer_linkage_band_aware"):
        a = rep["attacks"][name]
        assert a["status"] == "not_applicable" and a["reason"] and a["value"] is None and a["pass"] is None
        assert "threshold" in a and "detail" in a
        assert f"{name} not applicable" in printed and f"{name} 0.0" not in printed


def test_a_required_task_missing_from_the_scorecard_fails():
    ev = clean()
    ev["card"]["utility"] = ev["card"]["utility"][:1]
    v = redteam.evaluate(**ev)
    assert reasons(ev, "utility:") == ["utility: required task U2 not measured"]
    assert v["utility_check"]["pass"] is False and v["utility_check"]["below_floor"] == {"U2": None}


@pytest.mark.parametrize("score_value", [0.49, None, float("nan")])
def test_a_required_task_under_the_floor_or_without_a_score_fails(score_value):
    ev = clean()
    ev["card"]["utility"][1]["score"] = score_value
    assert len(reasons(ev, "utility: required task U2")) == 1


def test_the_required_list_comes_from_the_argument_not_the_scorecard_flags():
    ev = clean()
    ev["card"]["utility"].append({"id": "U3", "score": 0.1, "required": True})
    assert redteam.evaluate(**ev)["gate"] == "pass"
    assert len(reasons({**ev, "required_tasks": ["U1", "U2", "U3"]}, "utility:")) == 1


@pytest.mark.parametrize("tasks", [None, []])
def test_a_scenario_without_required_tasks_fails(tasks):
    assert verdict(required_tasks=tasks)["gate"] == "fail"


def test_an_identifier_scan_finding_fails():
    v = verdict(scan={"totals": {"EMAIL": 1}, "n_files_scanned": 8})
    assert v["reasons"] == ["identifier scan: found EMAIL 1"]


@pytest.mark.parametrize("scan", [None, {}, {"totals": {}}, {"totals": {}, "n_files_scanned": 0}, {"totals": "none", "n_files_scanned": 3}, "no findings"])
def test_a_scan_that_did_not_run_or_cannot_be_read_fails(scan):
    assert verdict(scan=scan)["reasons"] == ["identifier scan: did not run"]


@pytest.mark.parametrize("component", ["direct identifiers retained", "free-text identifier leakage"])
@pytest.mark.parametrize("value", [0.0001, None])
def test_scorer_identifier_risks_above_zero_or_unevaluated_fail(component, value):
    ev = clean()
    ev["card"]["risk_components"][f"labs: {component}"] = value
    assert reasons(ev, "scorer risk:") == [f"scorer risk: labs: {component} is {value}"]


def test_a_released_table_the_scorer_could_not_read_fails():
    ev = clean()
    ev["card"]["tables"]["labs"] = {"status": "error", "error": "ValueError"}
    assert reasons(ev, "scorecard:") == ["scorecard: table labs has status error"]


def test_a_stray_or_missing_file_fails():
    ev = clean()
    ev["csv_files"] = ["labs.csv", "plan.csv", "rowmap_labs.csv", "visits.csv", "old_contacts.csv", "sub/deep.csv"]
    assert reasons(ev, "files:") == ["files: unexpected CSV old_contacts.csv", "files: unexpected CSV sub/deep.csv",
                                     "files: expected CSV missing rowmap_visits.csv"]


def test_expected_files_are_the_released_tables_and_their_row_maps():
    assert redteam.expected_files(clean()["contract"]) == ["labs.csv", "rowmap_labs.csv", "rowmap_visits.csv", "visits.csv"]


def test_withdrawn_table_cannot_survive_a_rebuild(tmp_path):
    original = tmp_path / "toy"
    original.mkdir()
    pd.DataFrame({"id": ["1", "2"], "x": ["a", "b"]}).to_csv(original / "t.csv", index=False)
    c = {"tables": {"t": {"action": "release", "record_id": "id", "reason": "r"}},
         "columns": {"t": {"id": {"pet": "keep", "reason": "r"}, "x": {"pet": "keep", "reason": "r"}}}}
    labels = pd.DataFrame({"table": ["t", "t"], "column": ["id", "x"], "privacy_role": ["record_key", "non_sensitive"]})
    out = tmp_path / "out"
    protect.protect_folder(c, original, out, b"k" * 32, labels)
    assert (out / "t.csv").exists() and (out / "rowmap_t.csv").exists()
    withdrawn = {**c, "tables": {"t": {"action": "withhold", "reason": "withdrawn"}}}
    protect.protect_folder(withdrawn, original, out, b"k" * 32, labels)
    assert not (out / "t.csv").exists() and not (out / "rowmap_t.csv").exists()
    assert sorted(f.name for f in out.glob("*.csv")) == ["plan.csv"]


@pytest.fixture(scope="session")
def keys(tmp_path_factory):
    """The steward's and an intruder's throwaway key pairs."""
    d = tmp_path_factory.mktemp("keys")
    for name in ("steward", "intruder"):
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "test", "-f", str(d / name)], check=True)
    return d


def sign(policy_file, key, namespace=policy.NAMESPACE):
    Path(f"{policy_file}.sig").unlink(missing_ok=True)  # with no one to answer its prompt, ssh-keygen keeps an old signature and exits 0
    subprocess.run(["ssh-keygen", "-q", "-Y", "sign", "-f", str(key), "-n", namespace, str(policy_file)], check=True, capture_output=True)


@pytest.fixture
def world(tmp_path, monkeypatch, keys):
    """A whole build on a toy dataset under a signed policy: real protect, red team, gate and ssh-keygen; only the
    organisers' scorecard is faked."""
    pg = tmp_path / "pg"
    for d in ("data/toy", "data/unseen", "metadata", "truth", "adversary"):
        (pg / d).mkdir(parents=True)
    (pg / "data" / "unseen" / "u.csv").write_text("a\n1\n")
    (pg / "metadata" / "scenarios.json").write_text(json.dumps([{"id": "TOY-S1", "dataset": "toy", "utility_requirements": ["U1"]}]))
    (pg / "metadata" / "attack_specs.json").write_text(json.dumps({"attacks": []}))
    n = 30
    pd.DataFrame({"rec": [f"R-{i:03d}" for i in range(n)], "colour": ["red", "blue"] * (n // 2)}).to_csv(pg / "data" / "toy" / "t.csv", index=False)
    pd.DataFrame({"rec": ["R-000"], "note": ["n"]}).to_csv(pg / "data" / "toy" / "w.csv", index=False)
    base = tmp_path / "base"
    base.mkdir()
    (base / "toy_TOY-S1_x_raw.json").write_text("{}")
    contract = {"scenario": "TOY-S1", "dataset": "toy", "recipient": "r", "purpose": "p", "trust_level": "t", "threat_model": "m", "required_tasks": ["U1"],
                "tables": {"t": {"action": "release", "record_id": "rec", "reason": "r"}, "w": {"action": "withhold", "reason": "r"}},
                "columns": {"t": {"rec": {"pet": "token", "params": {"prefix": "T"}, "reason": "r"}, "colour": {"pet": "keep", "reason": "r"}}}}
    cpath = tmp_path / "toy.json"
    cpath.write_text(json.dumps(contract))
    pdir = tmp_path / "policies"
    pdir.mkdir()
    pfile = pdir / "TOY-S1.policy.json"
    pfile.write_text(json.dumps(toy_policy(cpath.read_bytes()), indent=2))
    signers = tmp_path / "trusted" / "allowed_signers"  # stands in for the repo's fixed policy/allowed_signers
    signers.parent.mkdir()
    signers.write_text(f'{policy.PRINCIPAL} namespaces="{policy.NAMESPACE}" {(keys / "steward.pub").read_text()}')
    monkeypatch.setattr(policy, "ALLOWED_SIGNERS", signers)
    monkeypatch.setattr(policy, "POLICY_DIR", pdir)  # stands in for the repo's fixed policy/
    sign(pfile, keys / "steward")

    def scorecard(original, protected, scenario, out, baseline=None, contract=None, pets_eval=None):
        return {"tables": {"t": {"status": "released"}, "w": {"status": "withheld"}}, "utility": [{"id": "U1", "score": 1.0}],
                "risk_components": {"t: direct identifiers retained": 0.0}, "scan": scan_path(protected)}
    monkeypatch.setattr(build, "PG", pg)
    monkeypatch.setattr(build, "BASELINE_DIR", base)
    monkeypatch.setattr(build.score, "run", scorecard)
    out, results, submission = tmp_path / "o", tmp_path / "r", tmp_path / "s"

    def go(contract_path=cpath, **kw):
        return build.run("TOY-S1", out=out, results=results, submission=submission, contract_path=contract_path, **kw)
    return SimpleNamespace(go=go, out=out, results=results, submission=submission, pdir=pdir, pfile=pfile, cpath=cpath, contract=contract,
                           root=tmp_path, signers=signers)


def test_build_copies_only_the_contract_files(world):
    (world.submission / "toy").mkdir(parents=True)
    (world.submission / "toy" / "t.csv").write_text("an earlier build\n")
    world.go()
    assert sorted(f.name for f in (world.submission / "toy").iterdir()) == ["rowmap_t.csv", "t.csv"]
    assert (world.submission / "toy" / "t.csv").read_text() != "an earlier build\n"
    assert (world.results / "checks" / "not_run.txt").exists()  # no k target: legitimate, and it does not fail the gate
    assert json.loads((world.results / "redteam.json").read_text())["gate"] == "pass"


def test_stray_csv_with_an_email_is_refused_and_nothing_is_copied(world):
    (world.out / "toy").mkdir(parents=True)
    (world.out / "toy" / "old_contacts.csv").write_text("name,email\nTest Person,test.person@example.invalid\n")
    with pytest.raises(SystemExit) as e:
        world.go()
    assert "files: unexpected CSV old_contacts.csv" in str(e.value) and "identifier scan: found EMAIL 1" in str(e.value)
    assert not world.submission.exists()
    rep = json.loads((world.results / "redteam.json").read_text())
    assert rep["gate"] == "fail" and len(rep["reasons"]) == 2


def test_refusal_lists_every_reason(world, monkeypatch):
    real = build.score.run

    def worse(*a, **k):
        return {**real(*a, **k), "utility": [], "scan": None}
    monkeypatch.setattr(build.score, "run", worse)
    with pytest.raises(SystemExit) as e:
        world.go()
    assert "utility: required task U1 not measured" in str(e.value) and "identifier scan: did not run" in str(e.value)
    assert not world.submission.exists()


def test_withdrawn_table_stays_out_of_a_rebuilt_submission(world):
    (world.out / "toy").mkdir(parents=True)
    (world.out / "toy" / "w.csv").write_text("rec,note\nR-000,n\n")
    (world.out / "toy" / "rowmap_w.csv").write_text("protected_row,original_record_id\n0,R-000\n")
    world.go()
    assert sorted(f.name for f in (world.out / "toy").glob("*.csv")) == ["plan.csv", "rowmap_t.csv", "t.csv"]
    assert sorted(f.name for f in (world.submission / "toy").iterdir()) == ["rowmap_t.csv", "t.csv"]


def _stub(tmp_path, check_body):
    """Stands in for pets-eval: scorecard writes a minimal card, check runs check_body with $4 the --out file."""
    stub = tmp_path / "pets-eval"
    card = '{"summary":{"privacy":1,"utility":1,"composite":1,"label":"x"},"utility":[],"risk_components":{},"tables":{}}'
    stub.write_text(f"""#!/bin/sh
if [ "$1" = "scorecard" ]; then
  printf '%s' '{card}' > "$9/scorecard.json"
  printf 'x' > "$9/scorecard.html"
  exit 0
fi
{check_body}
""")
    stub.chmod(0o755)
    pg = tmp_path / "a" / "b" / "pg"
    pg.mkdir(parents=True)
    protected, out = tmp_path / "prot", tmp_path / "res"
    protected.mkdir(), out.mkdir()
    (protected / "ed_visits.csv").write_text("a\n1\n")
    return stub, pg, protected, out


def test_a_scan_that_dies_leaves_no_result_and_no_stale_one(tmp_path):
    stub, pg, protected, out = _stub(tmp_path, "exit 3")
    (out / "check.json").write_text('{"totals": {}, "n_files_scanned": 7}')
    card = score.run(tmp_path, protected, "S", out, pets_eval=str(stub), proving_ground=str(pg))
    assert card["scan"] is None and not (out / "check.json").exists()


def test_a_scan_that_finds_something_exits_zero_and_still_reaches_the_gate(tmp_path):
    stub, pg, protected, out = _stub(tmp_path, """printf '%s' '{"totals":{"EMAIL":1},"n_files_scanned":1}' > "$4"
exit 0""")
    card = score.run(tmp_path, protected, "S", out, pets_eval=str(stub), proving_ground=str(pg))
    assert card["scan"]["totals"] == {"EMAIL": 1} and "scan" not in json.loads((out / "scorecard.json").read_text())
    assert verdict(scan=card["scan"])["reasons"] == ["identifier scan: found EMAIL 1"]


def assert_refused(world, match):
    with pytest.raises(SystemExit, match=match):
        world.go()
    assert not world.out.exists() and not world.results.exists() and not world.submission.exists()


def test_valid_signature_builds(world):
    world.go()
    assert (world.submission / "release_record.json").exists()


def test_unsigned_policy_is_refused(world):
    (world.pdir / "TOY-S1.policy.json.sig").unlink()
    assert_refused(world, "sig is missing")


def test_skip_signature_builds_an_unsigned_policy_and_the_record_says_so(world):
    (world.pdir / "TOY-S1.policy.json.sig").unlink()
    world.go(skip_signature=True)
    rec = json.loads((world.submission / "release_record.json").read_text())
    assert rec["signature_file"] == "skipped" and rec["signing_key_fingerprint"] == "skipped"
    assert rec["policy_sha256"] == policy.sha256(world.pfile.read_bytes())


def test_skip_signature_still_refuses_a_contract_the_policy_does_not_allow(world):
    world.cpath.write_bytes(world.cpath.read_bytes() + b" ")
    with pytest.raises(SystemExit, match="is not the one allowed"):
        world.go(skip_signature=True)
    assert not world.submission.exists()


def test_missing_allowed_signers_is_refused(world):
    world.signers.unlink()
    assert_refused(world, "allowed_signers is missing")


def test_no_policy_for_the_scenario_is_refused(world):
    world.pfile.unlink()
    assert_refused(world, "is missing")


def test_one_byte_changed_after_signing_is_refused(world):
    data = bytearray(world.pfile.read_bytes())
    data[data.index(b'"utility_floor": 0.5') + len('"utility_floor": 0.')] = ord("4")
    world.pfile.write_bytes(data)
    assert_refused(world, "does not verify")


def test_wrong_signer_is_refused(world, keys):
    sign(world.pfile, keys / "intruder")
    assert_refused(world, "does not verify")


def test_a_trusted_key_under_another_principal_is_refused(world, keys):
    world.signers.write_text(f'teammate namespaces="{policy.NAMESPACE}" {(keys / "steward.pub").read_text()}')
    assert_refused(world, "does not verify")


def test_a_signature_for_another_namespace_is_refused(world, keys):
    sign(world.pfile, keys / "steward", "file")
    assert_refused(world, "does not verify")


def test_ssh_keygen_missing_is_refused(world, monkeypatch, tmp_path):
    (tmp_path / "empty").mkdir()
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    assert_refused(world, "ssh-keygen could not run")


def test_contract_not_allowed_is_refused(world):
    world.cpath.write_bytes(world.cpath.read_bytes() + b" ")
    assert_refused(world, "is not the one allowed")


def test_a_contract_allowed_for_another_assumption_is_refused(world, keys):
    informed = world.root / "informed.json"
    informed.write_text(json.dumps({**world.contract, "purpose": "stricter"}))
    world.pfile.write_text(json.dumps(toy_policy(world.cpath.read_bytes(), allowed_contracts={
        "default": policy.sha256(world.cpath.read_bytes()), "informed": policy.sha256(informed.read_bytes())})))
    sign(world.pfile, keys / "steward")
    with pytest.raises(SystemExit, match="attacker assumption 'default'"):
        world.go(informed)
    world.pfile.write_text(json.dumps(toy_policy(world.cpath.read_bytes(), attacker_assumption="informed", allowed_contracts={
        "default": policy.sha256(world.cpath.read_bytes()), "informed": policy.sha256(informed.read_bytes())})))
    sign(world.pfile, keys / "steward")
    world.go(informed)


@pytest.fixture
def selecting(world, monkeypatch):
    """The scenario has no contracts/<scenario>.json: the selector runs, in a repo root that is a temporary folder."""
    monkeypatch.setattr(build, "ROOT", world.root / "repo")
    monkeypatch.setattr(build.selector, "select", lambda original, scenario, pg, **kw: (world.contract, {"scenario": scenario}))
    world.text = json.dumps(world.contract, indent=2, ensure_ascii=False) + "\n"
    world.pinned = world.root / "repo" / "contracts" / "generated" / "TOY-S1.auto.json"
    return world


def test_generated_contract_is_compared_after_selection(selecting, keys):
    w = selecting
    w.pfile.write_text(json.dumps(toy_policy(w.text.encode())))
    sign(w.pfile, keys / "steward")
    w.go(w.root / "no-such-contract.json")
    assert w.pinned.read_text() == w.text and (w.results / "selection.json").exists()


def test_generated_contract_that_differs_is_refused_and_leaves_the_signed_one_alone(selecting):
    w = selecting
    w.pinned.parent.mkdir(parents=True)
    w.pinned.write_text("the contract the steward signed\n")
    with pytest.raises(SystemExit, match="is not the one allowed"):
        w.go(w.root / "no-such-contract.json")
    assert w.pinned.read_text() == "the contract the steward signed\n" and not w.results.exists()


def test_record_hashes_match_the_files_and_it_says_what_stays_at_risk(world):
    world.go()
    rec = json.loads((world.submission / "release_record.json").read_text())
    assert rec == json.loads((world.results / "release_record.json").read_text())
    assert sorted(rec["files_for_recipient"]) == ["toy/t.csv", "toy_field_labels.csv", "unseen_field_labels.csv"]
    assert sorted(rec["files_for_organiser_scoring_only"]) == ["toy/rowmap_t.csv"] and "never to the recipient" in rec["row_maps"]
    assert "files_sha256" not in rec
    hashed = {**rec["files_for_recipient"], **rec["files_for_organiser_scoring_only"]}
    on_disk = {str(f.relative_to(world.submission)) for f in world.submission.rglob("*") if f.is_file()} - {"release_record.json"}
    assert on_disk == set(hashed)
    for name, digest in hashed.items():
        assert policy.sha256((world.submission / name).read_bytes()) == digest
    assert rec["policy_sha256"] == policy.sha256(world.pfile.read_bytes()) and rec["signature_file"] == "TOY-S1.policy.json.sig"
    assert rec["contract_sha256"] == policy.sha256(world.cpath.read_bytes())
    pol = json.loads(world.pfile.read_text())
    for field in ("recipient", "purpose", "agreement_ref", "recipient_duties", "enforced_after_release"):
        assert rec[field] == pol[field]
    assert rec["enforced_after_release"] == "none"
    assert rec["residual_risks"]["checks"] == "not run: no group to count"
    assert rec["residual_risks"]["attacks_not_applicable"]["order_attack"] == "no hour-only column in the release"


def test_record_carries_the_results_of_the_checks():
    ev = clean()
    ev["check_results"]["informed_attacker.json"] = {"result": {"protected": {"correct_rate": 0.09}}}
    ev["report"] = {"gate": "pass", "attacks": {"person_fingerprint": {"status": "not_applicable", "reason": "no person key"}, "plain_hash": {"status": "pass"}}}
    rec = policy.record(ev["policy"], "p", "s", "f", "c", {"h/v.csv": "1", "h/rowmap_v.csv": "2", "unseen_field_labels.csv": "3"}, ev["check_results"], ev["report"])
    assert rec["files_for_recipient"] == {"h/v.csv": "1", "unseen_field_labels.csv": "3"} and rec["files_for_organiser_scoring_only"] == {"h/rowmap_v.csv": "2"}
    r = rec["residual_risks"]
    assert r["checks"]["informed_attacker"]["protected"]["correct_rate"] == 0.09
    assert r["checks"]["joined_k"]["labs"]["result"]["min_k"] == 1 and r["checks"]["l_diversity"]["worst_group"]["distinct"] == 2
    assert r["attacks_not_applicable"] == {"person_fingerprint": "no person key"}


def test_a_refused_rebuild_leaves_no_record_in_results(world):
    world.go()
    (world.out / "toy" / "stray.csv").write_text("a\n1\n")
    with pytest.raises(SystemExit):
        world.go()
    assert not (world.results / "release_record.json").exists()


def test_a_signed_policy_of_another_scenario_is_refused():
    with pytest.raises(SystemExit, match="is for HEALTH-S1"):
        policy.parse(json.dumps(SHIPPED).encode(), "HEALTH-S3")


@pytest.mark.parametrize("changes, match", [
    ({"attack_thresholds": {k: v for k, v in T.items() if k != "plain_hash"}}, "attack_thresholds"),
    ({"attack_thresholds": {**T, "order_attack": None}}, "attack_thresholds"),
    ({"attack_thresholds": {**T, "extra": 1}}, "attack_thresholds"),
    ({"utility_floor": "half"}, "utility_floor"),
    ({"required_tasks": []}, "required_tasks"),
    ({"k_min": None}, "no_k_target"),
    ({"k_min": None, "l_min": None, "no_k_target": ""}, "no_k_target"),
    ({"no_k_target": "says both"}, "no_k_target"),
    ({"l_min": None}, "an integer of at least"),
    ({"k_min": 0}, "an integer of at least"),
    ({"k_min": 1}, "an integer of at least"),
    ({"k_min": True}, "an integer of at least"),
    ({"k_min": 5.0}, "an integer of at least"),
    ({"l_min": 0}, "an integer of at least"),
    ({"l_min": True}, "an integer of at least"),
    ({"utility_floor": True}, "utility_floor"),
    ({"attacker_assumption": "other"}, "allowed_contracts"),
])
def test_a_policy_without_a_usable_limit_is_refused_even_when_signed(changes, match):
    with pytest.raises(SystemExit, match=match):
        policy.parse(json.dumps({**SHIPPED, **changes}).encode(), "HEALTH-S1")


def test_a_policy_missing_a_field_or_not_json_is_refused():
    with pytest.raises(SystemExit, match="agreement_ref"):
        policy.parse(json.dumps({k: v for k, v in SHIPPED.items() if k != "agreement_ref"}).encode(), "HEALTH-S1")
    with pytest.raises(SystemExit, match="not valid JSON"):
        policy.parse(b"{", "HEALTH-S1")
    with pytest.raises(SystemExit, match="missing fields"):
        policy.parse(b"[]", "HEALTH-S1")


def test_the_limits_are_the_policys():
    ev = clean()
    ev["policy"]["k_min"] = 6
    assert reasons(ev, "k:") == ["k: scorer min k of visits 5 under 6"] and len(reasons(ev, "joined k:")) == 1
    ev = clean()
    ev["policy"]["l_min"] = 3
    assert len(reasons(ev, "l:")) == 1
    ev = clean()
    ev["policy"]["utility_floor"] = 0.95
    assert len(reasons(ev, "utility:")) == 2
    ev = clean()
    ev["policy"]["attack_thresholds"]["order_attack"] = 0.0001
    assert reasons(ev, "attack") == ["attack order_attack: 0.0002 over the threshold 0.0001"]


def test_a_policy_can_add_a_task_but_not_remove_one():
    ev = clean()
    ev["policy"]["required_tasks"] = ["U1", "U9"]
    assert reasons(ev, "utility:") == ["utility: required task U9 not measured"]
    ev = clean()
    ev["policy"]["required_tasks"] = ["U1"]
    ev["card"]["utility"] = ev["card"]["utility"][:1]
    assert reasons(ev, "utility:") == ["utility: required task U2 not measured"]


def test_policy_and_contract_must_agree_on_a_k_target():
    ev = clean()
    ev["policy"].update(k_min=None, l_min=None)
    assert reasons(ev, "policy:") == ["policy: k_min and the contract's k target do not match"]
    ev = clean()
    del ev["contract"]["k_target"]
    assert reasons(ev, "policy:") == ["policy: k_min and the contract's k target do not match"]


def test_redteam_run_takes_its_thresholds_from_the_argument(tmp_path):
    c, original, prot, specs, truth, adversary = _toy(tmp_path, "toy", {"pet": "hour_of_day"})
    a = redteam.run(prot, original, c, tmp_path, {**T, "order_attack": -1.0}, truth, adversary, specs_path=specs)["attacks"]["order_attack"]
    assert a["threshold"] == -1.0 and a["status"] == "fail"


def test_cli_redteam_needs_the_scenarios_policy(tmp_path, monkeypatch):
    c, original, prot, specs, truth, adversary = _toy(tmp_path, "toy", {"pet": "month"})
    cpath = tmp_path / "c.json"
    cpath.write_text(json.dumps(c))
    monkeypatch.setattr(policy, "POLICY_DIR", tmp_path / "no-policies")
    with pytest.raises(SystemExit, match="no policy file"):
        cli.main(["redteam", "--protected", str(prot), "--original", str(original), "--contract", str(cpath), "--out", str(tmp_path / "r.json")])


def test_a_contract_must_name_its_scenario(tmp_path):
    cpath = tmp_path / "c.json"
    cpath.write_text(json.dumps({"recipient": "r", "purpose": "p", "trust_level": "t", "threat_model": "m", "required_tasks": [], "tables": {}, "columns": {}}))
    with pytest.raises(ValueError, match="scenario"):
        ct.load(cpath)


@pytest.mark.parametrize("policy_floor, used", [(0.0, 0.85), (0.5, 0.85), (0.9, 0.9)])
def test_repair_search_uses_the_higher_of_its_floor_and_the_policys(tmp_path, policy_floor, used):
    original = tmp_path / "toy"
    original.mkdir()
    pd.DataFrame({"rec": [f"R-{i}" for i in range(12)], "age": ["30-39"] * 12}).to_csv(original / "t.csv", index=False)
    c = {"required_tasks": ["U1"], "tables": {"t": {"action": "release", "record_id": "rec", "reason": "r"}},
         "columns": {"t": {"rec": {"pet": "token", "params": {"prefix": "T"}, "reason": "r"}, "age": {"pet": "keep", "reason": "r"}}},
         "k_target": {"table": "t", "k": 5, "l": 1, "columns": ["age"], "ladder": {"wide": {"column": "age", "op": "widen_band", "width": 20, "reason": "r"}}, "reason": "r"}}
    labels = pd.DataFrame({"table": ["t", "t"], "column": ["rec", "age"], "privacy_role": ["record_key", "quasi_identifier"]})

    def card(prot, res):
        return {"utility": [{"id": "U1", "score": 1.0}], "summary": {"privacy": 1.0, "utility": 1.0, "composite": 1.0}}
    repair.search(c, original, tmp_path / "o", tmp_path / "r", b"k" * 32, labels, card, policy_floor=policy_floor)
    assert json.loads((tmp_path / "r" / "repair_search.json").read_text())["floor"] == used


def test_an_older_signed_policy_kept_outside_policy_is_never_read(world, keys, tmp_path, monkeypatch):
    # the steward signed an older policy that allowed an older contract with a laxer floor; both still verify
    old = tmp_path / "old-commit"
    old.mkdir()
    old_contract = old / "toy.json"
    old_contract.write_text(json.dumps({**world.contract, "purpose": "the earlier contract"}))
    (old / "TOY-S1.policy.json").write_text(json.dumps(toy_policy(old_contract.read_bytes(), utility_floor=0.0)))
    sign(old / "TOY-S1.policy.json", keys / "steward")
    (old / "allowed_signers").write_text(world.signers.read_text())
    assert policy.verify.__code__.co_argcount == 1  # the scenario only: no folder can be passed in
    opened = []
    real = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda self: opened.append(self) or real(self))
    with pytest.raises(SystemExit, match="is not the one allowed"):
        world.go(old_contract)
    assert not [f for f in opened if old in f.parents and f != old_contract]
    for cmd in (["build", "--scenario", "TOY-S1"], ["redteam", "--protected", "p", "--original", "o", "--contract", "c", "--out", "r"]):
        with pytest.raises(SystemExit) as e:
            cli.main(cmd + ["--policy-dir", str(old)])
        assert e.value.code == 2  # argparse: no such option


def test_no_argument_or_flag_can_move_the_policy_or_allowed_signers(capsys):
    assert policy.POLICY_DIR == ROOT / "policy" and policy.ALLOWED_SIGNERS == ROOT / "policy" / "allowed_signers"
    for f in (build.run, policy.verify, policy.load):
        assert not [n for n in inspect.signature(f).parameters if "signer" in n or "policy" in n or n.endswith("dir")]
    for cmd in ("build", "redteam"):
        with pytest.raises(SystemExit):
            cli.main([cmd, "--help"])
        help_text = capsys.readouterr().out
        assert "--allowed" not in help_text and "--policy" not in help_text


def test_record_names_the_signing_keys_fingerprint(world, keys):
    world.go()
    reported = subprocess.run(["ssh-keygen", "-lf", str(keys / "steward.pub")], capture_output=True, text=True, check=True).stdout.split()[1]
    rec = json.loads((world.submission / "release_record.json").read_text())
    assert reported.startswith("SHA256:") and rec["signing_key_fingerprint"] == reported


def test_the_contract_is_hashed_and_parsed_from_one_read(world, monkeypatch):
    signed_bytes = world.cpath.read_bytes()
    real = policy.verify

    def swap_after_the_read(*a):
        got = real(*a)
        world.cpath.write_text(json.dumps({**world.contract, "columns": {"t": {**world.contract["columns"]["t"], "colour": {"pet": "drop", "reason": "r"}}}}))
        return got
    monkeypatch.setattr(build.policy, "verify", swap_after_the_read)
    world.go()
    assert json.loads((world.results / "release_record.json").read_text())["contract_sha256"] == policy.sha256(signed_bytes)
    assert "colour" in (world.submission / "toy" / "t.csv").read_text().splitlines()[0]


def test_the_policy_is_parsed_from_the_bytes_that_verified(world, monkeypatch):
    real = subprocess.run

    def swap_after_verifying(*a, **k):
        r = real(*a, **k)
        world.pfile.write_text(json.dumps(toy_policy(world.cpath.read_bytes(), utility_floor=0.0)))
        return r
    monkeypatch.setattr(policy.subprocess, "run", swap_after_verifying)
    assert policy.verify("TOY-S1")[0]["utility_floor"] == 0.5


def test_a_refusal_at_signature_time_removes_the_earlier_verdict(world):
    world.results.mkdir()
    for name in ("release_record.json", "redteam.json"):
        (world.results / name).write_text('{"gate": "pass"}')
    (world.pdir / "TOY-S1.policy.json.sig").unlink()
    with pytest.raises(SystemExit, match="sig is missing"):
        world.go()
    assert sorted(world.results.iterdir()) == []


def test_a_refusal_at_contract_time_removes_the_earlier_verdict(world):
    world.results.mkdir()
    (world.results / "redteam.json").write_text('{"gate": "pass"}')
    world.cpath.write_bytes(world.cpath.read_bytes() + b" ")
    with pytest.raises(SystemExit, match="is not the one allowed"):
        world.go()
    assert not (world.results / "redteam.json").exists()


def test_a_submission_folder_holding_anything_else_is_refused_and_nothing_is_touched(world):
    world.go()
    for extra in ("notes.txt", "education/students.csv", "toy/sub/deep.csv", "toy/old_contacts.csv"):
        (world.submission / extra).parent.mkdir(parents=True, exist_ok=True)
        (world.submission / extra).write_text("x\n")
    (world.submission / "toy" / "t.csv").write_text("the earlier release\n")
    with pytest.raises(SystemExit) as e:
        world.go()
    for named in ("notes.txt", "education", "education/students.csv", "toy/sub", "toy/sub/deep.csv", "toy/old_contacts.csv"):
        assert named in str(e.value)
    assert (world.submission / "toy" / "t.csv").read_text() == "the earlier release\n"
    assert all((world.submission / x).exists() for x in ("notes.txt", "education/students.csv", "toy/sub/deep.csv", "toy/old_contacts.csv"))


@pytest.mark.parametrize("dirt", [".DS_Store", "education_field_labels.csv", "education/students.csv"])
def test_a_dirty_submission_folder_is_refused_before_any_work(world, monkeypatch, dirt):
    def no_work(*a, **k):
        raise AssertionError("the build started work on a dirty submission folder")
    monkeypatch.setattr(build.detect, "detect_dataset_report", no_work)
    (world.submission / dirt).parent.mkdir(parents=True, exist_ok=True)
    (world.submission / dirt).write_text("x\n")
    with pytest.raises(SystemExit, match=re.escape(dirt)):
        world.go()
    assert not world.out.exists() and (world.submission / dirt).exists()


@pytest.mark.parametrize("break_it", ["contract", "input"])
def test_any_refusal_removes_the_earlier_verdict_first(world, monkeypatch, break_it):
    world.results.mkdir()
    for name in ("release_record.json", "redteam.json"):
        (world.results / name).write_text('{"gate": "pass"}')
    if break_it == "contract":
        world.cpath.write_text("{ not json")
    else:
        monkeypatch.setattr(build, "BASELINE_DIR", world.root / "no-baselines")
    with pytest.raises((ValueError, FileNotFoundError)):
        world.go()
    assert sorted(world.results.iterdir()) == []


def test_a_rebuild_into_its_own_submission_folder_passes(world):
    world.go()
    world.go()
    assert sorted(str(f.relative_to(world.submission)) for f in world.submission.rglob("*") if f.is_file()) == [
        "release_record.json", "toy/rowmap_t.csv", "toy/t.csv", "toy_field_labels.csv", "unseen_field_labels.csv"]


def test_a_repeating_id_released_as_it_is_is_a_person_key(tmp_path):
    original = tmp_path / "toy"
    original.mkdir()
    n = 40
    pd.DataFrame({"rec": [f"R-{i:03d}" for i in range(n)], "pid": [f"P-{i % 10}" for i in range(n)],
                  "municipality": [["Turku", "Oulu", "Espoo", "Vantaa"][(i % 10) % 4] for i in range(n)]}).to_csv(original / "t.csv", index=False)
    c = {"scenario": "TOY-S1", "tables": {"t": {"action": "release", "record_id": "rec", "reason": "r"}},
         "columns": {"t": {"rec": {"pet": "token", "params": {"prefix": "T"}, "reason": "r"}, "municipality": {"pet": "keep", "reason": "r"}}},
         "roles": {"t": {"technical_identifier": {"pet": "keep", "reason": "kept as it is"}}}}
    specs = tmp_path / "specs.json"
    specs.write_text(json.dumps({"attacks": []}))

    def fingerprint(role):
        labels = pd.DataFrame({"table": ["t"] * 3, "column": ["rec", "pid", "municipality"], "privacy_role": ["record_key", role, "quasi_identifier"]})
        c["roles"]["t"] = {role: {"pet": "keep", "reason": "kept as it is"}}
        prot = tmp_path / role
        protect.protect_folder(c, original, prot, b"k" * 32, labels, seed=1)
        return redteam.run(prot, original, c, tmp_path, T, tmp_path, tmp_path, specs_path=specs)["attacks"]["person_fingerprint"]
    kept = fingerprint("technical_identifier")
    assert kept["status"] != "not_applicable" and kept["detail"]["person_column"] == "pid" and kept["detail"]["applicable"] is True
    assert fingerprint("non_sensitive")["status"] == "not_applicable"


def _two_hours(tmp_path, second_table_action):
    original = tmp_path / "health"
    original.mkdir()
    n = 40
    ts = [f"2025-01-{1 + i // 8:02d} {3 * (i % 8):02d}:15:00" for i in range(n)]
    pd.DataFrame({"rec": [f"R-{i:03d}" for i in range(n)], "ts": ts}).to_csv(original / "a.csv", index=False)
    pd.DataFrame({"lab": [f"L-{i:03d}" for i in range(n)], "sampled": ts}).to_csv(original / "b.csv", index=False)
    c = {"scenario": "TOY-S1", "tables": {"a": {"action": "release", "record_id": "rec", "reason": "r"},
                                          "b": {"action": second_table_action, "record_id": "lab", "reason": "r"}},
         "columns": {"a": {"rec": {"pet": "token", "params": {"prefix": "T"}, "reason": "r"}, "ts": {"pet": "hour_of_day", "reason": "r"}},
                     "b": {"lab": {"pet": "token", "params": {"prefix": "L"}, "reason": "r"}, "sampled": {"pet": "hour_of_day", "reason": "r"}}}}
    labels = pd.DataFrame({"table": ["a", "a", "b", "b"], "column": ["rec", "ts", "lab", "sampled"],
                           "privacy_role": ["record_key", "quasi_identifier", "record_key", "quasi_identifier"]})
    protect.protect_folder(c, original, tmp_path / "out", b"k" * 32, labels, seed=1)
    return redteam.run(tmp_path / "out", original, c, tmp_path, T)


def test_every_hour_column_of_a_released_table_is_attacked(tmp_path):
    rep = _two_hours(tmp_path, "release")
    checked = rep["attacks"]["order_attack"]["detail"]["columns_checked"]
    assert [(x["table"], x["column"]) for x in checked] == [("a", "ts"), ("b", "sampled")] and rep["time_columns"] == [["a", "ts"], ["b", "sampled"]]


def test_an_hour_column_of_a_withheld_table_is_not_attacked(tmp_path):
    rep = _two_hours(tmp_path, "withhold")
    assert rep["time_columns"] == [["a", "ts"]] and len(rep["attacks"]["order_attack"]["detail"]["columns_checked"]) == 1
    assert redteam._time_columns({"tables": {"w": {"action": "withhold"}}, "columns": {"w": {"h": {"pet": "hour_of_day"}}}}) == []


def _fake_ssh_keygen(tmp_path, monkeypatch, body):
    """A decoy ssh-keygen first on PATH; it records that it ran."""
    d = tmp_path / "decoy"
    d.mkdir()
    (d / "ssh-keygen").write_text(f"#!/bin/sh\n/usr/bin/touch {d}/ran\n{body}\n")
    (d / "ssh-keygen").chmod(0o755)
    monkeypatch.setenv("PATH", str(d))
    return d


def test_ssh_keygen_that_hangs_is_refused(world, monkeypatch, tmp_path):
    d = _fake_ssh_keygen(tmp_path, monkeypatch, "exec /bin/sleep 5")
    monkeypatch.setattr(policy, "VERIFY_TIMEOUT", 0.5)
    assert_refused(world, "did not answer within 0.5 seconds")
    assert (d / "ran").exists()


def test_a_verification_without_a_key_fingerprint_is_refused(world, monkeypatch, tmp_path):
    d = _fake_ssh_keygen(tmp_path, monkeypatch, "exit 0")
    assert_refused(world, "reported no key fingerprint")
    assert (d / "ran").exists()


SCENARIOS = {"HEALTH-S1": {"default": "HEALTH-S1.json", "informed": "HEALTH-S1-informed.json"}, "HEALTH-S3": {"default": "generated/HEALTH-S3.auto.json"},
             "EDU-S2": {"default": "generated/EDU-S2.auto.json"}, "ENERGY-S3": {"default": "generated/ENERGY-S3.auto.json"}, "PUB-S3": {"default": "PUB-S3.json"}}


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_shipped_policy_holds_todays_values_and_pins_the_committed_contracts(scenario):
    p = policy.load(scenario)
    assert p["attack_thresholds"] == {"order_attack": 0.05, "news_linkage": 0.0, "person_fingerprint": 0.05, "scorer_linkage_band_aware": 0.01, "plain_hash": 0.0}
    assert p["utility_floor"] == 0.5 and p["enforced_after_release"] == "none" and p["attacker_assumption"] == "default"
    assert len(p["recipient_duties"]) == 2 and "re-identification" in p["recipient_duties"][0] and "linkage" in p["recipient_duties"][1]
    assert p["allowed_contracts"] == {a: policy.sha256((ROOT / "contracts" / f).read_bytes()) for a, f in SCENARIOS[scenario].items()}
    c = json.loads((ROOT / "contracts" / SCENARIOS[scenario]["default"]).read_text())
    kt = c.get("k_target")
    assert (p["k_min"], p["l_min"]) == ((kt["k"], kt.get("l", 1)) if kt else (None, None)) and bool(p["no_k_target"]) == (not kt)
    assert p["recipient"] == c["recipient"] and p["purpose"] == c["purpose"] and sorted(p["required_tasks"]) == sorted(c["required_tasks"])


COMMITTED = {
    "health-s1-build": ("HEALTH-S1.json", None),
    "health-s1-informed-build": ("HEALTH-S1-informed.json", None),
    "health-s3-build": ("generated/HEALTH-S3.auto.json", None),
    "edu-s2-build": ("generated/EDU-S2.auto.json", None),
    "energy-s3-build": ("generated/ENERGY-S3.auto.json", None),
    "pub-s3-build": ("PUB-S3.json", "utility:"),
    "health-s1-noflag-build": ("HEALTH-S1-noflag.json", "joined k:"),
    "health-s1-pseudonym-build": ("HEALTH-S1-pseudonym.json", "attack person_fingerprint:"),
}


@pytest.mark.parametrize("run", COMMITTED)
def test_verdict_over_the_committed_results(run):
    contract_file, fails_on = COMMITTED[run]
    res = ROOT / "results" / run
    contract = json.loads((ROOT / "contracts" / contract_file).read_text())
    card = json.loads((res / "scorecard.json").read_text())
    text = (res / "check.txt").read_text()  # these runs predate check.json; a build always has the structured scan
    found = re.match(r"scanned (\d+) files\n  no residual direct identifiers found", text)
    scan = {"totals": {}, "n_files_scanned": int(found.group(1))} if found else None
    check_results = {f.name: json.loads(f.read_text()) for f in (res / "checks").glob("*.json")}
    # the folder is not committed; the scorecard's list of extra tables is what it recorded about it
    csvs = redteam.expected_files(contract) + [f"{t}.csv" for t in card["extra_protected_files"]]
    limits = policy.load(contract["scenario"])
    v = redteam.evaluate(limits, contract, json.loads((res / "redteam.json").read_text()), card, check_results, scan, csvs,
                         card["scenario"]["utility_requirements"])
    if fails_on is None:
        assert v["gate"] == "pass" and v["reasons"] == []
    else:
        assert v["gate"] == "fail" and v["reasons"] and all(r.startswith(fails_on) for r in v["reasons"])


def test_log_build_appends_one_line_per_gated_build(tmp_path):
    import json as _json
    from pets_transformer import build as _build
    _build.log_build(tmp_path, "HEALTH-S1", {"gate": "fail", "reasons": ["news_linkage above threshold"]})
    _build.log_build(tmp_path, "HEALTH-S1", {"gate": "pass", "reasons": []})
    rows = [_json.loads(x) for x in (tmp_path / "builds.jsonl").read_text().splitlines()]
    assert [r["gate"] for r in rows] == ["fail", "pass"]
    assert rows[0]["reasons"] == ["news_linkage above threshold"] and rows[0]["scenario"] == "HEALTH-S1"
    assert all(r["utc"].endswith("Z") for r in rows)


SCEN = {"id": "TOY-S9", "dataset": "toy_set", "recipient": "r", "purpose": "p", "utility_requirements": ["U1", "U2"]}


def test_a_drafted_policy_pins_the_contract_and_copies_k_and_l_from_its_target():
    data = json.dumps({"k_target": {"k": 5, "l": 2}}).encode()
    p = policy.draft(SCEN, data)
    assert p["allowed_contracts"] == {"default": policy.sha256(data)} and (p["k_min"], p["l_min"], p["no_k_target"]) == (5, 2, None)
    assert p["required_tasks"] == ["U1", "U2"] and p["attack_thresholds"] == policy.DRAFT_THRESHOLDS
    assert policy.check_contract(p, data) == policy.sha256(data)


def test_a_drafted_policy_without_a_k_target_says_why_and_still_parses():
    p = policy.draft(SCEN, b"{}")
    assert p["k_min"] is None and p["l_min"] is None and p["no_k_target"]


def test_draft_policy_never_overwrites_a_policy(capsys):
    with pytest.raises(SystemExit):
        cli.main(["draft-policy", "--scenario", "HEALTH-S1", "--contract", "contracts/HEALTH-S1.json"])
    assert "never overwrites" in capsys.readouterr().err
