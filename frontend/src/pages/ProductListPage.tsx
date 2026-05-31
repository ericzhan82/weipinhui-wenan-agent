import { Download, Plus, Search, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { Product } from '../types';

export function ProductListPage() {
  const [items, setItems] = useState<Product[]>([]);
  const [keyword, setKeyword] = useState('');
  const [message, setMessage] = useState('');
  const load = async () => setItems(await api.products(keyword));
  useEffect(() => { void load(); }, []);

  const exportExcel = async () => {
    const result = await api.exportExcel(keyword);
    window.location.href = result.download_url;
  };

  return (
    <main className="page">
      <div className="page-head">
        <div>
          <h1>商品工作台</h1>
          <p>录入商品资料，生成、校验和沉淀唯品渠道文案。</p>
        </div>
        <a className="button primary" href="#/products/new"><Plus size={16} />新建商品</a>
      </div>
      <section className="panel">
        <div className="toolbar searchbar">
          <Search size={17} />
          <input value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="款号、货号、品类、FBA" onKeyDown={(event) => event.key === 'Enter' && void load()} />
          <button onClick={load}>搜索</button>
          <button onClick={exportExcel}><Download size={16} />导出</button>
        </div>
        {message && <p className="notice">{message}</p>}
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>款号</th>
                <th>品类</th>
                <th>人群/季节</th>
                <th>状态</th>
                <th>文案</th>
                <th aria-label="操作"></th>
              </tr>
            </thead>
            <tbody>
              {items.map((product) => (
                <tr key={product.id}>
                  <td><a href={`#/products/${product.id}`}>{product.style_no || product.product_no}</a></td>
                  <td>{product.category_3} / {product.category_4}</td>
                  <td>{product.age_range} · {product.gender} · {product.season}</td>
                  <td><span className="status">{product.status}</span></td>
                  <td>{product.copy_output?.title || '未生成'}</td>
                  <td>
                    <button className="icon-button danger" title="删除商品" onClick={async () => {
                      if (!product.id) return;
                      await api.deleteProduct(product.id);
                      setMessage('已删除商品');
                      await load();
                    }}><Trash2 size={16} /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
