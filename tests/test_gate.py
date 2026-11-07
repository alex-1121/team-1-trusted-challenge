"""The release gate: one test per way a release must be refused, and the verdict over the committed results."""
import json
import re
from pathlib import Path

import pandas as pd
import pytest
from pets_eval.check import scan_path

from pets_transformer import build, cli, protect, redteam, score

ROOT = Path(__file__).parent.parent
FLOOR = build.UTILITY_FLOOR


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
        "contract": {"tables": tables, "k_target": target},
        "report": {"time_column": "ts", "attacks": attacks},
        "card": {"tables": {"visits": {"status": "released", "k_anonymity": {"min_k": 5}}, "labs": {"status": "released"}, "notes": {"status": "withheld"}},
                 "utility": [{"id": "U1", "score": 0.9}, {"id": "U2", "score": 0.5}],
                 "risk_components": {"visits: direct identifiers retained": 0.0, "visits: free-text identifier leakage": 0.0, "visits: records with k<5": 0.2}},
        "check_results": {"informed_attacker.json": {}, "joined_k.json": joined, "l_diversity.json": {"result": {"worst_group": {"distinct": 2}}}},
        "scan": {"totals": {}, "n_files_scanned": 7},
        "csv_files": ["labs.csv", "plan.csv", "rowmap_labs.csv", "rowmap_visits.csv", "visits.csv"],
        "required_tasks": ["U1", "U2"],
        "utility_floor": FLOOR,
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


def test_l_under_the_target_fails_and_l_of_one_is_not_checked():
    ev = clean()
    ev["check_results"]["l_diversity.json"]["result"]["worst_group"]["distinct"] = 1
    assert reasons(ev, "l:") == ["l: fewest distinct values in a group 1 under 2"]
    ev["contract"]["k_target"]["l"] = 1
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
    assert verdict(contract=ev["contract"], check_results={})["gate"] == "pass"


def test_k_target_without_join_or_sensitive_needs_only_the_informed_attacker():
    ev = clean()
    for key in ("join_flags", "sensitive"):
        del ev["contract"]["k_target"][key]
    ev["contract"]["k_target"]["l"] = 1
    assert verdict(contract=ev["contract"], check_results={"informed_attacker.json": {}})["gate"] == "pass"


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
    status, reason = redteam.attack_status(name, attack, time_col)
    assert status == "not_applicable" and why in reason


