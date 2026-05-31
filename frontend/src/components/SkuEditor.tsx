import { Image, Palette, Plus, Trash2 } from 'lucide-react';
import type { ProductSku } from '../types';

type Props = {
  skus: ProductSku[];
  onChange: (skus: ProductSku[]) => void;
};

export function SkuEditor({ skus, onChange }: Props) {
  const update = (index: number, patch: Partial<ProductSku>) => {
    const next = [...skus];
    next[index] = { ...next[index], ...patch };
    onChange(next);
  };
  const filledColors = skus.filter((sku) => sku.color_name || sku.color_code || sku.sku_no).length;

  return (
    <section className="panel color-context-panel">
      <div className="panel-head">
        <div>
          <h2><Palette size={18} />颜色素材</h2>
          <p className="muted">颜色、色号和图片会参与颜色词、主图卖点与场景表达推理。</p>
        </div>
        <button className="icon-button" title="添加SKC" onClick={() => onChange([...skus, {}])}>
          <Plus size={18} />
        </button>
      </div>
      <div className="color-context-summary">
        <span>{skus.length} 个颜色槽</span>
        <span>{filledColors} 个已提供素材</span>
        <span>{skus.some((sku) => sku.image_url) ? '含图片链接' : '暂无图片链接'}</span>
      </div>
      <div className="color-card-grid">
        {skus.map((sku, index) => (
          <article className="color-card" key={sku.id || index}>
            <div className="color-card-head">
              <span className="color-swatch" style={{ background: sku.color_code?.startsWith('#') ? sku.color_code : undefined }}>
                {!sku.color_code?.startsWith('#') && <Palette size={16} />}
              </span>
              <div>
                <strong>{sku.color_name || `颜色素材 ${index + 1}`}</strong>
                <small>{sku.sku_no || '待填写 SKC'}</small>
              </div>
              <button className="icon-button danger" title="删除SKC" onClick={() => onChange(skus.filter((_, itemIndex) => itemIndex !== index))}>
                <Trash2 size={16} />
              </button>
            </div>
            <div className="color-fields">
              <label>
                <span>颜色</span>
                <input value={sku.color_name || ''} onChange={(event) => update(index, { color_name: event.target.value })} />
              </label>
              <label>
                <span>色号</span>
                <input value={sku.color_code || ''} onChange={(event) => update(index, { color_code: event.target.value })} />
              </label>
              <label>
                <span>SKC</span>
                <input value={sku.sku_no || ''} onChange={(event) => update(index, { sku_no: event.target.value })} />
              </label>
              <label className="span-2">
                <span><Image size={13} />图片链接</span>
                <input value={sku.image_url || ''} onChange={(event) => update(index, { image_url: event.target.value })} />
              </label>
              <label className="span-2">
                <span>颜色备注</span>
                <input value={sku.color_remark || ''} onChange={(event) => update(index, { color_remark: event.target.value })} />
              </label>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
