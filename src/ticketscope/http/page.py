"""The search page (epic R4): server-rendered HTML with no JavaScript and no external assets.

Pure functions from the `/v1` contract models to `str`, so the page and `POST /v1/search`
share one result shape (AD-4). Every echoed value is escaped.
"""

from html import escape

from ticketscope.contract.search import SearchResult

BLANK_MESSAGE = "Paste the text of a ticket to find similar issues and how each one ended."
NO_MATCH_MESSAGE = "No matching issues."
NOT_LOADED_MESSAGE = "The corpus is not loaded yet. Try again in a few minutes."
ERROR_MESSAGE = "Something went wrong while searching. Try again later."

_KIND_LABELS = {"short": "short", "log_heavy": "log-heavy"}

# README.md's attribution line, verbatim (corpus terms condition 1).
_ATTRIBUTION = (
    "Issue text from the Mojang bug tracker (bugs.mojang.com), as collected in The Public"
    " Jira Dataset v7 by Lloyd Montgomery, Clara Lüders and Walid Maalej (Zenodo, "
    'doi:10.5281/zenodo.15719919, CC BY 4.0), described in "An Alternative Issue Tracking'
    ' Dataset of Public Jira Repositories", MSR 2022, pp. 73\u201377. The text belongs to its '
    "authors; each record links to its source issue. Data collected in January 2022; "
    "changes to source issues after that date are not reflected."
)

_STYLE = """
body { font-family: system-ui, sans-serif; max-width: 52rem; margin: 0 auto;
  padding: 1rem; color: #1a1a1a; background: #fff; line-height: 1.45; }
h1 { font-size: 1.4rem; margin: 0 0 1rem; }
textarea { width: 100%; box-sizing: border-box; min-height: 10rem;
  font-family: ui-monospace, monospace; font-size: 0.9rem; }
button { margin-top: 0.5rem; padding: 0.4rem 1rem; font-size: 1rem; }
ol.results { padding-left: 1.5rem; }
li.result { margin: 0 0 1rem; }
li.result .title { font-weight: 600; }
.kind, .outcome { display: inline-block; font-size: 0.8rem; padding: 0 0.4rem;
  border-radius: 0.25rem; margin-right: 0.3rem; background: #eee; }
.outcome { background: #e3eefc; }
.summary { margin: 0.2rem 0 0; color: #444; }
.message { padding: 0.6rem 0.8rem; background: #f4f4f4; border-radius: 0.25rem; }
.message.error { background: #fde8e8; color: #7a1212; }
footer { margin-top: 2rem; font-size: 0.75rem; color: #666; }
"""


def _esc(value: object) -> str:
    return escape(str(value), quote=True)


def _safe_url(url: str | None) -> str | None:
    """`url` if it may go in an `href` (http or https only), else None."""
    if url and url.startswith(("https://", "http://")):
        return url
    return None


def _link(url: str | None, text: str, css: str) -> str:
    href = _safe_url(url)
    if href is None:
        return f'<span class="{css}">{_esc(text)}</span>'
    return f'<a class="{css}" href="{_esc(href)}">{_esc(text)}</a>'


def _row(result: SearchResult) -> str:
    issue = result.issue
    outcome = result.outcome
    parts = [
        f'<li class="result" data-rank="{_esc(result.rank)}"'
        f' data-outcome="{_esc(outcome.status)}">',
        _link(issue.url, issue.title, "title"),
        "<div>",
        f'<span class="kind">{_esc(_KIND_LABELS.get(issue.kind, issue.kind))}</span>',
        f'<span class="outcome">{_esc(outcome.status)}</span>',
    ]
    if outcome.ref:
        parts.append(_link(outcome.ref, outcome.ref, "ref"))
    parts.append("</div>")
    if outcome.summary is not None:
        parts.append(f'<p class="summary">{_esc(outcome.summary)}</p>')
    parts.append("</li>")
    return "".join(parts)


def render(
    query: str,
    results: list[SearchResult] | None = None,
    message: str | None = None,
    *,
    error: bool = False,
) -> str:
    """The whole page: the form with `query` echoed, then `results` or `message`."""
    body: list[str] = []
    if message is not None:
        css = "message error" if error else "message"
        role = "alert" if error else "status"
        body.append(f'<p class="{css}" role="{role}">{_esc(message)}</p>')
    if results:
        rows = "".join(_row(r) for r in results)
        body.append(f'<ol class="results">{rows}</ol>')
    return (
        "<!doctype html>"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>ticketscope</title><style>{_STYLE}</style></head><body>"
        "<h1>ticketscope</h1>"
        '<form method="post" action="/">'
        '<label for="q">Ticket text</label>'
        # HTML drops one newline right after <textarea>: emit it so the query echoes exactly.
        f'<textarea id="q" name="q" rows="10">\n{_esc(query)}</textarea>'
        '<button type="submit">Search</button>'
        "</form>"
        f"<main>{''.join(body)}</main>"
        f"<footer>{_esc(_ATTRIBUTION)}</footer>"
        "</body></html>"
    )
