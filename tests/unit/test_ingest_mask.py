import pytest

from ticketscope.jobs.ingest.mask import EMAIL_MARKER, SECRET_MARKER, USER_MARKER, mask


@pytest.mark.parametrize(
    "secret",
    [
        "ghp_" + "a" * 36,
        "gho_" + "B1" * 18,
        "ghs_" + "c2" * 18,
        "github_pat_" + "11AAAA_" + "b" * 40,
        "AKIA" + "ABCDEFGHIJKLMNOP",
        "ASIA" + "ABCDEFGHIJKLMNOP",
        "xoxb-" + "1234567890-abcdef",
        "xoxp-" + "1234567890-abcdef",
        "AIza" + "x" * 35,
    ],
)
def test_token_shaped_secrets_are_masked(secret: str) -> None:
    assert mask(f"before {secret} after") == f"before {SECRET_MARKER} after"


def test_pem_private_key_block_is_masked_whole() -> None:
    text = (
        "key:\n-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnNzaC1rZXktdjEAAAAA\n"
        "-----END OPENSSH PRIVATE KEY-----\ndone"
    )
    assert mask(text) == f"key:\n{SECRET_MARKER}\ndone"


def test_truncated_pem_block_is_masked_to_the_blank_line() -> None:
    text = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASC\n\nnext paragraph"
    assert mask(text) == f"{SECRET_MARKER}\n\nnext paragraph"


def test_public_key_and_certificate_blocks_are_kept() -> None:
    text = "-----BEGIN CERTIFICATE-----\nMIIB\n-----END CERTIFICATE-----"
    assert mask(text) == text


@pytest.mark.parametrize(
    "email", ["jane.doe@example.com", "ops+k8s@corp.example.org", "a_b@sub.domain.io"]
)
def test_emails_are_masked(email: str) -> None:
    assert mask(f"mail {email}.") == f"mail {EMAIL_MARKER}."


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("@alice please look", f"{USER_MARKER} please look"),
        ("/assign @bob-smith", f"/assign {USER_MARKER}"),
        ("@k8s-ci-robot: thanks", f"{USER_MARKER}: thanks"),
        ("(@carol)", f"({USER_MARKER})"),
        ("cc @kubernetes/sig-node-bugs", "cc @kubernetes/sig-node-bugs"),
        ("github.com/org/repo/@main", "github.com/org/repo/@main"),
        ("image@sha256:abc", "image@sha256:abc"),
        ("k8s.io/api@v0.31.0", "k8s.io/api@v0.31.0"),
    ],
)
def test_handles_are_masked_and_teams_kept(text: str, expected: str) -> None:
    assert mask(text) == expected


def test_email_is_not_mistaken_for_a_mention() -> None:
    assert mask("dev@example.com") == EMAIL_MARKER


def test_mask_is_idempotent() -> None:
    once = mask("@alice ghp_" + "a" * 36 + " x@example.com")
    assert mask(once) == once


def test_plain_text_is_unchanged() -> None:
    text = "kubectl get pods -A\n```\nE1104 10:00:00 kubelet.go:1] boom\n```"
    assert mask(text) == text
