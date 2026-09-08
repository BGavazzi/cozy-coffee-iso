# Local discovery designer

The optional designer uses a local Ollama server to propose structured concepts.
It does not modify the game, execute model output, admit canon, or render art.

```text
ollama pull qwen3:4b
python tools/local_designer.py "Mimic Toe" "Brood Tick" --out proposal.json
```

The output is constrained to a small JSON schema: one trigger, one target, one
bounded effect, a cost from 1–4, and a base mesh family with at most three
approved attachments. A separate validator must map it to an implemented rule
template before the café factory is invoked. Unknown effects are rejected.

The intended batch workflow is:

1. Generate proposals offline and cache the prompt, model tag, and output.
2. Reject malformed, duplicate, recursive, or unimplemented effects.
3. Simulate the surviving mechanic against seeded runs.
4. Add an explicit recipe entry and visual review record.
5. Render through `game_factory.py`; never render arbitrary model text directly.

The model is a creative search aid, not a rules engine. Keep Ollama bound to
localhost; do not expose it from the hosted game.

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
