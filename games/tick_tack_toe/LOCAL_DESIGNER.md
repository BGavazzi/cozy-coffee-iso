# Local discovery designer

The optional designer uses a local Ollama server to propose structured concepts.
It does not modify the game, execute model output, admit canon, or render art.

```text
ollama pull qwen3:4b
python tools/local_designer.py "Mimic Toe" "Brood Tick" --out proposal.json
# Keep a replayable provenance record beside the raw proposal:
python tools/local_designer.py "Mimic Toe" "Brood Tick" --out proposal.json \
  --record out/games/tick_tack_toe/proposal-record.json
```

The output is constrained to a small JSON schema: one trigger, one target, one
bounded effect, a cost from 1–4, and a base mesh family with at most three
approved attachments. A separate validator must map it to an implemented rule
template before the café factory is invoked. Unknown effects are rejected.

The intended batch workflow is:

1. Generate proposals offline and cache the prompt, model tag, parent pair, and output.
2. Reject malformed, duplicate, recursive, or unimplemented effects.
3. Reject a proposal that reuses a parent name or merely restates a documented parent interaction;
   the admission gate currently knows the Tick + Toe feeding/reproduction pair.
4. Simulate the surviving mechanic against seeded runs.
5. Add an explicit recipe entry and visual review record.
6. Render through `game_factory.py`; never render arbitrary model text directly.

For a proposal that survives those steps, `tools/promote_game_content.py`
records the final decision only when admission, 100+ bounded simulation runs,
technical art checks, and visual approval all agree. It writes a ledger entry;
it does not edit the game's catalog. The simulation evidence is deliberately
small and machine-readable, for example:

```json
{"status":"passed","runs":100,"failures":0,"bounded":true}
```

Run the deterministic admission audit before simulation:

```text
python tools/audit_benchmark.py games/tick_tack_toe/local-designer-benchmark.json \
  --out games/tick_tack_toe/local-designer-admission.json
# A single proposal can carry its parent pair explicitly:
python tools/admit_proposal.py proposal.json --parents "Tick" "Toe"
# Or save the same decision in the envelope consumed by promotion tooling:
python tools/admit_proposal.py proposal.json --parents "Tick" "Toe" \
  --out admission.json
```

The audit currently classifies proposals as `rejected`, `needs_authoring`, or
`eligible_for_simulation`. The 7B benchmark produced 4 rejected and 16
needs-authoring proposals; none was allowed directly into simulation. That is
the intended result while runtime templates are still authored by hand.

Eligibility also checks body-family compatibility, not only the trigger/effect
opcode. For example, `after_steps:spawn_tick` and `after_steps:spawn_tack` are
Egg-hatch behaviors, `on_eaten:spawn_tick` belongs to a Toe, and
`on_feed:spawn_egg` belongs to a Tick. The first newly authored template,
`after_steps:move_self`, belongs to a Tack and is implemented as a single
bounded adjacent shift. An otherwise valid proposal on the wrong body is
returned to `needs_authoring`. This prevents the factory from rendering an
attractive asset for a mechanic the game cannot execute.

The targeted prompt now states that mapping and asks the concept to name its
effect. Recent local probes nevertheless returned a schema-token concept,
parent-name duplication, and duplicate art attachments across three models;
the deterministic gate rejected all of them. Keep these failures in the ledger
as model-quality evidence rather than weakening the novelty or semantic checks.

A subsequent strengthened-prompt run produced `Nest Guardian`, a
body-compatible `on_feed:spawn_egg` proposal. Its `fertile-feed-v1` runtime
probe passed 100/100 seeded runs and its procedural render had no technical
blockers, but a runtime-novelty check rejected it as a duplicate of the base
fertile Tick behavior. The render and simulation remain retained evidence, not
promotion input.

The first novel executable control row is `Blink Tack`: its proposal envelope,
`blink-once-v1` admission, 100-run runtime evidence, procedural build and
joined record are retained under `out/games/tick_tack_toe/` (the exact paths
are listed in `NEXT_TASKS.md`). Its sprite is awaiting a human visual decision;
no catalog mutation or export occurs before that gate.

The expanded targeted prompt was re-run with `qwen2.5:7b` on Snare Tack +
Lure after the relocation template was authored. The model returned
`Whispering Snares`, a schema-valid `after_steps:spawn_tack` proposal whose
concept described a Lure moving and spawning a snare, while its body was a
Tick. Admission rejected it for effect/prose mismatch before any render. This
is retained as `out/games/tick_tack_toe/blink-local-proposal.json` and shows
that adding an executable template to the prompt does not guarantee that a
small local model selects it or keeps body/effect semantics aligned.

An additional prompt sentence naming the exact `Tack`/`adjacent_empty` mapping
improved the body choice but not the opcode: the next sample (`Tick Tack Sway`)
used a Tack while selecting `after_steps:remove_enemy`. It is therefore
`needs_authoring`, another clean example that schema validity and partial
semantic alignment are not enough for factory admission.

The `qwen2.5-coder:7b` targeted benchmark (six pairs, 2026-09-13) returned
6/6 schema-valid rows. Before the quality patch, two looked eligible:
`Egg's Nest` was a field-list disguised as a concept and `Glimmer Tack` was a
second name for the already-authored relocation signature. The admission gate
now rejects schema-token leakage (`after_steps`, `on_feed`, `base_kind`, and
similar field/opcode combinations) as non-player-facing prose. The rerun
produced five `needs_authoring`/rejected rows and no new executable candidate;
the strongest remaining failure was generic or wrong-body opcode selection.
This is useful evidence that a small model can satisfy JSON formatting much
more reliably than it can produce novel, body-compatible, player-legible
mechanics. Raw rerun evidence is kept at
`out/games/tick_tack_toe/local-targeted-coder-2026-09-13-rerun.json`.

The model is a creative search aid, not a rules engine. Keep Ollama bound to
localhost; do not expose it from the hosted game.

To inspect a directory of records during a bounded generation cycle, use the
read-only queue audit. It counts proposal-only records, admission outcomes, and
promotion gate failures without changing the catalog:

```text
python tools/audit_promotion_queue.py out/games/tick_tack_toe \
  --out out/games/tick_tack_toe/promotion-queue-audit.json
```

Benchmark/admission files with a `rows` array are expanded into individual
queue entries, so a batch cannot hide rejected or needs-authoring proposals
behind an otherwise ignored filename. The raw batch file remains unchanged.

## First local benchmark

On September 8, 2026, the installed `qwen2.5:7b` produced 20/20 schema-valid
proposals across the bounded pair list. Mean latency was 6.07 seconds (range
3.14–12.77 seconds). A five-pair smoke test with `qwen2.5-coder:1.5b-base`
also produced 5/5 valid JSON responses, but its names and concepts were much
less coherent (`X`, `TICK`, and generic `Egg` outputs). Treat the 1.5B model as
a parser/format experiment, not the creative baseline.

Raw local-only results are kept at:

- `games/tick_tack_toe/local-designer-benchmark.json`
- `games/tick_tack_toe/local-designer-benchmark-1.5b.json`
- `games/tick_tack_toe/local-designer-admission.json`
- `games/tick_tack_toe/local-designer-admission-1.5b.json`

A live localhost run on September 10, 2026, asked the 1.5B model for Tick +
Toe. It returned a schema-valid but redundant `after_steps: move_self` Tick;
the admission gate classified it as `needs_authoring` rather than letting it
become canon. This is the desired failure mode: format validity is not novelty,
and a familiar mechanic is not silently promoted just because the model emitted
valid JSON. The scratch output is under `out/games/tick_tack_toe/` and is
intentionally not a catalog entry.
