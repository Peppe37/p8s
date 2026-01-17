/**
 * P8s Admin API Client
 *
 * Functions to interact with the admin API endpoints
 */

import type { ModelSchema, PaginatedResponse, Filter, Sort } from '../types/admin';

const API_BASE = import.meta.env.DEV ? 'http://localhost:8000' : '';

// Get auth token from localStorage
function getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('p8s_token');
    return {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    } as HeadersInit;
}

// Handle API response
async function handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        // If 401, maybe trigger logout? but we throw error first
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        const errorMessage = error.detail || `HTTP ${response.status}`;
        const err = new Error(errorMessage);
        (err as any).status = response.status;
        throw err;
    }
    return response.json();
}

export async function login(identifier: string, password: string): Promise<{ access_token: string; token_type: string }> {
    const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ identifier, password }),
    });
    return handleResponse(response);
}

/**
 * Fetch all registered admin models
 */
export async function getAdminModels(): Promise<ModelSchema[]> {
    const response = await fetch(`${API_BASE}/admin/models`, {
        headers: getAuthHeaders(),
    });
    return handleResponse<ModelSchema[]>(response);
}

/**
 * Fetch schema for a specific model
 */
export async function getModelSchema(modelName: string): Promise<ModelSchema> {
    const response = await fetch(`${API_BASE}/admin/models/${modelName}`, {
        headers: getAuthHeaders(),
    });
    return handleResponse<ModelSchema>(response);
}

/**
 * List records for a model with pagination and filters
 */
export async function listRecords<T = Record<string, unknown>>(
    modelName: string,
    options: {
        page?: number;
        pageSize?: number;
        filters?: Record<string, any>;
        sort?: Sort;
        search?: string;
    } = {}
): Promise<PaginatedResponse<T>> {
    const params = new URLSearchParams();

    if (options.page) params.set('page', options.page.toString());
    if (options.pageSize) params.set('page_size', options.pageSize.toString());
    if (options.search) params.set('search', options.search);
    if (options.sort) {
        params.set('order_by', options.sort.direction === 'desc' ? `-${options.sort.field}` : options.sort.field);
    }
    if (options.filters) {
        Object.entries(options.filters).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                params.set(key, String(value));
            }
        });
    }

    const response = await fetch(`${API_BASE}/admin/${modelName}?${params}`, {
        headers: getAuthHeaders(),
    });
    return handleResponse<PaginatedResponse<T>>(response);
}

/**
 * Get a single record by ID
 */
export async function getRecord<T = Record<string, unknown>>(
    modelName: string,
    id: string
): Promise<T> {
    const response = await fetch(`${API_BASE}/admin/${modelName}/${id}`, {
        headers: getAuthHeaders(),
    });
    return handleResponse<T>(response);
}

/**
 * Create a new record
 */
export async function createRecord<T = Record<string, unknown>>(
    modelName: string,
    data: Partial<T>
): Promise<T> {
    const response = await fetch(`${API_BASE}/admin/${modelName}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(data),
    });
    return handleResponse<T>(response);
}

/**
 * Update an existing record
 */
export async function updateRecord<T = Record<string, unknown>>(
    modelName: string,
    id: string,
    data: Partial<T>
): Promise<T> {
    const response = await fetch(`${API_BASE}/admin/${modelName}/${id}`, {
        method: 'PATCH',
        headers: getAuthHeaders(),
        body: JSON.stringify(data),
    });
    return handleResponse<T>(response);
}

/**
 * Delete a record (soft delete if supported)
 */
export async function deleteRecord(
    modelName: string,
    id: string,
    permanent: boolean = false
): Promise<void> {
    const params = permanent ? '?permanent=true' : '';
    const response = await fetch(`${API_BASE}/admin/${modelName}/${id}${params}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
    });
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Delete failed' }));
        throw new Error(error.detail);
    }
}

/**
 * Restore a soft-deleted record
 */
export async function restoreRecord<T = Record<string, unknown>>(
    modelName: string,
    id: string
): Promise<T> {
    const response = await fetch(`${API_BASE}/admin/${modelName}/${id}/restore`, {
        method: 'POST',
        headers: getAuthHeaders(),
    });
    return handleResponse<T>(response);
}

/**
 * Bulk delete records
 */
export async function bulkDelete(
    modelName: string,
    ids: string[],
    permanent: boolean = false
): Promise<{ deleted: number }> {
    const params = permanent ? '?permanent=true' : '';
    const response = await fetch(`${API_BASE}/admin/${modelName}/bulk-delete${params}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ ids }),
    });
    return handleResponse<{ deleted: number }>(response);
}

/**
 * Export records to CSV
 */
export async function exportRecords(
    modelName: string,
    format: 'csv' | 'json' = 'csv',
    filters?: Filter[]
): Promise<Blob> {
    const params = new URLSearchParams({ format });
    if (filters) {
        filters.forEach(f => {
            params.set(`filter[${f.field}][${f.operator}]`, String(f.value));
        });
    }

    const response = await fetch(`${API_BASE}/admin/${modelName}/export?${params}`, {
        headers: getAuthHeaders(),
    });

    if (!response.ok) {
        throw new Error('Export failed');
    }

    return response.blob();
}

/**
 * Get admin dashboard stats
 */
export async function getDashboardStats(): Promise<{
    models: Array<{ name: string; count: number }>;
    recent_activity: Array<{ action: string; model: string; id: string; timestamp: string }>;
}> {
    const response = await fetch(`${API_BASE}/admin/dashboard`, {
        headers: getAuthHeaders(),
    });
    return handleResponse(response);
}
/**
 * Get simple list of items for a model (for dropdowns)
 */
export async function getModelItems(
    modelName: string,
    params: { search?: string } = {}
): Promise<Array<{ value: string; label: string }>> {
    // Reuse listRecords but map to options
    // Assuming backend supports filtering/search
    // We request a resonable limit for dropdowns
    const response = await listRecords(modelName, {
        page: 1,
        pageSize: 100,
        search: params.search
    });

    // Map items to label/value
    // We assume items have 'id' and 'name' or string representation
    return response.items.map((item: any) => ({
        value: item.id,
        label: item.name || item.title || item.slug || item.email || item.username || item.id,
    }));
}

/**
 * Execute an admin action on selected items
 */
export async function executeAction(
    modelName: string,
    actionName: string,
    ids: string[]
): Promise<{ message?: string; affected?: number }> {
    const response = await fetch(`${API_BASE}/admin/${modelName}/action`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ action: actionName, ids }),
    });
    return handleResponse(response);
}
