import { ArrowRight, CheckCircle2, Database, Download, FileCheck2, Plus, Search, Sparkles, Trash2, Workflow } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { Product } from '../types';

export function ProductListPage() {
  const [items, setItems] = useState<Product[]>([]);
  const [keyword, setKeyword] = useState('');
  const [message, setMessage] = useState('');
  const load = async () => setItems(await api.products(keyword));
  useEffect(() => { void load(); }, []);

  const readyCount = items.filter((product) => product.category_3 && product.category_4 && product.fba).length;
  const generatedCount = items.filter((product) => product.copy_output?.title).length;
  const draftCount = items.length - generatedCount;

  const exportExcel = async () => {
    const result = await api.exportExcel(keyword);
    window.location.href = result.download_url;
  };

  return (
    <main className="page ai-page">
      <div className="page-head ai-head">
        <div>
          <span className="eyebrow"><Workflow size={14} />AI copy mission control</span>
          <h1>文案生成任务队列</h1>
          <p>每个商品是一条 AI 任务：先看上下文是否可用，再进入生成、校验、定稿和沉淀。</p>
        </div>
        <div className="toolbar">
          <button onClick={exportExcel}><Download size={16} />导出任务结果</button>
          <a className="button primary" href="#/products/new"><Plus size={16} />新建上下文</a>
        </div>
      </div>

      <section className="ai-command-strip">
        <div>
          <Database size={18} />
          <span>上下文任务</span>
          <strong>{items.length}</strong>
        </div>
        <div>
          <CheckCircle2 size={18} />
          <span>可直接生成</span>
          <strong>{readyCount}</strong>
        </div>
        <div>
          <Sparkles size={18} />
          <span>已有草稿</span>
          <strong>{generatedCount}</strong>
        </div>
        <div>
          <FileCheck2 size={18} />
          <span>待模型处理</span>
          <strong>{draftCount}</strong>
        </div>
      </section>

      <section className="panel task-queue-panel">
        <div className="panel-head">
          <div>
            <h2>生成队列</h2>
            <p className="muted">优先处理上下文完整、但尚未产出文案的商品。</p>
          </div>
        </div>
        <div className="toolbar searchbar">
          <Search size={17} />
          <input value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="搜索款号、货号、品类、FBA 上下文" onKeyDown={(event) => event.key === 'Enter' && void load()} />
          <button onClick={load}>更新队列</button>
        </div>
        {message && <p className="notice">{message}</p>}
        <div className="task-queue">
          {items.map((product) => {
            const contextReady = Boolean(product.category_3 && product.category_4 && product.fba);
            const title = product.copy_output?.title;
            return (
              <article className="queue-card" key={product.id}>
                <div className="queue-card-top">
                  <div>
                    <span className={contextReady ? 'status ready' : 'status'}>{contextReady ? '上下文可用' : '待补上下文'}</span>
                    <h2>{product.style_no || product.product_no || `商品 ${product.id}`}</h2>
                    <p>{product.category_3 || '待补品类'} / {product.category_4 || '待补细分'} · {product.gender || '待补人群'} · {product.season || '待补季节'}</p>
                  </div>
                  <a className="button primary" href={`#/products/${product.id}`}>
                    进入生成 <ArrowRight size={16} />
                  </a>
                </div>
                <div className="queue-signals">
                  <span><Database size={14} />{product.fba ? '有卖点素材' : '缺卖点素材'}</span>
                  <span><Sparkles size={14} />{title ? '已有模型草稿' : '未生成'}</span>
                  <span><FileCheck2 size={14} />{product.status || 'draft'}</span>
                </div>
                <div className="queue-output">
                  <b>{title || '等待模型生成首版标题'}</b>
                  <small>{product.copy_output?.main_image_tags?.join(' / ') || product.fba || '补充 FBA、场景和颜色素材后，模型输出会更稳定。'}</small>
                </div>
                <div className="queue-actions">
                  <a className="button" href={`#/products/${product.id}`}>查看上下文</a>
                  <button className="icon-button danger" title="删除商品" onClick={async () => {
                    if (!product.id) return;
                    await api.deleteProduct(product.id);
                    setMessage('已删除商品');
                    await load();
                  }}><Trash2 size={16} /></button>
                </div>
              </article>
            );
          })}
          {items.length === 0 && (
            <div className="empty-state">
              <Sparkles size={26} />
              <strong>队列里还没有商品上下文</strong>
              <p>新建商品或从 Excel 接入素材后，这里会显示可生成任务。</p>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
