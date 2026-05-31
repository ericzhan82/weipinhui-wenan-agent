import { Boxes, FileSpreadsheet, History, Library, Settings, Shirt, Sparkles } from 'lucide-react';
import { useEffect, useState } from 'react';
import { ExcelImportPage } from './pages/ExcelImportPage';
import { HistoryCasePage } from './pages/HistoryCasePage';
import { LearningCenterPage } from './pages/LearningCenterPage';
import { ProductCreatePage } from './pages/ProductCreatePage';
import { ProductDetailPage } from './pages/ProductDetailPage';
import { ProductListPage } from './pages/ProductListPage';
import { RuleManagePage } from './pages/RuleManagePage';
import { SettingsPage } from './pages/SettingsPage';

const nav = [
  ['#/products', Shirt, '商品'],
  ['#/excel-import', FileSpreadsheet, 'Excel'],
  ['#/rules', Library, '规则'],
  ['#/history-cases', History, '案例'],
  ['#/learning', Sparkles, '学习'],
  ['#/settings', Settings, '设置'],
] as const;

function useHashRoute() {
  const [hash, setHash] = useState(window.location.hash || '#/products');
  useEffect(() => {
    const handler = () => setHash(window.location.hash || '#/products');
    window.addEventListener('hashchange', handler);
    if (!window.location.hash) window.location.hash = '#/products';
    return () => window.removeEventListener('hashchange', handler);
  }, []);
  return hash;
}

export function App() {
  const route = useHashRoute();
  const productMatch = route.match(/^#\/products\/(\d+)/);
  let page = <ProductListPage />;
  if (route === '#/products/new') page = <ProductCreatePage />;
  else if (productMatch) page = <ProductDetailPage id={Number(productMatch[1])} />;
  else if (route.startsWith('#/excel-import')) page = <ExcelImportPage />;
  else if (route.startsWith('#/rules')) page = <RuleManagePage />;
  else if (route.startsWith('#/history-cases')) page = <HistoryCasePage />;
  else if (route.startsWith('#/learning')) page = <LearningCenterPage />;
  else if (route.startsWith('#/settings')) page = <SettingsPage />;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#/products">
          <Boxes size={24} />
          <span>唯品童装文案</span>
        </a>
        <nav>
          {nav.map(([href, Icon, label]) => (
            <a className={route.startsWith(href.replace('#', '')) || route === href ? 'active' : ''} href={href} key={href}>
              <Icon size={18} />
              {label}
            </a>
          ))}
        </nav>
      </aside>
      {page}
    </div>
  );
}
