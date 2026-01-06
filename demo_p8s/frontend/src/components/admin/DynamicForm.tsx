/**
 * P8s Admin - Dynamic Form Component
 * 
 * A form component that generates fields based on model schema
 */

import React, { useState, useEffect } from 'react';
import type { FormField, FieldMeta } from '../../types/admin';

interface DynamicFormProps {
    fields: FormField[];
    initialValues?: Record<string, unknown>;
    onSubmit: (values: Record<string, unknown>) => Promise<void>;
    onCancel?: () => void;
    submitLabel?: string;
    loading?: boolean;
}

export function DynamicForm({
    fields,
    initialValues = {},
    onSubmit,
    onCancel,
    submitLabel = 'Save',
    loading = false,
}: DynamicFormProps) {
    const [values, setValues] = useState<Record<string, unknown>>(initialValues);
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        setValues(initialValues);
    }, [initialValues]);

    const handleChange = (name: string, value: unknown) => {
        setValues(prev => ({ ...prev, [name]: value }));
        // Clear error when field changes
        if (errors[name]) {
            setErrors(prev => {
                const { [name]: _, ...rest } = prev;
                return rest;
            });
        }
    };

    const validate = (): boolean => {
        const newErrors: Record<string, string> = {};

        for (const field of fields) {
            const value = values[field.name];

            if (field.required && (value === undefined || value === null || value === '')) {
                newErrors[field.name] = `${field.label} is required`;
                continue;
            }

            if (field.validation) {
                const { min, max, pattern, message } = field.validation;

                if (typeof value === 'number') {
                    if (min !== undefined && value < min) {
                        newErrors[field.name] = message || `Minimum value is ${min}`;
                    }
                    if (max !== undefined && value > max) {
                        newErrors[field.name] = message || `Maximum value is ${max}`;
                    }
                }

                if (typeof value === 'string' && pattern) {
                    if (!new RegExp(pattern).test(value)) {
                        newErrors[field.name] = message || 'Invalid format';
                    }
                }
            }
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!validate()) return;

        setSubmitting(true);
        try {
            await onSubmit(values);
        } catch (error) {
            // Handle submission error
            if (error instanceof Error) {
                setErrors({ _form: error.message });
            }
        } finally {
            setSubmitting(false);
        }
    };

    const renderField = (field: FormField) => {
        const value = values[field.name];
        const error = errors[field.name];

        const baseProps = {
            id: field.name,
            name: field.name,
            disabled: loading || submitting || field.type === 'readonly',
            className: `form-input ${error ? 'error' : ''}`,
            placeholder: field.placeholder,
        };

        switch (field.type) {
            case 'textarea':
                return (
                    <textarea
                        {...baseProps}
                        value={String(value ?? '')}
                        onChange={(e) => handleChange(field.name, e.target.value)}
                        rows={4}
                    />
                );

            case 'select':
                return (
                    <select
                        {...baseProps}
                        value={String(value ?? '')}
                        onChange={(e) => handleChange(field.name, e.target.value)}
                    >
                        <option value="">Select {field.label}...</option>
                        {field.options?.map(opt => (
                            <option key={opt.value} value={opt.value}>
                                {opt.label}
                            </option>
                        ))}
                    </select>
                );

            case 'checkbox':
                return (
                    <label className="checkbox-label">
                        <input
                            type="checkbox"
                            checked={Boolean(value)}
                            onChange={(e) => handleChange(field.name, e.target.checked)}
                            disabled={loading || submitting}
                        />
                        <span>{field.label}</span>
                    </label>
                );

            case 'number':
                return (
                    <input
                        {...baseProps}
                        type="number"
                        value={value ?? ''}
                        onChange={(e) => handleChange(field.name, e.target.value ? Number(e.target.value) : null)}
                    />
                );

            case 'date':
                return (
                    <input
                        {...baseProps}
                        type="date"
                        value={value ? String(value).split('T')[0] : ''}
                        onChange={(e) => handleChange(field.name, e.target.value)}
                    />
                );

            case 'datetime':
                return (
                    <input
                        {...baseProps}
                        type="datetime-local"
                        value={value ? String(value).slice(0, 16) : ''}
                        onChange={(e) => handleChange(field.name, e.target.value)}
                    />
                );

            case 'json':
                return (
                    <textarea
                        {...baseProps}
                        value={typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
                        onChange={(e) => {
                            try {
                                const parsed = JSON.parse(e.target.value);
                                handleChange(field.name, parsed);
                            } catch {
                                handleChange(field.name, e.target.value);
                            }
                        }}
                        rows={6}
                        className={`${baseProps.className} font-mono`}
                    />
                );

            case 'readonly':
                return (
                    <div className="readonly-field">
                        {typeof value === 'object' ? JSON.stringify(value) : String(value ?? '—')}
                    </div>
                );

            case 'password':
                return (
                    <input
                        {...baseProps}
                        type="password"
                        value={String(value ?? '')}
                        onChange={(e) => handleChange(field.name, e.target.value)}
                    />
                );

            case 'email':
                return (
                    <input
                        {...baseProps}
                        type="email"
                        value={String(value ?? '')}
                        onChange={(e) => handleChange(field.name, e.target.value)}
                    />
                );

            default:
                return (
                    <input
                        {...baseProps}
                        type="text"
                        value={String(value ?? '')}
                        onChange={(e) => handleChange(field.name, e.target.value)}
                    />
                );
        }
    };

    return (
        <form onSubmit={handleSubmit} className="dynamic-form">
            {errors._form && (
                <div className="form-error-banner">
                    {errors._form}
                </div>
            )}

            {fields.map(field => (
                field.type !== 'checkbox' ? (
                    <div key={field.name} className="form-group">
                        <label htmlFor={field.name} className="form-label">
                            {field.label}
                            {field.required && <span className="required">*</span>}
                        </label>
                        {renderField(field)}
                        {errors[field.name] && (
                            <span className="field-error">{errors[field.name]}</span>
                        )}
                    </div>
                ) : (
                    <div key={field.name} className="form-group checkbox-group">
                        {renderField(field)}
                        {errors[field.name] && (
                            <span className="field-error">{errors[field.name]}</span>
                        )}
                    </div>
                )
            ))}

            <div className="form-actions">
                {onCancel && (
                    <button
                        type="button"
                        onClick={onCancel}
                        className="btn btn-secondary"
                        disabled={submitting}
                    >
                        Cancel
                    </button>
                )}
                <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={loading || submitting}
                >
                    {submitting ? 'Saving...' : submitLabel}
                </button>
            </div>
        </form>
    );
}

/**
 * Convert model field metadata to form field definition
 */
export function fieldMetaToFormField(
    name: string,
    meta: FieldMeta,
    config: { readonly?: boolean }
): FormField {
    const baseField = {
        name,
        label: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        required: meta.required && !meta.nullable,
    };

    if (config.readonly) {
        return { ...baseField, type: 'readonly' as const };
    }

    switch (meta.type) {
        case 'number':
            return { ...baseField, type: 'number' as const };

        case 'boolean':
            return { ...baseField, type: 'checkbox' as const, required: false };

        case 'date':
            return { ...baseField, type: 'date' as const };

        case 'datetime':
            return { ...baseField, type: 'datetime' as const };

        case 'json':
            return { ...baseField, type: 'json' as const };

        case 'ai':
            return {
                ...baseField,
                type: 'textarea' as const,
                placeholder: 'AI-generated field (leave empty to auto-generate)',
            };

        default:
            if (meta.choices) {
                return {
                    ...baseField,
                    type: 'select' as const,
                    options: meta.choices,
                };
            }
            return { ...baseField, type: 'text' as const };
    }
}

export default DynamicForm;
