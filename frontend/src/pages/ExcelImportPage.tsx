import { FileUp } from 'lucide-react';
import { useState } from 'react';
import { api } from '../api/client';

export function ExcelImportPage() {
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [file, setFile] = useState<File | null>(null);
  return (
    <main className="page">
      <div className="page-head">
        <div>
          <h1>Excel 导入</h1>
          <p>支持 .xlsx，自动识别款号、货号、FBA、品类、颜色、SKC 等字段。</p>
        </div>
        <button className="primary" disabled={!file} onClick={async () => file && setResult(await api.importExcel(file))}><FileUp size={16} />导入</button>
      </div>
      <section className="panel upload-panel">
        <input type="file" accept=".xlsx" onChange={(event) => setFile(event.target.files?.[0] || null)} />
        {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
      </section>
    </main>
  );
}
