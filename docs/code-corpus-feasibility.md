# Code corpus feasibility: can tickets be linked to the code that fixed them?

Findings from a first look, 2026-11-15. Nothing here is built or decided. The question was whether ticketscope could add the code of the product its tickets are about to the retrieval corpus, and what stands in the way on the Mojang data.

## Summary

- **The loaded corpus cannot be linked to code.** MCL, REALMS and MCD are the launcher, Realms and Dungeons. Their code is not the Java Edition jar, and only 651 of their Fixed issues name a single fix version.
- **The Java Edition project (MC) can.** 11,870 Fixed MC issues name exactly one fix version. 3,691 of those, across 131 versions from September 2019 to January 2022, were released with Mojang's official obfuscation mappings, so their code can be read with real names.
- **The code may be read locally but not published.** The mappings licence allows copying and use "for development purposes"; the EULA forbids distributing anything Mojang made. A code index or its embeddings cannot ship in a snapshot Release, a CI artifact or an image.
- **So a code prototype needs two things the project does not have:** MC issues in the corpus, and a corpus that is built and kept on the machine that uses it.

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

## Next steps, if this goes ahead

1. Decompile two adjacent mapped snapshots locally and measure the diff: files changed, time taken, size on disk. This settles whether the label is usable.
2. On a sample of the 3,691 issues, test whether the class names and stack frames in the issue text match the changed files by keyword alone. That one number decides whether a code index is worth building.
3. Only then write the stories: `fixVersions` in the snapshot, a separate code table and search tool, the local-only build.

## Reproduce

```sh
curl -sS -o /tmp/manifest.json https://piston-meta.mojang.com/mc/game/version_manifest_v2.json
unzip -p "ThePublicJiraDataset.zip" \
    "ThePublicJiraDataset/3. DataDump/mongodump-JiraReposAnon.archive" | gzip -dc \
    | uv run python scripts/fixversion_coverage.py --manifest /tmp/manifest.json
```

The script streams the archive without MongoDB (about 40 seconds) and prints counts and version names only.
