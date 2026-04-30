# Metrics Sanity Check

- Verdict: `PASS`
- Candidate count: `11`
- Continue to Phase 2: `True`

## Checks

- `mean_violation`: `passed=True`; `max_abs_diff=0.00000000`
- `high_disruption_action_rate`: `passed=True`; `max_abs_diff=0.00000000`
- `business/cost margin sign`: `passed=True`; `sign_mismatch_detected=False`

## Notes

- `normalized_mean_violation` is a reporting-only audit metric.
- It uses per-episode `(business_shortfall / |d_business|) + (cost_shortfall / |d_cost|)` and does not replace the main `mean_violation` definition.