"""Masking under the corpus terms (spikes 2 and 12): secrets, emails and mentions.

Also drops NUL characters, which Postgres text cannot store.

Applied to the title, the body and every comment body before a record is written.
Order matters: secrets first (a PEM block may hold anything), then emails,
then mentions, so `user@example.com` is masked as an email and never as a mention.
"""

import re

EMAIL_MARKER = "[email masked]"
SECRET_MARKER = "[secret masked]"
USER_MARKER = "@[user]"
JIRA_USER_MARKER = "[~user]"

_PEM_BLOCK = re.compile(
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"
    # Up to the matching END line, or, for a truncated block, to a blank line or the end.
    r"(?:.*?-----END [A-Z0-9 ]*PRIVATE KEY-----|.*?(?=\n[ \t]*\n|\Z))",
    re.DOTALL,
)
_SECRETS = re.compile(
    "|".join(
        (
            r"\bgh[a-z]_[A-Za-z0-9]{20,}",  # GitHub tokens: ghp_, gho_, ghu_, ghs_, ghr_
            r"\bgithub_pat_[A-Za-z0-9_]{20,}",  # GitHub fine-grained tokens
            r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",  # AWS access key ids
            r"\bxox[a-z]-[A-Za-z0-9-]{10,}",  # Slack tokens
            r"\bAIza[0-9A-Za-z_-]{35}",  # Google API keys
        )
    )
)
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b")
# `@handle`, not `@org/team`, not an email, not `path/@x` or `a.@x`.
_MENTION = re.compile(r"(?<![\w/.@])@([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))(?![\w/-])")
# Jira user mentions: `[~username]` and `[~accountid:5b10ac8d82e05b22cc7d4ef5]`.
_JIRA_MENTION = re.compile(r"\[~(?:accountid:)?[^\]\n]+\]")


def mask(text: str) -> str:
    """Drop NUL characters, then replace secrets, emails and @handle mentions with markers.

    NUL (U+0000) is valid in JSON but not in a Postgres text column, so a snapshot holding
    one cannot be loaded. It goes first, so it can never split a secret and hide it.
    """
    text = text.replace("\x00", "")
    text = _PEM_BLOCK.sub(SECRET_MARKER, text)
    text = _SECRETS.sub(SECRET_MARKER, text)
    text = _EMAIL.sub(EMAIL_MARKER, text)
    return _MENTION.sub(USER_MARKER, text)


def mask_jira(text: str) -> str:
    """Every Jira `[~user]` / `[~accountid:…]` mention becomes `[~user]`, then `mask`.

    Mentions go first, so one holding an email still becomes exactly `[~user]`.
    """
    return mask(_JIRA_MENTION.sub(JIRA_USER_MARKER, text))
