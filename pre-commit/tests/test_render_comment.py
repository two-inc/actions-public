from pre_commit_action.render_comment import MAX_OUTPUT_BYTES, middle_truncate, render_comment


def test_success_shows_trophy(tmp_path):
    out = tmp_path / "output.txt"
    out.write_text("All hooks passed.")
    result = render_comment(str(out), "0", "success", "main", "alice")
    assert "🏆" in result
    assert "@alice" in result
    assert "All hooks passed." in result


def test_failure_shows_stop_sign_and_hint(tmp_path):
    out = tmp_path / "output.txt"
    out.write_text("Hook failed.")
    result = render_comment(str(out), "1", "failure", "main", "bob")
    assert "🚫" in result
    assert "pre-commit run --from-ref origin/main" in result
    assert "@bob" in result


def test_success_has_no_hint(tmp_path):
    out = tmp_path / "output.txt"
    out.write_text("ok")
    result = render_comment(str(out), "0", "success", "main", "carol")
    assert "pre-commit install" not in result


def test_exit_code_in_comment(tmp_path):
    out = tmp_path / "output.txt"
    out.write_text("done")
    result = render_comment(str(out), "42", "failure", "main", "x")
    assert "Exit code: 42" in result


def test_missing_output_file(tmp_path):
    result = render_comment(str(tmp_path / "nonexistent.txt"), "1", "failure", "main", "x")
    assert "failed to read" in result


def test_middle_truncate_short_passthrough():
    text = "hello world"
    assert middle_truncate(text) == text


def test_middle_truncate_long_string():
    big = "x" * (MAX_OUTPUT_BYTES + 2000)
    result = middle_truncate(big)
    assert "truncated" in result
    assert len(result.encode("utf-8")) < MAX_OUTPUT_BYTES + 500


def test_middle_truncate_preserves_head_and_tail():
    head = "START" + "a" * (MAX_OUTPUT_BYTES // 2)
    tail = "b" * (MAX_OUTPUT_BYTES // 2) + "END"
    big = head + tail
    result = middle_truncate(big)
    assert result.startswith("START")
    assert result.endswith("END")
