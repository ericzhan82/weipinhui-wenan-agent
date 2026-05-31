import { RotateCcw } from 'lucide-react';
import type { CopyVersion } from '../types';

type Props = {
  versions: CopyVersion[];
  onRestore: (id: number) => void;
};

export function VersionPanel({ versions, onRestore }: Props) {
  return (
    <section className="panel">
      <div className="panel-head">
        <h2>版本记录</h2>
      </div>
      <div className="version-list">
        {versions.map((version) => (
          <article className="version-item" key={version.id}>
            <div>
              <strong>v{version.version_no} · {version.version_type}</strong>
              <p>{version.title}</p>
              <small>{version.main_image_tags?.join(' / ')} · {version.color_copy}</small>
            </div>
            <button className="icon-button" title="恢复版本" onClick={() => onRestore(version.id)}>
              <RotateCcw size={16} />
            </button>
          </article>
        ))}
        {versions.length === 0 && <p className="muted">暂无版本。</p>}
      </div>
    </section>
  );
}
