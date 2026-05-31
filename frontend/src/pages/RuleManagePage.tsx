import { Plus } from 'lucide-react';
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
    <main className="page">
      <div className="page-head">
        <div>
          <h1>规则库</h1>
          <p>规则可编辑、启停；学习建议必须人工接受后才生效。</p>
        </div>
        <button onClick={() => setRules([newRule, ...rules])}><Plus size={16} />新增规则</button>
      </div>
      <section className="rule-grid">
        {rules.map((rule, index) => (
          <RuleEditor key={rule.id || `new-${index}`} rule={rule} onSave={async (draft) => {
            if (draft.id) await api.updateRule(draft.id, draft);
            else await api.createRule(draft);
            await load();
          }} />
        ))}
      </section>
      <section className="panel">
        <div className="panel-head"><h2>规则建议</h2></div>
        {suggestions.map((suggestion) => (
          <article className="suggestion" key={suggestion.id}>
            <strong>{suggestion.suggestion_type} · {suggestion.status}</strong>
            <p>{suggestion.content}</p>
            <small>样本数：{suggestion.sample_count} · {suggestion.source_basis}</small>
            {suggestion.status === 'pending' && (
              <div className="toolbar">
                <button onClick={async () => { await api.acceptSuggestion(suggestion.id, '运营'); await load(); }}>接受</button>
                <button onClick={async () => { await api.rejectSuggestion(suggestion.id, '运营'); await load(); }}>拒绝</button>
              </div>
            )}
          </article>
        ))}
      </section>
    </main>
  );
}
