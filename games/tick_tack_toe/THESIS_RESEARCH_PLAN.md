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

## Academic positioning

This is best presented as AI/computer-science research in constrained generative
systems, procedural content generation, game AI, and human-in-the-loop
evaluation. Esteban Clua's UFF Computação Visual / MediaLab is a strong formal
home because its stated scope includes rendering, games, storytelling,
game-engine architecture, AI, and interactive visual systems.
