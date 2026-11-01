# FIN 377 Final Project: Rules and Standards

Source: course "Final Project Seeds" handout (Sep 2026).

## About the seeds

The seeds are starting points, not assignments. A good project usually starts
from one of them and gets narrower. Students may also bring their own idea.
Either way, talk to the professor early.

Each seed lists:
- the question
- who would pay for the answer
- one row of the final dataset
- free data checked as reachable (as of Sep 2026)
- the method (tools from this class)
- a dashboard idea
- a minimum viable version (about two weeks of work)
- stretch goals
- what the auditors will poke at

## The standard

The repo, dashboard, and analysis will be interrogated by state-of-the-art AI
agents and by the professor. They will clone the repo, rerun it, recompute the
numbers, and look for the problems that sink real research.

### What gets checked on every project

| # | Check | What it means |
|---|-------|---------------|
| 1 | **It reproduces** | `run_all.py` (or the README's steps) rebuilds every table and figure from the raw inputs, on a fresh machine, with no hand edits. Every number in the slides and dashboard comes from a file in `outputs/`. |
| 2 | **Every input has a provenance** | For each raw file: where it came from, when it was pulled, and the code (or link) that gets it again. |
| 3 | **Correct unit of observation** | Keys are unique (assert it), and merges use `validate=`. You can say what one row is. |
| 4 | **No look-ahead** | At each date, use only information that was public then. Watch for restated financials, today's index membership used for past years (survivorship), and fiscal-year dates vs. filing dates. |
| 5 | **No LLM leakage** | An LLM may already "know" what happened after a headline. Test on dates after the model's training cutoff, or show it doesn't matter. |
| 6 | **No p-hacking** | Keep a log (`specs_tried.md`) of every specification run, not just the one that worked. Report how many things were tried. |
| 7 | **Magnitudes, not just stars** | Is the effect big enough to matter to the person who'd pay for it? After trading costs, if it's a strategy? |
| 8 | **Checks by hand** | At least one number in each pipeline step is recomputed independently and matches (like HW6 Step 3). |
| 9 | **Honest limits** | A "Threats to validity" section in the README. A problem the auditor finds that was already disclosed is much less of a problem. |
| 10 | **You understand it** | Every teammate can explain every step, including parts an agent wrote. Expect questions. |
| 11 | **Red-team yourself first** | Before each checkpoint, run the *Skeptical review* prompt from the Quick Reference (Starter prompts for coding agents, #5) on the repo and fix what it finds. The auditors will be at least that skeptical. |
