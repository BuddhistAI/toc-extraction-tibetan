# Notes for agents working in this repo

## Start here (every BuddhistAI repo)

- Read the maintainer handbook first: https://buddhistai.github.io/knowledge-base/handbook/ (source: BuddhistAI/knowledge-base `handbook/`). Follow its rules and conventions.
- Check the Development board for cards assigned to you: https://github.com/orgs/BuddhistAI/projects/3. Status and next steps: `handbook/status.md`.
- Rules: plain English for non-native readers, no idioms. "Buddhist tasks", not only texts. "Top performance" and "Best value". Neutral credits: WeBuddhist is one contributor among others. Never invent data, scores, votes or links. Never edit generated files by hand.
- buddhist-benchmarks stays clean (short `result.json`, outputs, scores). Provenance records (`buddhistai/provenance@1`) live in the skill's own repo.
- When you change something the handbook describes, update the handbook in the same pull request.
- Any change users see follows EGM: see "Changes users see" below.
- This repo: the workshop repo for the `toc-extraction-tibetan` skill: variants, runs, provenance records and `REPORT.md`. It holds no test data (the benchmark is pinned in `benchmark/benchmark.json`). Run each variant at least 3 times, never tune on the test set, and check records with `python scripts/provenance.py --check`.

## Changes users see: follow EGM

This covers pages, forms, install steps, app screens and the words on them. A text or bug fix you can describe in two sentences skips this: tick "Small change" in the pull request. Everything runs in your own Claude session. No API key is needed.

1. **Install EGM** if `/egm:egm-draft` is missing: `claude plugin marketplace add google/elephant-goldfish-model`, then `claude plugin install egm@egm`.
2. **Elephant: design first, no code.** Use the `buddhistai-elephant` skill to load the context. Then write the design in `docs/designs/<yyyy-mm-dd>-<slug>.md` from knowledge-base `docs/designs/TEMPLATE.md`. Name the journeys and pages it changes.
3. **Goldfish: review in this session.** Use the `buddhistai-ux-review` skill. It runs EGM `egm-review-loop` with EGM's reviewers plus the persona files of those journeys (knowledge-base `ux/personas/`) as fresh subagents.
4. **Fix and repeat** until two rounds in a row are clean (no open Blocker or Major finding), at most 5 rounds. Run EGM in its uninterrupted mode where it has one. Resolve findings yourself. Do not ask about each finding one at a time, even if an EGM skill says to.
5. **Ask only real product decisions, once.** Answer gaps yourself from the code, the knowledge base, the handbook, the personas and the journeys, and say which source you used. Ask the developer only about choices that no source settles: what to build, for whom, trade-offs, words that change meaning. Put them in one short list with your recommendation for each. Then the developer approves the design.
6. **Build to the design.** Link it in the pull request under "EGM review". If journey steps changed, update knowledge-base `ux/journeys/`.

If this repo has no `.claude/skills/buddhistai-*`, read them from https://github.com/BuddhistAI/knowledge-base/tree/main/.claude/skills. The `egm-review` label on a pull request runs one more review in CI when the org key is set. That review is optional. Details: handbook `ux.md`.

EGM artifact directory: docs/designs
