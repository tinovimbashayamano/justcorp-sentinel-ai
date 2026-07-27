# Explainability visualizations

The authenticated routes under
`/api/v1/explainability-visualizations` provide plot-ready SHAP data,
base64-encoded PNG charts, and investigation report exports.

## Routes

- `GET /health`
- `POST /local/data`
- `POST /local/waterfall`
- `POST /local/force`
- `GET /global/data`
- `GET /global/summary`
- `GET /dependence/{feature_name}`
- `POST /reports/html`
- `POST /reports/pdf`

Local visualization and report routes require an administrator or fraud
analyst. Global and dependence routes also allow auditors. The health
route is available to any authenticated user.

PNG responses use the `image/png` media type and place the encoded image
in `image_base64`. Report responses use `content_base64` and include a
suggested filename and media type.

The feature name supplied to the dependence route must be a public
transformed feature name returned by the model-insight endpoints.
