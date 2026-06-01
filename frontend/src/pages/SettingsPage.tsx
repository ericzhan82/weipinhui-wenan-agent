import { CheckCircle2, Cpu, KeyRound, Plus, Save, Server, ShieldCheck, SlidersHorizontal } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { LlmConfig, LlmConfigPayload } from '../types';

const providerPresets = [
  { provider: 'deepseek', display_name: 'DeepSeek', base_url: 'https://api.deepseek.com/v1', model: 'deepseek-chat' },
  { provider: 'openai', display_name: 'OpenAI', base_url: 'https://api.openai.com/v1', model: 'gpt-4o-mini' },
  { provider: 'qwen', display_name: '通义千问', base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1', model: 'qwen-plus' },
  { provider: 'moonshot', display_name: 'Moonshot', base_url: 'https://api.moonshot.cn/v1', model: 'moonshot-v1-8k' },
  { provider: 'openai_compatible', display_name: 'OpenAI Compatible', base_url: '', model: '' },
  { provider: 'mock', display_name: 'Mock 演示模型', base_url: '', model: 'mock' },
] as const;

const emptyDraft: LlmConfigPayload = {
  provider: 'deepseek',
  display_name: 'DeepSeek',
  base_url: 'https://api.deepseek.com/v1',
  api_key: '',
  model: 'deepseek-chat',
  temperature: 0.4,
  timeout_seconds: 90,
  max_retries: 0,
  enabled: true,
  updated_by: '运营',
};

export function SettingsPage() {
  const [status, setStatus] = useState<Record<string, unknown>>({});
  const [configs, setConfigs] = useState<LlmConfig[]>([]);
  const [draft, setDraft] = useState<LlmConfigPayload>(emptyDraft);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const statusSource = String(status.source || '');
  const apiKeyState = status.api_key_set
    ? statusSource === 'database'
      ? '数据库已保存'
      : '.env 已配置'
    : '未保存';

  const load = async () => {
    const [nextStatus, nextConfigs] = await Promise.all([api.llmStatus(), api.llmConfigs()]);
    setStatus(nextStatus);
    setConfigs(nextConfigs);
  };

  useEffect(() => { void load(); }, []);

  const chooseProvider = (provider: string) => {
    const preset = providerPresets.find((item) => item.provider === provider);
    if (!preset) return;
    setDraft({
      ...draft,
      provider: preset.provider,
      display_name: preset.display_name,
      base_url: preset.base_url,
      model: preset.model,
      api_key: '',
    });
  };

  const editConfig = (config: LlmConfig) => {
    setEditingId(config.id);
    setDraft({
      provider: config.provider,
      display_name: config.display_name || config.provider,
      base_url: config.base_url || '',
      api_key: '',
      model: config.model,
      temperature: config.temperature,
      timeout_seconds: config.timeout_seconds,
      max_retries: config.max_retries,
      enabled: config.enabled,
      updated_by: '运营',
    });
    setMessage(config.api_key_set ? '正在编辑配置。API Key 已存在数据库；留空则不覆盖。' : '正在编辑配置。请补充 API Key 后保存。');
  };

  const resetDraft = () => {
    setEditingId(null);
    setDraft(emptyDraft);
    setMessage('');
  };

  const saveConfig = async () => {
    setBusy(true);
    setMessage('');
    try {
      const payload: Partial<LlmConfigPayload> = { ...draft };
      if (editingId && !draft.api_key?.trim()) {
        delete payload.api_key;
      }
      if (editingId) {
        await api.updateLlmConfig(editingId, payload);
      } else {
        await api.createLlmConfig(draft);
      }
      await load();
      setMessage('模型配置已保存到数据库');
      if (!editingId) setDraft({ ...draft, api_key: '' });
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(false);
    }
  };

  const activate = async (id: number) => {
    setBusy(true);
    setMessage('');
    try {
      await api.activateLlmConfig(id);
      await load();
      setMessage('已切换启用模型配置');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="page ai-page">
      <div className="page-head ai-head">
        <div>
          <span className="eyebrow"><Server size={14} />runtime state</span>
          <h1>模型 API 配置</h1>
          <p>参考 Codex 的任务式面板组织模型运行状态；API Key 保存到数据库，读取时只显示是否已设置。</p>
        </div>
        <button onClick={resetDraft}><Plus size={16} />新增厂商</button>
      </div>

      <section className="settings-grid">
        <div className="runtime-card">
          <Server size={22} />
          <span>Provider</span>
          <strong>{String(status.display_name || status.provider || '未配置')}</strong>
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
          <small>{statusSource === 'database' ? '使用数据库配置' : '使用环境变量兜底'}</small>
        </div>
        <div className="runtime-card secure">
          <KeyRound size={22} />
          <span>API Key</span>
          <strong>{apiKeyState}</strong>
        </div>
      </section>

      {message && <p className={message.includes('失败') || message.includes('HTTP') ? 'notice error' : 'notice'}>{message}</p>}

      <section className="llm-config-layout">
        <div className="panel llm-config-form">
          <div className="panel-head">
            <div>
              <h2><SlidersHorizontal size={18} />{editingId ? '编辑厂商配置' : '新增厂商配置'}</h2>
              <p className="muted">非 mock 厂商按 OpenAI-compatible chat/completions 协议调用。</p>
            </div>
          </div>
          <div className="form-grid">
            <label>
              <span>厂商</span>
              <select value={draft.provider} onChange={(event) => chooseProvider(event.target.value)}>
                {providerPresets.map((preset) => <option key={preset.provider} value={preset.provider}>{preset.display_name}</option>)}
              </select>
            </label>
            <label>
              <span>显示名称</span>
              <input value={draft.display_name || ''} onChange={(event) => setDraft({ ...draft, display_name: event.target.value })} />
            </label>
            <label className="span-2">
              <span>Base URL</span>
              <input value={draft.base_url || ''} onChange={(event) => setDraft({ ...draft, base_url: event.target.value })} placeholder="https://.../v1" />
            </label>
            <label>
              <span>模型名</span>
              <input value={draft.model} onChange={(event) => setDraft({ ...draft, model: event.target.value })} placeholder="deepseek-chat / qwen-plus / ..." />
            </label>
            <label>
              <span>API Key</span>
              <input type="password" value={draft.api_key || ''} onChange={(event) => setDraft({ ...draft, api_key: event.target.value })} placeholder={editingId ? '留空则不覆盖数据库密钥' : '保存到数据库'} />
            </label>
            <label>
              <span>Temperature</span>
              <input type="number" min="0" max="2" step="0.1" value={draft.temperature} onChange={(event) => setDraft({ ...draft, temperature: Number(event.target.value) })} />
            </label>
            <label>
              <span>超时秒数</span>
              <input type="number" min="10" value={draft.timeout_seconds} onChange={(event) => setDraft({ ...draft, timeout_seconds: Number(event.target.value) })} />
            </label>
            <label>
              <span>失败重试</span>
              <input type="number" min="0" max="5" value={draft.max_retries} onChange={(event) => setDraft({ ...draft, max_retries: Number(event.target.value) })} />
            </label>
            <label className="check-row llm-enabled">
              <input type="checkbox" checked={draft.enabled} onChange={(event) => setDraft({ ...draft, enabled: event.target.checked })} />
              启用为当前生成模型
            </label>
          </div>
          <div className="toolbar">
            <button className="primary" disabled={busy} onClick={saveConfig}><Save size={16} />{busy ? '保存中' : '保存到数据库'}</button>
            {editingId && <button disabled={busy} onClick={resetDraft}>取消编辑</button>}
          </div>
        </div>

        <div className="panel llm-config-list">
          <div className="panel-head">
            <div>
              <h2><KeyRound size={18} />数据库配置</h2>
              <p className="muted">只允许一个配置处于启用状态；列表不会回显明文 API Key。</p>
            </div>
          </div>
          <div className="llm-provider-list">
            {configs.map((config) => (
              <article className={config.enabled ? 'llm-provider-card active' : 'llm-provider-card'} key={config.id}>
                <div>
                  <span>{config.enabled ? '当前启用' : '备用配置'}</span>
                  <strong>{config.display_name || config.provider}</strong>
                  <small>{config.provider} · {config.model}</small>
                </div>
                <p>{config.base_url || '本地 mock / 未配置 Base URL'}</p>
                <div className="queue-signals">
                  <span><KeyRound size={14} />{config.api_key_set ? 'API Key 已入库' : '未保存密钥'}</span>
                  <span><Cpu size={14} />{config.temperature}</span>
                  <span><Server size={14} />{config.timeout_seconds}s</span>
                </div>
                <div className="toolbar">
                  <button onClick={() => editConfig(config)}>编辑</button>
                  {!config.enabled && <button className="primary" disabled={busy} onClick={() => activate(config.id)}><CheckCircle2 size={16} />启用</button>}
                </div>
              </article>
            ))}
            {configs.length === 0 && (
              <div className="empty-state">
                <KeyRound size={26} />
                <strong>数据库里还没有模型配置</strong>
                <p>新增厂商并保存后，生成文案会优先使用数据库中的启用配置。</p>
              </div>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}
