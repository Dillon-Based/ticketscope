"""The by-key lookup through real SQL, as the read-only role, and agreeing with the fake
(test design: "The by-key lookup works through the Postgres adapter and agrees with the fake")."""

from dataclasses import replace

import pytest

from tests import key_oracle as oracle
from tests.postgres.test_dense_postgres import META, _row
from ticketscope.adapters.postgres import PostgresCorpusStore, replace_corpus
from ticketscope.core.fakes import InMemoryCorpusStore
from ticketscope.core.model import IssueRecord

URLS = {
    1: "https://bugs.mojang.com/browse/MCL-6629",
    2: "https://bugs.mojang.com/browse/REALMS-12",
    3: "https://github.com/o/r/issues/7",
}
BODIES = {1: "body one", 2: None, 3: "body three"}


@pytest.fixture
def stores(pg_conninfo: str) -> tuple[PostgresCorpusStore, InMemoryCorpusStore]:
    rows = [replace(_row(n), url=URLS[n], body=BODIES[n]) for n in URLS]
    replace_corpus(pg_conninfo, META, rows)
    # The role the api connects as; the superuser's session is switched to it.
    read_only = PostgresCorpusStore(f"{pg_conninfo} options='-c role=ticketscope_ro'")
    fake = InMemoryCorpusStore(
        [
            (
                IssueRecord(
                    number=n,
                    title=f"t{n}",
                    url=URLS[n],
                    kind="short",
                    state="closed",
                    outcome_status="fixed",
                ),
                f"t{n}",
            )
            for n in URLS
        ],
        corpus_version="snap",
        bodies=BODIES,
    )
    return read_only, fake


def test_a_loaded_key_returns_its_issue_and_body(
    stores: tuple[PostgresCorpusStore, InMemoryCorpusStore],
) -> None:
    store, _fake = stores
    found = store.get_issue_by_key("MCL-6629")
    assert found is not None
    assert (found.issue.number, found.issue.url, found.body) == (1, URLS[1], "body one")


@pytest.mark.parametrize("key", ["MCL-1", *oracle.HOSTILE_KEYS, "MCL-1' OR '1'='1"])
def test_an_unknown_or_sql_shaped_key_returns_none(
    stores: tuple[PostgresCorpusStore, InMemoryCorpusStore], key: str
) -> None:
    store, _fake = stores
    assert store.get_issue_by_key(key) is None


@pytest.mark.parametrize("key", ["MCL-6629", "REALMS-12", "MCL-1", "mcl-6629", "%", "MCL-6629 "])
def test_the_adapter_and_the_fake_agree(
    stores: tuple[PostgresCorpusStore, InMemoryCorpusStore], key: str
) -> None:
    store, fake = stores
    assert store.get_issue_by_key(key) == fake.get_issue_by_key(key)
