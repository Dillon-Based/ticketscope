"""scripts/run_summary.py keeps what an env run did and drops the noise. The log lines below copy
the shapes of a real env-down log (`gh run view --log`: job, step, timestamp), with a fake
account id."""

from scripts.run_summary import summarise

ACCT = "000000000000"


def _line(text: str, step: str = "Tear down", ts: str = "2026-11-19T17:40:16.1512123Z") -> str:
    return f"teardown\t{step}\t﻿{ts} {text}\n"


LOG = [
    _line("##[group]Run set -o pipefail"),
    _line("\x1b[36;1mscripts/eks-teardown.sh --kubeconfig x 2>&1 | tee log\x1b[0m"),
    _line("  TF_VAR_account_id: ***"),
    _line(f"  AWS_ROLE: arn:aws:iam::{ACCT}:role/x"),
    _line("[17:40:16 +  40s] stage: controller-config-objects"),
    _line("gatewayclass alb is gone"),
    _line(
        '\x1b[0m\x1b[1mmodule.eks.aws_eks_addon.this["coredns"]: Refreshing state... [id=x]\x1b[0m'
    ),
    _line("\x1b[0m\x1b[1mDestroy complete! Resources: 52 destroyed.\x1b[0m"),
    _line("eks-teardown: the zone still holds records for ticketscope.example.dev:"),
    _line("ticketscope.example.dev.\tAAAA"),
    _line("--- eks-teardown stage times ---"),
    _line("gateway-and-alb                 25s"),
    _line("total                          697s"),
    _line("some unrelated chatter"),
    _line(
        f"User: arn:aws:sts::{ACCT}:assumed-role/d is not authorized to perform: tag:GetResources"
    ),
    _line("##[error]Process completed with exit code 3."),
]


def test_it_keeps_stages_verdicts_tables_and_errors_and_drops_the_noise() -> None:
    out = list(summarise(LOG))
    text = "\n".join(out)
    for kept in (
        "stage: controller-config-objects",
        "gatewayclass alb is gone",
        "Destroy complete! Resources: 52 destroyed.",
        "still holds records",
        "ticketscope.example.dev.\tAAAA",
        "--- eks-teardown stage times ---",
        "gateway-and-alb                 25s",
        "total                          697s",
        "not authorized to perform: tag:GetResources",
        "exit code 3",
    ):
        assert kept in text, kept
    for dropped in (
        "eks-teardown.sh --kubeconfig",
        "TF_VAR_account_id",
        "Refreshing state",
        "chatter",
    ):
        assert dropped not in text, dropped
    assert "\x1b[" not in text


def test_each_line_names_job_step_and_clock_and_hides_account_ids() -> None:
    out = list(summarise(LOG))
    assert out[0].startswith("teardown | Tear down | 17:40:16 | ")
    assert ACCT not in "\n".join(out)
    assert any("<acct>" in line for line in out)


def test_lines_without_the_log_shape_are_skipped() -> None:
    assert list(summarise(["not a log line\n", "\n"])) == []
