import { BrainCircuit, CheckCircle2, Library, Plus, ShieldCheck, XCircle } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { RuleEditor } from '../components/RuleEditor';
import type { Rule, RuleSuggestion } from '../types';

const newRule: Rule = { rule_type: 'general', rule_name: '新规则', content: '', enabled: true, updated_by: '运营' };

export function RuleManagePage() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [suggestions, setSuggestions] = useState<RuleSuggestion[]>([]);
  const load = async () => {
    setRules(await api.rules());
    setSuggestions(await api.suggestions());
  };
  useEffect(() => { void load(); }, []);
  return (
    <main className="page ai-page">
      <div className="page-head ai-head">
        <div>
          <span className="eyebrow"><Library size={14} />rule memory</span>
          <h1>规则记忆库</h1>
          <p>这里不是普通配置页，而是模型生成时会被装载的品牌语气、渠道约束和禁用边界。</p>
        </div>
        <button className="primary" onClick={() => setRules([newRule, ...rules])}><Plus size={16} />新增记忆</button>
      </div>

      <section className="ai-command-strip">
        <div>
          <ShieldCheck size={18} />
          <span>启用规则</span>
          <strong>{rules.filter((rule) => rule.enabled).length}</strong>
        </div>
        <div>
          <BrainCircuit size={18} />
          <span>学习建议</span>
          <strong>{suggestions.length}</strong>
        </div>
        <div>
          <CheckCircle2 size={18} />
          <span>待人工确认</span>
          <strong>{suggestions.filter((suggestion) => suggestion.status === 'pending').length}</strong>
        </div>
      </section>

      <section className="rule-grid">
        {rules.map((rule, index) => (
          <RuleEditor key={rule.id || `new-${index}`} rule={rule} onSave={async (draft) => {
            if (draft.id) await api.updateRule(draft.id, draft);
            else await api.createRule(draft);
            await load();
          }} />
        ))}
      </section>
      <section className="panel memory-suggestion-panel">
        <div className="panel-head">
          <div>
            <h2><BrainCircuit size={18} />学习建议入库队列</h2>
            <p className="muted">AI 从人工修改里提炼候选规则，接受后才会成为正式生成记忆。</p>
          </div>
        </div>
        {suggestions.map((suggestion) => (
          <article className="suggestion" key={suggestion.id}>
            <strong>{suggestion.suggestion_type} · {suggestion.status}</strong>
            <p>{suggestion.content}</p>
            <small>样本数：{suggestion.sample_count} · {suggestion.source_basis}</small>
            {suggestion.status === 'pending' && (
              <div className="toolbar">
                <button className="primary" onClick={async () => { await api.acceptSuggestion(suggestion.id, '运营'); await load(); }}><CheckCircle2 size={16} />写入记忆</button>
                <button onClick={async () => { await api.rejectSuggestion(suggestion.id, '运营'); await load(); }}><XCircle size={16} />忽略</button>
              </div>
            )}
          </article>
        ))}
        {suggestions.length === 0 && <p className="muted">暂无学习建议。先在文案工作台保存人工优化版本，再运行学习回路。</p>}
      </section>
    </main>
  );
}
