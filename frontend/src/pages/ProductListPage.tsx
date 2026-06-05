import { AlertTriangle, ArrowRight, CheckCircle2, Database, Download, FileCheck2, FileClock, Filter, Plus, RotateCcw, Search, Sparkles, Trash2, Workflow } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { api, type ProductFilters } from '../api/client';
import type { Product } from '../types';

type Props = {
  workspaceId: number | null;
};

const statusOptions = [
  ['', '全部状态'],
  ['draft', '待补素材'],
  ['ready', '可生成'],
  ['queued', '已排队'],
  ['generating', '生成中'],
  ['generated', '已生成'],
  ['failed', '生成失败'],
] as const;

function statusLabel(status?: string) {
  return statusOptions.find(([value]) => value === status)?.[1] || status || '待补素材';
}

function contextReady(product: Product) {
  return Boolean(product.category_3 && product.category_4 && product.fba);
}

export function ProductListPage({ workspaceId }: Props) {
  const [items, setItems] = useState<Product[]>([]);
  const [keyword, setKeyword] = useState('');
  const [status, setStatus] = useState('');
  const [contextStatus, setContextStatus] = useState('');
  const [copyState, setCopyState] = useState('');
  const [gender, setGender] = useState('');
  const [season, setSeason] = useState('');
  const [message, setMessage] = useState('');
  const [loadError, setLoadError] = useState('');
  const [loading, setLoading] = useState(false);
  const [useHotSearch, setUseHotSearch] = useState(false);
  const [overwriteExisting, setOverwriteExisting] = useState(false);
  const [batchBusy, setBatchBusy] = useState(false);
  const filters = useMemo<ProductFilters>(() => ({
    keyword: keyword.trim() || undefined,
    status: status || undefined,
    gender: gender || undefined,
    season: season || undefined,
    context_status: contextStatus || undefined,
    copy_state: copyState || undefined,
  }), [keyword, status, gender, season, contextStatus, copyState]);

  const load = async () => {
    setLoading(true);
    setLoadError('');
    try {
      setItems(await api.products(filters));
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : String(error));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, [workspaceId]);
  useEffect(() => {
    const onFocus = () => { void load(); };
    window.addEventListener('focus', onFocus);
    return () => window.removeEventListener('focus', onFocus);
  }, [workspaceId, filters]);

  const readyCount = items.filter(contextReady).length;
  const generatedCount = items.filter((product) => product.copy_output?.title).length;
  const runningCount = items.filter((product) => product.status === 'queued' || product.status === 'generating').length;
  const failedCount = items.filter((product) => product.status === 'failed').length;

  const exportExcel = async () => {
    const result = await api.exportExcel(keyword);
    window.location.href = result.download_url;
  };

  const createBatch = async () => {
    setBatchBusy(true);
    setMessage('');
    try {
      const batch = await api.createCopyBatch({
        ...filters,
        overwrite_existing: overwriteExisting,
        use_hot_search: useHotSearch,
      });
      setMessage(`批量任务 ${batch.batch_no} 已创建：${batch.pending_count} 条待生成，${batch.skipped_count} 条已跳过。`);
      window.location.hash = `#/copy-batches/${batch.batch_no}`;
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error));
    } finally {
      setBatchBusy(false);
    }
  };

  const resetFilters = () => {
    setKeyword('');
    setStatus('');
    setContextStatus('');
    setCopyState('');
    setGender('');
    setSeason('');
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
          <button disabled={batchBusy} onClick={createBatch}><FileClock size={16} />{batchBusy ? '创建中' : '创建批量任务'}</button>
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
          <span>生成中/排队</span>
          <strong>{runningCount}</strong>
        </div>
        <div>
          <AlertTriangle size={18} />
          <span>生成失败</span>
          <strong>{failedCount}</strong>
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
          <button disabled={loading} onClick={load}>{loading ? '刷新中' : '更新队列'}</button>
        </div>
        <div className="filter-bar">
          <span><Filter size={15} />筛选</span>
          <select value={status} onChange={(event) => setStatus(event.target.value)}>
            {statusOptions.map(([value, label]) => <option key={value || 'all'} value={value}>{label}</option>)}
          </select>
          <select value={contextStatus} onChange={(event) => setContextStatus(event.target.value)}>
            <option value="">全部上下文</option>
            <option value="ready">上下文可用</option>
            <option value="missing">待补上下文</option>
          </select>
          <select value={copyState} onChange={(event) => setCopyState(event.target.value)}>
            <option value="">全部生成状态</option>
            <option value="generated">已有文案</option>
            <option value="not_generated">未生成</option>
          </select>
          <select value={gender} onChange={(event) => setGender(event.target.value)}>
            <option value="">全部性别</option>
            <option value="女童">女童</option>
            <option value="男童">男童</option>
            <option value="中性">中性</option>
          </select>
          <select value={season} onChange={(event) => setSeason(event.target.value)}>
            <option value="">全部季节</option>
            <option value="春季">春季</option>
            <option value="夏季">夏季</option>
            <option value="秋季">秋季</option>
            <option value="冬季">冬季</option>
          </select>
          <button onClick={load}><Search size={15} />应用</button>
          <button onClick={resetFilters}><RotateCcw size={15} />重置</button>
        </div>
        <div className="batch-create-strip">
          <div>
            <strong><FileClock size={16} />按当前筛选创建批量生成任务</strong>
            <span>{keyword.trim() ? `筛选关键词：${keyword.trim()}` : '未输入关键词时会纳入当前工作空间匹配筛选的商品'}</span>
          </div>
          <label className="check-row">
            <input type="checkbox" checked={useHotSearch} onChange={(event) => setUseHotSearch(event.target.checked)} />
            启用热搜词
          </label>
          <label className="check-row">
            <input type="checkbox" checked={overwriteExisting} onChange={(event) => setOverwriteExisting(event.target.checked)} />
            覆盖已有标题
          </label>
          <button className="primary" disabled={batchBusy} onClick={createBatch}><FileClock size={16} />创建任务号</button>
        </div>
        {loadError && (
          <p className="notice error compact-notice">
            <AlertTriangle size={16} />后端连接暂时不可用，已保留上一次成功加载的队列。{loadError}
          </p>
        )}
        {message && <p className="notice">{message}</p>}
        <div className="task-queue">
          {items.map((product) => {
            const isContextReady = contextReady(product);
            const title = product.copy_output?.title;
            return (
              <article className="queue-card" key={product.id}>
                <div className="queue-card-top">
                  <div>
                    <span className={isContextReady ? 'status ready' : 'status'}>{isContextReady ? '上下文可用' : '待补上下文'}</span>
                    <span className={`status task-status ${product.status || 'draft'}`}>{statusLabel(product.status)}</span>
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
                  <span><FileCheck2 size={14} />{statusLabel(product.status)}</span>
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
