import { KeyRound, LogIn, ShieldCheck, Sparkles } from 'lucide-react';
import { useState } from 'react';
import { api, setAuthToken } from '../api/client';
import type { AuthUser } from '../types';

type Props = {
  onLogin: (user: AuthUser, token: string) => void;
};

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : String(error);
}

export function LoginPage({ onLogin }: Props) {
  const [email, setEmail] = useState('admin@example.com');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setBusy(true);
    setMessage('');
    try {
      const result = await api.login({ email, password });
      setAuthToken(result.access_token);
      onLogin(result.user, result.access_token);
    } catch (error) {
      setMessage(errorMessage(error));
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="login-page">
      <section className="login-panel">
        <div className="login-hero">
          <span><Sparkles size={16} />Vipshop Copy Agent</span>
          <h1>登录 AI 文案工作台</h1>
          <p>账号会决定可见工作空间、可操作的任务队列，以及是否能配置模型和成员权限。</p>
          <div className="login-signals">
            <b><ShieldCheck size={16} />工作空间隔离</b>
            <b><KeyRound size={16} />角色权限</b>
            <b><Sparkles size={16} />批量生成队列</b>
          </div>
        </div>
        <div className="login-card">
          <h2>账号登录</h2>
          <label>
            <span>邮箱</span>
            <input value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="username" />
          </label>
          <label>
            <span>密码</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              onKeyDown={(event) => event.key === 'Enter' && void submit()}
              placeholder="输入部署时设置的 ADMIN_PASSWORD"
            />
          </label>
          {message && <p className="notice error">{message}</p>}
          <button className="primary" disabled={busy || !email || !password} onClick={submit}>
            <LogIn size={16} />{busy ? '登录中' : '进入工作台'}
          </button>
          <small>首次部署请使用环境变量 `ADMIN_EMAIL` / `ADMIN_PASSWORD` 创建的管理员账号。</small>
        </div>
      </section>
    </main>
  );
}
