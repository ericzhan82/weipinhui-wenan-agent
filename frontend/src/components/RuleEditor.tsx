import { Save, ShieldCheck } from 'lucide-react';
import { useState } from 'react';
import type { Rule } from '../types';

type Props = {
  rule: Rule;
  onSave: (rule: Rule) => void;
};

export function RuleEditor({ rule, onSave }: Props) {
  const [draft, setDraft] = useState(rule);
  return (
    <article className={draft.enabled ? 'rule-item' : 'rule-item disabled'}>
      <div className="rule-item-head">
        <span><ShieldCheck size={14} />生成约束</span>
        <strong>{draft.enabled ? '参与生成' : '已停用'}</strong>
      </div>
      <div className="rule-meta">
        <input value={draft.rule_type} onChange={(event) => setDraft({ ...draft, rule_type: event.target.value })} />
        <input value={draft.rule_name} onChange={(event) => setDraft({ ...draft, rule_name: event.target.value })} />
        <label className="check-row"><input type="checkbox" checked={draft.enabled} onChange={(event) => setDraft({ ...draft, enabled: event.target.checked })} />启用</label>
      </div>
      <textarea value={draft.content} onChange={(event) => setDraft({ ...draft, content: event.target.value })} rows={5} />
      <button title="保存规则记忆" onClick={() => onSave(draft)}><Save size={16} />保存记忆</button>
    </article>
  );
}
