# Bounded Emergent Content Factories for Games

## Working research question

How can a local AI content factory propose novel game rules and matching visual
assets at live-service scale while preserving readability, bounded execution,
player agency, style coherence, and economically sustainable production cost?

The thesis contribution is the constrained generation-and-evaluation system,
not the Tick Tack Toe prototype by itself. The game is a reproducible testbed:
the same proposal can be admitted, simulated, rendered, reviewed, promoted, or
rejected with an auditable reason.

## Experimental platform

- **Rule proposals:** a local Ollama model emits one JSON proposal from an
  allowlisted grammar (trigger, target, effect, cost, base body, attachments).
- **Mechanic compiler:** human-authored templates map eligible proposals to
  executable rules; arbitrary model code is never run.
- **Simulation:** seeded expeditions check termination, loop freedom, resource
  bounds, and degenerate strategies before visual work begins.
- **Asset factory:** the proposal's body and attachments select deterministic
  procedural geometry, rendered through the café factory's palette, camera,
  pixelization, and technical review gates.
- **Promotion:** proposal, simulation, render, technical review, visual review,
  and explicit canon approval remain separate lifecycle states.
- **Factory record join:** each proposal can be joined to its admission, build,
  export, and asset hashes without promoting across a failed gate. A rejected
  proposal therefore records `not_attempted` downstream stages even when an
  unrelated asset with the same base kind already exists.
- **Joined record command:** `tools/join_factory_record.py` produces one
  auditable row from proposal, admission, build, and export JSON. It reports a
  matching asset only as a candidate for an eligible proposal; rejected or
  authoring-needed proposals cannot inherit a same-named reviewed sprite.

## Variables and measures

Compare four authority levels:

1. human-authored recipe;
2. local-model proposal + deterministic validation;
3. proposal + simulation + visual review + player vote;
4. automatic promotion after all machine gates.

For each generated candidate record:

- novelty relative to parent signatures and prior catalog;
- rule readability (effect, timing, target, cost understood by a player);
- meaningful decision value (not a renamed or duplicated parent);
- boundedness (maximum steps, targets, spawned pieces, and no recursion);
- visual legibility and style distance from the approved palette/silhouette;
- player utility: choice rate, repeat use, perceived agency, and return intent;
- production cost: model latency, CPU/GPU seconds, queue time, storage, and
  human review minutes;
- rejection reasons and defect leakage at every gate.

The first live signal is already informative: a fresh ten-pair `qwen2.5:7b`
batch was 10/10 schema-valid, but the deterministic admission audit classified
6 as `needs_authoring` and 4 as `rejected`. A second twenty-pair batch was also
20/20 schema-valid, with 11 `needs_authoring` and 9 `rejected`. Format
compliance therefore cannot stand in for novelty or fun: in these two samples,
zero proposals were directly eligible for simulation.

A third local-only rerun with `qwen2.5-coder:1.5b-base` was 8/8 schema-valid,
with 3 `needs_authoring` and 5 `rejected`; it also produced zero directly
simulatable proposals. Across the three batches (38 total proposals), the
current allowlisted runtime vocabulary has admitted none. This is a measured
boundary, not a reason to loosen the gate: either the proposal prompt needs to
target the implemented templates, or the next runtime template must earn its
way in through an authored rule and bounded simulation.

## Targeted-prompt admission experiment (2026-09-12)

To separate prompt discoverability from gate quality, an 8-pair batch asked the
same local model to choose only one of the five currently simulatable
trigger/effect templates. Before semantic checks, 3/8 rows were structurally
eligible. The strengthened deterministic gate then rejected all 8: model names
such as `spawn_tick` and `after_steps`, generic concepts such as `a game piece`,
and duplicate art attachments are not useful discoveries even when their
runtime opcode is executable.

This is the desired factory behavior. A targeted prompt can raise the apparent
admission rate without producing player-facing novelty; semantic naming and
concept checks prevent that false positive from consuming simulation, render,
or human-review budget. The experiment therefore leaves the eligible-sample
queue open rather than manufacturing a candidate.

