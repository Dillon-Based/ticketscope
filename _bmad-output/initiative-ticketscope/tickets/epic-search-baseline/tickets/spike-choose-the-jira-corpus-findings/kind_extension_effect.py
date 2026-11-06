"""How much the {code}/{noformat} extension changes log-heavy counts, per project."""

import sys

sys.path.insert(0, sys.argv[1])  # findings dir

from measure import extended_kind, is_duplicate_resolution, iter_issues

from ticketscope.core.derive import DEFAULT_KIND_THRESHOLD, kind_score

instance, project = sys.argv[2], sys.argv[3]
seen = set()
raw_all = ext_all = raw_dup = ext_dup = 0
for issue in iter_issues(instance, {"fields.project.key": project}):
    if issue["key"] in seen or (issue.get("fields") or {}).get("resolution") is None:
        continue
    seen.add(issue["key"])
    body = issue["fields"].get("description")
    raw = kind_score(body) >= DEFAULT_KIND_THRESHOLD
    ext = extended_kind(body) == "log_heavy"
    raw_all += raw
    ext_all += ext
    if is_duplicate_resolution(issue):
        raw_dup += raw
        ext_dup += ext
print(
    f"{instance} {project}: resolved log-heavy raw={raw_all} ext={ext_all}; "
    f"duplicate-resolved log-heavy raw={raw_dup} ext={ext_dup}"
)
