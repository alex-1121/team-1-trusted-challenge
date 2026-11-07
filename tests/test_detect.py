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


def test_hetu_without_century_sign():
    check = "0123456789ABCDEFHJKLMNPRSTUVWXY"
    bases = [f"{d:02d}{m:02d}{y:02d}{i:03d}" for d, m, y, i in
             zip(range(1, 29), [1 + k % 12 for k in range(28)], range(50, 78), range(2, 900, 31))]
    assert label([b + check[int(b) % 31] for b in bases]) == ("direct_identifier", "NATIONAL_ID")
    # same shape with wrong check characters is not a HETU
    assert label([b + check[(int(b) + 1) % 31] for b in bases]) != ("direct_identifier", "NATIONAL_ID")


def test_address_with_postcode_and_city_repeats():
    addrs = [f"Koivutie {i % 7 + 1} A {i % 3 + 1}, 2{i % 2}100 Turku" for i in range(N)]
    assert label(addrs) == ("direct_identifier", "STREET_ADDRESS")


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


def test_sequential_prefixed_id_is_record_key_even_when_not_first(tmp_path):
    pd.DataFrame({"a": [f"{40000000 + i * 7919 % 9999991}" for i in range(N)],
                  "b": [f"SR-2024-{i + 1:06d}" for i in range(N)]}).to_csv(tmp_path / "t.csv", index=False)
    lab = detect_dataset(tmp_path, "synthetic").set_index("column")
    assert lab.at["b", "privacy_role"] == "record_key"
    assert lab.at["a", "privacy_role"] == "technical_identifier"


def test_repeating_short_prefix_number_is_employee_id(tmp_path):
    ids = [f"KC-{1000 + i % 300}" for i in range(1200)]
    pd.DataFrame({"emp": ids}).to_csv(tmp_path / "t.csv", index=False)
    lab = detect_dataset(tmp_path, "synthetic").set_index("column")
    assert tuple(lab.loc["emp", ["privacy_role", "subtype"]]) == ("direct_identifier", "EMPLOYEE_ID")


def test_hash_paired_one_to_one_with_person_id_is_technical(tmp_path):
    import hashlib
    ids = [f"KC-{1000 + i % 300}" for i in range(1200)]
    pd.DataFrame({"emp": ids, "h": [hashlib.sha256(x.encode()).hexdigest() for x in ids],
                  "f": [hashlib.sha256(str(i).encode()).hexdigest() for i in range(1200)]}
                 ).to_csv(tmp_path / "t.csv", index=False)
    lab = detect_dataset(tmp_path, "synthetic").set_index("column")
    assert lab.at["h", "privacy_role"] == "technical_identifier"
    # a hash with no person id behind it stays non_sensitive
    assert lab.at["f", "privacy_role"] == "non_sensitive"


def test_code_blank_where_amount_is_zero_is_sensitive(tmp_path):
    code = ["", "AY-A", "AY-B", "AY-C"]
    pd.DataFrame({"emp": [f"KC-{1000 + i % 300}" for i in range(1200)],
                  "union": [code[i % 4] for i in range(1200)],
                  "fee": ["0.00" if i % 4 == 0 else f"{20 + i % 30}.{i % 100:02d}" for i in range(1200)]}
                 ).to_csv(tmp_path / "t.csv", index=False)
    lab = detect_dataset(tmp_path, "synthetic").set_index("column")
    assert lab.at["union", "privacy_role"] == "sensitive_attribute"
    assert tuple(lab.loc["fee", ["privacy_role", "subtype"]]) == ("sensitive_attribute", "FINANCIAL_DATA")


def test_monthly_pay_is_sensitive_financial():
    assert label([f"{2 + i % 3} {i * 7 % 1000:03d},{i % 100:02d}" for i in range(N)]) == ("sensitive_attribute",
                                                                                         "FINANCIAL_DATA")
    # small purchase amounts stay quasi-identifiers
    assert label([f"{1 + i * 0.37:.2f}" for i in range(N)]) == ("quasi_identifier", "FINANCIAL_DATA")


def test_finnish_care_titles_are_occupation():
    assert label(["lähihoitaja", "sairaanhoitaja", "osastonhoitaja", "erikoislääkäri"]) == ("quasi_identifier",
                                                                                              "OCCUPATION")


def test_eight_digit_code_starting_with_zero_is_not_phone():
    assert label([f"0{i * 7919 % 10000000:07d}" for i in range(N)])[1] != "PHONE"
    assert label([f"040{i * 7919 % 10000000:07d}" for i in range(N)]) == ("direct_identifier", "PHONE")


def test_hetu_with_text_prefix():
    check = "0123456789ABCDEFHJKLMNPRSTUVWXY"
    bases = [(f"{d:02d}{m:02d}{y:02d}", f"{i:03d}") for d, m, y, i in
             zip(range(1, 29), [1 + k % 12 for k in range(28)], range(50, 78), range(2, 900, 31))]
    hetus = [f"{b}-{n}{check[int(b + n) % 31]}" for b, n in bases]
    assert label([("HETU " if k % 3 else "") + h for k, h in enumerate(hetus)]) == ("direct_identifier", "NATIONAL_ID")


def test_long_prefixed_number_does_not_crash(tmp_path):
    pd.DataFrame({"id": [f"TXN{10**21 + i}" for i in range(300)]}).to_csv(tmp_path / "t.csv", index=False)
    assert len(detect_dataset(tmp_path, "synthetic")) == 1


def test_code_blank_where_amount_is_never_zero_is_not_paired(tmp_path):
    pd.DataFrame({"emp": [f"KC-{1000 + i % 300}" for i in range(1200)],
                  "union": ["" if i % 20 == 0 else "ABC"[i % 3] for i in range(1200)],
                  "fee": [f"{20 + i % 30}.{i % 100:02d}" for i in range(1200)]}
                 ).to_csv(tmp_path / "t.csv", index=False)
    lab = detect_dataset(tmp_path, "synthetic").set_index("column")
    assert lab.at["union", "privacy_role"] != "sensitive_attribute"
