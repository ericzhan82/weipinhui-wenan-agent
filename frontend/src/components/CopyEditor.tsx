import { CheckCircle2, Save, Sparkles, Wand2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import type { CopyOutput, ValidationResult } from '../types';
import { ValidationPanel } from './ValidationPanel';

type Props = {
  copy?: CopyOutput | null;
  onGenerate: () => Promise<CopyOutput | void>;
  onRewrite: (instruction: string) => Promise<CopyOutput | void>;
  onSave: (payload: { title: string; main_image_tags: string[]; color_copy: string; operator_name: string; change_reason: string }) => Promise<void>;
  onValidate: (payload: Partial<CopyOutput> & { operator_name: string }) => Promise<ValidationResult>;
};

export function CopyEditor({ copy, onGenerate, onRewrite, onSave, onValidate }: Props) {
  const [title, setTitle] = useState('');
  const [tags, setTags] = useState(['', '', '']);
  const [colorCopy, setColorCopy] = useState('');
  const [operatorName, setOperatorName] = useState('运营');
  const [changeReason, setChangeReason] = useState('人工优化');
  const [instruction, setInstruction] = useState('标题更突出核心卖点，颜色词更适合夏季');
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [busyAction, setBusyAction] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    setTitle(copy?.title || '');
    setTags([...(copy?.main_image_tags || []), '', '', ''].slice(0, 3));
    setColorCopy(copy?.color_copy || '');
  }, [copy]);

  const payload = {
    title,
    main_image_tags: tags.map((tag) => tag.trim()).filter(Boolean),
    color_copy: colorCopy,
    operator_name: operatorName,
  };

  const runAction = async (actionName: string, action: () => Promise<void>) => {
    setError('');
    setBusyAction(actionName);
    try {
      await action();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusyAction('');
    }
  };

  return (
    <section className="panel copy-panel">
      <div className="panel-head">
        <h2>文案生成与编辑</h2>
        <div className="toolbar">
          <button title="生成文案" disabled={Boolean(busyAction)} onClick={() => runAction('generate', async () => { await onGenerate(); })}>
            <Sparkles size={16} />{busyAction === 'generate' ? '生成中' : '生成'}
          </button>
          <button title="重写文案" disabled={Boolean(busyAction)} onClick={() => runAction('rewrite', async () => { await onRewrite(instruction); })}>
            <Wand2 size={16} />{busyAction === 'rewrite' ? '重写中' : '重写'}
          </button>
          <button title="校验文案" disabled={Boolean(busyAction)} onClick={() => runAction('validate', async () => { setValidation(await onValidate(payload)); })}>
            <CheckCircle2 size={16} />{busyAction === 'validate' ? '校验中' : '校验'}
          </button>
          <button title="保存文案" disabled={Boolean(busyAction)} onClick={() => runAction('save', async () => { await onSave({ ...payload, change_reason: changeReason }); })}>
            <Save size={16} />{busyAction === 'save' ? '保存中' : '保存'}
          </button>
        </div>
      </div>
      {error && <p className="notice error">{error}</p>}
      <div className="form-grid">
        <label className="span-2">
          <span>唯品标题 <b className={title.length === 29 || title.length === 30 ? 'ok' : 'bad'}>{title.length}/29-30</b></span>
          <input className={title.length === 29 || title.length === 30 ? '' : 'invalid'} value={title} onChange={(event) => setTitle(event.target.value)} />
        </label>
        {tags.map((tag, index) => (
          <label key={index}>
            <span>主图卖点{index + 1} <b className={tag.length >= 4 && tag.length <= 10 ? 'ok' : 'bad'}>{tag.length}/4-10</b></span>
            <input className={tag && (tag.length < 4 || tag.length > 10) ? 'invalid' : ''} value={tag} onChange={(event) => setTags(tags.map((item, itemIndex) => (itemIndex === index ? event.target.value : item)))} />
          </label>
        ))}
        <label>
          <span>颜色词文案 <b className={colorCopy.length >= 4 && colorCopy.length <= 6 ? 'ok' : 'bad'}>{colorCopy.length}/4-6</b></span>
          <input className={colorCopy && (colorCopy.length < 4 || colorCopy.length > 6) ? 'invalid' : ''} value={colorCopy} onChange={(event) => setColorCopy(event.target.value)} />
        </label>
        <label>
          <span>操作人</span>
          <input value={operatorName} onChange={(event) => setOperatorName(event.target.value)} />
        </label>
        <label>
          <span>保存原因</span>
          <input value={changeReason} onChange={(event) => setChangeReason(event.target.value)} />
        </label>
        <label className="span-2">
          <span>重写要求</span>
          <input value={instruction} onChange={(event) => setInstruction(event.target.value)} />
        </label>
      </div>
      <ValidationPanel result={validation} />
    </section>
  );
}
