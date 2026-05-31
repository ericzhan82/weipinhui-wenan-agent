import { BadgeCheck, Save } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { CopyEditor } from '../components/CopyEditor';
import { ProductForm } from '../components/ProductForm';
import { SkuEditor } from '../components/SkuEditor';
import { VersionPanel } from '../components/VersionPanel';
import type { CopyOutput, CopyVersion, Product, ValidationResult } from '../types';

export function ProductDetailPage({ id }: { id: number }) {
  const [product, setProduct] = useState<Product | null>(null);
  const [loadedSkuIds, setLoadedSkuIds] = useState<number[]>([]);
  const [versions, setVersions] = useState<CopyVersion[]>([]);
  const [message, setMessage] = useState('');

  const load = async () => {
    const next = await api.product(id);
    setProduct(next);
    setLoadedSkuIds(next.skus.map((sku) => sku.id).filter((skuId): skuId is number => Boolean(skuId)));
    setVersions(await api.versions(id));
  };
  useEffect(() => { void load(); }, [id]);

  if (!product) return <main className="page"><p>加载中...</p></main>;

  const refreshCopy = async (next?: CopyOutput | void) => {
    if (next) setProduct({ ...product, copy_output: next });
    await load();
  };

  return (
    <main className="page">
      <div className="page-head">
        <div>
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
            setMessage('商品资料已保存');
          }}><Save size={16} />保存资料</button>
        </div>
      </div>
      {message && <p className="notice">{message}</p>}
      <section className="panel">
        <ProductForm value={product} onChange={setProduct} />
      </section>
      <SkuEditor skus={product.skus} onChange={(skus) => setProduct({ ...product, skus })} />
      <CopyEditor
        copy={product.copy_output}
        onGenerate={async () => refreshCopy(await api.generateCopy(id))}
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
