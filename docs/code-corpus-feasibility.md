# Code corpus feasibility: can tickets be linked to the code that fixed them?

Findings from a first look, 2026-11-15. Nothing here is built or decided. The question was whether ticketscope could add the code of the product its tickets are about to the retrieval corpus, and what stands in the way on the Mojang data.

## Summary

- **The loaded corpus cannot be linked to code.** MCL, REALMS and MCD are the launcher, Realms and Dungeons. Their code is not the Java Edition jar, and only 651 of their Fixed issues name a single fix version.
- **The Java Edition project (MC) can.** 11,870 Fixed MC issues name exactly one fix version. 3,691 of those, across 131 versions from September 2019 to January 2022, were released with Mojang's official obfuscation mappings, so their code can be read with real names.
- **The code may be read locally but not published.** The mappings licence allows copying and use "for development purposes"; the EULA forbids distributing anything Mojang made. A code index or its embeddings cannot ship in a snapshot Release, a CI artifact or an image.
- **So a code prototype needs two things the project does not have:** MC issues in the corpus, and a corpus that is built and kept on the machine that uses it.
- **Keyword search over code is good enough for an agent that reads the top 10.** On versions that changed 40 files or fewer, a file the fix changed is in the top 10 for 53% of issues, against 15% for issues scored on the wrong version and 5% by chance. It is first for far fewer, so it suits a consumer that reads several results and searches again.
- **A local prototype works end to end.** `scripts/code_corpus_spike/` builds a SQLite index from a source tree and serves `search_code` and `get_code` over MCP.

## What the data holds

The Mojang tracker has no link from an issue to a commit or pull request. The nearest thing is `fields.fixVersions`, which the ingest projection (`adapters/jira_dump.py`) does not read today. Counts are over the whole `Mojang` collection of The Public Jira Dataset v7 (420,819 issues, collected January 2022), from `scripts/fixversion_coverage.py`.

| Project | Product | Resolved | Fixed | Fixed, one fix version | Fix versions | Issues per version (median / p90 / max) |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| MC | Java Edition | 205,547 | 12,338 | 11,870 | 537 | 15 / 48 / 127 |
| MCPE | Bedrock | 140,317 | 5,668 | 4,480 | 364 | 8 / 30 / 87 |
| MCL | Launcher (in corpus) | 16,965 | 582 | 375 | 121 | 2 / 6 / 55 |
| REALMS | Realms (in corpus) | 8,712 | 204 | 118 | 41 | 1 / 3 / 41 |
| MCD | Dungeons (in corpus) | 6,242 | 175 | 158 | 24 | 4 / 18 / 24 |

MC fix versions are mostly weekly snapshots (`21w11a`, `1.16 Pre-release 3`), so the code change between one version and the one before it is small. Matched against Mojang's public version list (`piston-meta.mojang.com/mc/game/version_manifest_v2.json`):

| MC Fixed issues with one fix version | Issues | Versions |
| --- | ---: | ---: |
| All | 11,870 | 537 |
| Fix version found in the version list | 11,275 | 499 |
| Fix version released with official mappings | 3,691 | 131 |

