import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import client from '../api/client';
import styles from './Login.module.css';

export default function Login() {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [orgName, setOrgName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const { dark, toggle } = useTheme();
  const navigate = useNavigate();

  const handle = async (e) => {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      const endpoint = mode === 'login' ? '/auth/login' : '/auth/signup';
      const payload = mode === 'login'
        ? { email, password }
        : { email, password, organization_name: orgName };
      const { data } = await client.post(endpoint, payload);
      login(data.access_token);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <button className={styles.modeBtn} onClick={toggle}>
        {dark ? '● Dark' : '○ Light'}
      </button>

      <div className={`${styles.card} fade-up`}>
        <div className={styles.wordmark}>Knowledge<em>AI</em></div>
        <p className={styles.sub}>
          {mode === 'login' ? 'Sign in to your knowledge base' : 'Create your knowledge base'}
        </p>

        <form onSubmit={handle} className={styles.form}>
          {mode === 'signup' && (
            <div className={`${styles.field} fade-up-1`}>
              <label className={styles.label}>Organisation</label>
              <input
                className={styles.input}
                value={orgName}
                onChange={e => setOrgName(e.target.value)}
                placeholder="Acme Corp"
                required
              />
            </div>
          )}
          <div className={`${styles.field} fade-up-2`}>
            <label className={styles.label}>Email</label>
            <input
              className={styles.input}
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
            />
          </div>
          <div className={`${styles.field} fade-up-3`}>
            <label className={styles.label}>Password</label>
            <input
              className={styles.input}
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          {error && <p className={styles.error}>{error}</p>}

          <button className={`${styles.submit} fade-up-4`} disabled={loading}>
            {loading ? 'Please wait…' : mode === 'login' ? 'Sign in →' : 'Create account →'}
          </button>
        </form>

        <p className={`${styles.toggle} fade-up-5`}>
          {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
          <span onClick={() => { setMode(mode === 'login' ? 'signup' : 'login'); setError(''); }}>
            {mode === 'login' ? 'Sign up' : 'Sign in'}
          </span>
        </p>
      </div>
    </div>
  );
}