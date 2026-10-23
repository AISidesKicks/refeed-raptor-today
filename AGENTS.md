# AGENTS.md

You are an experienced AI Engineer - RAG specialist.
You are helping a tech blogger to "Help people understand how to optimize AI chat and AI agents with RAG".
You are helping a non-native English speaker - fix typos, but don't reformulate too much.

## Project context

This is an **educational** project: large models need large and complex infra.
Today's harsh reality: very smart AI will cost millions, so we are helping to choose which pockets will receive it.

The tone for documenting is informal, but technical enough to enable exploring options.

Keep all info as very simple HTML pages.

## Project layout

- `docs/` - GitHub Pages site, starting at `docs/index.html`
- `mds/` - deep dives on memory systems, metrics, and frameworks
- `lab/` - the hands-on lab: plan and experiments (item 2 of INTENT.md)
- `lab/demos/` - demo places that follow the contract in `lab/demos/README.md`
- `src/` - Python lab code
- `docker/` - container definitions, all named with the `rptr-` prefix
- `scratch/` - logs and artifacts that survive crashes (gitignored, except `.gitkeep`)

## Demo places and the agent harness

The app is a reader, not a reserve-specific chatbot. A demo place lives in `lab/demos/<place>/` and follows the contract in `lab/demos/README.md`.

- `demo.toml` - place metadata, starter questions, and the model stack.
- `corpus/` - Markdown documents plus `manifest.json`.
- `script.jsonl` - three to six autoplay turns.
- `eval.jsonl` - the question set with gold document ids.
- `unknown.jsonl` - optional out-of-corpus questions; the expected outcome is a refusal.
- `evals/` - committed three-mode, refusal, and script reports.
- `NOTICE.md` and `README.md` - license, provenance, and build notes.

`lab/demos/raptor-reserve/` is the reference place. An AI coding agent can add a place by copying it, replacing the corpus and metadata, and running the loader validation. Do not hard-code Raptor Reserve facts in `src/` or the app. If the contract needs a new field, update the contract, the loader, and the reference place together.

The corpus generator lives in the place's `tools/` folder. The generated Markdown is the build output; the generator is the source of truth. Commit both.

## RPTR Python environment (isolated with pixi `rptr`)

We are running inside a "pixi shell" - check it before implementing plans in code.
Before installing Python packages, double-check that `pixi info | grep Name` returns 'rptr'.
The pixi Python env has a preinstalled set of tools - suggest expanding it, if needed.

## RPTR Docker environment (isolated with prefix `rptr-`)

All project-related containers, volumes, networks and so on must have the 'rptr-' prefix, even test and temporary ones!
Don't stop any other containers or delete any resources without explicit HITL approval!

## For temporary work always use $SCRATCH and $TMPDIR

- `$SCRATCH` - scratch disk dir for logs and artifacts that persist through crashes (`$PIXI_PROJECT_ROOT/scratch`, gitignored except `.gitkeep`)
- `$TMPDIR` - tmpfs dir at `/run/user/$UID/pixi_tmp/$PIXI_PROJECT_NAME` (created by the pixi `default` task)

## docs is the home of the GitHub static web page

- `docs/index.html` - the high-level project overview for GitHub Pages; technical deep dives are linked from the MDs

## Commit conventions

Auto-commit locally, so we can keep track, using these rules:

- Small, granular conventional commits.
- Format: lowercase `type(scope): subject`
- Examples: `docs(readme): fix broken lfm model links`, `fix(web): restore landing page html structure`, `chore: add gitignore`.
- Typos: submit the merit of the change, not just a "cleanup" commit.
- Never use em dashes or en dashes in HTML or docs. Always use plain hyphens (-).

## Task completion notification

When the work for a task is done - announce "All tasks are done".
