"""Do fixed tickets point, by keyword alone, at the Java files their fix version changed?

For each <old>:<new> version pair: the corpus is the Java files of <old> (the code as it
was when the bug existed); a file is relevant when it was modified or removed in <new>;
the queries are the MC issues whose single fix version is <new>.

usage: keyword_check.py <mc_fixed.jsonl> <mc root> <old>:<new>...
"""

import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


def _words(text: str) -> frozenset[str]:
    return frozenset(text.split())


JAVA_WORDS = _words(
    "abstract boolean break byte case catch char class const continue default double else enum "
    "extends final finally float for goto implements import instanceof int interface long native "
    "new null package private protected public return short static super switch synchronized this "
    "throw throws transient true false try void volatile while var string object override list "
    "java util net minecraft com mojang get set"
)
STOP = _words(
    "the and that this with for are was not but you have has had from when what which will would "
    "can could should there their they them then than into out about after before also any all "
    "its it's does did doing being been were your our more most some such only very just over "
    "under again once here why how where who whom both each few other same too use used using "
    "see steps reproduce expected observed result results actual bug issue game minecraft"
)
WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+")
HUMP = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+")


def tokens(text: str) -> list[str]:
    out = []
    for word in WORD.findall(text):
        for part in HUMP.findall(word):
            t = part.lower()
            if len(t) > 3 and t.endswith("s"):
                t = t[:-1]
            if len(t) >= 3 and t not in JAVA_WORDS and t not in STOP:
                out.append(t)
    return out


def manifest_id(name: str) -> str:
    n = re.sub(r"^Minecraft\s+", "", name.strip(), flags=re.IGNORECASE)
    m = re.match(r"^(\S+)\s+Pre-?release\s*(\d+)$", n, flags=re.IGNORECASE)
    if m:
        return f"{m.group(1)}-pre{m.group(2)}"
    m = re.match(r"^(\S+)\s+Release Candidate\s*(\d+)$", n, flags=re.IGNORECASE)
    return f"{m.group(1)}-rc{m.group(2)}" if m else n


class Bm25:
    def __init__(self, docs: dict[str, list[str]], k1: float = 1.2, b: float = 0.75):
        self.ids = list(docs)
        self.len = [len(docs[i]) for i in self.ids]
        self.avg = sum(self.len) / len(self.len)
        self.post: dict[str, list[tuple[int, int]]] = defaultdict(list)
        for n, i in enumerate(self.ids):
            for term, tf in Counter(docs[i]).items():
                self.post[term].append((n, tf))
        self.k1, self.b = k1, b

    def rank(self, query: list[str]) -> list[tuple[float, str]]:
        scores: dict[int, float] = defaultdict(float)
        total = len(self.ids)
        for term in set(query):
            post = self.post.get(term)
            if not post:
                continue
            idf = math.log(1 + (total - len(post) + 0.5) / (len(post) + 0.5))
            for n, tf in post:
                norm = tf + self.k1 * (1 - self.b + self.b * self.len[n] / self.avg)
                scores[n] += idf * tf * (self.k1 + 1) / norm
        return sorted(((s, self.ids[n]) for n, s in scores.items()), reverse=True)


def main() -> None:
    issues = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines()]
    root = Path(sys.argv[2])
    by_fix: dict[str, list[dict]] = defaultdict(list)
    for issue in issues:
        by_fix[manifest_id(issue["fix"]).lower()].append(issue)
    tot: Counter[str] = Counter()
    for pair in sys.argv[3:]:
        old, new, *rest = pair.split(":")
        queries_from = rest[0] if rest else new  # a third field scores another version's issues
        src = root / old / "src"
        diff = json.loads((root / f"diff-{old}-{new}.json").read_text())
        relevant = {k for k, v in diff.items() if k.endswith(".java") and "added_file" not in v}
        docs, stems = {}, {}
        for path in src.rglob("*.java"):
            rel = str(path.relative_to(src))
            name = tokens(path.stem)
            docs[rel] = tokens(path.read_text(errors="replace")) + name * 10
            stems[path.stem] = rel
        index = Bm25(docs)
        n_docs, n_rel = len(docs), len(relevant)
        base = n_rel / n_docs
        row: Counter[str] = Counter()
        for issue in by_fix.get(queries_from.lower(), []):
            text = issue["summary"] + "\n" + issue["description"]
            row["issues"] += 1
            # A: exact class names written in the ticket (two humps or more, or a stack frame)
            named = {
                stems[w]
                for w in set(re.findall(r"\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+\b", text))
                if w in stems
            }
            if named:
                row["names_a_class"] += 1
                row["named_class_changed"] += bool(named & relevant)
            if re.search(r"\bat (?:net\.minecraft|com\.mojang)\.", text):
                row["has_stack_frame"] += 1
            # B: BM25 ranking of all files against the ticket text
            ranked = [rel for _, rel in index.rank(tokens(text))]
            for k in (1, 5, 10):
                row[f"hits@{k}"] += sum(1 for rel in ranked[:k] if rel in relevant)
            row["any@10"] += any(rel in relevant for rel in ranked[:10])
            # AUC: chance a changed file outranks an unchanged one; unranked files tie last
            pos = {rel: i for i, rel in enumerate(ranked)}
            tail = (len(ranked) + n_docs - 1) / 2
            rel_ranks = [pos.get(rel, tail) for rel in relevant]
            mean_rank = sum(rel_ranks) / n_rel
            row["auc_x1000"] += round(1000 * (1 - (mean_rank - (n_rel - 1) / 2) / (n_docs - n_rel)))
        n = row["issues"]
        if not n:
            print(pair, "no issues")
            continue
        chance_any = 1 - math.comb(n_docs - n_rel, 10) / math.comb(n_docs, 10)
        print(
            f"{pair}: issues={n} files={n_docs} changed={n_rel} base={base:.3f} | "
            f"P@1={row['hits@1'] / n:.3f} P@5={row['hits@5'] / n / 5:.3f} "
            f"P@10={row['hits@10'] / n / 10:.3f} | any@10={row['any@10'] / n:.2f} "
            f"(chance {chance_any:.2f}) | AUC={row['auc_x1000'] / n / 1000:.3f} | "
            f"names a class={row['names_a_class']} of which changed={row['named_class_changed']} "
            f"stack frames={row['has_stack_frame']}"
        )
        tot.update(row)
        tot["base_x_issues"] += base * n
        tot["chance_any_x_issues"] += chance_any * n
    n = tot["issues"]
    if n:
        print(
            f"ALL: issues={n} base={tot['base_x_issues'] / n:.3f} | P@1={tot['hits@1'] / n:.3f} "
            f"P@5={tot['hits@5'] / n / 5:.3f} P@10={tot['hits@10'] / n / 10:.3f} | "
            f"any@10={tot['any@10'] / n:.2f} (chance {tot['chance_any_x_issues'] / n:.2f}) | "
            f"AUC={tot['auc_x1000'] / n / 1000:.3f} | names a class={tot['names_a_class']} "
            f"of which changed={tot['named_class_changed']} stack frames={tot['has_stack_frame']}"
        )


main()
