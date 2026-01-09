/**
 * P8s Admin - Sidebar Component
 * 
 * Navigation sidebar with model list
 */

import type { ModelSchema } from '../../types/admin';
import { LayoutGrid, Database } from 'lucide-react';
import p8sLogo from '../../assets/p8s.svg';

interface SidebarProps {
    models: ModelSchema[];
    currentModel: string | null;
    onSelectModel: (name: string) => void;
    collapsed?: boolean;
    onToggleCollapse?: () => void;
}

export function Sidebar({
    models,
    currentModel,
    onSelectModel,
    collapsed = false,
}: SidebarProps) {
    return (
        <aside className={`admin-sidebar ${collapsed ? 'collapsed' : ''}`}>
            <div className="sidebar-header">
                {!collapsed ? (
                    <div className="sidebar-logo">
                        <span className="logo-icon"><img src={p8sLogo} alt="P8s Logo" style={{ height: '24px', width: '24px' }} /></span>
                        <span className="logo-text">P8s Admin</span>
                    </div>
                ) : (
                    <span className="logo-icon"><img src={p8sLogo} alt="P8s Logo" style={{ height: '24px', width: '24px' }} /></span>
                )}
            </div>

            <nav className="sidebar-nav">
                <a
                    href="#"
                    className={`nav-item ${!currentModel ? 'active' : ''}`}
                    onClick={(e) => { e.preventDefault(); onSelectModel(''); }}
                >
                    <span className="nav-icon"><LayoutGrid size={18} /></span>
                    {!collapsed && <span>Dashboard</span>}
                </a>

                <div className="nav-divider"></div>
                {!collapsed && <div className="nav-label">Models</div>}

                {models.map(model => (
                    <a
                        key={model.name}
                        href="#"
                        className={`nav-item ${currentModel === model.name ? 'active' : ''}`}
                        onClick={(e) => { e.preventDefault(); onSelectModel(model.name); }}
                        title={model.admin.name}
                    >
                        <span className="nav-icon">
                            {/* In future we can map model icon from schema */}
                            <Database size={18} />
                        </span>
                        {!collapsed && <span>{model.admin.plural_name}</span>}
                    </a>
                ))}
            </nav>
            {/* Footer with version or user info could go here */}
        </aside>
    );
}

export default Sidebar;
