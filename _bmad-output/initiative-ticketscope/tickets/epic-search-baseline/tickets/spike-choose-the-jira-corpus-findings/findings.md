# Spike 1.12 findings: choose the Jira corpus

**Status: a draft for the author.** Nothing here has been written to the spike ticket or the epic. The Decision line at the end is a proposal and needs the author's sign-off.

Measured on 2026-11-06 from The Public Jira Dataset v7 (Zenodo 15719919, CC BY 4.0). The dump was restored into a throwaway MongoDB container (`jira-spike-mongo`, mongo:7, database `JiraReposAnon`): 16 collections, 2,686,282 documents, none failed.

**The data ends at its collection date.** In every candidate, the latest `created` date falls between 2021-12-27 and 2022-01-05.

## Short answer

**Switch, with conditions.** The dump clears the ground-truth test easily. Kubernetes did not: 21 duplicates, none with a target.

**Recommended subset: Mojang MCL + REALMS + MCD** (the launcher, Realms and Dungeons). It takes the resolved issues up to January 2022, plus the 236 unresolved issues that resolved duplicates point to:

- 32,154 issues
- 10,466 in-subset pairs: 10,162 short, 304 log-heavy
- 0.7% unknown outcomes
- a load of 3.9 s against 600 s

It is the subset closest to support tickets: players reporting that they can't log in, the launcher crashes, or they can't join a Realm.

- **Terms: accepted by the author.** Nothing grants third parties the right to republish Mojang bug-tracker text, and nothing forbids it (see `terms.md`), the same footing GitHub text had before spike 2. The author ruled that this is enough, on spike 2's conditions (user, 2026-11-06).
- **Fallback: Apache SPARK.** 35,034 issues, 1,847 pairs (1,419 short, 428 log-heavy), 0.0% unknown, a load of 10.0 s. Its terms footing is better, since the Apache License's definition of "Contribution" arguably covers issue-tracker text. But these are developer bug reports, so they fit support tickets no better than Kubernetes.
- **Ruled out:**
  - MongoDB SERVER: its site terms forbid redistribution without written permission.
  - Jira JRASERVER: only 169 log-heavy pairs (182 with open targets).
  - Mojang MC time windows: most pairs are lost because their targets fall outside the window.

## Method

- **Scripts:**
  - `measure.py` computes metrics per instance, per project and per named subset, and draws the samples.
  - `convert.py` writes a schema-v1 snapshot and its kinds sidecar.
  - `test_spike.py` holds 15 tests, one or more per row of the plan's I/O matrix.
  - `tables.py` renders the tables below from the CSVs: `python3 tables.py <csv> instances|projects|subsets`.
- **Subset:** a scope's resolved issues. The `plus_open_targets_*` columns add the unresolved issues that resolved duplicates point to. The recommendation uses that variant, because a duplicate's target has to be in the corpus to count as ground truth.
- **Pair:** an issue resolved `Duplicate` (or "Duplicate Issue") with a link whose type maps to Duplicate in `jira_issue_linktype_mapping.json`, pointing to another issue in the same subset.
  - Sakai's link type "3 - Duplicate" is matched after stripping its number prefix.
  - The "duplicates" direction is preferred. When an issue resolved Duplicate has no link reading "duplicates", any Duplicate-mapped link counts as a fallback, in either direction (typically "is duplicated by"). These pairs are **included** in `pairs` and the kind columns, and also counted in `pairs_link_reversed`: 58 of 6,747 in mojang-mcl-realms-mcd, 156 of 1,847 in apache-spark, 268 of 4,349 in mongodb-server, 153 of 3,225 in jira-jraserver. Pairs are unordered, so the direction does not change the pair count. It only changes which issue's kind the pair is counted under, and `convert.py` emits a `marked_as_duplicate` event for these issues too.
  - Each unordered pair counts once, under the kind of the duplicate issue.
  - Targets that are out of scope, unresolved, or missing are counted separately.
