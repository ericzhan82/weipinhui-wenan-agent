import { BadgeCheck, FileClock, Save, Workflow } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { CopyEditor } from '../components/CopyEditor';
import { ProductForm } from '../components/ProductForm';
import { SkuEditor } from '../components/SkuEditor';
import { VersionPanel } from '../components/VersionPanel';
import type { CopyOutput, CopyVersion, HotSearchConfig, Product, ValidationResult } from '../types';

export function ProductDetailPage({ id }: { id: number }) {
  const [product, setProduct] = useState<Product | null>(null);
  const [loadedSkuIds, setLoadedSkuIds] = useState<number[]>([]);
  const [versions, setVersions] = useState<CopyVersion[]>([]);
  const [hotSearchConfig, setHotSearchConfig] = useState<HotSearchConfig | null>(null);
  const [message, setMessage] = useState('');
  const [activeBatchNo, setActiveBatchNo] = useState('');

  const load = async () => {
    const [next, config] = await Promise.all([
      api.product(id),
      api.hotSearchConfig().catch(() => null),
    ]);
    setProduct(next);
    setHotSearchConfig(config);
    setLoadedSkuIds(next.skus.map((sku) => sku.id).filter((skuId): skuId is number => Boolean(skuId)));
    setVersions(await api.versions(id));
  };
  useEffect(() => { void load(); }, [id]);
  useEffect(() => {
    if (!activeBatchNo) return undefined;
    const timer = window.setInterval(async () => {
      try {
        const detail = await api.copyBatch(activeBatchNo);
        if (['completed', 'completed_with_errors', 'canceled'].includes(detail.batch.status)) {
          await load();
          setMessage(`生成任务 ${activeBatchNo} 已${detail.batch.success_count ? '完成' : '结束'}。`);
          setActiveBatchNo('');
        }
      } catch (error) {
        setMessage(error instanceof Error ? error.message : String(error));
      }
    }, 4000);
    return () => window.clearInterval(timer);
  }, [activeBatchNo, id]);

  if (!product) return <main className="page"><p>加载中...</p></main>;

  const refreshCopy = async (next?: CopyOutput | void) => {
    if (!next) {
      await load();
      return;
    }
    const refreshed = await api.product(id);
    setProduct({ ...refreshed, copy_output: { ...(refreshed.copy_output || {}), ...next } });
    setLoadedSkuIds(refreshed.skus.map((sku) => sku.id).filter((skuId): skuId is number => Boolean(skuId)));
    setVersions(await api.versions(id));
  };

  return (
    <main className="page ai-page">
      <div className="page-head ai-head">
        <div>
          <span className="eyebrow"><Workflow size={14} />active generation task</span>
          <h1>{product.style_no || product.product_no}</h1>
          <p>{product.category_3} / {product.category_4} · {product.gender} · {product.season}</p>
        </div>
        <div className="toolbar">
          <button onClick={async () => {
            await api.saveHistory(id, '人工确认优秀案例', product.updated_by || '运营');
            setMessage('已保存为优秀案例');
          }}><BadgeCheck size={16} />优秀案例</button>
          <button className="primary" onClick={async () => {
            const { skus: _skus, copy_output: _copy, ...payload } = product;
            setProduct(await api.updateProduct(id, payload));
            const currentIds = product.skus.map((sku) => sku.id).filter((skuId): skuId is number => Boolean(skuId));
            for (const removedId of loadedSkuIds.filter((skuId) => !currentIds.includes(skuId))) {
              await api.deleteSku(removedId);
            }
            for (const sku of product.skus) {
              if (sku.id) await api.updateSku(sku.id, sku);
              else await api.createSku(id, sku);
            }
            await load();
            setMessage('模型上下文已保存');
          }}><Save size={16} />保存上下文</button>
        </div>
      </div>
      {message && <p className="notice">{message}</p>}
      {activeBatchNo && (
        <p className="notice task-job-notice">
          <FileClock size={16} />后台生成任务已创建：
          <a href={`#/copy-batches/${activeBatchNo}`}>{activeBatchNo}</a>
          。可以离开页面，任务会继续执行。
        </p>
      )}
      <section className="panel">
        <ProductForm value={product} onChange={setProduct} />
      </section>
      <SkuEditor skus={product.skus} onChange={(skus) => setProduct({ ...product, skus })} />
      <CopyEditor
        copy={product.copy_output}
        hotSearchConfig={hotSearchConfig}
        activeBatchNo={activeBatchNo}
        onGenerate={async (useHotSearch) => {
          const batch = await api.generateCopyJob(id, useHotSearch);
          setActiveBatchNo(batch.batch_no);
          setMessage(`已加入后台生成队列：${batch.batch_no}`);
          await load();
          return batch;
        }}
        onRewrite={async (instruction) => refreshCopy(await api.rewriteCopy(id, instruction, product.updated_by || '运营'))}
        onSave={async (payload) => {
          await refreshCopy(await api.saveCopy(id, payload));
          setMessage('文案已保存并创建版本');
        }}
        onValidate={async (payload): Promise<ValidationResult> => api.validateCopy(id, payload)}
      />
      <VersionPanel versions={versions} onRestore={async (versionId) => refreshCopy(await api.restoreVersion(id, versionId))} />
    </main>
  );
}
