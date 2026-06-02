import {
  CheckCircle2,
  DatabaseZap,
  FileSpreadsheet,
  FileUp,
  Flame,
  RotateCcw,
  ScanLine,
  Settings2,
  Sparkles,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { HotSearchConfig } from '../types';

type IntakeKind = 'product' | 'hot-search';

function ResultGrid({ result }: { result: Record<string, unknown> | null }) {
  if (!result) return null;
  return (
    <div className="ingest-result-grid">
      {Object.entries(result).map(([key, value]) => (
        <div key={key}>
          <span>{key}</span>
          <strong>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</strong>
        </div>
      ))}
    </div>
  );
}

export function ExcelImportPage() {
  const [activeKind, setActiveKind] = useState<IntakeKind>('product');
  const [productFile, setProductFile] = useState<File | null>(null);
  const [hotSearchFile, setHotSearchFile] = useState<File | null>(null);
  const [productResult, setProductResult] = useState<Record<string, unknown> | null>(null);
  const [hotSearchResult, setHotSearchResult] = useState<Record<string, unknown> | null>(null);
  const [hotSearchConfig, setHotSearchConfig] = useState<HotSearchConfig | null>(null);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    void api.hotSearchConfig().then(setHotSearchConfig).catch(() => setHotSearchConfig(null));
  }, []);

  const run = async (label: string, action: () => Promise<void>) => {
    setError('');
    setBusy(label);
    try {
      await action();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusy('');
    }
  };

  const importProductExcel = async () => {
    if (!productFile) return;
    await run('product', async () => {
      setProductResult(await api.importExcel(productFile));
      setActiveKind('product');
    });
  };

  const importHotSearchExcel = async () => {
    if (!hotSearchFile) return;
    await run('hot-search', async () => {
      setHotSearchResult(await api.importHotSearch(hotSearchFile));
      setActiveKind('hot-search');
    });
  };

  const toggleHotSearchDefault = async () => {
    const nextEnabled = !hotSearchConfig?.enabled_by_default;
    await run('config', async () => {
      setHotSearchConfig(await api.updateHotSearchConfig({ enabled_by_default: nextEnabled, updated_by: '运营' }));
    });
  };

  return (
    <main className="page ai-page">
      <div className="page-head ai-head">
        <div>
          <span className="eyebrow"><DatabaseZap size={14} />material intake</span>
          <h1>素材接入管线</h1>
          <p>把商品素材和热搜词数据源接入系统，生成可配置的标题增强任务。</p>
        </div>
        <div className="toolbar">
          <button disabled={!productFile || Boolean(busy)} onClick={importProductExcel}>
            <FileUp size={16} />{busy === 'product' ? '商品接入中' : '接入商品素材'}
          </button>
          <button className="primary" disabled={!hotSearchFile || Boolean(busy)} onClick={importHotSearchExcel}>
            <Flame size={16} />{busy === 'hot-search' ? '热搜词接入中' : '接入热搜词'}
          </button>
        </div>
      </div>

      {error && <p className="notice error">{error}</p>}

      <section className="intake-flow">
        <div className="intake-step ready"><FileSpreadsheet size={18} /><span>接入类型</span><b>商品 / 热搜词</b></div>
        <div className={(productFile || hotSearchFile) ? 'intake-step ready' : 'intake-step'}><ScanLine size={18} /><span>选择文件</span><b>{productFile?.name || hotSearchFile?.name || '待选择'}</b></div>
        <div className={(productResult || hotSearchResult) ? 'intake-step ready' : 'intake-step'}><Sparkles size={18} /><span>接入结果</span><b>{productResult || hotSearchResult ? '已完成' : '待接入'}</b></div>
      </section>

      <section className="hot-search-config-panel">
        <div>
          <span className="task-eyebrow"><Settings2 size={14} />热搜词全局配置</span>
          <strong>默认{hotSearchConfig?.enabled_by_default ? '开启' : '关闭'}热搜词标题增强</strong>
          <p>商品详情页仍可按“本次开启 / 本次关闭”覆盖全局默认值。</p>
        </div>
        <button className={hotSearchConfig?.enabled_by_default ? 'primary' : ''} disabled={Boolean(busy)} onClick={toggleHotSearchDefault}>
          <RotateCcw size={16} />{busy === 'config' ? '保存中' : hotSearchConfig?.enabled_by_default ? '改为默认关闭' : '改为默认开启'}
        </button>
      </section>

      <div className="intake-tabs">
        <button className={activeKind === 'product' ? 'active' : ''} onClick={() => setActiveKind('product')}>
          <FileSpreadsheet size={16} />商品素材接入
        </button>
        <button className={activeKind === 'hot-search' ? 'active' : ''} onClick={() => setActiveKind('hot-search')}>
          <Flame size={16} />热搜词数据源
        </button>
      </div>

      {activeKind === 'product' ? (
        <section className="panel upload-panel intake-panel">
          <label className="file-drop">
            <FileUp size={26} />
            <strong>{productFile ? productFile.name : '选择 Excel 商品素材表'}</strong>
            <span>系统会抽取款号、货号、FBA、品类、颜色、SKC 和图片链接，写入 AI 任务上下文。</span>
            <input type="file" accept=".xlsx" onChange={(event) => setProductFile(event.target.files?.[0] || null)} />
          </label>
          {productResult && (
            <div className="ingest-result">
              <div className="panel-head">
                <h2><CheckCircle2 size={18} />商品接入结果</h2>
                <a className="button primary" href="#/products">查看任务队列</a>
              </div>
              <ResultGrid result={productResult} />
            </div>
          )}
        </section>
      ) : (
        <section className="panel upload-panel intake-panel hot-search-intake">
          <label className="file-drop">
            <Flame size={26} />
            <strong>{hotSearchFile ? hotSearchFile.name : '选择热搜词数据源 .xlsx'}</strong>
            <span>仅需上传包含“搜索词主分类、关键词、排名、搜索UV指数、机会指数、成交金额指数、销售量指数”的热搜词数据源。</span>
            <input type="file" accept=".xlsx" onChange={(event) => setHotSearchFile(event.target.files?.[0] || null)} />
          </label>
          {hotSearchResult && (
            <div className="ingest-result">
              <div className="panel-head">
                <h2><CheckCircle2 size={18} />热搜词接入结果</h2>
                <a className="button primary" href="#/products">去生成标题</a>
              </div>
              <ResultGrid result={hotSearchResult} />
            </div>
          )}
        </section>
      )}
    </main>
  );
}
