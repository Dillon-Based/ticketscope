import io

import pytest

from ticketscope.jobs.ingest.version import main, next_version


def test_version_taken_gives_the_next_n() -> None:
    tags = ["snapshot-2026.11.1", "snapshot-2026.11.2", "snapshot-2026.10.7", "v1.0"]
    assert next_version(tags, "2026.11") == "2026.11.3"


def test_first_of_a_month_is_1() -> None:
    assert next_version(["snapshot-2026.10.4"], "2026.11") == "2026.11.1"
    assert next_version([], "2026.11") == "2026.11.1"


def test_n_is_numeric_and_never_reuses_a_gap() -> None:
    # .1 was taken down; its number is still never chosen again.
    tags = ["snapshot-2026.11.2", "snapshot-2026.11.10", "snapshot-2026.11.9"]
    assert next_version(tags, "2026.11") == "2026.11.11"


def test_git_refs_are_accepted() -> None:
    assert next_version(["refs/tags/snapshot-2026.11.1"], "2026.11") == "2026.11.2"


@pytest.mark.parametrize("month", ["2026.13", "2026-11", "26.11", ""])
def test_bad_month_is_refused(month: str) -> None:
    with pytest.raises(ValueError, match=r"YYYY\.MM"):
        next_version([], month)


def test_cli_reads_tags_from_stdin(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "sys.stdin", io.StringIO("snapshot-2026.11.1\nrefs/tags/snapshot-2026.11.2\n")
    )
    assert main(["--month", "2026.11"]) == 0
    assert capsys.readouterr().out == "2026.11.3\n"
