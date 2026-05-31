import { Save } from 'lucide-react';
import { useState } from 'react';
import { api } from '../api/client';
import { ProductForm } from '../components/ProductForm';
import { SkuEditor } from '../components/SkuEditor';
import type { Product } from '../types';

const emptyProduct: Product = {
  style_no: '',
  product_no: '',
  category_3: '',
  category_4: '',
  age_range: '',
  gender: '',
  season: '',
  scene: '',
  fba: '',
  remark: '',
  created_by: '运营',
  updated_by: '运营',
  status: 'draft',
  skus: [{}],
};

export function ProductCreatePage() {
  const [product, setProduct] = useState<Product>(emptyProduct);
  const [message, setMessage] = useState('');
  return (
    <main className="page">
      <div className="page-head">
        <div>
          <h1>新建商品</h1>
          <p>先建立模型上下文和颜色素材，再进入 AI 文案生成。</p>
        </div>
        <button className="primary" onClick={async () => {
          const created = await api.createProduct(product);
          setMessage('商品已创建');
          window.location.hash = `#/products/${created.id}`;
        }}><Save size={16} />保存上下文</button>
      </div>
      {message && <p className="notice">{message}</p>}
      <section className="panel">
        <ProductForm value={product} onChange={setProduct} />
      </section>
      <SkuEditor skus={product.skus} onChange={(skus) => setProduct({ ...product, skus })} />
    </main>
  );
}
