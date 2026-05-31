import { Brain, Check, GitCompareArrows, Lightbulb, Sparkles, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { LearningReport, RuleSuggestion } from '../types';

export function LearningCenterPage() {
  const [summary, setSummary] = useState<Record<string, number>>({});
  const [reports, setReports] = useState<LearningReport[]>([]);
  const [suggestions, setSuggestions] = useState<RuleSuggestion[]>([]);
  const load = async () => {
    setSummary(await api.learningSummary());
    setReports(await api.reports());
    setSuggestions(await api.suggestions());
  };
  useEffect(() => { void load(); }, []);
  return (
    <main className="page ai-page">
      <div className="page-head ai-head">
        <div>
          <span className="eyebrow"><GitCompareArrows size={14} />feedback loop</span>
          <h1>AI 学习回路</h1>
          <p>把“模型初稿”和“人工定稿”的差异变成可审核的偏好总结和规则记忆。</p>
        </div>
        <button className="primary" onClick={async () => { await api.analyzeLearning(); await load(); }}><Brain size={16} />运行学习回路</button>
      </div>
      <section className="metrics">
        {Object.entries(summary).map(([key, value]) => <div className="metric" key={key}><strong>{value}</strong><span>{key}</span></div>)}
        {Object.keys(summary).length === 0 && (
          <>
            <div className="metric"><strong>0</strong><span>可学习样本</span></div>
            <div className="metric"><strong>0</strong><span>待确认建议</span></div>
          </>
        )}
      </section>
      <section className="panel learning-panel">
        <div className="panel-head">
          <div>
            <h2><Sparkles size={18} />模型偏好摘要</h2>
            <p className="muted">这里展示模型需要保留什么、删掉什么、下次如何更贴近人工定稿。</p>
          </div>
        </div>
        {reports.map((report) => (
          <article className="report" key={report.id}>
            <strong>{report.report_title}</strong>
            <p>{report.summary}</p>
            <small>保留词：{report.high_frequency_kept_terms_json.join(' / ') || '暂无'} · 删除词：{report.high_frequency_removed_terms_json.join(' / ') || '暂无'}</small>
          </article>
        ))}
        {reports.length === 0 && <p className="muted">暂无学习报告。保存几版人工优化文案后再运行学习回路。</p>}
      </section>
      <section className="panel">
        <div className="panel-head">
          <div>
            <h2><Lightbulb size={18} />待确认规则建议</h2>
            <p className="muted">建议不会自动生效，必须由运营确认后写入规则记忆库。</p>
          </div>
        </div>
        {suggestions.map((suggestion) => (
          <article className="suggestion" key={suggestion.id}>
            <strong>{suggestion.status} · {suggestion.suggestion_type}</strong>
            <p>{suggestion.content}</p>
            {suggestion.status === 'pending' && (
              <div className="toolbar">
                <button className="primary" onClick={async () => { await api.acceptSuggestion(suggestion.id, '运营'); await load(); }}><Check size={16} />写入记忆</button>
                <button onClick={async () => { await api.rejectSuggestion(suggestion.id, '运营'); await load(); }}><X size={16} />忽略建议</button>
              </div>
            )}
          </article>
        ))}
        {suggestions.length === 0 && <p className="muted">暂无待确认建议。</p>}
      </section>
    </main>
  );
}
