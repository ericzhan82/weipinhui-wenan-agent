import { Cpu, KeyRound, Server, ShieldCheck } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';

export function SettingsPage() {
  const [status, setStatus] = useState<Record<string, unknown>>({});
  useEffect(() => { void api.llmStatus().then(setStatus); }, []);
  return (
    <main className="page ai-page">
      <div className="page-head ai-head">
        <div>
          <span className="eyebrow"><Server size={14} />runtime state</span>
          <h1>模型运行状态</h1>
          <p>前端只显示模型可用性和运行配置，不暴露 API Key。</p>
        </div>
      </div>
      <section className="settings-grid">
        <div className="runtime-card">
          <Server size={22} />
          <span>Provider</span>
          <strong>{String(status.provider || '未配置')}</strong>
        </div>
        <div className="runtime-card">
          <Cpu size={22} />
          <span>Model</span>
          <strong>{String(status.model || '未配置')}</strong>
        </div>
        <div className="runtime-card">
          <ShieldCheck size={22} />
          <span>Health</span>
          <strong>{String(status.message || '等待后端返回')}</strong>
        </div>
        <div className="runtime-card secure">
          <KeyRound size={22} />
          <span>API Key</span>
          <strong>仅服务器保存</strong>
        </div>
      </section>
    </main>
  );
}
