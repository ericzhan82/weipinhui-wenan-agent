import { Boxes, CheckCircle2, CircleDashed, Layers3, Sparkles, Target } from 'lucide-react';
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

const contextSlots: Array<[string, Array<keyof Product>]> = [
  ['商品身份', ['style_no', 'product_no', 'category_3', 'category_4']],
  ['人群场景', ['age_range', 'gender', 'season', 'scene']],
  ['核心卖点', ['fba']],
  ['运营备注', ['remark', 'updated_by']],
];

export function ProductForm({ value, onChange }: Props) {
  const setField = (field: keyof Product, next: string) => onChange({ ...value, [field]: next });
  const filledFields = fields.filter(([field]) => String(value[field] || '').trim()).length;
  const completion = Math.round((filledFields / fields.length) * 100);
  const hasCoreContext = Boolean(value.category_3 && value.category_4 && value.fba);

  return (
    <div className="context-composer">
      <div className="context-head">
        <div>
          <h2><Sparkles size={18} />模型上下文</h2>
          <p>这些资料会作为文案生成的输入。先组织上下文，再让模型产出草稿。</p>
        </div>
        <div className="context-score">
          <strong>{completion}%</strong>
          <span>{hasCoreContext ? '可生成' : '缺核心上下文'}</span>
        </div>
      </div>

      <div className="context-map">
        {contextSlots.map(([slot, slotFields]) => {
          const ready = slotFields.some((field) => String(value[field] || '').trim());
          return (
            <div className={ready ? 'context-slot ready' : 'context-slot'} key={slot}>
              {ready ? <CheckCircle2 size={16} /> : <CircleDashed size={16} />}
              <span>{slot}</span>
              <b>{slotFields.filter((field) => String(value[field] || '').trim()).length}/{slotFields.length}</b>
            </div>
          );
        })}
      </div>

      <div className="context-brief">
        <div>
          <span><Target size={14} />当前模型会理解为</span>
          <strong>{value.category_3 || '待补品类'} / {value.category_4 || '待补细分'} · {value.gender || '待补性别'} · {value.season || '待补季节'}</strong>
        </div>
        <div>
          <span><Boxes size={14} />关键卖点素材</span>
          <p>{value.fba || '还没有 FBA/设计师卖点，模型会缺少生成依据。'}</p>
        </div>
      </div>

      <div className="raw-context">
        <h3><Layers3 size={16} />可编辑原始资料</h3>
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
      </div>
    </div>
  );
}
