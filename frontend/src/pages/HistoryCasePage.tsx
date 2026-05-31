import { Search } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';

export function HistoryCasePage() {
  const [keyword, setKeyword] = useState('');
  const [items, setItems] = useState<Array<Record<string, unknown>>>([]);
  const load = async () => setItems(await api.historyCases(keyword));
  useEffect(() => { void load(); }, []);
  return (
    <main className="page">
      <div className="page-head">
        <div>
          <h1>历史优秀案例</h1>
          <p>沉淀人工确认过的高质量文案，作为后续生成参考。</p>
        </div>
      </div>
      <section className="panel">
        <div className="toolbar searchbar">
          <Search size={17} />
          <input value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="款号、品类、卖点、场景" />
          <button onClick={load}>搜索</button>
        </div>
        <div className="case-grid">
          {items.map((item) => (
            <article className="case-card" key={String(item.id)}>
              <strong>{String(item.style_no || '未命名款号')}</strong>
              <p>{String(item.title || '')}</p>
              <small>{Array.isArray(item.main_image_tags) ? item.main_image_tags.join(' / ') : ''} · {String(item.color_copy || '')}</small>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
