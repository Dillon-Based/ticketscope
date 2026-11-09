# Spike 3.3 findings: choose the embedding model

Run on 2026-11-09 against snapshot `2026.11.1` (32,153 issues loaded on the local kind cluster), scoring all 10,473 labelled pairs (10,164 `short`, 309 `log_heavy`). Same scoring as the eval job: cluster relevance, k=10, query issue excluded, query = title + description, queries embedded live. Harness: `scripts/embedding_spike.py` (host process against kind's Postgres; vectors were stored in `issue_embedding` under each model id and removed afterwards).

## Recommendation

**Keep `BAAI/bge-small-en-v1.5` with preprocessing version `pre1.kind2-t3.outcome3.emb1`** (title + description, cut at 2000 characters). No follow-up change is needed.

Why: bge-small has the best dense quality overall and on `log_heavy`, and ties all-MiniLM-L6-v2 on hybrid, the mode most likely to ship as the default. MiniLM embeds about 4.6 times faster but has a 256-token limit that truncates 8.2% of issues (bge: 3.5% at 512), and it is clearly weaker on `log_heavy` dense. arctic-embed-xs is worse on every quality measure. Embedding time is a one-off build cost (the asset is precomputed), so speed does not outweigh quality here.

## Quality: Recall@10 / MRR@10

| Model | Mode | Overall | short | log_heavy |
|---|---|---|---|---|
| (none) | keyword | 0.771 / 0.550 | 0.769 / 0.547 | 0.822 / 0.679 |
| bge-small-en-v1.5 | dense | **0.796 / 0.579** | **0.796 / 0.576** | **0.806 / 0.653** |
| bge-small-en-v1.5 | hybrid | **0.817** / 0.594 | **0.815** / 0.590 | **0.880 / 0.711** |
| all-MiniLM-L6-v2 | dense | 0.793 / 0.572 | 0.795 / 0.572 | 0.748 / 0.601 |
| all-MiniLM-L6-v2 | hybrid | 0.815 / **0.597** | 0.814 / **0.594** | 0.858 / 0.684 |
| arctic-embed-xs | dense | 0.753 / 0.537 | 0.753 / 0.535 | 0.748 / 0.598 |
| arctic-embed-xs | hybrid | 0.805 / 0.578 | 0.803 / 0.574 | 0.864 / 0.693 |

Recall@1 overall, hybrid: bge 0.480, MiniLM 0.486, arctic 0.464.

- Hybrid beats keyword and dense for every model overall. Dense alone beats keyword overall for bge and MiniLM, but not on `log_heavy`, where keyword (0.822 / 0.679) beats every dense run.
- The bge and MiniLM hybrid results are a tie (0.002 apart overall).
- **`log_heavy` has only 309 pairs**, so its figures carry roughly ±4.5 points of sampling error at 95% confidence. The bge versus MiniLM `log_heavy` gap (0.806 vs 0.748 dense) is suggestive, not conclusive.

## Cost

| Model | Dim | Token limit | Issues cut by the limit (of 32,153) | Embed time per issue / whole snapshot | Model size on disk | Memory after model load (process, MB) |
|---|---|---|---|---|---|---|
| bge-small-en-v1.5 | 384 | 512 | 1,129 (3.5%) | 35.7 ms / 1,146 s | 67 MB | 370 (baseline 193) |
| all-MiniLM-L6-v2 | 384 | 256 | 2,643 (8.2%) | 7.7 ms / 248 s | 90 MB | 378 |
| arctic-embed-xs | 384 | 512 | 1,129 (3.5%) | 11.8 ms / 380 s | 90 MB | 372 |

Dense query latency p95 (in-process, includes live query embedding and a 32k-row exact scan): bge 139 ms, MiniLM 119 ms, arctic 119 ms. Hybrid p95: 172, 146, 146 ms. Keyword p95: 58 ms.

Image size: the model files sit on top of the 190 MB app image. Sizes above are the models' published sizes (the cache directories measured about twice that, from fastembed's duplicate blob and snapshot copies).

## Limits of this run (read before relying on the cost numbers)

- **Host, not kind.** The ticket asked for the eval on kind with each model. This ran on the host against kind's Postgres to avoid three image rebuilds and three loads of up to 50 minutes each. Quality scores are unaffected. Timings and memory are not api/load pod figures.
- **Timings are noisy.** The machine was running other work. A separate 2,000-issue re-measure gave bge 68.6 ms, arctic 27.3 ms and MiniLM 11.7 ms per issue, so the ordering holds but the absolute values do not.
- **Memory is an upper bound for the model.** Peak process memory (760 to 1,122 MB in the re-measure, over 2,000 issues) includes the harness holding all issue texts and the tokenizer pass, so it says little about the api's needs. The model-attributable part is about 130 to 185 MB after load plus inference workspace. Epic 5's sizing should be measured in the api pod when story 4 sets the chart defaults.
- **The cut was tested, not varied.** Truncation counts at each model's token limit come from tokenizing the 2000-character text. No other cut length was scored, so the `emb1` rule is unchanged rather than tuned.
- Two other fastembed candidates were not run: `jinaai/jina-embeddings-v2-small-en` and `snowflake/snowflake-arctic-embed-s`.

## For the person recording the decision

Record in the epic's Notes a Decision line along the lines of: model `BAAI/bge-small-en-v1.5`, preprocessing `pre1.kind2-t3.outcome3.emb1`, chosen by spike 3.3 (see this file). Story 4 can then build the asset with these ids, and the default retrieval mode will most likely be hybrid.
