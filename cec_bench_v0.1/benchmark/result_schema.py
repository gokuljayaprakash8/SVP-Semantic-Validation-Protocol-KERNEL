REQUIRED_RESULT_FIELDS = [
    "case_id",
    "oracle_result",
    "baseline_result",
    "agreement",
    "oracle_violation",
    "baseline_missed_violation"
]


def validate_result(result):
    missing = [
        field
        for field in REQUIRED_RESULT_FIELDS
        if field not in result
    ]

    if missing:
        raise ValueError(
            f"Missing benchmark result fields: {missing}"
        )

    if result["oracle_result"] not in {
        "VIOLATION",
        "CONTAINED"
    }:
        raise ValueError("Invalid oracle result")

    if result["baseline_result"] not in {
        "VIOLATION",
        "CONTAINED"
    }:
        raise ValueError("Invalid baseline result")

    expected_agreement = (
        result["oracle_result"] == result["baseline_result"]
    )

    if result["agreement"] != expected_agreement:
        raise ValueError("Agreement field is inconsistent")

    expected_miss = (
        result["oracle_result"] == "VIOLATION"
        and result["baseline_result"] == "CONTAINED"
    )

    if result["baseline_missed_violation"] != expected_miss:
        raise ValueError(
            "Baseline-missed-violation field is inconsistent"
        )

    return True
