# Human training-data export

`heuristic selection data.csv` is the immutable 240-row export of completed
human virtual-scenario labels from `run_007`.

- `outcome` is the binary training target (`ACCEPTED` or `REJECTED`).
- `store_atmosphere` is a factual store feature and remains available for
  model training.
- `requested_atmosphere_code` is retained only as historical provenance. It
  must not be used as an input feature in future recommendation models because
  the user-facing atmosphere question has been removed.
- Existing `ATMOSPHERE_MISMATCH` labels are historical records; future
  atmosphere-related dislike is recorded as `LOW_APPEAL`.

See `config/recommendation_model_features.json` for the future model feature
contract.
