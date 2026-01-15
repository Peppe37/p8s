/**
 * P8s Admin - Inline Editor Component
 *
 * Renders inline related models (TabularInline, StackedInline) 
 * similar to Django admin inlines.
 */

import React, { useState } from 'react';
import { Trash2, Plus, GripVertical } from 'lucide-react';

// Types for inline configuration
interface InlineField {
    name: string;
    type: string;
    required: boolean;
    readonly: boolean;
}

interface InlineConfig {
    model: string;
    fk_field: string;
    fields: InlineField[];
    template: 'tabular' | 'stacked';
    extra: number;
    max_num: number | null;
    min_num: number;
    can_delete: boolean;
    verbose_name: string;
    verbose_name_plural: string;
    ordering: string[];
}

interface InlineItem {
    id?: string | number;
    [key: string]: unknown;
    _deleted?: boolean;
    _new?: boolean;
}

interface InlineEditorProps {
    config: InlineConfig;
    items: InlineItem[];
    parentId?: string | number;
    onChange: (items: InlineItem[]) => void;
    disabled?: boolean;
}

/**
 * InlineEditor - Renders inline related model forms
 */
const InlineEditor: React.FC<InlineEditorProps> = ({
    config,
    items,
    parentId,
    onChange,
    disabled = false,
}) => {
    const [localItems, setLocalItems] = useState<InlineItem[]>(() => {
        // Initialize with existing items + extra empty ones
        const existingItems = items.map(item => ({ ...item, _deleted: false, _new: false }));
        const emptyItems = Array(config.extra).fill(null).map(() => ({
            _new: true,
            _deleted: false,
            [config.fk_field]: parentId,
        }));
        return [...existingItems, ...emptyItems];
    });

    const handleFieldChange = (index: number, fieldName: string, value: unknown) => {
        const updatedItems = [...localItems];
        updatedItems[index] = { ...updatedItems[index], [fieldName]: value };
        setLocalItems(updatedItems);
        onChange(updatedItems.filter(item => !item._deleted));
    };

    const handleDelete = (index: number) => {
        if (!config.can_delete) return;

        const updatedItems = [...localItems];
        if (updatedItems[index]._new) {
            // Remove new items completely
            updatedItems.splice(index, 1);
        } else {
            // Mark existing items as deleted
            updatedItems[index] = { ...updatedItems[index], _deleted: true };
        }
        setLocalItems(updatedItems);
        onChange(updatedItems.filter(item => !item._deleted));
    };

    const handleAdd = () => {
        if (config.max_num && localItems.filter(i => !i._deleted).length >= config.max_num) {
            return;
        }

        const newItem: InlineItem = {
            _new: true,
            _deleted: false,
            [config.fk_field]: parentId,
        };

        const updatedItems = [...localItems, newItem];
        setLocalItems(updatedItems);
        onChange(updatedItems.filter(item => !item._deleted));
    };

    const canAdd = !config.max_num || localItems.filter(i => !i._deleted).length < config.max_num;
    const visibleItems = localItems.filter(item => !item._deleted);

    // Render input based on field type
    const renderInput = (field: InlineField, item: InlineItem, index: number) => {
        const value = item[field.name] ?? '';
        const isReadonly = field.readonly || disabled;

        const baseInputClass = "inline-input";

        if (field.type.includes('bool')) {
            return (
                <input
                    type="checkbox"
                    checked={Boolean(value)}
                    onChange={(e) => handleFieldChange(index, field.name, e.target.checked)}
                    disabled={isReadonly}
                    className="inline-checkbox"
                />
            );
        }

        if (field.type.includes('int') || field.type.includes('float')) {
            return (
                <input
                    type="number"
                    value={String(value)}
                    onChange={(e) => handleFieldChange(index, field.name, e.target.value)}
                    disabled={isReadonly}
                    className={baseInputClass}
                    step={field.type.includes('float') ? '0.01' : '1'}
                />
            );
        }

        return (
            <input
                type="text"
                value={String(value)}
                onChange={(e) => handleFieldChange(index, field.name, e.target.value)}
                disabled={isReadonly}
                className={baseInputClass}
            />
        );
    };

    // Tabular template - table layout
    if (config.template === 'tabular') {
        return (
            <div className="inline-editor tabular-inline">
                <div className="inline-header">
                    <h3>{config.verbose_name_plural}</h3>
                    {canAdd && !disabled && (
                        <button type="button" onClick={handleAdd} className="btn-add-inline">
                            <Plus size={16} /> Add {config.verbose_name}
                        </button>
                    )}
                </div>

                {visibleItems.length > 0 ? (
                    <table className="inline-table">
                        <thead>
                            <tr>
                                <th className="th-drag"></th>
                                {config.fields.map(field => (
                                    <th key={field.name}>
                                        {field.name.replace(/_/g, ' ')}
                                        {field.required && <span className="required">*</span>}
                                    </th>
                                ))}
                                {config.can_delete && <th className="th-actions">Actions</th>}
                            </tr>
                        </thead>
                        <tbody>
                            {visibleItems.map((item, _displayIndex) => {
                                const actualIndex = localItems.findIndex(i => i === item);
                                return (
                                    <tr key={actualIndex} className={item._new ? 'row-new' : ''}>
                                        <td className="td-drag">
                                            <GripVertical size={16} className="drag-handle" />
                                        </td>
                                        {config.fields.map(field => (
                                            <td key={field.name}>
                                                {renderInput(field, item, actualIndex)}
                                            </td>
                                        ))}
                                        {config.can_delete && (
                                            <td className="td-actions">
                                                <button
                                                    type="button"
                                                    onClick={() => handleDelete(actualIndex)}
                                                    className="btn-delete-inline"
                                                    disabled={disabled}
                                                    title="Delete"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            </td>
                                        )}
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                ) : (
                    <p className="inline-empty">No {config.verbose_name_plural.toLowerCase()} yet.</p>
                )}
            </div>
        );
    }

    // Stacked template - card/block layout
    return (
        <div className="inline-editor stacked-inline">
            <div className="inline-header">
                <h3>{config.verbose_name_plural}</h3>
                {canAdd && !disabled && (
                    <button type="button" onClick={handleAdd} className="btn-add-inline">
                        <Plus size={16} /> Add {config.verbose_name}
                    </button>
                )}
            </div>

            {visibleItems.length > 0 ? (
                <div className="stacked-items">
                    {visibleItems.map((item, displayIndex) => {
                        const actualIndex = localItems.findIndex(i => i === item);
                        return (
                            <div key={actualIndex} className={`stacked-item ${item._new ? 'item-new' : ''}`}>
                                <div className="stacked-item-header">
                                    <span className="item-title">
                                        {config.verbose_name} #{displayIndex + 1}
                                        {item._new && <span className="badge-new">New</span>}
                                    </span>
                                    {config.can_delete && (
                                        <button
                                            type="button"
                                            onClick={() => handleDelete(actualIndex)}
                                            className="btn-delete-inline"
                                            disabled={disabled}
                                            title="Delete"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    )}
                                </div>
                                <div className="stacked-item-fields">
                                    {config.fields.map(field => (
                                        <div key={field.name} className="stacked-field">
                                            <label>
                                                {field.name.replace(/_/g, ' ')}
                                                {field.required && <span className="required">*</span>}
                                            </label>
                                            {renderInput(field, item, actualIndex)}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        );
                    })}
                </div>
            ) : (
                <p className="inline-empty">No {config.verbose_name_plural.toLowerCase()} yet.</p>
            )}
        </div>
    );
};

export default InlineEditor;
export type { InlineConfig, InlineItem, InlineField };
