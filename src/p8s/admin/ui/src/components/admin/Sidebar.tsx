/**
 * P8s Admin - Sidebar Component
 * 
 * Navigation sidebar with model list
 */

import type { ModelSchema } from '../../types/admin';

interface SidebarProps {
    models: ModelSchema[];
    currentModel: string | null;
    onSelectModel: (name: string) => void;
    collapsed?: boolean;
    onToggleCollapse?: () => void;
}

// Default icons for common model names
const modelIcons: Record<string, string> = {
    user: '👤',
    users: '👥',
    product: '📦',
    products: '📦',
    category: '📁',
    categories: '📁',
    order: '🛒',
    orders: '🛒',
    post: '📝',
    posts: '📝',
    blog: '📰',
    comment: '💬',
    comments: '💬',
    tag: '🏷️',
    tags: '🏷️',
    setting: '⚙️',
    settings: '⚙️',
    file: '📄',
    files: '📄',
    image: '🖼️',
    images: '🖼️',
    document: '📑',
    documents: '📑',
};

function getModelIcon(model: ModelSchema): string {
    if (model.admin.icon) return model.admin.icon;

    const name = model.name.toLowerCase();
    return modelIcons[name] || modelIcons[model.admin.plural_name.toLowerCase()] || '📋';
}

export function Sidebar({
    models,
    currentModel,
    onSelectModel,
    collapsed = false,
    onToggleCollapse,
}: SidebarProps) {
    return (
        <aside className={`admin-sidebar ${collapsed ? 'collapsed' : ''}`}>
            <div className="sidebar-header">
                <div className="sidebar-logo">
                    {!collapsed && <span className="logo-text">P8s Admin</span>}
                    <span className="logo-icon">⚡</span>
                </div>
                {onToggleCollapse && (
                    <button
                        className="collapse-btn"
                        onClick={onToggleCollapse}
                        title={collapsed ? 'Expand' : 'Collapse'}
                    >
                        {collapsed ? '→' : '←'}
                    </button>
                )}
            </div>

            <nav className="sidebar-nav">
                <div className="nav-section">
                    <a
                        href="#dashboard"
                        className={`nav-item ${currentModel === null ? 'active' : ''}`}
                        onClick={(e) => { e.preventDefault(); onSelectModel(''); }}
                    >
                        <span className="nav-icon">📊</span>
                        {!collapsed && <span className="nav-label">Dashboard</span>}
                    </a>
                </div>

                <div className="nav-section">
                    {!collapsed && <div className="nav-section-title">Models</div>}

                    {models.map(model => (
                        <a
                            key={model.name}
                            href={`#${model.name}`}
                            className={`nav-item ${currentModel === model.name ? 'active' : ''}`}
                            onClick={(e) => { e.preventDefault(); onSelectModel(model.name); }}
                            title={collapsed ? model.admin.plural_name : undefined}
                        >
                            <span className="nav-icon">{getModelIcon(model)}</span>
                            {!collapsed && <span className="nav-label">{model.admin.plural_name}</span>}
                        </a>
                    ))}
                </div>
            </nav>

            <div className="sidebar-footer">
                {!collapsed && (
                    <div className="footer-info">
                        <span className="version">P8s v0.1.0</span>
                    </div>
                )}
            </div>
        </aside>
    );
}

export default Sidebar;
