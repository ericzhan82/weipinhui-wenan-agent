import { Brain, Check, X } from 'lucide-react';
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
    <main className="page">
      <div className="page-head">
        <div>
          <h1>文案学习中心</h1>
          <p>对比模型生成版与人工编辑版，生成学习报告和待确认规则建议。</p>
        </div>
        <button className="primary" onClick={async () => { await api.analyzeLearning(); await load(); }}><Brain size={16} />生成学习报告</button>
      </div>
      <section className="metrics">
        {Object.entries(summary).map(([key, value]) => <div className="metric" key={key}><strong>{value}</strong><span>{key}</span></div>)}
      </section>
      <section className="panel">
        <div className="panel-head"><h2>学习报告</h2></div>
        {reports.map((report) => (
          <article className="report" key={report.id}>
            <strong>{report.report_title}</strong>
            <p>{report.summary}</p>
            <small>保留词：{report.high_frequency_kept_terms_json.join(' / ') || '暂无'} · 删除词：{report.high_frequency_removed_terms_json.join(' / ') || '暂无'}</small>
          </article>
        ))}
      </section>
      <section className="panel">
        <div className="panel-head"><h2>规则优化建议</h2></div>
        {suggestions.map((suggestion) => (
          <article className="suggestion" key={suggestion.id}>
            <strong>{suggestion.status} · {suggestion.suggestion_type}</strong>
            <p>{suggestion.content}</p>
            {suggestion.status === 'pending' && (
              <div className="toolbar">
                <button onClick={async () => { await api.acceptSuggestion(suggestion.id, '运营'); await load(); }}><Check size={16} />接受</button>
                <button onClick={async () => { await api.rejectSuggestion(suggestion.id, '运营'); await load(); }}><X size={16} />拒绝</button>
              </div>
            )}
          </article>
        ))}
      </section>
    </main>
  );
}
