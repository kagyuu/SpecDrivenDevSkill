from app.validation.reservation import is_capacity_ok, is_time_range_valid, overlaps


def test_overlaps_true_when_partially_overlapping():
    assert overlaps("10:30", "11:30", "10:00", "11:00") is True


def test_overlaps_true_when_new_contains_existing():
    assert overlaps("09:00", "12:00", "10:00", "11:00") is True


def test_overlaps_false_when_back_to_back_new_starts_at_existing_end():
    # docs/P003-backend-spec.md §5.9: 11:00-12:00 は既存10:00-11:00と重複しない。
    assert overlaps("11:00", "12:00", "10:00", "11:00") is False


def test_overlaps_false_when_back_to_back_new_ends_at_existing_start():
    # docs/P003-backend-spec.md §5.9: 09:00-10:00 は既存10:00-11:00と重複しない。
    assert overlaps("09:00", "10:00", "10:00", "11:00") is False


def test_is_time_range_valid_rejects_equal_times():
    assert is_time_range_valid("10:00", "10:00") is False


def test_is_time_range_valid_accepts_end_after_start():
    assert is_time_range_valid("10:00", "10:01") is True


def test_is_capacity_ok_equal_to_capacity_is_allowed():
    assert is_capacity_ok(10, 10) is True


def test_is_capacity_ok_over_capacity_rejected():
    assert is_capacity_ok(11, 10) is False


def test_is_capacity_ok_none_always_allowed():
    assert is_capacity_ok(None, 1) is True
