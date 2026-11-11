# Reflection on GenAI usage: Phase I (midpoint)

**AI-aided pair**

| First name | Last name | Student ID |
|---|---|---|
| Pavao | Kipson | k12337106 |
| Gergely | Terenyi | k12557665 |

Team: Mittens. Model: Maia-2. Question: when and why does Maia-2 fail to predict the human move?

The interactions this reflection refers to are recorded in [`ai-interactions/`](ai-interactions/).

## 1. How we used GenAI

We used Claude (claude.ai chat) in three roles.

1. **Scaffolding.** We gave it the repository of the human-only pair and the assignment text and asked for next steps. It read the other pair's results, proposed directions they had not covered (failure types, calibration per Elo, human mistakes against Maia failures, interactive charts) and generated two starter notebooks, `pavao.ipynb` and `colleague.ipynb`.
2. **Reviewing.** We asked it to audit the existing notebooks, including the ones it had generated itself, and to plan the next iteration.
3. **Building the deeper analysis.** From that audit it wrote `terenyi.ipynb`: ten hypotheses stated before looking at results, game-clustered confidence intervals, a Stockfish-based classification of misses, a noise-ceiling estimate, a counterfactual Elo experiment, a failure atlas, and a single-file interactive dashboard.

The AI never had our data. The Lichess dump, the Maia-2 weights and our parquet file were unreachable from its sandbox, so every notebook was written without being executed on real data. We ran everything ourselves.

## 2. Where it helped

**Speed and breadth.** The human-only pair produced one notebook with PCA/ICA projections, per-square heatmaps and two PDF reports. Within a few days we had three notebooks and a dashboard with ten tabs. Linked Plotly views, board rendering with arrows for Maia's move and the human move, and the HTML export are things we would not have built by hand in Phase I.

**Methodological criticism.** This was the most valuable part, more than the code. Examples from the log:

- It pointed out that positions from the same game are not independent, so with 670k positions from 10k games naive confidence intervals are too narrow. The notebook now bootstraps over games. On our data the endgame interval is about 36 % wider than the naive one.
- It caught a flaw in a finding from its own first notebook. "Maia predicts knight moves too often" had been measured only inside confident misses, a population selected for disagreement, which proves nothing about bias. Re-measured over all positions the bias is real but mostly an opening effect (+8.9 percentage points knight moves in the opening, +1.8 in the middlegame).
- It noted that Maia's value head predicts the human game outcome while the engine's win chance is an evaluation. They are different quantities, so the "gap" we had plotted is partly expected.
- It noted that the notebooks binned Elo differently from Maia-2's own categories, and that ratings below 1100 and above 2000 are clamped.

**Reframing the question.** The idea that a top-1 miss is not necessarily an error, and that it can be split with an engine into equally good alternatives, human errors and real Maia errors, came from the AI's plan. It turned out to be our strongest result: only 17 % of misses are real Maia errors.

**Matching the task wording.** When we asked whether the notebook satisfied the requirement to understand patterns in depth, it answered "only partly" and listed what was missing: the slices were identified but not explained. That honest self-assessment led to the slice dossiers, the sub-slice checks on held-out games and the input-space map.

## 3. Where it fell short

**Code that was confidently wrong.** None of the generated code had been run on real data, and it showed:

- The Maia-2 models were not set to evaluation mode in the Elo experiment. This does not crash. It silently gives slightly wrong probabilities. We only found it because a sanity cell compares the experiment at the true Elo against the stored predictions.
- `clock_frac` contained 698 infinite values, which broke the gradient boosting step.
- The Plotly renderer was not set for Jupyter, so figures did not display.
- A clock chart had its x-axis in the wrong order and needed a second prompt.
- A print label did not match the quantity it printed.

**Environment problems it could not see.** The prediction file was not in the repository, so we first had to write `run_maia.py`. Jupyter used a Python from another course without `pyarrow`. Our first full run was accidentally still on the 20k-position test subset. The AI could not have noticed any of these.

**Volume over understanding.** The AI produces analysis faster than we can absorb it. `terenyi.ipynb` has 54 cells and the dashboard is 21 MB. At the midpoint, the findings table at the end of that notebook and the summary section of `colleague.ipynb` are still empty templates, and several "verification" fields in our log still say `TO FILL`. The AI wrote the scaffolding for conclusions and even an "understanding protocol", but the conclusions themselves have to come from us, and we are behind on that. This is the main risk we see: a dashboard that looks finished can hide that the humans have not yet looked at every tab critically.

**Generic first drafts.** The first two notebooks were sensible but obvious (accuracy by Elo, reliability diagrams). The specific, chess-aware questions only appeared after we pushed back with the task text and asked for a critique.

**Text style.** Its markdown was long and full of hedged, textbook-style explanations. In `pavao.ipynb` we shortened all of it and wrote the findings ourselves.

## 4. Compared with the human-only pair

| | Human-only pair | AI-aided pair |
|---|---|---|
| Output | 1 notebook, 2 PDF reports, heatmaps | 3 notebooks, 7 static figures, 1 interactive dashboard |
| Strength | Every figure was designed and understood by its authors. The per-square heatmap and the `Nf3` versus `e4` table are concrete and easy to explain. | Wider coverage, statistical care (clustered intervals, held-out checks), an external reference (Stockfish), interactivity |
| Weakness | No uncertainty estimates, no check whether a miss is an error | Much unverified output, findings not yet written down, harder to explain every chart |

The two approaches complement each other. The human-only pair found the concrete phenomenon (opening failures concentrated on a few squares). The AI-aided analysis then showed what kind of failure it is and how much of it is real.

## 5. What we learned and will change in Phase II

1. **Demand sanity checks with the code.** The checks the AI wrote on request (reproduce known accuracies, compare against stored predictions, hand-verify one consensus position) caught the worst bug. We will ask for them every time.
2. **Give the AI real outputs.** Pasting actual tables back into the chat produced much better follow-ups than letting it reason from code alone.
3. **Ask it to criticise before asking it to build.** The audit prompts gave more value per minute than the generation prompts.
4. **Limit scope.** We will ask for one question per notebook and write the finding before generating the next analysis.
5. **Log as we go.** The CSV log written from inside the notebook worked well. Filling in the verification column afterwards did not, so in Phase II we will fill it in the same session.

## 6. Verification status at the midpoint

| Item | Status |
|---|---|
| Row counts and top-1 / top-3 accuracy match across all notebooks (0.498 / 0.780) | checked |
| Clustered intervals are wider than naive ones | checked |
| Leave-one-out consensus hand-verified on the starting position | checked |
| Elo experiment reproduces stored probabilities at the true Elo (max difference 0.0) | checked, after fixing eval mode |
| Stockfish categories inspected by eye on sample boards | partly, trusted |
| Failure-mode clusters, input-space regions and slice dossiers read critically | not yet done |
