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

The 240 human labels remain the source data. By the human label owner's
decision, the eight `ATMOSPHERE_MISMATCH` rejections in the training export are
reclassified as `LOW_APPEAL`; their binary `REJECTED` outcome is unchanged.
`requested_atmosphere_code` remains in the export only as provenance and is
excluded from model inputs.

## Future runs and UI

- Do not generate or display `atmosphere_code` as a user scenario condition.
- Do not offer `ATMOSPHERE_MISMATCH` in the future labeling UI.
- Use `LOW_APPEAL` when a point of sale is not appealing, including an
  unspoken atmosphere preference.
- Exclude `requested_atmosphere_code` from model inputs.
- Retain `store_atmosphere` as a model input.
