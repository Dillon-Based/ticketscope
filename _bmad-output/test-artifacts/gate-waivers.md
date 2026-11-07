# Gate waivers

bmad-tea-trace validates each entry against `checklist.md` "Waiver Scenarios" (fail_only, business_justification, approver_authority, expiry_present, remediation_due_date, not_security, contract_complete) and reports it. A valid waiver never changes the derived gate; the approver applies WAIVED on top of it.

## W-001: Retired GitHub-era criteria of stories 1.3, 1.4 and 1.14

**Covers**: `ticketscope--e1-s3--AC-1` (P0), `ticketscope--e1-s3--AC-2` (P1), `ticketscope--e1-s3--AC-3` (P1), `ticketscope--e1-s4--AC-1` (P1), `ticketscope--e1-s4--AC-2` (P1), `ticketscope--e1-s14--AC-2` (P1)

**Original Decision**: ❌ FAIL

**Reason for Failure**:

- These six criteria describe the GitHub ingest path (recordings, github.com URLs, `snapshot.yml`) and story 4's GitHub outcome rules. Spike 12 switched the corpus to The Public Jira Dataset v7 (epic Notes, Decision 2026-11-06), story 13 replaced the ingest, story 14 replaced the derivation, and the refactor sweep (1.10) removed the GitHub code. No current test can establish them; the stories are `done` and their criteria are frozen, so they cannot be rewritten (PO replan rule: nothing already built is rewritten).

**Waiver Information**:

- **Waiver Reason**: The criteria are superseded, not failing. Their intent is carried by story 13 AC-1..4 (schema-v2 ingest, checksum, drift, publish) and story 14 AC-1/AC-3 (Jira outcome and kind rules), which the trace maps separately.
- **Waiver Approver**: Dillon, Product Owner
- **Approval Date**: 2026-11-07
- **Waiver Expiry**: 2027-11-07 (**NOTE**: Does NOT apply to next release)

**Monitoring Plan**:

- Story 13 and 14 criteria stay in the gate; any regression there fails it independently.
- The integrated check (story 11) validates the loaded snapshot against schema v2 on every PR.
- Escalate if any code path reintroduces GitHub ingest or GitHub outcome rules.

**Remediation Plan**:

- **Fix Target**: epic-eval-gate (epic 2): the ticket tree records these six criteria as superseded, with a TEA/PO change so trace honors it
- **Due Date**: 2027-11-07
- **Owner**: Dillon
- **Verification**: A fresh bmad-tea-trace run no longer selects these six criteria, or selects them with a superseded disposition the workflow honors.

**Business Justification**:
The epic deliberately replaced its corpus source after spike 12 showed the GitHub corpus had too little duplicate ground truth for epic-eval-gate. Holding the epic gate on behavior that was intentionally removed blocks release without reducing risk; the replacement behavior is covered by its own criteria.