Mappings exist for 1.14.4 and for every version from 19w36a (2019-09-04) on; 1.14.3, 19w34a and 19w35a have none (checked in each version's metadata). For the 131 mapped versions the median is 20 fixed issues per version, p90 62, max 127.

Not counted: issues resolved Duplicate whose target was Fixed. They inherit the target's fix version through the duplicate cluster and would add labels.

## What the terms allow

Read from the primary texts on 2026-11-15. This is a reading, not legal advice.

- **Mappings licence** (header of every mappings file, here 1.18's `client.txt`): "You may copy and use the mappings for development purposes, but you may not redistribute the mappings complete and unmodified. ... Use and modification of this document or the source code (in any form) of Minecraft: Java Edition is governed by the Minecraft End User License Agreement".
- **EULA** (<https://www.minecraft.net/en-us/eula>): "you must not distribute anything we've made unless we specifically agree to it", and a Mod is "something original ... that doesn't contain a substantial part of our copyrightable code or content". It allows developing "tools, plug-ins and services". It does not mention decompiling.
- **Obfuscation is gone from current versions** ([Removing obfuscation in Java Edition](https://www.minecraft.net/en-us/article/removing-obfuscation-in-java-edition)): the jars ship with original names and "a LICENSE file inside the jar that links directly to the EULA". Version 26.3 (2026-09-15) has no mappings download, as announced. This does not help here: the dataset stops in January 2022, so every labelled issue is from an obfuscated version.

## What follows for ticketscope

1. **The corpus would have to grow.** A code prototype needs MC issues, which the corpus spike left out. The smallest useful set is the 3,691 Fixed MC issues with a mapped fix version, loaded beside the current corpus, not replacing it: the duplicate-pair eval and its baseline stay as they are.
2. **Ingest would read `fixVersions`.** That is a snapshot schema change (v3) and a new projected field. A version name is not a person identifier.
3. **The code corpus is local only.** It is built from jars downloaded from Mojang by the person running it, and is never committed, published as a Release asset, uploaded by CI or baked into an image. `AGENTS.md` would need that rule beside the one about raw dump documents.
4. **CI cannot score real code.** The eval gate would run on a small invented code fixture; scores on real code would come from a local run and could not be the CI baseline (`docs/decisions/adr-eval-baseline-is-ci-output-only.md`).
5. **The label is coarse.** "The files that changed between the version before and the fix version" is shared by every issue fixed in that version, a median of 20. It measures whether retrieval lands in the right change set, not the right file.

## Measured: decompiling and the keyword check

Run locally on 2026-11-15 with a portable JDK 21, NeoForged AutoRenamingTool 2.0.18 (applies the mappings) and Vineflower 1.11.1 (decompiles). The decompiled code stayed in a scratch folder outside the repository.

**Decompiling is cheap.** One version takes about 2 seconds to remap and 20 to decompile, and gives 3,300 to 4,100 Java files (about 465,000 lines, 19 MB) plus about 10,000 data and asset files. All 131 mapped versions would take under an hour and about 2.5 GB of Java source.

**The change set is small but uneven.** Java files modified between a version and the one before it:

| Pair | Java files | Modified | Share |
| --- | ---: | ---: | ---: |
| 1.16-pre1 to 1.16-pre2 | 3,568 | 8 | 0.2% |
| 21w10a to 21w11a | 3,768 | 177 | 4.7% |
| 19w41a to 19w42a | 3,306 | 189 | 5.7% |
| 20w22a to 1.16-pre1 | 3,552 | 247 | 7.0% |
| 1.16-pre2 to 1.16-pre3 | 3,568 | 273 | 7.7% |
| 21w03a to 21w05a | 3,701 | 320 | 8.6% |
| 20w21a to 20w22a | 3,536 | 501 | 14.2% |
| 21w11a to 21w13a | 3,786 | 1,301 | 34.4% |

The median modified file changes by 4 to 10 lines, depending on the pair. Data files are noisier: 874 of about 4,100 changed between 21w10a and 21w11a, so they were left out of the check below.

**The keyword check.** The corpus is the Java files of the earlier version (the code as it was when the bug existed). A file is relevant when the fix version modified or removed it. Each query is one issue's summary and description, ranked with BM25 over identifiers split on camelCase, with the class name weighted. The control scores the same change sets with the issues of a version fixed a year or more away. Five pairs, 545 issues (control 544):

| | Base rate | P@1 | P@10 | Any changed file in top 10 | AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| Issues against their own fix version | 0.083 | 0.497 | 0.370 | 0.95 | 0.661 |
| Issues against the wrong version (control) | 0.083 | 0.272 | 0.259 | 0.82 | 0.645 |

P@k is the share of the top k files that are in the change set; AUC is the chance a changed file outranks an unchanged one.

What this shows:

- **There is fix-specific signal.** P@1 is 0.50 against 0.27 for the control, and it holds in each of the five pairs (0.29 to 0.63 against 0.18 to 0.39).
- **More than half the lift over chance is not about the fix.** Any issue, scored against any version, lands on a changed file three times as often as chance. The likely cause, not tested here, is that keyword search favours large, central files and those change in most versions.
- **"Any changed file in the top 10" and AUC cannot be used.** They barely separate the real run from the control.
- **The signal is in ordinary words, not identifiers.** Only 29 of 545 issues name a class and 19 hold a stack frame. Of the 29 named classes, 25 were in the change set.

## Measured for an agent: is a changed file in the top k?

The consumer is an LLM calling a tool over MCP. It reads the top 10 to 20 results and can search again, so the first result matters less than whether a relevant file is in the set. The coarse label hides that: when a version changes hundreds of files, almost any top 10 contains one.

So this run uses the 64 pre-release, release-candidate and patch versions with fixed issues. They are bug-fix builds, and 43 of them changed 40 Java files or fewer, which makes "the files this version changed" a precise label. Ranking is the prototype's own index (`code_index.py`, SQLite FTS5 BM25). The control scores each change set with 60 issues fixed a year or more away.

Share of issues with a changed file in the top k, ranking whole files:

| Changed files | Pairs | Issues | Top 5 | Top 10 | Top 20 |
| --- | ---: | ---: | --- | --- | --- |
| 1 to 10 | 23 | 117 | 0.16 (control 0.02, chance 0.01) | 0.21 (0.05, 0.01) | 0.29 (0.09, 0.03) |
| 11 to 40 | 20 | 168 | 0.67 (0.15, 0.03) | 0.75 (0.26, 0.07) | 0.83 (0.39, 0.13) |
| 41 to 150 | 15 | 449 | 0.64 (0.38, 0.10) | 0.79 (0.53, 0.19) | 0.92 (0.72, 0.34) |
| 151 or more | 6 | 400 | 0.87 (0.65, 0.29) | 0.94 (0.81, 0.50) | 0.98 (0.92, 0.74) |
| 40 or fewer, together | 43 | 285 | 0.46 (0.08, 0.02) | 0.53 (0.15, 0.05) | 0.61 (0.23, 0.09) |

- **The signal is clear where the label is precise.** With 40 changed files or fewer, the real run is three to six times the control in the top 5 and top 10.
- **The 1 to 10 row is a floor, not the truth.** Those versions fixed 117 issues with 4 changed Java files on average, so many of those fixes were probably in data or asset files, which this index does not hold.
- **Whole files rank slightly better than methods.** Ranking one chunk per method gave 0.49 in the top 10 for the 40-or-fewer group, against 0.53. The prototype ranks files and returns the best-matching method as the snippet.
- **Some hits are coincidence.** A few files (`Player.java`, `Minecraft.java`, the version constant) change in most builds. The control measures how often that happens; it is why the real figure should always be read beside it.

One pair as an example, 1.16-pre6 to 1.16-pre7 (34 changed files, 24 issues): 22 issues have a changed file in the top 20 and 8 have it first. "Turtle eggs hatching broken" ranks `TurtleEggBlock.java` first, "Striders left/right leg uses the same texture" ranks `StriderModel.java` first, and "Heads and skulls on a wall cause z-fighting" ranks `SkullBlockRenderer.java` second.

## The prototype

Three scripts in `scripts/code_corpus_spike/`. They are not product code: nothing in `src/`, the chart or CI knows about them.

- `code_index.py` builds one SQLite file from any source tree: a full-text table of files and one of methods, with identifiers split on camelCase. Minecraft 1.18 (4,203 files, 37,840 chunks) indexes in a few seconds into about 80 MB.
- `mcp_code_server.py` is a stdio MCP server over that file with two tools. `search_code(query, k)` returns the top files with the best-matching method of each as a snippet. `get_code(path, start_line, end_line)` reads further.
- `mcp_smoke.py` starts the server and calls both tools as a client would.

To use it from Claude Code beside the ticketscope server, with an index already built:

```sh
claude mcp add ticketscope-code \
    -e TICKETSCOPE_CODE_INDEX=$HOME/.local/share/ticketscope-code/minecraft-1.18.sqlite \
    -- uv run --project /path/to/ticketscope python /path/to/ticketscope/scripts/code_corpus_spike/mcp_code_server.py
```

The index holds the source text, and tool results carry it to the client. Build it locally and connect it only to a client that may see the code.

## What a real version would need

1. **A corpus the project may hold.** The prototype works on any source tree. With a team's own repositories the publishing problem goes away, and so does the coarse label: tickets link to the pull requests that fixed them.
2. **A place in the architecture.** A code table and a search path beside the issue ones, a `/v1` endpoint, and the MCP tool calling it like `search_similar_issues` does. Postgres already has BM25 through pg_textsearch; the camelCase splitting would move into the load job.
3. **A way to keep it current.** Re-index what changed on each push. This prototype rebuilds the whole index, which is fine at this size.
4. **An eval that reads beside a control.** Top-10 hit rate on small change sets, with the wrong-version control, is the measure that held up here.
5. **Still untested:** dense embeddings over code, data and asset files, and whether an agent given these tools reaches the right file more often than the ranking alone suggests.

## Reproduce

```sh
curl -sS -o /tmp/manifest.json https://piston-meta.mojang.com/mc/game/version_manifest_v2.json
unzip -p "ThePublicJiraDataset.zip" \
    "ThePublicJiraDataset/3. DataDump/mongodump-JiraReposAnon.archive" | gzip -dc \
    | uv run python scripts/fixversion_coverage.py --manifest /tmp/manifest.json
```

The script streams the archive without MongoDB (about 40 seconds) and prints counts and version names only.

The decompile and keyword measurements use the scripts in `scripts/code_corpus_spike/`, run against a scratch folder outside the repository (`$ROOT`), with the two tool jars in `$ROOT/tools/`:

```sh
S=scripts/code_corpus_spike
bash $S/fetch_version.sh /tmp/manifest.json $ROOT/mc 21w10a 21w11a
JAVA=/path/to/java bash $S/decompile.sh $ROOT 21w10a
JAVA=/path/to/java bash $S/decompile.sh $ROOT 21w11a
uv run python $S/diffstat.py $ROOT/mc/21w10a/src $ROOT/mc/21w11a/src $ROOT/mc/diff-21w10a-21w11a.json
unzip -p "ThePublicJiraDataset.zip" \
    "ThePublicJiraDataset/3. DataDump/mongodump-JiraReposAnon.archive" | gzip -dc \
    | uv run python $S/dump_mc_fixed.py scripts $ROOT/mc_fixed.jsonl
uv run python $S/keyword_check.py $ROOT/mc_fixed.jsonl $ROOT/mc 21w10a:21w11a   # real
uv run python $S/keyword_check.py $ROOT/mc_fixed.jsonl $ROOT/mc 21w10a:21w11a:20w22a   # control
```

`$ROOT` holds Mojang's code and issue text with unmasked mentions. Never commit or publish it.

The top-k table is `topk_check.py` over the pairs `bugfix_pairs.py` lists, each fetched, decompiled and diffed as above:

```sh
PAIRS=$(uv run python $S/bugfix_pairs.py /tmp/manifest.json $ROOT/mc_fixed.jsonl pairs)
(cd $S && uv run python topk_check.py $ROOT/mc_fixed.jsonl $ROOT/mc /tmp/manifest.json $PAIRS)
```