- **Kind:** `ticketscope.core.derive.kind_score` at threshold 3, run over the description after each `{code…}` / `{noformat}` toggle is rewritten as a ``` fence.
  - For Mojang the extension barely matters. In MCL, log-heavy issues among the resolved go from 771 to 800, and among the Duplicate-resolved from 522 to 535.
  - It matters much more for Apache. In SPARK, log-heavy issues among the resolved go from 3,518 to 4,846, and among the Duplicate-resolved from 385 to 506.
  - These are issue counts, not pairs. They come from `kind_extension_effect.py <findings-dir> <instance> <project>`, which compares raw `kind_score` with the extended rule.
- **Outcome:** per `outcome-mapping.md`. All 89 resolution values are mapped; the file also holds the "answered" rule.
- **Hygiene:** resolved issues containing:
  - wiki markup
  - `[~…]` mentions
  - email or secret patterns (from `ticketscope.jobs.ingest.mask`)
  - NUL characters
- **Repeated documents:** the dump repeats a few issue keys (Apache 17, MongoDB 22, Jira 10, Mojang 5). The first document wins.

## Per instance

**Bold** rows have at least 1,000 pairs and at least 200 of each kind. Every instance has at most 0.7% unknown outcomes. Mojang's top 10 reporters file only 1.7% of its issues, among 239,523 distinct reporters: the most public, support-like pattern in the dump.

| Instance | Resolved issues | Log-heavy | Pairs | Pairs short | Pairs log-heavy | Target open / outside / no link | Dup / fixed / not_planned / stale / answered | Unknown | Bug | Question/Support | Wiki / mention / email / secret / NUL |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Apache** | 833,730 | 79,547 | 19,423 | 15,767 | 3,656 | 2,560 / 17 / 20,037 | 5.1% / 78.9% / 15.3% / 0.3% / 0.4% | 0.0% | 52.7% | 0.2% | 243,818 / 183,156 / 112,042 / 74 / 0 |
| Hyperledger | 25,190 | 1,638 | 335 | 269 | 66 | 42 / 2 / 285 | 2.6% / 82.8% / 14.6% / 0.0% / 0.0% | 0.0% | 28.0% | 0.0% | 5,080 / 4,535 / 447 / 4 / 0 |
| IntelDAOS | 8,419 | 1,213 | 174 | 91 | 83 | 17 / 0 / 374 | 6.8% / 84.6% / 8.7% / 0.0% / 0.0% | 0.0% | 40.2% | 0.0% | 2,932 / 1,666 / 1,883 / 1 / 0 |
| JFrog | 10,229 | 1,142 | 354 | 295 | 59 | 45 / 0 / 132 | 5.2% / 65.5% / 29.3% / 0.0% / 0.0% | 0.0% | 60.5% | 0.1% | 2,180 / 242 / 171 / 3 / 0 |
| **Jira** | 216,719 | 11,723 | 13,633 | 12,910 | 723 | 4,130 / 95 / 6,670 | 11.4% / 35.9% / 35.9% / 7.9% / 8.9% | 0.0% | 51.4% | 1.1% | 124,037 / 21,738 / 8,697 / 15 / 0 |
| **JiraEcosystem** | 36,542 | 2,568 | 1,339 | 1,032 | 307 | 114 / 0 / 895 | 6.5% / 62.0% / 28.3% / 0.8% / 2.1% | 0.3% | 49.2% | 0.3% | 8,151 / 4,379 / 581 / 1 / 0 |
| MariaDB | 23,150 | 6,159 | 850 | 548 | 302 | 207 / 0 / 529 | 6.9% / 74.6% / 18.5% / 0.0% / 0.0% | 0.0% | 75.9% | 0.0% | 11,884 / 186 / 994 / 0 / 1 |
| Mindville | 616 | 12 | 5 | 5 | 0 | 4 / 0 / 14 | 3.9% / 85.1% / 6.8% / 0.0% / 4.2% | 0.0% | 73.5% | 0.0% | 211 / 0 / 2 / 0 / 0 |
| **Mojang** | 406,490 | 8,722 | 147,170 | 142,259 | 4,911 | 42,769 / 10 / 2,380 | 47.3% / 5.1% / 42.6% / 5.0% / 0.0% | 0.0% | 100.0% | 0.0% | 249,523 / 6,864 / 955 / 0 / 0 |
| **MongoDB** | 122,351 | 6,974 | 7,258 | 6,530 | 728 | 850 / 1 / 2,625 | 8.8% / 69.7% / 20.5% / 0.0% / 1.0% | 0.0% | 37.1% | 1.3% | 47,301 / 20,308 / 66,696 / 7 / 2 |
| Qt | 120,862 | 5,014 | 2,800 | 2,624 | 176 | 547 / 0 / 6,311 | 8.0% / 58.1% / 33.9% / 0.0% / 0.0% | 0.0% | 74.4% | 0.0% | 37,365 / 11,154 / 1,141 / 1 / 7 |
| **RedHat** | 313,508 | 32,085 | 4,035 | 3,343 | 692 | 298 / 24 / 6,419 | 3.5% / 78.6% / 17.3% / 0.0% / 0.7% | 0.0% | 47.7% | 0.1% | 88,506 / 53,464 / 41,638 / 25 / 0 |
| Sakai | 44,572 | 2,437 | 1,397 | 1,304 | 93 | 108 / 0 / 993 | 5.7% / 70.9% / 23.5% / 0.0% / 0.0% | 0.0% | 66.5% | 0.0% | 2,638 / 2,803 / 2,069 / 0 / 0 |
| SecondLife | 1,633 | 33 | 0 | 0 | 0 | 0 / 0 / 84 | 5.1% / 69.9% / 24.2% / 0.0% / 0.0% | 0.7% | 6.7% | 0.0% | 432 / 5 / 410 / 0 / 0 |
| Sonatype | 81,637 | 2,015 | 251 | 207 | 44 | 29 / 0 / 6,985 | 8.9% / 74.6% / 6.6% / 5.8% / 4.1% | 0.0% | 7.2% | 11.5% | 11,358 / 2,126 / 4,683 / 0 / 0 |
| **Spring** | 61,564 | 5,761 | 1,278 | 1,052 | 226 | 118 / 2 / 1,327 | 4.5% / 74.8% / 20.7% / 0.0% / 0.0% | 0.0% | 39.6% | 0.2% | 37,226 / 2,485 / 595 / 0 / 0 |

## Per project (at least 5,000 resolved issues and 300 pairs, sorted by log-heavy pairs)

At 20–50k issues, log-heavy pairs are the binding constraint. Developer-facing projects have the logs but few duplicates. Player-facing projects have the duplicates, but those are mostly short. All of `projects.csv` (952 projects across Mojang, Jira, MongoDB, RedHat and Apache) is in the CSV.

| Project | Resolved issues | Log-heavy | Pairs | Pairs short | Pairs log-heavy | Target open / outside / no link | Dup / fixed / not_planned / stale / answered | Unknown | Bug | Question/Support | Wiki / mention / email / secret / NUL |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Mojang MC** | 205,545 | 7,847 | 89,493 | 85,138 | 4,355 | 14,663 / 2,651 / 619 | 52.3% / 6.0% / 35.4% / 6.3% / 0.0% | 0.0% | 100.0% | 0.0% | 96,209 / 4,633 / 578 / 0 / 0 |
| **MongoDB SERVER** | 52,970 | 3,567 | 4,349 | 3,828 | 521 | 497 / 102 / 1,095 | 11.5% / 66.4% / 20.6% / 0.0% / 1.5% | 0.0% | 46.8% | 2.7% | 20,959 / 9,477 / 33,875 / 5 / 2 |
| **Apache SPARK** | 35,034 | 4,846 | 1,847 | 1,419 | 428 | 55 / 4 / 484 | 6.9% / 65.4% / 27.4% / 0.2% / 0.1% | 0.0% | 41.2% | 1.1% | 11,775 / 8,541 / 1,106 / 0 / 0 |
| **Mojang MCL** | 16,964 | 800 | 3,974 | 3,679 | 295 | 845 / 1,434 / 366 | 39.1% / 3.5% / 50.3% / 7.2% / 0.0% | 0.0% | 100.0% | 0.0% | 11,728 / 259 / 78 / 0 / 0 |
| Apache CASSANDRA | 14,815 | 2,886 | 767 | 506 | 261 | 94 / 0 / 655 | 10.3% / 68.3% / 20.5% / 0.6% / 0.3% | 0.0% | 58.2% | 0.0% | 7,897 / 4,581 / 597 / 4 / 0 |
| Apache FLINK | 21,398 | 2,774 | 901 | 672 | 229 | 153 / 2 / 524 | 7.4% / 75.8% / 16.2% / 0.0% / 0.5% | 0.0% | 41.3% | 0.0% | 8,328 / 7,134 / 4,949 / 10 / 0 |
| Jira CONFSERVER | 37,287 | 2,498 | 2,775 | 2,599 | 176 | 584 / 41 / 841 | 11.5% / 33.5% / 38.4% / 6.0% / 10.7% | 0.0% | 61.9% | 0.0% | 22,828 / 3,943 / 1,230 / 0 / 0 |
| Jira JRASERVER | 38,676 | 2,545 | 3,225 | 3,056 | 169 | 652 / 212 / 529 | 12.0% / 31.8% / 38.7% / 9.1% / 8.4% | 0.0% | 47.7% | 3.8% | 22,214 / 4,065 / 1,669 / 1 / 0 |
| Apache YARN | 7,806 | 1,202 | 534 | 395 | 139 | 59 / 44 / 307 | 12.2% / 76.8% / 10.8% / 0.0% / 0.1% | 0.0% | 44.8% | 0.0% | 4,500 / 5,828 / 786 / 0 / 0 |
| Apache HDFS | 12,328 | 1,402 | 575 | 453 | 122 | 66 / 82 / 477 | 9.8% / 78.2% / 11.9% / 0.1% / 0.1% | 0.0% | 43.4% | 0.0% | 6,685 / 6,483 / 405 / 0 / 0 |
| Apache HIVE | 18,515 | 2,227 | 631 | 509 | 122 | 56 / 1 / 621 | 7.1% / 85.0% / 7.8% / 0.1% / 0.1% | 0.0% | 54.8% | 0.0% | 12,883 / 10,586 / 540 / 0 / 0 |
| RedHat JBIDE | 26,045 | 3,801 | 561 | 463 | 98 | 20 / 16 / 436 | 4.0% / 77.0% / 19.0% / 0.0% / 0.0% | 0.0% | 53.8% | 0.0% | 7,890 / 3,893 / 2,533 / 0 / 0 |
| Apache HADOOP | 13,217 | 1,340 | 493 | 401 | 92 | 61 / 76 / 818 | 11.1% / 74.1% / 14.8% / 0.0% / 0.0% | 0.0% | 51.7% | 0.0% | 5,644 / 4,034 / 1,359 / 2 / 0 |
| Apache KAFKA | 8,682 | 1,357 | 342 | 259 | 83 | 81 / 0 / 326 | 8.7% / 76.0% / 13.4% / 1.4% / 0.4% | 0.0% | 56.0% | 0.0% | 2,860 / 2,965 / 3,659 / 0 / 0 |
| Apache IMPALA | 8,869 | 1,508 | 338 | 259 | 79 | 68 / 4 / 478 | 10.0% / 72.7% / 16.5% / 0.0% / 0.8% | 0.0% | 60.5% | 0.2% | 4,715 / 2,978 / 4,927 / 0 / 0 |
| RedHat KEYCLOAK | 14,559 | 1,250 | 500 | 424 | 76 | 37 / 0 / 354 | 6.2% / 57.8% / 34.1% / 0.0% / 1.9% | 0.0% | 47.9% | 0.0% | 4,039 / 3,194 / 2,322 / 3 / 0 |
| Jira SRCTREEWIN | 5,199 | 229 | 997 | 923 | 74 | 120 / 2 / 311 | 27.7% / 28.4% / 37.9% / 0.1% / 5.8% | 0.0% | 80.4% | 0.0% | 803 / 186 / 84 / 0 / 0 |
| Apache HBASE | 22,773 | 2,985 | 318 | 250 | 68 | 37 / 0 / 945 | 5.7% / 79.3% / 14.9% / 0.0% / 0.1% | 0.0% | 47.1% | 0.0% | 13,410 / 10,691 / 2,431 / 0 / 0 |
| Apache MESOS | 7,147 | 842 | 312 | 244 | 68 | 87 / 0 / 131 | 7.5% / 79.6% / 12.8% / 0.0% / 0.1% | 0.0% | 51.5% | 0.0% | 3,945 / 1,896 / 4,401 / 0 / 0 |
| Apache MNG | 5,589 | 723 | 371 | 303 | 68 | 43 / 43 / 111 | 10.3% / 54.4% / 34.2% / 0.9% / 0.2% | 0.0% | 58.3% | 0.0% | 2,077 / 323 / 231 / 0 / 0 |
| Apache IGNITE | 11,949 | 1,471 | 364 | 297 | 67 | 55 / 0 / 301 | 6.0% / 80.9% / 12.9% / 0.1% / 0.1% | 0.0% | 43.0% | 0.0% | 5,253 / 5,143 / 1,814 / 0 / 0 |
| Jira BAM | 12,415 | 1,451 | 603 | 544 | 59 | 183 / 2 / 223 | 8.2% / 53.8% / 13.9% / 17.1% / 6.9% | 0.0% | 46.6% | 0.0% | 4,864 / 755 / 270 / 8 / 0 |
| Apache SOLR | 11,785 | 1,148 | 403 | 345 | 58 | 72 / 18 / 295 | 6.7% / 73.1% / 19.4% / 0.0% / 0.7% | 0.0% | 47.6% | 0.0% | 5,211 / 4,927 / 2,318 / 0 / 0 |
| MongoDB WT | 7,499 | 441 | 437 | 392 | 45 | 37 / 7 / 146 | 8.5% / 82.0% / 9.4% / 0.0% / 0.0% | 0.0% | 35.6% | 0.0% | 4,758 / 2,943 / 4,169 / 0 / 0 |
| Apache OAK | 8,810 | 693 | 526 | 493 | 33 | 11 / 3 / 63 | 6.9% / 82.6% / 10.4% / 0.1% / 0.0% | 0.0% | 39.6% | 0.0% | 4,344 / 2,769 / 108 / 0 / 0 |
| Jira CONFCLOUD | 20,150 | 762 | 728 | 701 | 27 | 366 / 95 / 474 | 8.3% / 23.1% / 41.9% / 16.1% / 10.5% | 0.0% | 46.9% | 0.0% | 18,699 / 2,662 / 713 / 0 / 0 |
| Jira JRACLOUD | 22,142 | 913 | 839 | 819 | 20 | 388 / 203 / 388 | 8.3% / 18.1% / 60.7% / 5.6% / 7.4% | 0.0% | 37.6% | 3.6% | 20,435 / 3,141 / 998 / 0 / 0 |
| Jira JSWSERVER | 10,928 | 381 | 809 | 789 | 20 | 273 / 100 / 193 | 12.7% / 35.2% / 30.7% / 4.7% / 16.6% | 0.0% | 49.2% | 0.0% | 3,705 / 1,183 / 239 / 0 / 0 |
| Apache CB | 12,860 | 483 | 371 | 352 | 19 | 33 / 1 / 331 | 5.8% / 66.3% / 27.0% / 0.7% / 0.3% | 0.0% | 62.1% | 0.0% | 3,053 / 4,879 / 2,759 / 0 / 0 |
| Jira BSERV | 5,663 | 532 | 647 | 631 | 16 | 329 / 8 / 66 | 18.6% / 42.3% / 16.8% / 2.1% / 20.2% | 0.0% | 46.8% | 0.0% | 2,679 / 1,610 / 298 / 1 / 0 |
| Jira JSWCLOUD | 10,029 | 171 | 546 | 539 | 7 | 306 / 48 / 218 | 11.2% / 33.0% / 36.1% / 5.5% / 14.2% | 0.0% | 35.1% | 0.0% | 5,064 / 1,169 / 253 / 0 / 0 |
| MongoDB DOCS | 12,513 | 196 | 431 | 425 | 6 | 19 / 18 / 453 | 7.5% / 71.1% / 21.0% / 0.0% / 0.4% | 0.0% | 32.3% | 0.0% | 4,238 / 1,083 / 6,107 / 1 / 0 |
| MongoDB EVG | 11,383 | 129 | 549 | 544 | 5 | 67 / 9 / 221 | 7.5% / 66.3% / 26.0% / 0.0% / 0.2% | 0.0% | 24.3% | 0.4% | 3,417 / 1,406 / 5,069 / 0 / 0 |
| Mojang REALMS | 8,712 | 10 | 996 | 992 | 4 | 2,022 / 1,409 / 26 | 51.1% / 2.6% / 41.9% / 4.3% / 0.0% | 0.0% | 100.0% | 0.0% | 7,024 / 69 / 7 / 0 / 0 |
| Mojang MCPE | 140,317 | 35 | 42,585 | 42,584 | 1 | 20,310 / 1,223 / 527 | 46.1% / 4.1% / 46.6% / 3.2% / 0.0% | 0.0% | 100.0% | 0.0% | 109,652 / 1,693 / 210 / 0 / 0 |
| Mojang MCCE | 11,774 | 2 | 1,287 | 1,287 | 0 | 0 / 39 / 808 | 18.2% / 9.4% / 69.6% / 2.8% / 0.0% | 0.0% | 100.0% | 0.0% | 5,257 / 101 / 57 / 0 / 0 |
| Mojang MCD | 6,242 | 1 | 1,559 | 1,559 | 0 | 841 / 208 / 8 | 41.9% / 2.8% / 49.2% / 6.0% / 0.0% | 0.0% | 100.0% | 0.0% | 5,177 / 24 / 7 / 0 / 0 |

## Candidate subsets

| Subset | Resolved issues | Log-heavy | Pairs | Pairs short | Pairs log-heavy | Target open / outside / no link | Dup / fixed / not_planned / stale / answered | Unknown | Bug | Question/Support | Wiki / mention / email / secret / NUL |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **mojang-mcl (Mojang)** | 16,964 | 800 | 3,974 | 3,679 | 295 | 845 / 1,434 / 366 | 39.1% / 3.5% / 50.3% / 7.2% / 0.0% | 0.0% | 100.0% | 0.0% | 11,728 / 259 / 78 / 0 / 0 |
| **mojang-mcl-realms-mcd (Mojang)** | 31,918 | 811 | 6,747 | 6,448 | 299 | 3,719 / 2,822 / 400 | 42.9% / 3.1% / 47.8% / 6.2% / 0.0% | 0.0% | 100.0% | 0.0% | 23,929 / 352 / 92 / 0 / 0 |
| mojang-mc-2021 (Mojang) | 26,792 | 203 | 3,761 | 3,735 | 26 | 770 / 7,294 / 10 | 44.2% / 3.3% / 44.1% / 8.4% / 0.0% | 0.0% | 100.0% | 0.0% | 19,271 / 458 / 10 / 0 / 0 |
| mojang-mc-2020 (Mojang) | 62,873 | 554 | 12,697 | 12,613 | 84 | 2,548 / 12,499 / 76 | 44.2% / 3.8% / 42.7% / 9.2% / 0.0% | 0.0% | 100.0% | 0.0% | 40,510 / 1,186 / 24 / 0 / 0 |
| **apache-spark (Apache)** | 35,034 | 4,846 | 1,847 | 1,419 | 428 | 55 / 4 / 484 | 6.9% / 65.4% / 27.4% / 0.2% / 0.1% | 0.0% | 41.2% | 1.1% | 11,775 / 8,541 / 1,106 / 0 / 0 |
| jira-jraserver (Jira) | 38,676 | 2,545 | 3,225 | 3,056 | 169 | 652 / 212 / 529 | 12.0% / 31.8% / 38.7% / 9.1% / 8.4% | 0.0% | 47.7% | 3.8% | 22,214 / 4,065 / 1,669 / 1 / 0 |
| **mongodb-server (MongoDB)** | 52,970 | 3,567 | 4,349 | 3,828 | 521 | 497 / 102 / 1,095 | 11.5% / 66.4% / 20.6% / 0.0% / 1.5% | 0.0% | 46.8% | 2.7% | 20,959 / 9,477 / 33,875 / 5 / 2 |

The recommended subset's log-heavy pairs come almost entirely from MCL (295 of 299). REALMS adds 4 and MCD adds none. REALMS and MCD add short pairs and support-like breadth.

## Decision rule, applied

All columns use the "+ open targets" variant: resolved issues plus the unresolved targets of their duplicates.

| Test | mojang-mcl-realms-mcd | apache-spark | mongodb-server | jira-jraserver |
|---|---|---|---|---|
| Terms allow a public Release asset | **Yes**: accepted by the author (user, 2026-11-06) | Arguably yes (ALv2 "Contribution") | **No**: written permission required | Author's call |
| ≥ ~1,000 pairs, ≥ ~200 of each kind | 10,466; 10,162 / 304 | 1,902; 1,464 / 438 | 4,846; 4,259 / 587 | **No**: 182 log-heavy |
| < 20% unknown | 0.7% | 0.1% | 0.7% | 1.1% |
| Within the 600 s load | **3.9 s** (32,154 issues) | **10.0 s** (resolved only, 35,034 issues; the 35,082-issue + open variant was not timed) | not timed | not timed |
| Support fit (tie-break) | Closest | Developer | Developer | Customer-facing |

## Timed loads (`scripts/time-load.sh`, exit 0 for all three)

| Version | Issues | Load |
|---|---|---|
| `jira-mojang-mcl-realms-mcd` | 31,918 | 4.0 s |
| `jira-mojang-mcl-realms-mcd-open` | 32,154 | 3.9 s (rerun after review: 3.0 s) |
| `jira-apache-spark` | 35,034 | 10.0 s |

Both Mojang snapshots validate against `snapshot/schema-v1.json` with `jsonschema`, format checks on, and every number is unique:

- the recommended `jira-mojang-mcl-realms-mcd-open`: 32,154 of 32,154 lines
- the resolved-only `jira-mojang-mcl-realms-mcd`: 31,918 of 31,918 lines

The sidecar of the resolved-only snapshot is computed on masked text, and its 811 log-heavy issues match `subsets.csv`'s 811, computed on raw text. So masking does not shift kinds here. `convert.py` also validates every line with `SnapshotIssue`. The snapshots are kept outside git.

## Samples and duplicate pairs

- **Samples:** 20 issues per candidate, drawn with `random.Random(12)`:
  - `samples-mojang-mcl-realms-mcd.md`
  - `samples-apache-spark.md`
  - `samples-jira-jraserver.md`

  **Author's judgement (Mojang, 2026-11-06):** 18 of 20 issues support-like, 2 noise (MCL-12073 in Czech, MCL-7793 in Hungarian), none dev bug. The Apache SPARK and Jira JRASERVER samples were not judged.
- **Duplicate pairs:** 10 of the recommended subset's 10,466 pairs, drawn with unresolved targets included (3 of the 10 point at an unresolved target). All 10 are confirmed in the dump's changelog: the resolution was set to Duplicate and the link was added.
  - This shows a moderator made the call, not that the call was right. Most pairs read as real duplicates (e.g. REALMS-4485 "Can't download my world from Realms for backup" → REALMS-419 "Unable to Download Realm world"). Some are loose, e.g. MCL-9958 "minecraft launcher issue" → MCL-6629 "Launcher floated out of desktop boundaries when taskbar is at the top", and MCD-3976 (a crash in one level) → MCD-1354 ("Freezes and crashes when playing on Switch").
  - Author's judgement of the 10 pairs: 9 dup, 1 related (REALMS-9649 "Book and quill, Sing and chat do not work" → REALMS-9150 "Chat has long delay"), none not dup.
  - The live tracker was not checked. It moved to Jira Cloud in February 2025, and its pages render client-side.

## Findings for the replan

1. **Outcome rules.** Core's outcome rules read GitHub signals: PRs, labels, `author_association`. Only `duplicate` survives conversion, through the emitted `marked_as_duplicate` events. A switch needs `resolution` in the snapshot (schema v2), mapped in core per `outcome-mapping.md`.
2. **Issue numbers.** `number` is the Jira id, unique only within one instance, so a subset must stay inside one instance. v2 should carry the readable key (e.g. `MCL-123`).
3. **"Answered" rule.** Jira has no `author_association`. The answered rule uses masked reporter and author ids, which must not ship. v2 needs a derived "non-reporter comment" boolean. Converted comments currently carry `author_association: NONE`.
4. **Hygiene in the recommended subset:**
   - wiki markup in 75% of issues
   - 352 issues with mentions and 92 with emails
   - no secrets and no NUL characters
   - some text not in English (Czech, Hungarian and Spanish appear in the samples)
   - Apache has bogus dates (a `created` year of 0010)
5. **Duplicate documents.** The dump repeats some issue keys; the ingest must dedupe them.
6. **Thin log-heavy margin.** 304 log-heavy pairs at threshold 3 sits close to the 200 floor. Re-measure if story 5 raises the threshold.
7. **Stale data.** The data ends in January 2022. Red Hat now redirects to `redhat.atlassian.net`, and Mojang has moved to Jira Cloud.
8. **No "answered" in Mojang.** Every Mojang issue is typed Bug, so `answered` is 0%.

## Proposed Decision line (draft, needs the author's sign-off)

> Decision: Switch the corpus to The Public Jira Dataset v7 (Zenodo 15719919, CC BY 4.0), subset Mojang MCL + REALMS + MCD: resolved issues to January 2022, plus the unresolved targets of their duplicates. That gives 32,154 issues with 10,466 in-subset duplicate pairs (10,162 short, 304 log-heavy at threshold 3), 0.7% unknown, loaded in 3.9 s. Outcomes come from `resolution` per spike 12's `outcome-mapping.md`. "Answered" means a Question/Support-type issue resolved after a comment by someone other than the reporter. The kind rule maps Jira `{code}`/`{noformat}` blocks onto fences, which needs a reload and a baseline update. Attribution is the line in spike 12's `terms.md`, plus a link to each source issue. If Mojang's terms are judged insufficient, fall back to Apache SPARK. The data lane (stories 1–5 and the snapshot schema) and epic-eval-gate are to be replanned (user, 2026-11-06).

approved, dillon heffernan
## Proposed epic amendments (draft)

- **Corpus scope:**
  - Source: v7's resolved Mojang MCL/REALMS/MCD issues, plus their duplicates' unresolved targets: about 32k issues, collected January 2022, all from one instance.
  - Cap: raise from 20,000 to about 50,000.
  - Load budget: 600 s, unchanged.
- **Corpus terms:**
  - Cite the dataset and the MSR 2022 paper.
  - State that the text belongs to its authors on bugs.mojang.com.
  - Keep spike 2's four conditions:
    1. attribution, with a link per issue
    2. no identities: no masked ids, and `[~…]` mentions masked
    3. masking
    4. takedown
- **Outcome precedence and terms:** add a Jira branch that maps `resolution`, with the "answered" rule above. The GitHub-specific terms do not apply to this corpus.
- **Kind rule:** Jira `{code…}`/`{noformat}` toggles count as fences.
