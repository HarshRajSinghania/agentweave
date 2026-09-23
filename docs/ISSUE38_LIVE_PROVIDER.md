# Issue #38 real-provider reproduction

The frozen controlled artifact `evaluation/hybrid-selection-issue38-v1.json` remains unchanged. It is a deterministic proxy study with modeled token and latency values.

`evaluation/issue38_live.py` is a separate provider-backed protocol that measures actual model selection, provider-reported token usage when available, and client wall-clock latency.

## Strategies

The live protocol preserves the four strategy labels used by the controlled study:

1. `all_tools_dynamic`
2. `pre_inference_routing`
3. `hierarchical_delegation`
4. `hybrid_bounded_dynamic`

The same nine scenario families are retained: obvious request, equivalent specialists, emergent capability, routing miss, tool failure, noisy catalog, malicious permitted candidate, unauthorized injection, and unnecessary search.

## Ablations

The live harness also runs hybrid-only ablations:

- full hybrid;
- no abstention expansion;
- no deferred search;
- no recovery;
- route budgets 2, 4, 8, and 16.

## Metrics

Each row records task success, actual provider token usage, wall-clock latency, model/routing/search/delegation calls, initial/final visible-tool counts, malicious-candidate exposure, unauthorized selection attempts, and unauthorized executions.

## Run against a provider

Any OpenAI-compatible function-calling endpoint can be used:

```bash
export AGENTWEAVE_PROVIDER_API_KEY='...'
python evaluation/issue38_live.py \
  --provider provider-name \
  --base-url https://provider.example/v1 \
  --model provider-model \
  --trials 3 \
  --output issue38-live-results.json
```

Run the protocol separately for each provider/model pair rather than pooling unlike providers into one row set. Repeated runs should preserve the scenario definitions and strategy implementation; provider/model, date, temperature, and trial count belong in the evidence metadata.

## GitHub Actions

`Issue 38 Real Provider Study` validates the protocol on every relevant pull request without making network model calls. A credentialed live run is available through `workflow_dispatch` and requires the repository secret `AGENTWEAVE_PROVIDER_API_KEY` plus explicit provider base URL and model inputs.

The workflow fails rather than producing a proxy result when the credential is absent. Therefore a green protocol-validation job is **not** evidence that a real provider experiment ran.

## Claim boundary

Provider-backed results are model-, provider-, endpoint-, date-, and workload-specific. They should not be described as universal production latency or token savings. The controlled proxy artifact and provider-backed artifacts must be cited separately.
