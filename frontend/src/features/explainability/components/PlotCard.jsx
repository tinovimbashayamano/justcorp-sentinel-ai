import { createDataUrl } from "../utils/base64";

export default function PlotCard({
  title,
  description,
  plot,
  loading,
}) {
  let content = (
    <div className="plot-placeholder">
      No visualization generated yet.
    </div>
  );

  if (loading) {
    content = (
      <div className="plot-placeholder">
        Generating visualization…
      </div>
    );
  } else if (plot?.image_base64) {
    content = (
      <img
        className="explainability-plot"
        src={createDataUrl(
          plot.image_base64,
          plot.media_type,
        )}
        alt={title}
      />
    );
  }

  return (
    <section className="panel">
      <div className="panel__header">
        <div>
          <p className="eyebrow">Model visualization</p>
          <h2>{title}</h2>
        </div>
      </div>
      {description ? (
        <p className="muted">{description}</p>
      ) : null}
      {content}
    </section>
  );
}
