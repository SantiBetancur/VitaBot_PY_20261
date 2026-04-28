import styles from './UserProfile.module.css'

const UserProfile = ({ user, onSignOut }) => {
  const initials = user
    ? `${(user.first_name || user.firstName || '?')[0]}${(user.last_name || user.lastName || '')[0] || ''}`.toUpperCase()
    : '?'

  const fullName = user
    ? `${user.first_name || user.firstName || ''} ${user.last_name || user.lastName || ''}`.trim()
    : 'Usuario'

  const email = user?.email_id || user?.email || ''

  return (
    <div className={styles.profileContainer}>
      <div className={styles.profileHeader}>
        <div className={styles.avatar}>{initials}</div>
        <div className={styles.userInfo}>
          <span className={styles.userName}>{fullName}</span>
          {email && <span className={styles.userEmail}>{email}</span>}
        </div>
      </div>

      <div className={styles.divider} />

      <button className={styles.signOutButton} onClick={onSignOut}>
        <span className={styles.signOutIcon}>→</span>
        Cerrar sesión
      </button>
    </div>
  )
}

export default UserProfile