/**
 * Composant Skeleton générique avec animate-pulse.
 * Utilisé partout où les données sont en cours de chargement
 * pour éviter les sauts de layout et améliorer la performance perçue.
 */
export function Skeleton({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return (
    <div
      className={`animate-pulse rounded-xl ${className ?? ''}`}
      style={{ background: 'rgba(255,255,255,0.06)', ...style }}
    />
  );
}
