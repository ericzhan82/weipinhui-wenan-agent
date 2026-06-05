import {
  Boxes,
  FileClock,
  FileSpreadsheet,
  History,
  Library,
  LogOut,
  Settings,
  ShieldCheck,
  Shirt,
  Sparkles,
  UsersRound,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { clearAuthToken, getAuthToken, getWorkspaceId, setWorkspaceId, api } from './api/client';
import { AdminPage } from './pages/AdminPage';
import { CopyBatchPage } from './pages/CopyBatchPage';
import { ExcelImportPage } from './pages/ExcelImportPage';
import { HistoryCasePage } from './pages/HistoryCasePage';
import { LearningCenterPage } from './pages/LearningCenterPage';
import { LoginPage } from './pages/LoginPage';
import { ProductCreatePage } from './pages/ProductCreatePage';
import { ProductDetailPage } from './pages/ProductDetailPage';
import { ProductListPage } from './pages/ProductListPage';
import { RuleManagePage } from './pages/RuleManagePage';
import { SettingsPage } from './pages/SettingsPage';
import type { AuthUser, WorkspaceRef } from './types';

const baseNav = [
  { href: '#/products', icon: Shirt, label: '任务' },
  { href: '#/copy-batches', icon: FileClock, label: '批量任务' },
  { href: '#/excel-import', icon: FileSpreadsheet, label: '接入' },
  { href: '#/rules', icon: Library, label: '规则记忆' },
  { href: '#/history-cases', icon: History, label: '案例记忆' },
  { href: '#/learning', icon: Sparkles, label: '学习回路' },
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

function pickWorkspace(workspaces: WorkspaceRef[]) {
  const stored = getWorkspaceId();
  if (stored && workspaces.some((workspace) => workspace.id === stored)) return stored;
  return workspaces[0]?.id || null;
}

function roleLabel(role?: string) {
  if (role === 'system_admin') return '系统管理员';
  if (role === 'workspace_admin') return '工作空间管理员';
  if (role === 'editor') return '编辑';
  if (role === 'viewer') return '只读';
  return '未分配';
}

export function App() {
  const route = useHashRoute();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [workspaces, setWorkspaces] = useState<WorkspaceRef[]>([]);
  const [workspaceId, setSelectedWorkspaceId] = useState<number | null>(getWorkspaceId());
  const [booting, setBooting] = useState(true);
  const [bootError, setBootError] = useState('');

  const loadSession = async () => {
    if (!getAuthToken()) {
      setBooting(false);
      return;
    }
    try {
      const currentUser = await api.me();
      const nextWorkspaces = currentUser.is_system_admin
        ? (await api.workspaces()).map((workspace) => ({ ...workspace, role: 'system_admin' as const }))
        : currentUser.workspaces;
      const nextWorkspaceId = pickWorkspace(nextWorkspaces);
      setUser({ ...currentUser, workspaces: nextWorkspaces });
      setWorkspaces(nextWorkspaces);
      setSelectedWorkspaceId(nextWorkspaceId);
      setWorkspaceId(nextWorkspaceId);
      setBootError('');
    } catch (error) {
      clearAuthToken();
      setUser(null);
      setWorkspaces([]);
      setBootError(error instanceof Error ? error.message : String(error));
    } finally {
      setBooting(false);
    }
  };

  useEffect(() => {
    void loadSession();
  }, []);

  const currentWorkspace = useMemo(
    () => workspaces.find((workspace) => workspace.id === workspaceId) || null,
    [workspaces, workspaceId],
  );
  const canManageWorkspace = Boolean(user?.is_system_admin || currentWorkspace?.role === 'workspace_admin');

  const switchWorkspace = (nextWorkspaceId: number) => {
    setSelectedWorkspaceId(nextWorkspaceId);
    setWorkspaceId(nextWorkspaceId);
    void loadSession();
    if (window.location.hash !== '#/products') window.location.hash = '#/products';
  };

  const logout = async () => {
    try {
      await api.logout();
    } catch {
      // local logout is enough for the current token style
    }
    clearAuthToken();
    setUser(null);
    setWorkspaces([]);
    setSelectedWorkspaceId(null);
    window.location.hash = '#/products';
  };

  if (booting) {
    return (
      <main className="login-page">
        <div className="empty-state boot-state">
          <Sparkles size={28} />
          <strong>正在进入工作台</strong>
          <p>正在校验登录态和工作空间。</p>
        </div>
      </main>
    );
  }

  if (!user) {
    return (
      <>
        {bootError && <div className="floating-error">{bootError}</div>}
        <LoginPage onLogin={() => {
          setBooting(true);
          void loadSession();
        }} />
      </>
    );
  }

  const productMatch = route.match(/^#\/products\/(\d+)/);
  const batchMatch = route.match(/^#\/copy-batches\/(.+)/);
  let page = <ProductListPage workspaceId={workspaceId} />;
  if (route === '#/products/new') page = <ProductCreatePage />;
  else if (productMatch) page = <ProductDetailPage id={Number(productMatch[1])} />;
  else if (route.startsWith('#/copy-batches')) page = <CopyBatchPage batchNo={batchMatch ? decodeURIComponent(batchMatch[1]) : undefined} />;
  else if (route.startsWith('#/excel-import')) page = <ExcelImportPage />;
  else if (route.startsWith('#/rules')) page = <RuleManagePage />;
  else if (route.startsWith('#/history-cases')) page = <HistoryCasePage />;
  else if (route.startsWith('#/learning')) page = <LearningCenterPage />;
  else if (route.startsWith('#/settings') && user.is_system_admin) page = <SettingsPage />;
  else if (route.startsWith('#/admin') && canManageWorkspace) {
    page = <AdminPage user={user} workspaceId={workspaceId} workspaces={workspaces} onRefreshAuth={loadSession} />;
  }

  const nav = [
    ...baseNav,
    ...(canManageWorkspace ? [{ href: '#/admin', icon: UsersRound, label: '权限' } as const] : []),
    ...(user.is_system_admin ? [{ href: '#/settings', icon: Settings, label: '模型配置' } as const] : []),
  ];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#/products">
          <Boxes size={24} />
          <span>AI 童装文案舱</span>
        </a>

        <div className="workspace-card">
          <span>工作空间</span>
          <select value={workspaceId || ''} onChange={(event) => switchWorkspace(Number(event.target.value))}>
            {workspaces.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.name}</option>)}
          </select>
          <small>{roleLabel(currentWorkspace?.role)}</small>
        </div>

        <nav>
          {nav.map(({ href, icon: Icon, label }) => (
            <a className={route.startsWith(href) ? 'active' : ''} href={href} key={href}>
              <Icon size={18} />
              {label}
            </a>
          ))}
        </nav>

        <div className="sidebar-user">
          <ShieldCheck size={18} />
          <div>
            <strong>{user.display_name}</strong>
            <span>{user.email}</span>
          </div>
        </div>
        <button className="sidebar-logout" onClick={logout}><LogOut size={16} />退出登录</button>
      </aside>
      {page}
    </div>
  );
}
