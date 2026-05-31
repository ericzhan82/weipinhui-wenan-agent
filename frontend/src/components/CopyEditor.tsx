import {
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  Circle,
  Clock3,
  Database,
  FileCheck2,
  FileJson,
  ListChecks,
  Loader2,
  MessageSquareText,
  Save,
  ShieldCheck,
  Sparkles,
  Target,
  Wand2,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import type { CopyOutput, ValidationResult } from '../types';
import { ValidationPanel } from './ValidationPanel';

const generationSteps = [
  { label: '商品资料', detail: '读取品类、FBA、场景与 SKC 色系', icon: Database },
  { label: '规则与案例', detail: '装载禁用词、字数规则和历史优秀案例', icon: ListChecks },
  { label: '模型生成', detail: '调用配置模型生成标题、卖点和颜色词', icon: BrainCircuit },
  { label: 'JSON 解析', detail: '识别中英文字段并归一化输出结构', icon: FileJson },
  { label: '校验修正', detail: '校验字数、空值和禁用词，必要时本地补全', icon: ShieldCheck },
  { label: '版本落库', detail: '写入当前文案并生成可回滚版本', icon: FileCheck2 },
];

const rewritePresets = [
  '标题更突出核心卖点，颜色词更适合夏季',
  '更像唯品会主图文案，表达更短更有货架感',
  '减少夸张词，突出面料舒适和穿着场景',
];

type BusyAction = '' | 'generate' | 'rewrite' | 'validate' | 'save';
type ProcessStatus = 'idle' | 'running' | 'done' | 'error';

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
  const [busyAction, setBusyAction] = useState<BusyAction>('');
  const [error, setError] = useState('');
  const [processStatus, setProcessStatus] = useState<ProcessStatus>(copy ? 'done' : 'idle');
  const [activeStep, setActiveStep] = useState(copy ? generationSteps.length - 1 : 0);
  const [processStartedAt, setProcessStartedAt] = useState<number | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [lastDuration, setLastDuration] = useState<number | null>(null);

  useEffect(() => {
    setTitle(copy?.title || '');
    setTags([...(copy?.main_image_tags || []), '', '', ''].slice(0, 3));
    setColorCopy(copy?.color_copy || '');
  }, [copy]);

  useEffect(() => {
    if (processStatus !== 'running' || !processStartedAt) return undefined;
    const timer = window.setInterval(() => {
      const nextElapsed = Math.floor((Date.now() - processStartedAt) / 1000);
      setElapsedSeconds(nextElapsed);
      setActiveStep(Math.min(generationSteps.length - 1, Math.floor(nextElapsed / 3)));
    }, 400);
    return () => window.clearInterval(timer);
  }, [processStartedAt, processStatus]);

  useEffect(() => {
    if (copy && processStatus === 'idle') {
      setProcessStatus('done');
      setActiveStep(generationSteps.length - 1);
    }
  }, [copy, processStatus]);

  const payload = {
    title,
    main_image_tags: tags.map((tag) => tag.trim()).filter(Boolean),
    color_copy: colorCopy,
    operator_name: operatorName,
  };

  const processProgress = processStatus === 'done'
    ? 100
    : processStatus === 'running'
      ? Math.min(92, 8 + (activeStep / (generationSteps.length - 1)) * 84)
      : 0;

  const runAction = async (actionName: BusyAction, action: () => Promise<void>) => {
    setError('');
    setBusyAction(actionName);
    let actionStartedAt: number | null = null;
    if (actionName === 'generate') {
      actionStartedAt = Date.now();
      setProcessStatus('running');
      setProcessStartedAt(actionStartedAt);
      setElapsedSeconds(0);
      setLastDuration(null);
      setActiveStep(0);
    }
    try {
      await action();
      if (actionName === 'generate') {
        const duration = actionStartedAt ? Math.max(1, Math.ceil((Date.now() - actionStartedAt) / 1000)) : elapsedSeconds;
        setLastDuration(duration);
        setElapsedSeconds(duration);
        setActiveStep(generationSteps.length - 1);
        setProcessStatus('done');
      }
    } catch (caught) {
      const nextError = caught instanceof Error ? caught.message : String(caught);
      setError(nextError);
      if (actionName === 'generate') {
        setProcessStatus('error');
      }
    } finally {
      setBusyAction('');
    }
  };

  return (
    <section className="panel copy-panel ai-workbench">
      <div className="panel-head">
        <div>
          <h2>AI 文案工作台</h2>
          <p className="muted">把商品资料交给模型生成首版文案，再由运营按意图接管和定稿。</p>
        </div>
        <div className="toolbar">
          <button className="primary" title="生成文案" disabled={Boolean(busyAction)} onClick={() => runAction('generate', async () => { await onGenerate(); })}>
            <Sparkles size={16} />{busyAction === 'generate' ? '生成中' : '启动生成'}
          </button>
          <button title="重写文案" disabled={Boolean(busyAction)} onClick={() => runAction('rewrite', async () => { await onRewrite(instruction); })}>
            <Wand2 size={16} />{busyAction === 'rewrite' ? '重写中' : '按意图重写'}
          </button>
          <button title="校验文案" disabled={Boolean(busyAction)} onClick={() => runAction('validate', async () => { setValidation(await onValidate(payload)); })}>
            <CheckCircle2 size={16} />{busyAction === 'validate' ? '校验中' : '规则校验'}
          </button>
          <button title="保存文案" disabled={Boolean(busyAction)} onClick={() => runAction('save', async () => { await onSave({ ...payload, change_reason: changeReason }); })}>
            <Save size={16} />{busyAction === 'save' ? '保存中' : '保存版本'}
          </button>
        </div>
      </div>
      {error && <p className="notice error">{error}</p>}
      <div className="ai-task-board">
        <div className="task-card task-objective">
          <span className="task-eyebrow"><Target size={14} />模型任务</span>
          <strong>生成一版可上架的唯品童装文案</strong>
          <p>目标是一次产出标题、主图卖点和颜色词，并在生成后进入可编辑草稿。</p>
        </div>
        <div className="task-card">
          <span className="task-eyebrow"><Database size={14} />输入上下文</span>
          <div className="task-pills">
            <span>商品资料</span>
            <span>FBA 卖点</span>
            <span>规则库</span>
            <span>历史案例</span>
          </div>
        </div>
        <div className="task-card">
          <span className="task-eyebrow"><FileCheck2 size={14} />输出契约</span>
          <div className="task-contract">
            <span>标题 29-30 字</span>
            <span>3 个主图卖点</span>
            <span>颜色词 4-6 字</span>
          </div>
        </div>
        <div className="task-card task-command">
          <span className="task-eyebrow"><MessageSquareText size={14} />下一轮意图</span>
          <textarea rows={3} value={instruction} onChange={(event) => setInstruction(event.target.value)} />
          <div className="intent-chips">
            {rewritePresets.map((preset) => (
              <button type="button" key={preset} onClick={() => setInstruction(preset)}>{preset}</button>
            ))}
          </div>
        </div>
      </div>
      <div className={`generation-process ${processStatus}`}>
        <div className="process-topline">
          <div>
            <h3><BrainCircuit size={18} />AI 生成过程</h3>
            <p>
              {processStatus === 'running' && `运行中 · ${elapsedSeconds}s`}
              {processStatus === 'done' && `已完成${lastDuration ? ` · ${lastDuration}s` : ''}`}
              {processStatus === 'error' && '生成中断'}
              {processStatus === 'idle' && '待启动'}
            </p>
          </div>
          <span className="process-chip">
            {processStatus === 'running' && <Loader2 size={14} className="spin" />}
            {processStatus === 'done' && <CheckCircle2 size={14} />}
            {processStatus === 'error' && <AlertTriangle size={14} />}
            {processStatus === 'idle' && <Clock3 size={14} />}
            {copy?.llm_model || 'AI Agent'}
          </span>
        </div>
        <div className="process-meter" aria-hidden="true">
          <span style={{ width: `${processProgress}%` }} />
        </div>
        <ol className="process-steps">
          {generationSteps.map((step, index) => {
            const Icon = step.icon;
            const stepState = processStatus === 'done' || index < activeStep ? 'done' : index === activeStep ? processStatus : 'waiting';
            return (
              <li key={step.label} className={stepState}>
                <span className="step-icon">
                  {stepState === 'done' ? <CheckCircle2 size={16} /> : stepState === 'running' ? <Loader2 size={16} className="spin" /> : stepState === 'error' ? <AlertTriangle size={16} /> : <Circle size={16} />}
                </span>
                <span className="step-body">
                  <b><Icon size={14} />{step.label}</b>
                  <small>{step.detail}</small>
                </span>
              </li>
            );
          })}
        </ol>
        <div className="process-evidence">
          <span><b>输入</b>{payload.main_image_tags.length ? `${payload.main_image_tags.length} 个卖点草稿` : '商品资料 + 规则库'}</span>
          <span><b>输出</b>{title ? `${title.length} 字标题 / ${payload.main_image_tags.length} 个主图卖点` : '等待生成'}</span>
          <span><b>依据</b>{copy?.source_basis || '生成后展示模型依据'}</span>
        </div>
      </div>
      <div className="output-head">
        <div>
          <h3>模型输出草稿</h3>
          <p>字段仍可人工接管，保存后才进入正式版本。</p>
        </div>
        <span className={title || payload.main_image_tags.length || colorCopy ? 'draft-state ready' : 'draft-state'}>
          {title || payload.main_image_tags.length || colorCopy ? '有草稿' : '等待生成'}
        </span>
      </div>
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
      </div>
      <ValidationPanel result={validation} />
    </section>
  );
}
