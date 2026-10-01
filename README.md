# Next Best Action v3 — Wealthsimple case study

I built and evaluated a LightGBM next-best-action system for Wealthsimple’s personalized recommendations, then productionized its training pipeline. The project replaces an existing prompt-based LLM propensity ranker with a model learned from historical client–action outcomes.

**[Read or download the six-page PDF](next-best-action-case-study.pdf)** · **[Read the case study on GitHub](CASE_STUDY.md)**

![Matched offline benchmark: Precision@4 improved from 0.126 for the LLM to 0.186 for LightGBM](assets/precision-at-4.svg)

The matched offline benchmark improved **Precision@4 from 0.126 to 0.186 (+47.6% relative)**. NDCG@4 improved from 0.310 to 0.452. These measure recovery of historically completed actions in the evaluated cohort; they do not establish live conversion or deposit lift.

The case study covers:

- Why we replaced v2, the model’s data grain, and metrics matched to the recommendation surface.
- Point-in-time features, label construction, rare-positive training, benchmarking, and statistical backtesting.
- Per-action recommendation-volume analysis and a sparse web-intent feature ablation.
- Production training validation, followed by the remaining inference rollout work.
- A contextual-bandit decision layer to address policy-driven feedback loops.
- Gaps in exposure telemetry and the distinction between adoption propensity, financial value, and behavioral value.

**Status:** the documented production training run completed across 856,889 users with held-out ROC-AUC 0.906. Customer-facing inference validation and live bandit learning remain separate milestones in the reviewed project notes.

## Supplementary workspace

[Next Best Action (NBA) v3 Ranking System Workspace on Notion](https://app.notion.com/p/Next-Best-Action-NBA-v3-Ranking-System-Workspace-3b1d597724dd8008b43ddaf6059ae088?source=copy_link)

The workspace is an evolving technical record. The PDF provides a standalone reading path and distinguishes earlier prototypes, measured results, and work in progress. Notion access depends on the page’s sharing settings.

Source notes used: **NBA Universal evaluation metrics** (headline benchmark chart), **NBA v3 Backtesting / Statistical Testing Strategy** (per-action intervals), **NBA v3 Refactoring & Deployment** (binary model, scale run, intent ablation), **Funding → Premium+ Acceleration Deep dive analysis** (persona analysis), **Contextual Bandit** (staging evaluation), and **NBA metric & data enhancement** (value target and telemetry gaps).

## Rebuild the document

The narrative is maintained in `case-study.json`. The generator creates the PDF, Markdown case study, and SVG chart from that reviewed source.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python build_case_study.py
```

This repository contains a project narrative and regenerated figures. It does not include client data, employer source code, or model artifacts.
