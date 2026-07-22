# Atmosphere input policy

## Decision

The service no longer asks users to choose a preferred atmosphere. This removes
one input step from the user flow.

The master-data `STORE.atmosphere` field remains a factual store attribute and
is retained in training data and future model features. The model may learn
average relationships between store atmosphere and the remaining observable
scenario conditions, but it must not claim to know an individual user's
unspoken atmosphere preference.

## Historical human labels

`run_007` and its 240 completed labels are immutable. Their
`requested_atmosphere_code` and `ATMOSPHERE_MISMATCH` values remain preserved
as historical provenance. The binary `outcome` remains eligible for training.

## Future runs and UI

- Do not generate or display `atmosphere_code` as a user scenario condition.
- Do not offer `ATMOSPHERE_MISMATCH` in the future labeling UI.
- Use `LOW_APPEAL` when a point of sale is not appealing, including an
  unspoken atmosphere preference.
- Exclude `requested_atmosphere_code` from model inputs.
- Retain `store_atmosphere` as a model input.
