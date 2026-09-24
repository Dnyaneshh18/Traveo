import { useState, type FormEvent } from 'react';
import { ApiError } from '@traveo/shared';
import { useStore } from '../lib/store';

export function LoginPage() {
  const login = useStore((s) => s.login);
  const [email, setEmail] = useState('admin@traveo.app');
  const [password, setPassword] = useState('Admin@123');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Login failed');
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="login">
      <form className="card" onSubmit={submit}>
        <div className="brand" style={{ color: 'var(--text)', padding: 0 }}>🎓🛺 <div>Traveo<small>Ops console</small></div></div>
        <label>Email</label>
        <input className="input" value={email} onChange={(e) => setEmail(e.target.value)} type="email" autoFocus />
        <label>Password</label>
        <input className="input" value={password} onChange={(e) => setPassword(e.target.value)} type="password" />
        {error ? <div className="error">{error}</div> : null}
        <button className="btn primary" style={{ width: '100%', marginTop: 18, padding: 11 }} disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
        <p className="small" style={{ marginTop: 14 }}>Default dev credentials are pre-filled (change ADMIN_EMAIL / ADMIN_PASSWORD in production).</p>
      </form>
    </div>
  );
}
