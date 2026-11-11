# GenAI interaction record: Phase I

Only the AI-aided pair used GenAI for the analysis. The human-only pair (`non-ai-phase1/`) did not.

| File | Who | Tool | What it covers |
|---|---|---|---|
| [`2026-11-08_pavao_claude_notebook-scaffold.md`](2026-11-08_pavao_claude_notebook-scaffold.md) | Pavao Kipson | Claude (chat) | Starter notebooks `pavao.ipynb` and `colleague.ipynb`: prompts, what was kept, what was changed, problems |
| [`2026-11-09_terenyi_claude_notebook-log.csv`](2026-11-09_terenyi_claude_notebook-log.csv) | Terenyi | Claude (chat) | Step-by-step log for `terenyi.ipynb`: planning, review of the earlier notebooks, generation, self-assessment against the task text, human verification notes |

The CSV has one row per interaction with the columns `id, date, step, tool, prompt_summary, ai_output_summary, human_decision, verification`. It is written by `log_ai()` inside `ai-phase1/terenyi.ipynb` (the working copy is `ai-phase1/ai_phase1_out/ai_log.csv`) and is also shown in the *AI log* tab of the dashboard.

Our reflection on these interactions is in [`../ai_reflection_midpoint.md`](../ai_reflection_midpoint.md).
