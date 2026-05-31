import type { Product } from '../types';

type Props = {
  value: Product;
  onChange: (value: Product) => void;
};

const fields: Array<[keyof Product, string, 'input' | 'textarea']> = [
  ['style_no', '款号', 'input'],
  ['product_no', '货号', 'input'],
  ['category_3', '三级品类', 'input'],
  ['category_4', '四级品类', 'input'],
  ['age_range', '适用岁段', 'input'],
  ['gender', '性别', 'input'],
  ['season', '季节', 'input'],
  ['scene', '场景', 'input'],
  ['fba', 'FBA/设计师卖点', 'textarea'],
  ['remark', '备注', 'textarea'],
  ['updated_by', '操作人', 'input'],
];

export function ProductForm({ value, onChange }: Props) {
  const setField = (field: keyof Product, next: string) => onChange({ ...value, [field]: next });
  return (
    <div className="form-grid">
      {fields.map(([field, label, kind]) => (
        <label className={kind === 'textarea' ? 'span-2' : ''} key={field}>
          <span>{label}</span>
          {kind === 'textarea' ? (
            <textarea value={(value[field] as string) || ''} onChange={(event) => setField(field, event.target.value)} rows={3} />
          ) : (
            <input value={(value[field] as string) || ''} onChange={(event) => setField(field, event.target.value)} />
          )}
        </label>
      ))}
    </div>
  );
}
