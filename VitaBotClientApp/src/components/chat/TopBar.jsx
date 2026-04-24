import styles from './TopBar.module.css'

export default function TopBar({ title }) {
  return (
    <header className={styles.bar} role="banner">
      <h1 className={styles.title}>{title}</h1>
      
      <span className={styles.badge} aria-label="Modelo de IA">Haiku-4.5</span>
    </header>
  )
}