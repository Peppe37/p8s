/**
 * P8s Admin Panel - Main Component
 * 
 * The main admin panel that brings together all components
 */

import { useState, useEffect } from 'react';
import { Sidebar } from './Sidebar';
import { DataTable, Pagination } from './DataTable';
import { DynamicForm, fieldMetaToFormField } from './DynamicForm';
import * as adminApi from '../../api/admin';
import type { ModelSchema, Sort, TableColumn, FormField } from '../../types/admin';

// View modes
type ViewMode = 'list' | 'create' | 'edit';

interface AdminPanelProps {
    apiUrl?: string;
}

interface RecordWithId {
    id: string;
    [key: string]: unknown;
}

export function AdminPanel({ }: AdminPanelProps) {
    // Auth State
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(!!localStorage.getItem('p8s_token'));
    const [loginUser, setLoginUser] = useState('');
    const [loginPass, setLoginPass] = useState('');
    const [loginError, setLoginError] = useState('');

    // State
    const [models, setModels] = useState<ModelSchema[]>([]);
    const [currentModel, setCurrentModel] = useState<string | null>(null);
    const [currentSchema, setCurrentSchema] = useState<ModelSchema | null>(null);
    const [viewMode, setViewMode] = useState<ViewMode>('list');
    const [editingId, setEditingId] = useState<string | null>(null);

    // List state
    const [records, setRecords] = useState<RecordWithId[]>([]);
    const [totalRecords, setTotalRecords] = useState(0);
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(25);
    const [sort, setSort] = useState<Sort | undefined>();
    const [search, setSearch] = useState('');
    const [selectedIds, setSelectedIds] = useState<string[]>([]);

    // UI state
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

    // Initial load handled by auth effect
    useEffect(() => {
        if (isAuthenticated) {
            loadModels();
        }
    }, [isAuthenticated]);

    // Load records when model changes
    useEffect(() => {
        if (currentModel && isAuthenticated) {
            loadRecords();
        }
    }, [currentModel, page, pageSize, sort, search, isAuthenticated]);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoginError('');
        setLoading(true);
        try {
            const res = await adminApi.login(loginUser, loginPass);
            if (res.access_token) {
                localStorage.setItem('p8s_token', res.access_token);
                setIsAuthenticated(true);
            }
        } catch (err) {
            setLoginError('Invalid credentials');
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('p8s_token');
        setIsAuthenticated(false);
        setModels([]);
        setCurrentModel(null);
        setLoginUser('');
        setLoginPass('');
    };

    const loadModels = async () => {
        try {
            setLoading(true);
            const data = await adminApi.getAdminModels();
            setModels(data);
        } catch (err: any) {
            if (err.status === 401) {
                setIsAuthenticated(false);
                localStorage.removeItem('p8s_token');
                return;
            }
            showNotification('Failed to load models', 'error');
        } finally {
            setLoading(false);
        }
    };

    const loadRecords = async () => {
        if (!currentModel) return;

        try {
            setLoading(true);
            setError(null);

            const data = await adminApi.listRecords<RecordWithId>(currentModel, {
                page,
                pageSize,
                sort,
                search: search || undefined,
            });

            setRecords(data.items);
            setTotalRecords(data.total);
        } catch (err: any) {
            if (err.status === 401) {
                setIsAuthenticated(false);
                localStorage.removeItem('p8s_token');
                return;
            }
            setError(err instanceof Error ? err.message : 'Failed to load records');
        } finally {
            setLoading(false);
        }
    };

    const handleModelSelect = async (name: string) => {
        setCurrentModel(name || null);
        setViewMode('list');
        setEditingId(null);
        setSelectedIds([]);
        setPage(1);
        setSearch('');
        setSort(undefined);

        if (name) {
            try {
                const schema = await adminApi.getModelSchema(name);
                setCurrentSchema(schema);
            } catch (err: any) {
                if (err.status === 401) {
                    setIsAuthenticated(false);
                    return;
                }
                setCurrentSchema(null);
            }
        } else {
            setCurrentSchema(null);
        }
    };

    const handleCreate = () => {
        setViewMode('create');
        setEditingId(null);
    };

    const handleEdit = (row: unknown) => {
        const r = row as RecordWithId;
        setEditingId(r.id);
        setViewMode('edit');
    };

    const handleBack = () => {
        setViewMode('list');
        setEditingId(null);
    };

    const handleSubmit = async (values: Record<string, unknown>) => {
        if (!currentModel) return;

        try {
            if (viewMode === 'create') {
                await adminApi.createRecord(currentModel, values);
            } else if (viewMode === 'edit' && editingId) {
                await adminApi.updateRecord(currentModel, editingId, values);
            }

            showNotification('Operation successful', 'success');
            setViewMode('list');
            setEditingId(null);
            loadRecords();
        } catch (err) {
            throw err;
        }
    };

    const handleDelete = async (ids: string[]) => {
        if (!currentModel || ids.length === 0) return;

        const confirm = window.confirm(
            `Are you sure you want to delete ${ids.length} record(s)?`
        );

        if (!confirm) return;

        try {
            if (ids.length === 1) {
                await adminApi.deleteRecord(currentModel, ids[0]);
            } else {
                await adminApi.bulkDelete(currentModel, ids);
            }

            showNotification(`Deleted ${ids.length} record(s)`, 'success');
            setSelectedIds([]);
            loadRecords();
        } catch (err) {
            showNotification('Failed to delete records', 'error');
        }
    };

    const handleExport = async () => {
        if (!currentModel) return;

        try {
            const blob = await adminApi.exportRecords(currentModel, 'csv');
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${currentModel}_export.csv`;
            a.click();
            URL.revokeObjectURL(url);
        } catch {
            showNotification('Export failed', 'error');
        }
    };

    const showNotification = (message: string, type: 'success' | 'error') => {
        setNotification({ message, type });
        setTimeout(() => setNotification(null), 3000);
    };

    // Generate table columns from schema
    const getTableColumns = (): TableColumn[] => {
        if (!currentSchema) return [];

        return currentSchema.admin.list_display.map(fieldName => {
            const fieldMeta = currentSchema.fields[fieldName];
            return {
                key: fieldName,
                label: fieldName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                type: fieldMeta?.type || 'string',
                sortable: true,
            };
        });
    };

    // Generate form fields from schema
    const getFormFields = (): FormField[] => {
        if (!currentSchema) return [];

        const hiddenFields = ['id', 'created_at', 'updated_at', 'deleted_at'];

        return Object.entries(currentSchema.fields)
            .filter(([name]) => !hiddenFields.includes(name))
            .filter(([name]) => !currentSchema.admin.hidden_fields.includes(name))
            .map(([name, meta]) =>
                fieldMetaToFormField(name, meta, {
                    readonly: currentSchema.admin.readonly_fields.includes(name),
                })
            );
    };

    // Get initial values for editing
    const getEditValues = (): Record<string, unknown> => {
        if (!editingId) return {};
        return records.find(r => r.id === editingId) || {};
    };

    if (!isAuthenticated) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#f3f4f6', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
                <form onSubmit={handleLogin} style={{ background: 'white', padding: '2.5rem', borderRadius: '12px', boxShadow: '0 10px 25px rgba(0,0,0,0.05)', width: '100%', maxWidth: '380px' }}>
                    <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#111827', margin: 0 }}>P8s Admin</h2>
                        <p style={{ marginTop: '0.5rem', color: '#6b7280', fontSize: '0.875rem' }}>Sign in to manage your application</p>
                    </div>

                    {loginError && (
                        <div style={{ marginBottom: '1.5rem', padding: '0.75rem', background: '#fee2e2', color: '#991b1b', borderRadius: '6px', fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span style={{ fontWeight: 'bold' }}>!</span> {loginError}
                        </div>
                    )}

                    <div style={{ marginBottom: '1.25rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', color: '#374151', fontSize: '0.875rem', fontWeight: 500 }}>Username</label>
                        <input
                            type="text"
                            value={loginUser}
                            onChange={e => setLoginUser(e.target.value)}
                            style={{ width: '100%', padding: '0.625rem 0.75rem', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '0.875rem', transition: 'border-color 0.15s' }}
                            placeholder="Enter your username"
                            required
                        />
                    </div>
                    <div style={{ marginBottom: '1.5rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', color: '#374151', fontSize: '0.875rem', fontWeight: 500 }}>Password</label>
                        <input
                            type="password"
                            value={loginPass}
                            onChange={e => setLoginPass(e.target.value)}
                            style={{ width: '100%', padding: '0.625rem 0.75rem', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '0.875rem' }}
                            placeholder="••••••••"
                            required
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={loading}
                        style={{ width: '100%', padding: '0.75rem', background: '#f97316', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 600, fontSize: '0.875rem', transition: 'background-color 0.15s' }}
                    >
                        {loading ? 'Signing In...' : 'Sign In'}
                    </button>

                    <div style={{ marginTop: '2rem', textAlign: 'center', fontSize: '0.75rem', color: '#9ca3af' }}>
                        Powered by P8s Framework
                    </div>
                </form>
            </div>
        );
    }

    return (
        <div className="admin-panel">
            <Sidebar
                models={models}
                currentModel={currentModel}
                onSelectModel={handleModelSelect}
                collapsed={sidebarCollapsed}
                onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
            />
            {/* Added Logout button absolute positioned or in a header inside main if Sidebar doesn't have it */}
            <div style={{ position: 'absolute', bottom: '1rem', left: sidebarCollapsed ? '0.5rem' : '1rem', zIndex: 100 }}>
                {/* Sidebar usually covers left side. Let's put logout in Sidebar? 
                    But Sidebar is imported. I can pass a logout action prop if Sidebar accepts it? 
                    Sidebar props: models, currentModel, onSelectModel, collapsed, onToggleCollapse.
                    It doesn't accept extra children or logout.
                    I'll put logout in the main area header or a floating button.
                 */}
            </div>

            <main className="admin-main">
                {/* Global Header/Toolbar */}
                <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '1rem', background: 'white', borderBottom: '1px solid #e5e7eb' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>Admin User</span>
                        <button
                            onClick={handleLogout}
                            style={{ padding: '0.5rem 1rem', background: 'white', border: '1px solid #d1d5db', borderRadius: '6px', cursor: 'pointer', fontSize: '0.875rem', color: '#374151' }}
                        >
                            Logout
                        </button>
                    </div>
                </div>

                {/* Notification */}
                {notification && (
                    <div className={`notification ${notification.type}`}>
                        {notification.message}
                    </div>
                )}

                {/* Dashboard */}
                {!currentModel && (
                    <div className="admin-dashboard">
                        <h1>Dashboard</h1>
                        <div className="dashboard-cards">
                            {models.map(model => (
                                <div
                                    key={model.name}
                                    className="dashboard-card"
                                    onClick={() => handleModelSelect(model.name)}
                                >
                                    <div className="card-icon">📋</div>
                                    <div className="card-content">
                                        <h3>{model.admin.plural_name}</h3>
                                        <p>Manage {model.admin.plural_name.toLowerCase()}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* ... existing code ... */}
                {/* Model List View */}
                {currentModel && viewMode === 'list' && (
                    <div className="admin-list">
                        <header className="list-header">
                            <h1>{currentSchema?.admin.plural_name || currentModel}</h1>

                            <div className="list-actions">
                                <div className="search-box">
                                    <input
                                        type="text"
                                        placeholder="Search..."
                                        value={search}
                                        onChange={(e) => setSearch(e.target.value)}
                                    />
                                </div>

                                {selectedIds.length > 0 && (
                                    <button
                                        className="btn btn-danger"
                                        onClick={() => handleDelete(selectedIds)}
                                    >
                                        Delete ({selectedIds.length})
                                    </button>
                                )}

                                <button className="btn btn-secondary" onClick={handleExport}>
                                    Export
                                </button>

                                <button className="btn btn-primary" onClick={handleCreate}>
                                    + Add New
                                </button>
                            </div>
                        </header>

                        {error && (
                            <div className="error-banner">{error}</div>
                        )}

                        <DataTable
                            columns={getTableColumns()}
                            data={records}
                            loading={loading}
                            selectable
                            selectedIds={selectedIds}
                            onSelect={setSelectedIds}
                            onSort={setSort}
                            currentSort={sort}
                            onRowClick={handleEdit}
                        />

                        <Pagination
                            page={page}
                            totalPages={Math.ceil(totalRecords / pageSize)}
                            onPageChange={setPage}
                            pageSize={pageSize}
                            onPageSizeChange={setPageSize}
                            totalItems={totalRecords}
                        />
                    </div>
                )}

                {/* Create/Edit Form */}
                {currentModel && (viewMode === 'create' || viewMode === 'edit') && (
                    <div className="admin-form">
                        <header className="form-header">
                            <button className="btn-back" onClick={handleBack}>
                                ← Back
                            </button>
                            <h1>
                                {viewMode === 'create'
                                    ? `Create ${currentSchema?.admin.name || currentModel}`
                                    : `Edit ${currentSchema?.admin.name || currentModel}`
                                }
                            </h1>
                        </header>

                        <DynamicForm
                            fields={getFormFields()}
                            initialValues={viewMode === 'edit' ? getEditValues() : {}}
                            onSubmit={handleSubmit}
                            onCancel={handleBack}
                            submitLabel={viewMode === 'create' ? 'Create' : 'Save Changes'}
                            loading={loading}
                        />
                    </div>
                )}
            </main>
        </div>
    );
}

export default AdminPanel;
