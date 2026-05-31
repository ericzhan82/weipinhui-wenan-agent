import { CheckCircle2, DatabaseZap, FileSpreadsheet, FileUp, ScanLine, Sparkles } from 'lucide-react';
import { useState } from 'react';
import { api } from '../api/client';

export function ExcelImportPage() {
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const resultEntries = result ? Object.entries(result) : [];

  return (
    <main className="page ai-page">
      <div className="page-head ai-head">
        <div>
          <span className="eyebrow"><DatabaseZap size={14} />material intake</span>
          <h1>素材接入管线</h1>
          <p>把 Excel 变成模型可读取的商品上下文、颜色素材和待生成任务。</p>
        </div>
        <button className="primary" disabled={!file} onClick={async () => file && setResult(await api.importExcel(file))}><FileUp size={16} />开始接入</button>
      </div>

      <section className="intake-flow">
        <div className="intake-step ready"><FileSpreadsheet size={18} /><span>读取表格</span><b>.xlsx</b></div>
        <div className={file ? 'intake-step ready' : 'intake-step'}><ScanLine size={18} /><span>识别字段</span><b>{file ? file.name : '待选择'}</b></div>
        <div className={result ? 'intake-step ready' : 'intake-step'}><Sparkles size={18} /><span>生成任务</span><b>{result ? '已完成' : '待接入'}</b></div>
      </section>

      <section className="panel upload-panel intake-panel">
        <label className="file-drop">
          <FileUp size={26} />
          <strong>{file ? file.name : '选择 Excel 素材表'}</strong>
          <span>系统会抽取款号、货号、FBA、品类、颜色、SKC 和图片链接，写入 AI 任务上下文。</span>
          <input type="file" accept=".xlsx" onChange={(event) => setFile(event.target.files?.[0] || null)} />
        </label>
        {result && (
          <div className="ingest-result">
            <div className="panel-head">
              <h2><CheckCircle2 size={18} />接入结果</h2>
              <a className="button primary" href="#/products">查看任务队列</a>
            </div>
            <div className="ingest-result-grid">
              {resultEntries.map(([key, value]) => (
                <div key={key}>
                  <span>{key}</span>
                  <strong>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</strong>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>
    </main>
  );
}
