import { buildAlertTimeline } from "../domain/alertCenter";
export default function AlertTimeline({ alert }) {
  return <section className="alert-timeline"><p className="alert-eyebrow">Timeline</p>{buildAlertTimeline(alert).map((event)=><div className={`alert-timeline__event ${event.complete ? "alert-timeline__event--complete" : ""}`} key={event.label}><span className="alert-timeline__marker"/><div><strong>{event.label}</strong><span>{event.timestamp ? new Date(event.timestamp).toLocaleString() : "Pending"}</span></div></div>)}</section>;
}
