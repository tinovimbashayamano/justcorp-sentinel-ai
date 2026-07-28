export default function AlertSeverityBadge({ severity }) {
  return <span className={`alert-severity alert-severity--${severity}`}>{severity}</span>;
}