@pytest.mark.parametrize("name, attack, why", [
    ("order_attack", {"value": 0.0, "detail": {"applicable": False, "why": "original time column has no dates"}}, "no dates"),
    ("order_attack", {"value": None, "detail": {}}, "did not run"),
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
    status, reason = redteam.attack_status(name, attack, "ts")
    assert status == "fail" and why in reason


def test_measured_zero_on_a_real_attack_is_a_pass():
    assert redteam.attack_status("news_linkage", {"value": 0.0, "detail": {"clips_with_date_and_hour": 25}}, "ts") == ("pass", None)
    ran = {"value": 0.01, "detail": {"applicable": False, "why": "x", "tables_checked": [{"applicable": True}]}}
    assert redteam.attack_status("person_fingerprint", ran, "ts") == ("pass", None)


def test_an_attack_missing_from_the_report_fails():
    ev = clean()
    del ev["report"]["attacks"]["plain_hash"]
    assert reasons(ev, "attack") == ["attack plain_hash: did not run"]


def _toy(tmp_path, folder, ts_rule):
    """A real small release through protect: 40 rows, one record key, a colour, and a time column under ts_rule."""
    original = tmp_path / folder
    original.mkdir()
    n = 40
    pd.DataFrame({"rec": [f"R-{i:03d}" for i in range(n)], "colour": ["red", "blue"] * (n // 2),
                  "ts": [f"2025-01-{1 + i // 8:02d} {3 * (i % 8):02d}:15:00" for i in range(n)]}).to_csv(original / "t.csv", index=False)
    c = {"recipient": "r", "purpose": "p", "trust_level": "t", "threat_model": "m", "required_tasks": ["U1"],
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
    rep = redteam.run(prot, original, c, tmp_path, truth, adversary, specs_path=specs)
    news = rep["attacks"]["news_linkage"]
    assert news["status"] == "fail" and news["pass"] is False and news["value"] is None and rep["gate"] == "fail"
    assert "news clips" in news["reason"] and rep["attacks"]["order_attack"]["status"] in ("pass", "fail")


def test_scorer_linkage_with_its_adversary_file_missing_fails_and_does_not_crash(tmp_path):
    c, original, prot, specs, truth, adversary = _toy(tmp_path, "health", {"pet": "hour_of_day"})
    specs.write_text(json.dumps({"attacks": [{"dataset": "health", "table": "t", "adversary": "gone",
                                              "qis": [{"kind": "exact", "adversary": ["x"], "protected": ["colour"]}]}]}))
    a = redteam.run(prot, original, c, tmp_path, truth, adversary, specs_path=specs)["attacks"]["scorer_linkage_band_aware"]
    assert a["status"] == "fail" and "gone.csv" in a["reason"]


def test_attacks_without_their_inputs_fail(tmp_path):
    c, original, prot, *_ = _toy(tmp_path, "health", {"pet": "hour_of_day"})
    a = redteam.run(prot, original, c, tmp_path)["attacks"]
    assert a["news_linkage"]["status"] == a["scorer_linkage_band_aware"]["status"] == "fail"


def test_health_clips_are_not_applicable_to_other_data_even_with_an_hour_column(tmp_path):
    c, original, prot, specs, truth, adversary = _toy(tmp_path, "toy", {"pet": "hour_of_day"})
    a = redteam.run(prot, original, c, tmp_path, truth, adversary, specs_path=specs)["attacks"]["news_linkage"]
    assert a["status"] == "not_applicable" and "health" in a["reason"]


def test_not_applicable_reads_as_not_applicable_in_json_and_on_screen(tmp_path, capsys):
    c, original, prot, specs, truth, adversary = _toy(tmp_path, "toy", {"pet": "month"})
    cpath, out = tmp_path / "c.json", tmp_path / "redteam.json"
    cpath.write_text(json.dumps(c))
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


@pytest.fixture
def world(tmp_path, monkeypatch):
    """A whole build on a toy dataset: real protect, red team and gate; only the organisers' scorecard is faked."""
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

    def scorecard(original, protected, scenario, out, baseline=None, contract=None, pets_eval=None):
        return {"tables": {"t": {"status": "released"}, "w": {"status": "withheld"}}, "utility": [{"id": "U1", "score": 1.0}],
                "risk_components": {"t: direct identifiers retained": 0.0}, "scan": scan_path(protected)}
    monkeypatch.setattr(build, "PG", pg)
    monkeypatch.setattr(build, "BASELINE_DIR", base)
    monkeypatch.setattr(build.score, "run", scorecard)
    out, results, submission = tmp_path / "o", tmp_path / "r", tmp_path / "s"
    return lambda: build.run("TOY-S1", out=out, results=results, submission=submission, contract_path=cpath), out, results, submission


def test_build_copies_only_the_contract_files(world):
    go, out, results, submission = world
    (submission / "toy").mkdir(parents=True)
    (submission / "toy" / "earlier.csv").write_text("x\n1\n")
    go()
    assert sorted(f.name for f in (submission / "toy").iterdir()) == ["rowmap_t.csv", "t.csv"]
    assert (results / "checks" / "not_run.txt").exists()  # no k target: legitimate, and it does not fail the gate
    assert json.loads((results / "redteam.json").read_text())["gate"] == "pass"


def test_stray_csv_with_an_email_is_refused_and_nothing_is_copied(world):
    go, out, results, submission = world
    (out / "toy").mkdir(parents=True)
    (out / "toy" / "old_contacts.csv").write_text("name,email\nTest Person,test.person@example.invalid\n")
    with pytest.raises(SystemExit) as e:
        go()
    assert "files: unexpected CSV old_contacts.csv" in str(e.value) and "identifier scan: found EMAIL 1" in str(e.value)
    assert not submission.exists()
    rep = json.loads((results / "redteam.json").read_text())
    assert rep["gate"] == "fail" and len(rep["reasons"]) == 2


def test_refusal_lists_every_reason(world, monkeypatch):
    go, out, results, submission = world
    real = build.score.run

    def worse(*a, **k):
        return {**real(*a, **k), "utility": [], "scan": None}
    monkeypatch.setattr(build.score, "run", worse)
    with pytest.raises(SystemExit) as e:
        go()
    assert "utility: required task U1 not measured" in str(e.value) and "identifier scan: did not run" in str(e.value)
    assert not submission.exists()


def test_withdrawn_table_stays_out_of_a_rebuilt_submission(world):
    go, out, results, submission = world
    (out / "toy").mkdir(parents=True)
    (out / "toy" / "w.csv").write_text("rec,note\nR-000,n\n")
    (out / "toy" / "rowmap_w.csv").write_text("protected_row,original_record_id\n0,R-000\n")
    go()
    assert sorted(f.name for f in (out / "toy").glob("*.csv")) == ["plan.csv", "rowmap_t.csv", "t.csv"]
    assert sorted(f.name for f in (submission / "toy").iterdir()) == ["rowmap_t.csv", "t.csv"]


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
    v = redteam.evaluate(contract, json.loads((res / "redteam.json").read_text()), card, check_results, scan, csvs,
                         card["scenario"]["utility_requirements"], FLOOR)
    if fails_on is None:
        assert v["gate"] == "pass" and v["reasons"] == []
    else:
        assert v["gate"] == "fail" and v["reasons"] and all(r.startswith(fails_on) for r in v["reasons"])
