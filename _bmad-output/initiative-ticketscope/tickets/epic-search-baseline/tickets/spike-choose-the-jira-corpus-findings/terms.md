# Terms: republishing issue text from the candidate instances

Checked on 2026-11-06 from public web pages. This is not legal advice, and for most instances no terms specific to the issue tracker could be found. The author decides.

## What the dataset licence covers, and what it does not

- The Public Jira Dataset v7 (Zenodo 15719919) is CC BY 4.0. Reuse requires crediting the creators and citing the MSR 2022 paper.
- The dataset authors anonymised user records (reporter, assignee, creator, comment and change authors) with UUID4 masks. **Issue and comment text is not anonymised**, and it can hold names, `[~username]` mentions and email addresses (see the hygiene columns in the CSVs).
- CC BY 4.0 licenses what the dataset creators hold rights in. It cannot grant rights in text written by thousands of issue reporters and commenters, and it does not override each source site's own terms. So the decision rule's first test ("its licence and terms allow a public Release asset") turns on each source site's terms, as it did for GitHub in spike 2.

## Per candidate instance

| Instance | Source tracker today | What its terms say about reuse of posted text | Reading |
|---|---|---|---|
| Mojang | `https://bugs.mojang.com` (moved from Jira Server to Jira Cloud in February 2025; old `/browse/MC-n` links still answer 200) | No bug-tracker terms found. The Minecraft EULA and Microsoft Services Agreement say users keep ownership of their content and give Mojang/Microsoft a licence; neither grants third parties a licence to republish it. | Not granted, not forbidden. Same footing as GitHub issue text before spike 2: needs the author's judgement, attribution and a takedown path. |
| Jira (Atlassian) | `https://jira.atlassian.com` | No tracker-specific terms found; the issue page footer links only Atlassian's privacy policy. Atlassian's Community terms (closest analogue) say posters keep ownership and grant Atlassian a licence; nothing grants third parties a licence. | Not granted, not forbidden. As Mojang. |
| Apache | `https://issues.apache.org/jira` | The Apache License 2.0 defines a "Contribution" to include communication "on electronic mailing lists, source code control systems, and issue tracking systems that are managed by, or on behalf of, the Licensor for the purpose of discussing and improving the Work". That arguably puts ASF Jira text under ALv2, though a bug report is not always "intentionally submitted for inclusion in the Work". | The strongest grant of the candidates, but arguable. |
| MongoDB | `https://jira.mongodb.org` | MongoDB's website Terms of Use: "MongoDB strictly prohibits the redistribution or copying of any part of this website or content on this website without written permission from MongoDB." Users who post grant MongoDB a licence. It is not stated whether these terms cover `jira.mongodb.org`. | **A stated prohibition.** Fails the terms test unless MongoDB gives written permission. |
| RedHat | `https://issues.redhat.com`, now redirecting to `https://redhat.atlassian.net` | No tracker-specific terms found. | Not granted, not forbidden. Note the moved host for attribution links. |

Sources: [Zenodo record 15719919](https://zenodo.org/records/15719919); [Minecraft EULA](https://www.minecraft.net/eula); [minecraft.net: final days to migrate your bug account](https://www.minecraft.net/en-us/article/final-days-to-migrate-your-bug-account); [Atlassian Community platform terms](https://www.atlassian.com/legal/community-platform-terms-of-use); [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0); [MongoDB Terms of Use](https://www.mongodb.com/legal/terms-of-use). Third-party summaries seen during the search (ConductAtlas pages on the Minecraft EULA) were not relied on.

## Conditions a switch would carry (proposal)

The same four conditions as spike 2, adapted:

1. **Attribution:** every record links to its source issue (`<jira_url>/browse/<key>`), and the Release notes and README carry the attribution line below.
2. **No identities:** the masked author ids are left out of the snapshot entirely; `[~user]`/`[~accountid:…]` mentions in text are masked (the converter does this).
3. **Masking:** emails and token- or key-shaped secrets in titles, bodies and comments are masked with ingest's `mask`.
4. **Takedown:** unchanged from spike 2.

## Draft attribution line

> Issue text from the Mojang bug tracker (bugs.mojang.com), as collected in The Public Jira Dataset v7 by Lloyd Montgomery, Clara Lüders and Walid Maalej (Zenodo, doi:10.5281/zenodo.15719919, CC BY 4.0), described in "An Alternative Issue Tracking Dataset of Public Jira Repositories", MSR 2022, pp. 73–77. The text belongs to its authors; each record links to its source issue. Data collected in January 2022; changes to source issues after that date are not reflected.

Replace "the Mojang bug tracker (bugs.mojang.com)" with the chosen instance if the author picks another.
