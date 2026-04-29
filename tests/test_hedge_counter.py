from hedge_counter import count_hedges


def test_count_hedges_total_rate_matches_raw_count():
    text = "I think this might be approximately right, but I could be wrong."
    result = count_hedges(text)

    total_raw = result["total"]["raw"]
    word_count = result["word_count"]
    expected_rate = round((total_raw / word_count) * 100, 3)

    assert result["total"]["per_100_words"] == expected_rate


def test_count_hedges_empty_text_returns_empty_dict():
    assert count_hedges("") == {}
