/**
 * P8s Admin Panel - Type Definitions
 *
 * Types for the admin panel components and API
 */

// Base model with P8s standard fields
export interface BaseModel {
    id: string;
    created_at: string;
    updated_at: string;
    deleted_at: string | null;
}

// Admin configuration for a model
export interface AdminConfig {
    name: string;
    plural_name: string;
    icon?: string;
    list_display: string[];
    search_fields: string[];
    list_filter: string[]; // Added list_filter
    filterable_fields: string[];
    readonly_fields: string[];
    hidden_fields: string[];
    ordering: string;
    page_size: number;
}

// Field metadata
export interface FieldMeta {
    name: string;
    type: 'string' | 'number' | 'boolean' | 'date' | 'datetime' | 'json' | 'relation' | 'ai' | 'vector' | 'richtext' | 'color' | 'tags' | 'code';
    primary_key: boolean;
    required: boolean;
    nullable: boolean;
    default?: any;
    description?: string;
    label?: string; // from verbose_name
    choices?: Array<{ value: string; label: string }>;
    api_readonly?: boolean;
    relation?: {
        model: string;
        field: string;
        local_field?: string;
    };
    ai_config?: {
        prompt: string;
        source_fields: string[];
    };
    language?: string; // For code fields
}

// Model schema from admin API
export interface ModelSchema {
    name: string;
    app_label: string;
    table_name: string;
    admin: AdminConfig;
    fields: Record<string, FieldMeta>;
    actions: Array<{
        name: string;
        description: string;
        confirm: boolean;
        confirm_message?: string;
    }>;
}

// Paginated response
export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    page_size: number;
    pages: number;
}

// API Error
export interface APIError {
    detail: string;
    code?: string;
    field?: string;
}

// User model
export interface User extends BaseModel {
    email: string;
    is_active: boolean;
    is_superuser: boolean;
}

// Auth state
export interface AuthState {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
}

// Admin context
export interface AdminContext {
    models: ModelSchema[];
    currentModel: ModelSchema | null;
    isLoading: boolean;
    error: string | null;
}

// Table column definition
export interface TableColumn {
    key: string;
    label: string;
    type: FieldMeta['type'];
    sortable: boolean;
    width?: string;
    render?: (value: unknown, row: Record<string, unknown>) => React.ReactNode;
}

// Form field definition
export interface FormField {
    name: string;
    label: string;
    description?: string; // Help text
    type: 'text' | 'number' | 'email' | 'password' | 'textarea' | 'select' | 'checkbox' | 'date' | 'datetime' | 'json' | 'readonly' | 'relation' | 'richtext' | 'color' | 'tags' | 'code';
    required: boolean;
    placeholder?: string;
    options?: Array<{ value: string; label: string }>;
    relation?: {
        model: string;
        field: string;
        local_field?: string;
    };
    language?: string; // For code fields
    validation?: {
        min?: number;
        max?: number;
        pattern?: string;
        message?: string;
    };
}

// Filter definition
export interface Filter {
    field: string;
    operator: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'like' | 'in' | 'is_null';
    value: unknown;
}

// Sort definition
export interface Sort {
    field: string;
    direction: 'asc' | 'desc';
}
