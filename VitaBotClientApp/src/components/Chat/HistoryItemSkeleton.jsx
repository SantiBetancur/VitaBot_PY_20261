import styles from './HistoryItemSkeleton.module.css'

export default function HistoryItemSkeleton() {
  return (
    <div className={styles.skeletonItem} role="status" aria-label="Cargando elemento del historial">
      <div className={styles.skeletonTitle} />
      <div className={styles.skeletonMeta} />
    </div>
  )
}
