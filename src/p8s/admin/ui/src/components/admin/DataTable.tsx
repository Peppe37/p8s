/**
 * P8s Admin - Data Table Component
 * 
 * A reusable table component for displaying model records
 */

import React, { useState } from 'react';
import type { TableColumn, Sort } from '../../types/admin';

interface DataTableProps<T> {
    columns: TableColumn[];
    data: T[];
    loading?: boolean;
    selectable?: boolean;
    selectedIds?: string[];
    onSelect?: (ids: string[]) => void;
    onSort?: (sort: Sort) => void;
    currentSort?: Sort;
    onRowClick?: (row: T) => void;
    emptyMessage?: string;
}

export function DataTable<T extends { id: string }>({
    columns,
    data,
    loading = false,
    selectable = false,
    selectedIds = [],
    onSelect,
    onSort,
    currentSort,
    onRowClick,
    emptyMessage = 'No records found',
}: DataTableProps<T>) {
    const [hoveredRow, setHoveredRow] = useState<string | null>(null);

    const handleSelectAll = () => {
        if (selectedIds.length === data.length) {
            onSelect?.([]);
        } else {
            onSelect?.(data.map(row => row.id));
        }
    };

    const handleSelectRow = (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        if (selectedIds.includes(id)) {
            onSelect?.(selectedIds.filter(i => i !== id));
        } else {
            onSelect?.([...selectedIds, id]);
        }
    };

    const handleSort = (field: string) => {
        if (!onSort) return;

        const direction = currentSort?.field === field && currentSort.direction === 'asc'
            ? 'desc'
            : 'asc';
        onSort({ field, direction });
    };

    const formatValue = (value: unknown, type: TableColumn['type']): React.ReactNode => {
        if (value === null || value === undefined) {
            return <span className="text-muted">—</span>;
        }

        switch (type) {
            case 'boolean':
                return value ? (
                    <span className="badge badge-success">✓</span>
                ) : (
                    <span className="badge badge-error">✗</span>
                );

            case 'date':
                return new Date(value as string).toLocaleDateString();

            case 'datetime':
                return new Date(value as string).toLocaleString();

            case 'json':
                return (
                    <code className="text-xs">
                        {JSON.stringify(value).slice(0, 50)}...
                    </code>
                );

            case 'ai':
                return (
                    <span className="flex items-center gap-1">
                        <span className="ai-badge">AI</span>
                        {String(value).slice(0, 50)}...
                    </span>
                );

            default:
                const str = String(value);
                return str.length > 100 ? str.slice(0, 100) + '...' : str;
        }
    };

    if (loading) {
        return (
            <div className="table-loading">
                <div className="spinner" />
                <span>Loading...</span>
            </div>
        );
    }

    if (data.length === 0) {
        return (
            <div className="table-empty">
                <span className="empty-icon">📭</span>
                <p>{emptyMessage}</p>
            </div>
        );
    }

    return (
        <div className="data-table-container">
            <table className="data-table">
                <thead>
                    <tr>
                        {selectable && (
                            <th className="checkbox-cell">
                                <label className="checkbox-label" style={{ marginBottom: 0 }}>
                                    <input
                                        type="checkbox"
                                        checked={selectedIds.length === data.length}
                                        onChange={handleSelectAll}
                                    />
                                </label>
                            </th>
                        )}
                        {columns.map(col => (
                            <th
                                key={col.key}
                                className={col.sortable ? 'sortable' : ''}
                                style={{ width: col.width }}
                                onClick={() => col.sortable && handleSort(col.key)}
                            >
                                <span className="th-content">
                                    {col.label}
                                    {col.sortable && currentSort?.field === col.key && (
                                        <span className="sort-indicator">
                                            {currentSort.direction === 'asc' ? '↑' : '↓'}
                                        </span>
                                    )}
                                </span>
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {data.map(row => (
                        <tr
                            key={row.id}
                            className={`
                ${hoveredRow === row.id ? 'hovered' : ''}
                ${selectedIds.includes(row.id) ? 'selected' : ''}
                ${onRowClick ? 'clickable' : ''}
              `}
                            onMouseEnter={() => setHoveredRow(row.id)}
                            onMouseLeave={() => setHoveredRow(null)}
                            onClick={() => onRowClick?.(row)}
                        >
                            {selectable && (
                                <td className="checkbox-cell">
                                    <label className="checkbox-label" style={{ marginBottom: 0 }}>
                                        <input
                                            type="checkbox"
                                            checked={selectedIds.includes(row.id)}
                                            onClick={(e) => handleSelectRow(row.id, e)}
                                            onChange={() => { }}
                                        />
                                    </label>
                                </td>
                            )}
                            {columns.map(col => (
                                <td key={col.key}>
                                    {col.render
                                        ? col.render((row as Record<string, unknown>)[col.key], row as Record<string, unknown>)
                                        : formatValue((row as Record<string, unknown>)[col.key], col.type)
                                    }
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

// Pagination component
interface PaginationProps {
    page: number;
    totalPages: number;
    onPageChange: (page: number) => void;
    pageSize: number;
    onPageSizeChange?: (size: number) => void;
    totalItems: number;
}

export function Pagination({
    page,
    totalPages,
    onPageChange,
    pageSize,
    onPageSizeChange,
    totalItems,
}: PaginationProps) {
    const pageSizes = [10, 25, 50, 100];
    const start = (page - 1) * pageSize + 1;
    const end = Math.min(page * pageSize, totalItems);

    return (
        <div className="pagination">
            <div className="pagination-info">
                Showing {start}-{end} of {totalItems} records
            </div>

            <div className="pagination-controls">
                {onPageSizeChange && (
                    <select
                        value={pageSize}
                        onChange={(e) => onPageSizeChange(Number(e.target.value))}
                        className="page-size-select"
                    >
                        {pageSizes.map(size => (
                            <option key={size} value={size}>{size} per page</option>
                        ))}
                    </select>
                )}

                <div className="page-buttons">
                    <button
                        onClick={() => onPageChange(1)}
                        disabled={page === 1}
                        className="btn-page"
                    >
                        ⟨⟨
                    </button>
                    <button
                        onClick={() => onPageChange(page - 1)}
                        disabled={page === 1}
                        className="btn-page"
                    >
                        ⟨
                    </button>

                    <span className="page-indicator">
                        Page {page} of {totalPages}
                    </span>

                    <button
                        onClick={() => onPageChange(page + 1)}
                        disabled={page === totalPages}
                        className="btn-page"
                    >
                        ⟩
                    </button>
                    <button
                        onClick={() => onPageChange(totalPages)}
                        disabled={page === totalPages}
                        className="btn-page"
                    >
                        ⟩⟩
                    </button>
                </div>
            </div>
        </div>
    );
}

export default DataTable;
