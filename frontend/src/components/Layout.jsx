import { NavLink, useNavigate } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import styles from './Layout.module.css';

export default function Layout({ children }) {
  const { dark, toggle } = useTheme();
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <div className={styles.shell}>
      <header className={`${styles.topbar} fade-up`}>
        <div className={styles.wordmark}>
          Knowledge<em>AI</em>
        </div>
        <nav className={styles.nav}>
          <NavLink to="/dashboard" className={({ isActive }) =>
            `${styles.navItem} ${isActive ? styles.active : ''}`}>
            Overview
          </NavLink>
          <NavLink to="/documents" className={({ isActive }) =>
            `${styles.navItem} ${isActive ? styles.active : ''}`}>
            Documents
          </NavLink>
          <NavLink to="/chat" className={({ isActive }) =>
            `${styles.navItem} ${isActive ? styles.active : ''}`}>
            Chat
          </NavLink>
        </nav>
        <div className={styles.topbarRight}>
          <button className={styles.modeBtn} onClick={toggle}>
            {dark ? '● Dark' : '○ Light'}
          </button>
          <button className={styles.logoutBtn} onClick={handleLogout}>
            Sign out
          </button>
        </div>
      </header>
      <main className={styles.main}>{children}</main>
    </div>
  );
}