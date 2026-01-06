/**
 * P8s Admin Panel - Main Component
 * 
 * The main admin panel that brings together all components
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar } from './Sidebar';
import { DataTable, Pagination } from './DataTable';
import { DynamicForm, fieldMetaToFormField } from './DynamicForm';
import * as adminApi from '../../api/admin';
import type { ModelSchema, Sort, TableColumn, FormField } from '../../types/admin';

// View modes
type ViewMode = 'list' | 'create' | 'edit' | 'view';

interface AdminPanelProps {
    apiUrl?: string;
}

export function AdminPanel({ apiUrl }: AdminPanelProps) {
    // State
    const [models, setModels] = useState<ModelSchema[]>([]);
    const [currentModel, setCurrentModel] = useState<string | null>(null);
    const [currentSchema, setCurrentSchema] = useState<ModelSchema | null>(null);
    const [viewMode, setViewMode] = useState<ViewMode>('list');
    const [editingId, setEditingId] = useState<string | null>(null);

    // List state
    const [records, setRecords] = useState<Record<string, unknown>[]>([]);
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

    // Load models on mount
    useEffect(() => {
        loadModels();
    }, []);

    // Load records when model changes
    useEffect(() => {
        if (currentModel) {
            loadRecords();
        }
    }, [currentModel, page, pageSize, sort, search]);

    const loadModels = async () => {
        try {
            setLoading(true);
            const data = await adminApi.getAdminModels();
            setModels(data);
        } catch (err) {
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

            const data = await adminApi.listRecords(currentModel, {
                page,
                pageSize,
                sort,
                search: search || undefined,
            });

            setRecords(data.items);
            setTotalRecords(data.total);
        } catch (err) {
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
            } catch {
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

    const handleEdit = (row: Record<string, unknown>) => {
        setEditingId(row.id as string);
        setViewMode('edit');
    };

    const handleView = (row: Record<string, unknown>) => {
        setEditingId(row.id as string);
        setViewMode('view');
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
                showNotification('Record created successfully', 'success');
            } else if (viewMode === 'edit' && editingId) {
                await adminApi.updateRecord(currentModel, editingId, values);
                showNotification('Record updated successfully', 'success');
            }

            setViewMode('list');
            setEditingId(null);
            loadRecords();
        } catch (err) {
            throw err; // Let the form handle the error
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

    return (
        <div className="admin-panel">
            <Sidebar
                models={models}
                currentModel={currentModel}
                onSelectModel={handleModelSelect}
                collapsed={sidebarCollapsed}
                onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
            />

            <main className="admin-main">
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
