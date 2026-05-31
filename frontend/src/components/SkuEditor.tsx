import { Plus, Trash2 } from 'lucide-react';
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
  return (
    <section className="panel">
      <div className="panel-head">
        <h2>SKC/颜色</h2>
        <button className="icon-button" title="添加SKC" onClick={() => onChange([...skus, {}])}>
          <Plus size={18} />
        </button>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>颜色</th>
              <th>色号</th>
              <th>SKC</th>
              <th>图片链接</th>
              <th>备注</th>
              <th aria-label="操作"></th>
            </tr>
          </thead>
          <tbody>
            {skus.map((sku, index) => (
              <tr key={sku.id || index}>
                <td><input value={sku.color_name || ''} onChange={(event) => update(index, { color_name: event.target.value })} /></td>
                <td><input value={sku.color_code || ''} onChange={(event) => update(index, { color_code: event.target.value })} /></td>
                <td><input value={sku.sku_no || ''} onChange={(event) => update(index, { sku_no: event.target.value })} /></td>
                <td><input value={sku.image_url || ''} onChange={(event) => update(index, { image_url: event.target.value })} /></td>
                <td><input value={sku.color_remark || ''} onChange={(event) => update(index, { color_remark: event.target.value })} /></td>
                <td>
                  <button className="icon-button danger" title="删除SKC" onClick={() => onChange(skus.filter((_, itemIndex) => itemIndex !== index))}>
                    <Trash2 size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
