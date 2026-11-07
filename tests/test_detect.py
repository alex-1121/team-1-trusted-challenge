import pandas as pd

from pets_transformer.detect import classify, detect_dataset

N = 200


def col(values):
    return pd.Series([values[i % len(values)] for i in range(N)], dtype=str)


def label(values):
    return classify(col(values))[:2]


def test_hetu_including_900_range():
    hetus = [f"{d:02d}0{m}8{y}-9{i:02d}{c}" for d, m, y, i, c in
             zip(range(10, 28), range(1, 10), range(0, 10), range(0, 99, 7), "ABCDEFHJKLMNPRSTUVWXY")]
    assert label(hetus) == ("direct_identifier", "NATIONAL_ID")


def test_iban():
    ibans = [f"FI{i % 100:02d} {i * 7 % 10000:04d} {i * 13 % 10000:04d} {i * 31 % 10000:04d} {i % 100:02d}" for i in range(N)]
    assert label(ibans) == ("direct_identifier", "IBAN")


def test_email():
    assert label([f"user{i}@mail{i % 5}.example" for i in range(N)]) == ("direct_identifier", "EMAIL")


def test_long_free_text():
    texts = [f"Patient {i} reports pain in the left knee after a fall on day {i % 30}, follow up in a week"
             for i in range(N)]
    assert label(texts) == ("free_text", "FREE_TEXT")


def test_three_value_category_is_non_sensitive():
    assert label(["red", "green", "blue"]) == ("non_sensitive", "CATEGORY")


def test_numeric_measurement():
    assert label([f"{20 + i * 0.37:.1f}" for i in range(N)]) == ("non_sensitive", "MEASUREMENT")


def test_record_key_and_reference_table(tmp_path):
    pd.DataFrame({"a": [f"WX{i:05d}" for i in range(N)],
                  "b": [f"{20 + i * 0.37:.1f}" for i in range(N)],
                  "c": [f"2025-01-{1 + i % 28:02d}" for i in range(N)]}).to_csv(tmp_path / "obs.csv", index=False)
    lab = detect_dataset(tmp_path, "synthetic").set_index("column")
    assert lab.at["a", "privacy_role"] == "record_key"
    # no person in the table, so the date is not a quasi-identifier
    assert lab.at["c", "privacy_role"] == "non_sensitive"
