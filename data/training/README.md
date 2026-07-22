# Human training-data export

`heuristic selection data.csv` is the 240-row human virtual-scenario training
dataset derived from `run_007`.

- `outcome` is the binary training target (`ACCEPTED` or `REJECTED`).
- `store_atmosphere` is a factual store feature and remains available for
  model training.
- `requested_atmosphere_code` is retained only as historical provenance. It
  must not be used as an input feature in future recommendation models because
  the user-facing atmosphere question has been removed.
- Eight human-reviewed atmosphere-related rejections were reclassified to
  `LOW_APPEAL`. Future atmosphere-related dislike is also recorded as
  `LOW_APPEAL`.

See `config/recommendation_model_features.json` for the future model feature
contract.
