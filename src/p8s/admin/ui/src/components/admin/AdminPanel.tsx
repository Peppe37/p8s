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
import { Moon, Sun, LogOut, Database } from 'lucide-react';
import p8sLogo from '../../assets/p8s.svg';

// View modes
type ViewMode = 'list' | 'create' | 'edit';

interface AdminPanelProps {
    apiUrl?: string;
}

interface RecordWithId {
    id: string;
    [key: string]: unknown;
}

// Stable empty object for initial values to prevent resets
const EMPTY_VALUES = {};

export function AdminPanel({ }: AdminPanelProps) {
    // Auth State
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(!!localStorage.getItem('p8s_token'));
    const [loginUser, setLoginUser] = useState('');
    const [loginPass, setLoginPass] = useState('');
    const [loginError, setLoginError] = useState('');
    const [p8sVersion, setP8sVersion] = useState<string>('');

    // Theme State
    const [theme, setTheme] = useState<'light' | 'dark'>(() => {
        return (localStorage.getItem('p8s_theme') as 'light' | 'dark') || 'light';
    });

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('p8s_theme', theme);
    }, [theme]);

    const toggleTheme = () => {
        setTheme(prev => prev === 'light' ? 'dark' : 'light');
    };

    // State
    const [models, setModels] = useState<ModelSchema[]>([]);
    const [currentModel, setCurrentModel] = useState<string | null>(null);
    const [currentSchema, setCurrentSchema] = useState<ModelSchema | null>(null);
    const [viewMode, setViewMode] = useState<ViewMode>('list');
    const [editingId, setEditingId] = useState<string | null>(null);
    const [formKey, setFormKey] = useState(0);

    // List state
    const [records, setRecords] = useState<RecordWithId[]>([]);
    const [totalRecords, setTotalRecords] = useState(0);
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(25);
    const [sort, setSort] = useState<Sort | undefined>();
    const [search, setSearch] = useState('');
    const [activeFilters, setActiveFilters] = useState<Record<string, any>>({});
    const [selectedIds, setSelectedIds] = useState<string[]>([]);
    const [actionLoading, setActionLoading] = useState(false);
    const [selectedAction, setSelectedAction] = useState('');

    // Modal state for inline create
    const [relatedModalOpen, setRelatedModalOpen] = useState(false);
    const [relatedModelName, setRelatedModelName] = useState<string | null>(null);
    const [relatedModelSchema, setRelatedModelSchema] = useState<ModelSchema | null>(null);


    // UI state
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const sidebarCollapsed = false;
    const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

    // Notification timer - Dismiss all messages after 5s
    useEffect(() => {
        if (notification) {
            const timer = setTimeout(() => {
                setNotification(null);
            }, 5000);
            return () => clearTimeout(timer);
        }
    }, [notification]);

    // Load version on mount (public endpoint)
    useEffect(() => {
        fetch('/admin/api/version')
            .then(res => res.json())
            .then(data => setP8sVersion(data.version || ''))
            .catch(() => { });
    }, []);

    // Initial load handled by auth effect
    useEffect(() => {
        if (isAuthenticated) {
            loadModels();
        }
    }, [isAuthenticated]);

    // Load records when dependencies change
    useEffect(() => {
        if (currentModel && isAuthenticated) {
            loadRecords();
        }
    }, [currentModel, page, pageSize, sort, search, activeFilters, isAuthenticated]);

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

    // Define functions before use or use function declaration for hoisting
    // Using const here, but defining BEFORE usage in future if feasible.
    // However, loadRecords is used in useEffect above.
    // To allow hoisting, we use function declaration for these helpers.

    async function loadModels() {
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
    }

    async function loadRecords() {
        if (!currentModel) return;

        try {
            setLoading(true);
            setError(null);

            const data = await adminApi.listRecords<RecordWithId>(currentModel, {
                page,
                pageSize,
                sort,
                search: search || undefined,
                filters: activeFilters,
            });

            setRecords(data.items);
            setTotalRecords(data.total);
        } catch (err: any) {
            if (err.status === 401) {
                setIsAuthenticated(false);
                localStorage.removeItem('p8s_token');
                return;
            }
            // Use toast instead of error banner
            showNotification(err instanceof Error ? err.message : 'Failed to load records', 'error');
        } finally {
            setLoading(false);
        }
    }

    const handleModelSelect = async (name: string) => {
        setCurrentModel(name || null);
        setViewMode('list');
        setEditingId(null);
        setSelectedIds([]);
        setPage(1);
        setSearch('');
        setPage(1);
        setSearch('');
        setSort(undefined);
        setActiveFilters({});
        setSelectedAction('');

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

    const handleFilterChange = (field: string, value: any) => {
        setPage(1); // Reset to first page on filter change
        setActiveFilters(prev => {
            const next = { ...prev };
            if (value === null || value === undefined || value === '') {
                delete next[field];
            } else {
                next[field] = value;
            }
            return next;
        });
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

    const handleSubmit = async (values: Record<string, unknown>, action: 'save' | 'save_continue' | 'save_add') => {
        if (!currentModel) return;

        try {
            let recordId = editingId;
            let newRecord: RecordWithId | null = null;

            if (viewMode === 'create') {
                newRecord = await adminApi.createRecord<RecordWithId>(currentModel, values);
                recordId = newRecord.id;
            } else if (viewMode === 'edit' && editingId) {
                await adminApi.updateRecord(currentModel, editingId, values);
            }

            showNotification('Operation successful', 'success');

            if (action === 'save') {
                setViewMode('list');
                setEditingId(null);
                loadRecords();
            } else if (action === 'save_continue') {
                if (viewMode === 'create' && newRecord) {
                    // Update verification: manually add to records or reload
                    // To be safe and simple, we reload records and verify id exists,
                    // but for immediate UI feedback we just set state.
                    // We need the new record in 'records' for getEditValues() to work.
                    setRecords(prev => [...prev, newRecord!]);
                    setEditingId(recordId);
                    setViewMode('edit');
                }
                // If already editing, stay in edit mode
            } else if (action === 'save_add') {
                setViewMode('create');
                setEditingId(null);
                setFormKey(prev => prev + 1); // Force form reset
            }

            // Always reload list in background to ensure sync
            if (action !== 'save') {
                loadRecords();
            }

        } catch (err: any) {
            console.error(err);
            const msg = err.message || 'Failed to save record';
            showNotification(msg, 'error');
            // Do not re-throw, as we handled it via notification.
            // Re-throwing causes DynamicForm to show a duplicate generic error banner.
        }
    };

    const handleAction = async () => {
        if (!selectedAction || selectedIds.length === 0) return;

        // Find action config
        const actionConfig = currentSchema?.actions.find(a => a.name === selectedAction);

        if (actionConfig?.confirm) {
            if (!window.confirm(actionConfig.confirm_message || 'Are you sure you want to proceed?')) {
                return;
            }
        }

        setActionLoading(true);
        try {
            await adminApi.executeAction(currentModel!, selectedAction, selectedIds);
            showNotification('Action executed successfully', 'success');
            loadRecords(); // Refresh data
            setSelectedIds([]);
        } catch (err) {
            setNotification({ message: 'Failed to execute action', type: 'error' });
        } finally {
            setActionLoading(false);
        }
    };

    // --- Inline Creation Handlers ---

    const handleAddRelated = async (modelName: string) => {
        setRelatedModelName(modelName);
        setRelatedModalOpen(true);

        try {
            // Find schema for related model
            // Try to find in loaded models first to avoid API call if possible
            let schema = models.find(m => m.name === modelName);
            if (!schema) {
                // Fetch if not found (though models should be loaded)
                const res = await adminApi.getModelSchema(modelName);
                schema = res;
            }
            setRelatedModelSchema(schema || null);
        } catch (err) {
            console.error("Failed to load related model schema", err);
            setNotification({ message: `Failed to load schema for ${modelName}`, type: 'error' });
            setRelatedModalOpen(false);
        }
    };

    const handleRelatedSubmit = async (values: Record<string, unknown>) => {
        if (!relatedModelName) return;

        try {
            // Create record
            await adminApi.createRecord(relatedModelName, values);
            setNotification({ message: `${relatedModelName} created successfully`, type: 'success' });
            setRelatedModalOpen(false);

            // Refresh parent schema/form to get new options
            // We need to reload the CURRENT model schema to refresh choices for the field
            if (currentModel) {
                const updatedSchema = await adminApi.getModelSchema(currentModel);
                setCurrentSchema(updatedSchema);
                // We also need to update this model in the global list
                setModels(prev => prev.map(m => m.name === currentModel ? updatedSchema : m));

                // Ideally we'd select the new item, but for now just refreshing the list is a good start
                // If the API returned the created ID, we could auto-select it.
            }

        } catch (err) {
            console.error(err);
            throw new Error("Failed to create related record");
        }
    };

    // --- Render Helpers ---
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

    // Relationship state
    const [relationOptions, setRelationOptions] = useState<Record<string, Array<{ value: string; label: string }>>>({});

    // Load relationship options when schema changes
    useEffect(() => {
        if (currentSchema) {
            loadRelationshipOptions();
        } else {
            setRelationOptions({});
        }
    }, [currentSchema]);

    const loadRelationshipOptions = async () => {
        if (!currentSchema) return;
        const newOptions: Record<string, Array<{ value: string; label: string }>> = {};

        const promises = Object.entries(currentSchema.fields)
            .filter(([_, meta]) => meta.type === 'relation' && meta.relation)
            .map(async ([name, meta]) => {
                if (meta.relation?.model) {
                    try {
                        const items = await adminApi.getModelItems(meta.relation.model);
                        newOptions[name] = items;
                    } catch (e) {
                        console.error('Failed to load relations for', name, e);
                    }
                }
            });

        await Promise.all(promises);
        setRelationOptions(newOptions);
    };

    // Generate form fields from schema
    const getFormFields = (): FormField[] => {
        if (!currentSchema) return [];

        const hiddenFields = ['id', 'created_at', 'updated_at', 'deleted_at'];

        // Find fields that should be hidden because they are handled by relations
        const relationFields = Object.values(currentSchema.fields)
            .filter(meta => meta.type === 'relation' && meta.relation?.local_field)
            .map(meta => meta.relation!.local_field!);

        return Object.entries(currentSchema.fields)
            .filter(([name]) => !hiddenFields.includes(name))
            .filter(([name]) => !currentSchema.admin.hidden_fields.includes(name))
            .filter(([name]) => !relationFields.includes(name)) // Hide raw FK fields
            .map(([name, meta]) => {
                const field = fieldMetaToFormField(name, meta, {
                    readonly: currentSchema.admin.readonly_fields.includes(name),
                });

                // Inject options for relations
                if (meta.type === 'relation' && relationOptions[name]) {
                    // field.type = 'select'; // Removed override to keep 'relation' type for DynamicForm
                    field.options = relationOptions[name];

                    // If this relation maps to a local field (FK), use that name for the form
                    // This ensures the form submits "category_id": "uuid" instead of "category": "uuid"
                    if (meta.relation?.local_field) {
                        field.name = meta.relation.local_field;
                    }

                    // Clean up label if it's "Category ID" -> "Category"
                    if (field.label.endsWith(' Id')) {
                        field.label = field.label.slice(0, -3);
                    }
                }

                return field;
            });
    };

    // Get initial values for editing
    const getEditValues = (): Record<string, unknown> => {
        if (!editingId) return {};
        return records.find(r => r.id === editingId) || {};
    };

    if (!isAuthenticated) {
        return (
            <div className="login-container">
                <form onSubmit={handleLogin} className="login-box">
                    <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                        <img src={p8sLogo} alt="P8s Logo" style={{ width: '64px', height: '64px', marginBottom: '1rem' }} />
                        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>P8s Admin</h2>
                        <p style={{ marginTop: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Sign in to manage your application</p>
                    </div>

                    {loginError && (
                        <div style={{ marginBottom: '1.5rem', padding: '0.75rem', background: 'var(--danger-bg)', color: 'var(--danger)', borderRadius: 'var(--radius)', fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span style={{ fontWeight: 'bold' }}>!</span> {loginError}
                        </div>
                    )}

                    <div className="form-group">
                        <label className="form-label">Email / Username</label>
                        <input
                            type="text"
                            value={loginUser}
                            onChange={e => setLoginUser(e.target.value)}
                            className="form-input"
                            placeholder="Enter your email or username"
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Password</label>
                        <input
                            type="password"
                            value={loginPass}
                            onChange={e => setLoginPass(e.target.value)}
                            className="form-input"
                            placeholder="••••••••"
                            required
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={loading}
                        className="btn btn-primary"
                        style={{ width: '100%', justifyContent: 'center' }}
                    >
                        {loading ? 'Signing In...' : 'Sign In'}
                    </button>

                    <div style={{ marginTop: '2rem', textAlign: 'center', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        Powered by P8s Framework {p8sVersion && <span style={{ opacity: 0.7 }}>v{p8sVersion}</span>}
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
            />
            {/* Added Logout button absolute positioned or in a header inside main if Sidebar doesn't have it */}
            <div style={{ position: 'absolute', bottom: '1rem', left: sidebarCollapsed ? '0.5rem' : '1rem', zIndex: 100 }}>
            </div>

            <main className="admin-main">
                {/* Global Header/Toolbar */}
                <div className="global-header">
                    <button className="theme-toggle" onClick={toggleTheme} title="Toggle Theme">
                        {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
                    </button>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Admin User</span>
                        <button
                            onClick={handleLogout}
                            className="btn btn-secondary"
                            style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '6px' }}
                        >
                            <LogOut size={14} />
                            Logout
                        </button>
                    </div>
                </div>

                {/* Notification */}
                {notification && (
                    <div className={`notification ${notification.type}`} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span>{notification.message}</span>
                        {notification.type === 'error' && (
                            <button
                                onClick={() => setNotification(null)}
                                style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', marginLeft: '10px' }}
                            >
                                ✕
                            </button>
                        )}
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
                                    <div className="card-icon"><Database size={24} className="text-primary" /></div>
                                    <div className="card-content">
                                        <h3>{model.admin.plural_name}</h3>
                                        <p>Manage {model.admin.plural_name.toLowerCase()}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Model List View & Filter Sidebar */}
                {/* ... existing code ... */}
                {
                    currentModel && viewMode === 'list' && (
                        <div className="list-wrapper">
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

                                        {selectedIds.length > 0 && currentSchema?.actions && currentSchema.actions.length > 0 && (
                                            <div className="action-params" style={{ display: 'flex', gap: '0.5rem' }}>
                                                <select
                                                    value={selectedAction}
                                                    onChange={(e) => setSelectedAction(e.target.value)}
                                                    className="form-input"
                                                    style={{ padding: '0.25rem 0.5rem', height: 'auto', minWidth: '150px' }}
                                                >
                                                    <option value="">-- Select Action --</option>
                                                    {currentSchema.actions.map(action => (
                                                        <option key={action.name} value={action.name}>
                                                            {action.description}
                                                        </option>
                                                    ))}
                                                </select>
                                                <button
                                                    className="btn btn-secondary"
                                                    disabled={!selectedAction || actionLoading}
                                                    onClick={handleAction}
                                                >
                                                    {actionLoading ? 'Running...' : 'Go'}
                                                </button>
                                            </div>
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

                            {/* Filter Sidebar */}
                            {currentSchema?.admin.list_filter && currentSchema.admin.list_filter.length > 0 && (
                                <div className="filter-sidebar">
                                    <h3>Filter</h3>
                                    {currentSchema.admin.list_filter.map(filterField => {
                                        const fieldMeta = currentSchema.fields[filterField];
                                        // Determine filter type based on field type
                                        // For relations, use select. For boolean, use All/Yes/No links.
                                        // For others, use basic input or predefined choices logic.

                                        const options = relationOptions[filterField] || fieldMeta?.choices;

                                        return (
                                            <div key={filterField} className="filter-group">
                                                <h4>{fieldMeta?.label || filterField}</h4>
                                                <ul>
                                                    <li className={!activeFilters[filterField] ? 'selected' : ''}>
                                                        <a href="#" onClick={(e) => { e.preventDefault(); handleFilterChange(filterField, null); }}>All</a>
                                                    </li>
                                                    {options ? (
                                                        options.map(opt => (
                                                            <li key={opt.value} className={activeFilters[filterField] === opt.value ? 'selected' : ''}>
                                                                <a href="#" onClick={(e) => { e.preventDefault(); handleFilterChange(filterField, opt.value); }}>
                                                                    {opt.label}
                                                                </a>
                                                            </li>
                                                        ))
                                                    ) : (
                                                        // Fallback for non-option fields (like boolean or simple lookup)
                                                        // TODO: Implement date hierarchy or smart ranges
                                                        // For now assumes everything else is basic choices or boolean treated as choices if possible
                                                        // If no choices, maybe render input? keeping it simple for now.
                                                        <li style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', fontStyle: 'italic' }}>
                                                            No options available
                                                        </li>
                                                    )}
                                                </ul>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    )
                }

                {/* Create/Edit Form */}
                {
                    currentModel && (viewMode === 'create' || viewMode === 'edit') && (
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
                                key={`${viewMode}-${editingId}-${formKey}`}
                                fields={getFormFields()}
                                initialValues={viewMode === 'edit' ? getEditValues() : {}}
                                onSubmit={handleSubmit}
                                onCancel={handleBack}
                                submitLabel={viewMode === 'create' ? 'Create' : 'Save Changes'}
                                loading={loading}
                                onAddRelated={handleAddRelated}
                            />
                        </div>
                    )
                }
            </main>

            {/* Modal for Inline Creation */}
            {relatedModalOpen && relatedModelSchema && (
                <div className="modal-overlay">
                    <div className="modal-content" style={{ maxWidth: '600px', width: '100%' }}>
                        <div className="modal-header">
                            <h3>Add New {relatedModelSchema.admin.name}</h3>
                            <button className="btn-close" onClick={() => setRelatedModalOpen(false)}>×</button>
                        </div>
                        <div className="modal-body">
                            <DynamicForm
                                fields={Object.entries(relatedModelSchema.fields)
                                    .filter(([name, meta]) =>
                                        !meta.api_readonly &&
                                        !['id', 'created_at', 'updated_at', 'deleted_at'].includes(name)
                                    )
                                    .map(([name, meta]) => fieldMetaToFormField(name, meta, {}))}
                                initialValues={EMPTY_VALUES}
                                onSubmit={handleRelatedSubmit}
                                onCancel={() => setRelatedModalOpen(false)}
                                submitLabel="Save"
                                cancelLabel="Close"
                                hideSaveOptions={true}
                            />
                        </div>
                    </div>
                </div>
            )}

            {/* Change Password Modal */}
            <ChangePasswordModal
                userId={editingId}
                onSuccess={() => showNotification('Password changed successfully', 'success')}
                onError={(msg) => showNotification(msg, 'error')}
            />
        </div>
    );
}

// Change Password Modal Component
function ChangePasswordModal({ userId, onSuccess, onError }: { userId: string | null; onSuccess: () => void; onError: (msg: string) => void }) {
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [saving, setSaving] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (newPassword.length < 8) {
            onError('Password must be at least 8 characters');
            return;
        }

        if (newPassword !== confirmPassword) {
            onError('Passwords do not match');
            return;
        }

        if (!userId) {
            onError('No user selected');
            return;
        }

        setSaving(true);
        try {
            const token = localStorage.getItem('p8s_token');
            const API_BASE = import.meta.env.DEV ? 'http://localhost:8000' : '';

            // Update user's password via admin endpoint
            const response = await fetch(`${API_BASE}/admin/User/${userId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
                },
                body: JSON.stringify({ password_hash: newPassword }),
            });

            if (!response.ok) {
                const err = await response.json().catch(() => ({ detail: 'Failed to change password' }));
                throw new Error(err.detail || 'Failed to change password');
            }

            onSuccess();
            setNewPassword('');
            setConfirmPassword('');
            const modal = document.getElementById('change-password-modal');
            if (modal) modal.style.display = 'none';
        } catch (err: any) {
            onError(err.message || 'Failed to change password');
        } finally {
            setSaving(false);
        }
    };

    const closeModal = () => {
        const modal = document.getElementById('change-password-modal');
        if (modal) modal.style.display = 'none';
        setNewPassword('');
        setConfirmPassword('');
    };

    return (
        <div
            id="change-password-modal"
            className="modal-overlay"
            style={{ display: 'none' }}
            onClick={(e) => { if (e.target === e.currentTarget) closeModal(); }}
        >
            <div className="modal-content" style={{ maxWidth: '400px', width: '100%' }}>
                <div className="modal-header">
                    <h3>Change Password</h3>
                    <button className="btn-close" onClick={closeModal}>×</button>
                </div>
                <form onSubmit={handleSubmit} className="modal-body" style={{ padding: '24px' }}>
                    <div className="form-group">
                        <label className="form-label">New Password</label>
                        <input
                            type="password"
                            className="form-input"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            placeholder="Minimum 8 characters"
                            required
                            minLength={8}
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Confirm Password</label>
                        <input
                            type="password"
                            className="form-input"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            placeholder="Repeat password"
                            required
                        />
                    </div>
                    <div className="form-actions" style={{ marginTop: '24px' }}>
                        <button type="button" className="btn btn-secondary" onClick={closeModal}>
                            Cancel
                        </button>
                        <button type="submit" className="btn btn-primary" disabled={saving}>
                            {saving ? 'Saving...' : 'Change Password'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default AdminPanel;
