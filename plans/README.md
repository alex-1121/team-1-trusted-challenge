# Plans

How planning works here.

- One markdown file per plan in `plans/`, named `YYYY-MM-DD-topic.md`.
- Comments go as PR review comments, or inline as lines starting with `> note (name):`.
- A plan is adopted when its status line says "adopted" and a row lands in `../decisions.md`.
- The spec and tickets will be produced with the grill-with-docs, to-spec and to-tickets flow and land here.

## Reviews of a plan

A review goes at the end of the plan file as its own section, so the author's text stays untouched and readers see the plan first.

- Heading: `## Review: <who>, <date>`. Say who reviewed (a teammate by name, or the model, run by whom) and that nothing in the section is a team decision.
- First line: **Verdict** in one sentence (GO, RESHAPE or KILL, and why).
- Then one short paragraph per finding, at most five, each with a bold lead of two or three words and no more than four sentences. Say what is wrong, why it matters, and the fix.
- Last line: "Not checked:" with what the review could not test.
- Plain words. Explain a term the first time it appears. No em-dash.
- Short comments on a single line still use `> note (name):` inline.

Example: the review section at the end of `2026-11-06-query-vault.md`.
