import { Download, FileClock, ListChecks, RefreshCw, RotateCcw, Search, StopCircle } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { api } from '../api/client';
import type { CopyBatch, CopyBatchDetail } from '../types';

type Props = {
  batchNo?: string;
};

const statusText: Record<string, string> = {
  queued: '排队中',
  running: '生成中',
  completed: '已完成',
  completed_with_errors: '有失败项',
  canceling: '取消中',
  canceled: '已取消',
};

const itemStatusText: Record<string, string> = {
  pending: '待生成',
  running: '生成中',
  success: '已生成',
  failed: '失败',
  skipped: '已跳过',
  canceled: '已取消',
};

function getError(error: unknown) {
  return error instanceof Error ? error.message : String(error);
}

function formatDate(value?: string | null) {
  if (!value) return '-';
  return new Date(value).toLocaleString();
}

function finishCount(batch: CopyBatch) {
  return batch.success_count + batch.failed_count + batch.skipped_count + batch.canceled_count;
}

function progress(batch: CopyBatch) {
  if (!batch.total_count) return 0;
  return Math.round((finishCount(batch) / batch.total_count) * 100);
}

export function CopyBatchPage({ batchNo }: Props) {
  const [batches, setBatches] = useState<CopyBatch[]>([]);
  const [detail, setDetail] = useState<CopyBatchDetail | null>(null);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState('');
  const selectedNo = batchNo || batches[0]?.batch_no;

  const activeBatch = useMemo(
    () => batches.find((batch) => batch.batch_no === selectedNo) || detail?.batch || null,
    [batches, detail, selectedNo],
  );

  const load = async (targetNo = selectedNo) => {
    const nextBatches = await api.copyBatches();
    setBatches(nextBatches);
    const nextNo = targetNo || nextBatches[0]?.batch_no;
    if (nextNo) setDetail(await api.copyBatch(nextNo));
    else setDetail(null);
  };

  useEffect(() => {
    void load(batchNo).catch((error) => setMessage(getError(error)));
  }, [batchNo]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      void load(selectedNo).catch(() => undefined);
    }, 5000);
    return () => window.clearInterval(timer);
  }, [selectedNo]);

  const run = async (label: string, action: () => Promise<void>) => {
    setBusy(label);
    setMessage('');
    try {
      await action();
      await load(selectedNo);
    } catch (error) {
      setMessage(getError(error));
    } finally {
      setBusy('');
    }
  };

  const exportBatch = async (targetNo: string) => {
    await run(`export-${targetNo}`, async () => {
      const result = await api.exportCopyBatch(targetNo);
      window.location.href = result.download_url;
      setMessage(`已生成导出文件：${result.filename}`);
    });
  };

  return (
    <main className="page ai-page">
      <div className="page-head ai-head">
        <div>
          <span className="eyebrow"><FileClock size={14} />batch queue</span>
          <h1>批量生成任务</h1>
          <p>后台按数据库队列逐条生成，任务结果按批量任务号隔离导出。</p>
        </div>
        <div className="toolbar">
          <button disabled={Boolean(busy)} onClick={() => void load(selectedNo)}><RefreshCw size={16} />刷新</button>
          <a className="button primary" href="#/products"><Search size={16} />从任务队列创建</a>
        </div>
      </div>

      {message && <p className={message.includes('失败') || message.includes('HTTP') || message.includes('无权') ? 'notice error' : 'notice'}>{message}</p>}

      <section className="batch-layout">
        <div className="panel batch-list-panel">
          <div className="panel-head">
            <div>
              <h2><ListChecks size={18} />任务号</h2>
              <p className="muted">每次批量生成都会创建独立任务号。</p>
            </div>
          </div>
          <div className="batch-list">
            {batches.map((batch) => (
              <a
                className={batch.batch_no === selectedNo ? 'batch-card active' : 'batch-card'}
                href={`#/copy-batches/${batch.batch_no}`}
                key={batch.batch_no}
              >
                <div>
                  <strong>{batch.batch_no}</strong>
                  <span>{statusText[batch.status] || batch.status}</span>
                </div>
                <div className="batch-progress">
                  <span style={{ width: `${progress(batch)}%` }} />
                </div>
                <small>{finishCount(batch)} / {batch.total_count} · {batch.created_by || '-'}</small>
              </a>
            ))}
            {batches.length === 0 && (
              <div className="empty-state">
                <FileClock size={26} />
                <strong>还没有批量任务</strong>
                <p>在商品任务队列中按当前筛选条件创建批量生成任务。</p>
              </div>
            )}
          </div>
        </div>

        <div className="panel batch-detail-panel">
          {activeBatch ? (
            <>
              <div className="panel-head">
                <div>
                  <h2>{activeBatch.batch_no}</h2>
                  <p className="muted">
                    {statusText[activeBatch.status] || activeBatch.status} · 创建于 {formatDate(activeBatch.created_at)}
                  </p>
                </div>
                <div className="toolbar">
                  <button disabled={Boolean(busy)} onClick={() => void exportBatch(activeBatch.batch_no)}>
                    <Download size={16} />导出成功结果
                  </button>
                  <button disabled={Boolean(busy) || !activeBatch.failed_count} onClick={() => void run(`retry-${activeBatch.batch_no}`, () => api.retryCopyBatch(activeBatch.batch_no).then(() => undefined))}>
                    <RotateCcw size={16} />重试失败项
                  </button>
                  <button className="danger" disabled={Boolean(busy) || !['queued', 'running'].includes(activeBatch.status)} onClick={() => void run(`cancel-${activeBatch.batch_no}`, () => api.cancelCopyBatch(activeBatch.batch_no).then(() => undefined))}>
                    <StopCircle size={16} />取消
                  </button>
                </div>
              </div>

              <section className="batch-metrics">
                <div><span>总数</span><strong>{activeBatch.total_count}</strong></div>
                <div><span>待生成</span><strong>{activeBatch.pending_count}</strong></div>
                <div><span>生成中</span><strong>{activeBatch.running_count}</strong></div>
                <div><span>成功</span><strong>{activeBatch.success_count}</strong></div>
                <div><span>失败</span><strong>{activeBatch.failed_count}</strong></div>
                <div><span>跳过</span><strong>{activeBatch.skipped_count}</strong></div>
              </section>

              <div className="batch-rule-strip">
                <span>筛选：{Object.keys(activeBatch.filter_json || {}).length ? JSON.stringify(activeBatch.filter_json) : '全部当前工作空间商品'}</span>
                <span>{activeBatch.overwrite_existing ? '覆盖已有标题' : '跳过已有标题'}</span>
                <span>{activeBatch.use_hot_search ? '启用热搜词' : activeBatch.use_hot_search === false ? '关闭热搜词' : '使用全局默认'}</span>
              </div>

              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>商品 ID</th>
                      <th>状态</th>
                      <th>开始时间</th>
                      <th>完成时间</th>
                      <th>错误</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(detail?.items || []).map((item) => (
                      <tr key={item.id}>
                        <td><a href={`#/products/${item.product_id}`}>{item.product_id}</a></td>
                        <td><span className={`status-pill ${item.status}`}>{itemStatusText[item.status] || item.status}</span></td>
                        <td>{formatDate(item.started_at)}</td>
                        <td>{formatDate(item.finished_at)}</td>
                        <td>{item.error_message || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="empty-state">
              <FileClock size={26} />
              <strong>请选择批量任务</strong>
              <p>任务创建后会在这里展示生成进度和导出入口。</p>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
