"""Reads a locally restored The Public Jira Dataset v7 dump (AD-6). The only pymongo user.

The dump is restored with `mongorestore` into a MongoDB on the person's machine
(database `JiraReposAnon`, one collection per instance). Documents come back sorted by
`_id`, so when the dump holds an issue key twice, the first by `_id` comes first.

The projection reads only what a schema v2 record needs. Reporter and comment-author ids
are read solely to compute each comment's `from_reporter` flag; assignee and creator are
never read.
"""

from collections.abc import Iterable, Iterator, Mapping
from typing import Any, Protocol

from pymongo import MongoClient

PROJECTION: Mapping[str, int] = {
    "_id": 1,
    "id": 1,
    "key": 1,
    "fields.summary": 1,
    "fields.description": 1,
    "fields.resolution.name": 1,
    "fields.resolutiondate": 1,
    "fields.created": 1,
    "fields.issuetype.name": 1,
    "fields.project.key": 1,
    "fields.reporter.key": 1,
    "fields.reporter.name": 1,
    "fields.reporter.accountId": 1,
    "fields.issuelinks.type": 1,
    "fields.issuelinks.outwardIssue.id": 1,
    "fields.issuelinks.outwardIssue.key": 1,
    "fields.issuelinks.inwardIssue.id": 1,
    "fields.issuelinks.inwardIssue.key": 1,
    "fields.comments.body": 1,
    "fields.comments.created": 1,
    "fields.comments.author.key": 1,
    "fields.comments.author.name": 1,
    "fields.comments.author.accountId": 1,
    "fields.comment.comments.body": 1,
    "fields.comment.comments.created": 1,
    "fields.comment.comments.author.key": 1,
    "fields.comment.comments.author.name": 1,
    "fields.comment.comments.author.accountId": 1,
}


class Cursor(Protocol):
    def sort(self, key: str, direction: int) -> Cursor: ...

    def __iter__(self) -> Iterator[dict[str, Any]]: ...

    def close(self) -> None: ...


class Collection(Protocol):
    def find(
        self, filter: Mapping[str, Any], projection: Mapping[str, Any], *, no_cursor_timeout: bool
    ) -> Cursor: ...


def read_issues(collection: Collection, projects: Iterable[str]) -> Iterator[dict[str, Any]]:
    """The documents of `projects`, in `_id` order."""
    query = {"fields.project.key": {"$in": sorted(projects)}}
    cursor = collection.find(query, PROJECTION, no_cursor_timeout=True).sort("_id", 1)
    try:
        yield from cursor
    finally:
        cursor.close()


def open_issues(
    uri: str, database: str, instance: str, projects: Iterable[str]
) -> Iterator[dict[str, Any]]:
    """`read_issues` over `<database>.<instance>` at `uri`."""
    client: MongoClient[dict[str, Any]] = MongoClient(uri)
    try:
        collection: Any = client[database][instance]
        yield from read_issues(collection, projects)
    finally:
        client.close()
