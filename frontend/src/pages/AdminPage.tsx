import { Building2, Plus, ShieldCheck, Trash2, UserCog, UsersRound } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { AuthUser, UserAccount, Workspace, WorkspaceMember, WorkspaceRef } from '../types';

type Props = {
  user: AuthUser;
  workspaceId: number | null;
  workspaces: WorkspaceRef[];
  onRefreshAuth: () => Promise<void>;
};

const roleOptions = [
  { value: 'workspace_admin', label: '工作空间管理员' },
  { value: 'editor', label: '编辑' },
  { value: 'viewer', label: '只读' },
];

function err(error: unknown) {
  return error instanceof Error ? error.message : String(error);
}

export function AdminPage({ user, workspaceId, workspaces, onRefreshAuth }: Props) {
  const [allWorkspaces, setAllWorkspaces] = useState<Workspace[]>([]);
  const [users, setUsers] = useState<UserAccount[]>([]);
  const [members, setMembers] = useState<WorkspaceMember[]>([]);
  const [workspaceDraft, setWorkspaceDraft] = useState({ name: '', slug: '' });
  const [userDraft, setUserDraft] = useState({
    email: '',
    display_name: '',
    password: '',
    is_system_admin: false,
    workspace_id: workspaceId,
    role: 'editor',
  });
  const [memberDraft, setMemberDraft] = useState({ user_id: '', role: 'editor' });
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState('');
  const canSystemManage = user.is_system_admin;
  const currentWorkspace = workspaces.find((workspace) => workspace.id === workspaceId);

  const load = async () => {
    const tasks: Promise<unknown>[] = [];
    if (canSystemManage) {
      tasks.push(api.workspaces().then(setAllWorkspaces));
      tasks.push(api.users().then(setUsers));
    }
    if (workspaceId) tasks.push(api.members(workspaceId).then(setMembers));
    await Promise.all(tasks);
  };

  useEffect(() => {
    void load().catch((error) => setMessage(err(error)));
  }, [workspaceId]);

  const run = async (label: string, action: () => Promise<void>) => {
    setBusy(label);
    setMessage('');
    try {
      await action();
      await load();
      await onRefreshAuth();
    } catch (error) {
      setMessage(err(error));
    } finally {
      setBusy('');
    }
  };

  const createWorkspace = async () => {
    if (!workspaceDraft.name.trim()) return;
    await run('workspace', async () => {
      await api.createWorkspace({ name: workspaceDraft.name.trim(), slug: workspaceDraft.slug.trim() || undefined });
      setWorkspaceDraft({ name: '', slug: '' });
      setMessage('工作空间已创建');
    });
  };

  const createUser = async () => {
    if (!userDraft.email || !userDraft.password || !userDraft.display_name) return;
    await run('user', async () => {
      await api.createUser({
        email: userDraft.email,
        display_name: userDraft.display_name,
        password: userDraft.password,
        is_system_admin: userDraft.is_system_admin,
        workspace_id: userDraft.workspace_id || null,
        role: userDraft.role,
      });
      setUserDraft({ ...userDraft, email: '', display_name: '', password: '' });
      setMessage('账号已创建');
    });
  };

  const addMember = async () => {
    if (!workspaceId || !memberDraft.user_id) return;
    await run('member', async () => {
      await api.addMember(workspaceId, { user_id: Number(memberDraft.user_id), role: memberDraft.role });
      setMemberDraft({ user_id: '', role: 'editor' });
      setMessage('成员已保存');
    });
  };

  return (
    <main className="page ai-page">
      <div className="page-head ai-head">
        <div>
          <span className="eyebrow"><ShieldCheck size={14} />access control</span>
          <h1>账号与工作空间</h1>
          <p>当前工作空间：{currentWorkspace?.name || '未选择'}。成员只能访问所属工作空间的数据。</p>
        </div>
      </div>

      {message && <p className={message.includes('失败') || message.includes('HTTP') || message.includes('无权') ? 'notice error' : 'notice'}>{message}</p>}

      <section className="admin-layout">
        {canSystemManage && (
          <div className="panel">
            <div className="panel-head">
              <div>
                <h2><Building2 size={18} />工作空间</h2>
                <p className="muted">系统管理员可以创建业务隔离空间。</p>
              </div>
            </div>
            <div className="form-grid">
              <label>
                <span>名称</span>
                <input value={workspaceDraft.name} onChange={(event) => setWorkspaceDraft({ ...workspaceDraft, name: event.target.value })} placeholder="例如：唯品童装组" />
              </label>
              <label>
                <span>Slug</span>
                <input value={workspaceDraft.slug} onChange={(event) => setWorkspaceDraft({ ...workspaceDraft, slug: event.target.value })} placeholder="可留空自动生成" />
              </label>
            </div>
            <div className="toolbar form-actions">
              <button className="primary" disabled={busy === 'workspace'} onClick={createWorkspace}><Plus size={16} />创建工作空间</button>
            </div>
            <div className="workspace-chip-list">
              {allWorkspaces.map((workspace) => <span key={workspace.id}>{workspace.name}<small>{workspace.slug}</small></span>)}
            </div>
          </div>
        )}

        {canSystemManage && (
          <div className="panel">
            <div className="panel-head">
              <div>
                <h2><UserCog size={18} />创建账号</h2>
                <p className="muted">创建时可直接分配到一个工作空间。</p>
              </div>
            </div>
            <div className="form-grid">
              <label>
                <span>邮箱</span>
                <input value={userDraft.email} onChange={(event) => setUserDraft({ ...userDraft, email: event.target.value })} />
              </label>
              <label>
                <span>姓名</span>
                <input value={userDraft.display_name} onChange={(event) => setUserDraft({ ...userDraft, display_name: event.target.value })} />
              </label>
              <label>
                <span>初始密码</span>
                <input type="password" value={userDraft.password} onChange={(event) => setUserDraft({ ...userDraft, password: event.target.value })} />
              </label>
              <label>
                <span>初始工作空间</span>
                <select value={userDraft.workspace_id || ''} onChange={(event) => setUserDraft({ ...userDraft, workspace_id: Number(event.target.value) || null })}>
                  <option value="">不分配</option>
                  {allWorkspaces.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.name}</option>)}
                </select>
              </label>
              <label>
                <span>角色</span>
                <select value={userDraft.role} onChange={(event) => setUserDraft({ ...userDraft, role: event.target.value })}>
                  {roleOptions.map((role) => <option key={role.value} value={role.value}>{role.label}</option>)}
                </select>
              </label>
              <label className="check-row llm-enabled">
                <input type="checkbox" checked={userDraft.is_system_admin} onChange={(event) => setUserDraft({ ...userDraft, is_system_admin: event.target.checked })} />
                系统管理员
              </label>
            </div>
            <div className="toolbar form-actions">
              <button className="primary" disabled={busy === 'user'} onClick={createUser}><Plus size={16} />创建账号</button>
            </div>
          </div>
        )}

        <div className="panel admin-members">
          <div className="panel-head">
            <div>
              <h2><UsersRound size={18} />当前工作空间成员</h2>
              <p className="muted">管理员可调整角色或移除成员。</p>
            </div>
          </div>

          {canSystemManage && workspaceId && (
            <div className="member-add-strip">
              <select value={memberDraft.user_id} onChange={(event) => setMemberDraft({ ...memberDraft, user_id: event.target.value })}>
                <option value="">选择账号</option>
                {users.map((account) => <option key={account.id} value={account.id}>{account.display_name} · {account.email}</option>)}
              </select>
              <select value={memberDraft.role} onChange={(event) => setMemberDraft({ ...memberDraft, role: event.target.value })}>
                {roleOptions.map((role) => <option key={role.value} value={role.value}>{role.label}</option>)}
              </select>
              <button disabled={busy === 'member'} onClick={addMember}><Plus size={16} />添加成员</button>
            </div>
          )}

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>成员</th>
                  <th>邮箱</th>
                  <th>角色</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {members.map((member) => (
                  <tr key={member.id}>
                    <td>{member.display_name || `用户 ${member.user_id}`}</td>
                    <td>{member.email || '-'}</td>
                    <td>
                      <select value={member.role} onChange={(event) => {
                        if (!workspaceId) return;
                        void run(`role-${member.user_id}`, () => api.updateMember(workspaceId, member.user_id, { role: event.target.value }).then(() => undefined));
                      }}>
                        {roleOptions.map((role) => <option key={role.value} value={role.value}>{role.label}</option>)}
                      </select>
                    </td>
                    <td>
                      <button className="icon-button danger" title="移除成员" onClick={() => {
                        if (!workspaceId) return;
                        void run(`delete-${member.user_id}`, () => api.deleteMember(workspaceId, member.user_id).then(() => undefined));
                      }}>
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </main>
  );
}
