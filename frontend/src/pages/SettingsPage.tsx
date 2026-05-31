import { ShieldCheck } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';

export function SettingsPage() {
  const [status, setStatus] = useState<Record<string, unknown>>({});
  useEffect(() => { void api.llmStatus().then(setStatus); }, []);
  return (
    <main className="page">
      <div className="page-head">
        <div>
          <h1>系统设置</h1>
          <p>模型密钥只在服务器 .env 配置，前端不展示 API Key。</p>
        </div>
      </div>
      <section className="panel settings">
        <ShieldCheck size={32} />
        <dl>
          <dt>LLM_PROVIDER</dt>
          <dd>{String(status.provider || '')}</dd>
          <dt>LLM_MODEL</dt>
          <dd>{String(status.model || '')}</dd>
          <dt>状态</dt>
          <dd>{String(status.message || '')}</dd>
        </dl>
      </section>
    </main>
  );
}
