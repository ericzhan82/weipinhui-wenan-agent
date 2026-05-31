import { History, Quote, Search, Sparkles } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';

export function HistoryCasePage() {
  const [keyword, setKeyword] = useState('');
  const [items, setItems] = useState<Array<Record<string, unknown>>>([]);
  const load = async () => setItems(await api.historyCases(keyword));
  useEffect(() => { void load(); }, []);
  return (
    <main className="page ai-page">
      <div className="page-head ai-head">
        <div>
          <span className="eyebrow"><History size={14} />case retrieval</span>
          <h1>案例记忆检索</h1>
          <p>让模型生成前能看到相近品类、卖点和颜色表达，减少从空白开始的随机感。</p>
        </div>
      </div>
      <section className="panel case-memory-panel">
        <div className="toolbar searchbar">
          <Search size={17} />
          <input value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="按款号、品类、卖点、场景检索模型参考" onKeyDown={(event) => event.key === 'Enter' && void load()} />
          <button onClick={load}>召回案例</button>
        </div>
        <div className="case-grid">
          {items.map((item) => (
            <article className="case-card" key={String(item.id)}>
              <span className="task-eyebrow"><Quote size={14} />可复用表达</span>
              <strong>{String(item.style_no || '未命名款号')}</strong>
              <p>{String(item.title || '')}</p>
              <small>{Array.isArray(item.main_image_tags) ? item.main_image_tags.join(' / ') : ''} · {String(item.color_copy || '')}</small>
            </article>
          ))}
          {items.length === 0 && (
            <div className="empty-state">
              <Sparkles size={26} />
              <strong>还没有可召回案例</strong>
              <p>在文案工作台把定稿保存为优秀案例后，模型会在这里形成可检索记忆。</p>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