After the prompt was strengthened to request a noun phrase and a concrete
decision sentence, a second 8-pair targeted batch produced 2 structurally
eligible rows and 1 authoring-needed row. The semantic gate rejected the two
apparent eligibles (`TickTackToe`/`Tick`) for generic names or concepts, leaving
0/8 promotable. This is a useful prompt–gate interaction result: better prompt
instructions reduced, but did not eliminate, the need for deterministic
semantic review.

A human-authored `Hatchery Trap` control row was then joined against the real
 factory batch. Its `after_steps:spawn_egg` template is eligible, its reviewed
 sprite is linked by build key `016fa9c87986c0812a23` and canonical pixel hash,
 and simulation remains explicitly `awaiting`. This exercises the complete
 evidence join without pretending that visual approval substitutes for a
 mechanic simulation or that the control row came from the local model.

## Constraints learned from playtests

- A larger board is more forgiving when rival pressure does not scale with it;
  win rate and opening clears must be measured, not assumed to be fun.
- Discovery needs visible parent-to-child affordances and a reason to try the
  next combination; a timer alone creates waiting, not anticipation.
- Composed rules should combine bounded clauses, not create recursive chains.
- Art must be generated from the same semantic definition as the mechanic;
  otherwise a valid rule can ship with an unreadable or misleading portrait.
- Queue scarcity is a production constraint and a pacing tool, but paid skips
  must remain out of the research prototype so engagement is not confounded by
  monetization pressure.

## Initial protocol

Run at least 100 seeded expeditions per balance condition and 20–50 proposals
per model/parent-pair condition. Keep raw prompts, model tag, latency, proposal,
admission decision, simulation report, build key, sprite hash, and reviewer
verdict. Do not silently replace a rejected proposal; version every accepted
recipe and retain the rejection ledger.

The immediate next study is a controlled difficulty/pacing comparison between
Classic 4×4, Tactical 4×4, and Duel 3×3, followed by a blinded player test of
base pieces versus the five-step discovery branch. The result should report
where novelty, clarity, challenge, queue time, and cost stop improving together.

The latest local-model record reinforces the lifecycle requirement: a
`qwen2.5-coder:1.5b-base` proposal named `Tick` was rejected for duplicating a
parent, so its simulation, render, visual-review, and export stages remain
explicitly `not_attempted` in the joined factory record. The existing reviewed
Tick sprite is not silently reused as evidence for that proposal.

## Manual smoke evidence (2026-09-12)

An agent-controlled browser run resumed a saved Classic 4×4 expedition and
completed part of encounters 3–4 without code or state resets. The sequence
provided a useful interaction trace for the study:

- Placing a Tick on the announced rival target completed a friendly line,
  reduced rival resolve from 2 to 1, and cleared the player's line. The causal
  feedback was visible in both the board and the field notes.
- Placing a Tack on the announced target did not visibly retarget the rival
  until **End turn**; the next intent then changed and the rival placed at a
  different cell. This is internally coherent, but the “occupy it to force a
  new target” copy should be evaluated for timing clarity.
- Tweezers (2 energy) removed a rival Tack and left one energy, making the
  opportunity cost legible. At zero energy, the end-turn preview warned that a
  heart would be lost.
- A Toe placed on the announced target caused the subsequent rival Tick to
  choose another cell, demonstrating bait as a real board intervention rather
  than a cosmetic tag.

The run reached encounter 4/5 with all three hearts intact. This is not a
balance result, but it confirms that the testbed can capture action → response →
resource/board-state evidence in a reproducible smoke pass. The next manual
round should measure whether that clarity survives a tighter board and whether
the target-retarget timing is understood without reading the field notes.

## Academic positioning

This is best presented as AI/computer-science research in constrained generative
systems, procedural content generation, game AI, and human-in-the-loop
evaluation. Esteban Clua's UFF Computação Visual / MediaLab is a strong formal
home because its stated scope includes rendering, games, storytelling,
game-engine architecture, AI, and interactive visual systems.
