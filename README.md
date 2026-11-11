# Mittens: When and why does Maia-2 fail to predict the human move?

Group project for *AI and Visualization* (JKU, 2026W), topic **Vis4AI**.
This repository holds Phase I ("How does the model behave?"), where the model is treated as a black box: we only look at its inputs and outputs.

**Phase I progress-update video (4:22):** https://drive.google.com/file/d/10iCEhxn686TU112FLxBlrJO6P4LKW_je/view?usp=sharing

## Task

Maia-2 is a chess model that does not try to play the best move. It tries to predict the move a **human of a given rating** would play. Its headline number is top-1 move-matching accuracy, which is about 50 %. That single number hides most of the interesting behaviour, so our shared question is:

> **When and why does Maia-2 fail to predict the human move, and is a "failure" actually an error?**

Two pairs worked on this question independently, as required by the course: one pair without GenAI and one pair with GenAI.

## Model

| | |
|---|---|
| Model | [Maia-2](https://github.com/CSSLab/maia2) (`pip install maia2`), pretrained `blitz` and `rapid` checkpoints |
| Input | One board position (mirrored so the side to move is always White), the mover's Elo category and the opponent's Elo category. No clock and no move history. |
| Output | A probability distribution over legal moves (policy head) and a win probability for the side to move (value head) |
| Elo categories | 11 buckets: `<1100`, `1100-1199`, …, `1900-1999`, `>=2000` (ratings outside this range are clamped) |
| Access | Black box only. We feed positions and Elo labels and read the outputs. No weights or activations are inspected in Phase I. |

## Dataset

| | |
|---|---|
| Source | [Lichess open database](https://database.lichess.org/), rated standard games, **June 2024** |
| Selection | First 10,000 games that have engine evaluations, at least 20 plies, both ratings between 600 and 2800, and a blitz or rapid time control |
| Size | **10,000 games, 676,579 positions** (669,759 non-forced, i.e. with more than one legal move) |
| Per position | FEN, move played, both Elos, clock before the move, time spent, game phase, number of legal moves, material, Lichess engine evaluation before and after, win-chance drop and move quality (good / inaccuracy / mistake / blunder) |
| Model outputs | Maia-2 top-1 to top-5 moves, probability of the top move, probability and rank of the human move, entropy, value head |
| Extra labels | Stockfish (depth 12) on a stratified sample of 24,000 positions, evaluating the best move, the human move and Maia's move |

Files: [`non-ai-phase1/data/games_2024-06.parquet`](non-ai-phase1/data/games_2024-06.parquet) and [`non-ai-phase1/data/moves_2024-06.parquet`](non-ai-phase1/data/moves_2024-06.parquet).
The file with Maia-2 predictions (`moves_maia_2024-06.parquet`) is too large for the repository and is regenerated with `python ai-phase1/run_maia.py`.

**Known limits of the dataset.** Only games with Lichess engine analysis are included, which is a selected subset of all games. Positions within one game are not independent, so the AI-aided notebook reports game-clustered bootstrap confidence intervals.

## Repository layout

```
README.md                    this file
team-info.json               team members
workload.json                workload split
ai_reflection_midpoint.md    reflection on GenAI usage in Phase I
ai-interactions/             record of GenAI interactions
non-ai-phase1/               human-only pair
  code-phase1.ipynb            data extraction, Maia-2 inference, visualizations
  maia2_phase_report.pdf       failures by game phase
  maia2_time_pressure_report.pdf   failures by time pressure
  maia2_square_diff_failures.png   per-square human-minus-Maia heatmaps
  maia2_opening_failure_pairs.csv  most common (Maia move, human move) pairs in the opening
ai-phase1/                   AI-aided pair
  run_maia.py                  reproduces the Maia-2 predictions used by both pairs
  pavao.ipynb                  failure types, confident misses, interactive explorer
  colleague.ipynb              calibration, human mistakes, value head
  terenyi.ipynb                hypothesis-driven analysis and dashboard
  sf_worker.py                 Stockfish worker used by terenyi.ipynb
  figures/                     static figures
  ai_phase1_out/maia2_failure_atlas.html   interactive dashboard (self-contained, about 21 MB)
```

## Phase I results in short

Overall: top-1 accuracy 49.8 %, top-3 78.0 %, top-5 87.8 % on non-forced positions.

**Human-only pair** (phase, time pressure, board geometry)

- Failure depends on the game phase: opening 55 %, middlegame 49 %, endgame 45 %.
- Time pressure has almost no effect in the middlegame and endgame: 48 % with more than a minute left, 46 % with 30 to 60 s, 47 % with under 30 s.
- The per-square heatmaps show where the disagreement sits. In the opening Maia-2 sends pieces to f3 far more often than humans do, while humans push the central pawns to c4, d4, e4 and f4.
- The single most common opening failure is Maia-2 predicting `Nf3` where the human plays `e4` (6,266 cases, 4.7 % of all opening failures). Maia-2 gives the human move only 2.5 % there.

**AI-aided pair** (what kind of failure, and is it an error?)

- Failure types: 28.3 % near misses (human move ranked 2 or 3), 19.0 % far misses, 2.9 % confident misses (Maia at least 60 % sure and the human move outside the top 3). The extra opening failures are far misses.
- Maia-2 is slightly overconfident in every Elo group (ECE 0.037 to 0.053), most in the opening (0.055) and for players rated 2000 and above.
- Maia-2 fails on 44 % of good human moves but on 77 % of blunders. It models typical play much better than human error.
- Stockfish check on 24,000 positions: only **17 % of misses are real Maia errors**. 40 % are equally good alternatives, 25 % are human errors where Maia's move was sound, 18 % are cases where both moves are inaccurate.
- Maia-2 cannot see the clock or the move history. Recaptures fail in only 8 to 15 % of cases, other moves in 47 to 59 %. Maia's uncertainty tracks human think-time only weakly (Spearman 0.13 to 0.29 outside the opening).
- Style bias over all positions: in the opening Maia-2 plays 8.9 percentage points more knight moves and 10.3 points fewer pawn moves than humans. It predicts captures 3.6 to 6.4 points too often in every phase.
- Failure is partly predictable from the situation alone: AUC 0.70 from position, player and clock features, 0.77 when Maia's own confidence is added.

**Open question for Phase II.** Maia-2 fails on 95 % of first moves, because it prefers `Nf3` in the starting position while 61 % of our games start with `e4`. The predictions match the official `maia2` inference function on a 2,000-position sample, so this looks like model behaviour, but we still want to rule out an input-encoding problem before we build on it. Without the first move the opening failure rate is 54 % instead of 55 %.

## Reproducing

```bash
pip install maia2 chess zstandard pandas pyarrow requests tqdm scikit-learn plotly matplotlib seaborn
python ai-phase1/run_maia.py        # writes ai-phase1/data/moves_maia_2024-06.parquet
```

Then run the notebooks. `terenyi.ipynb` needs a `stockfish` binary on the PATH for its section 2 and skips that section otherwise.
