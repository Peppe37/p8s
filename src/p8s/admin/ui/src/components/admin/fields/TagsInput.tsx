/**
 * TagsInput - Chip-style tag input component
 */
import { useState, KeyboardEvent } from 'react';

interface TagsInputProps {
    value?: string[];
    onChange: (value: string[]) => void;
    placeholder?: string;
    disabled?: boolean;
}

export function TagsInput({
    value = [],
    onChange,
    placeholder = 'Add tag...',
    disabled = false,
}: TagsInputProps) {
    const [inputValue, setInputValue] = useState('');

    const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            addTag();
        } else if (e.key === 'Backspace' && !inputValue && value.length > 0) {
            removeTag(value.length - 1);
        }
    };

    const addTag = () => {
        const tag = inputValue.trim().toLowerCase();
        if (tag && !value.includes(tag)) {
            onChange([...value, tag]);
        }
        setInputValue('');
    };

    const removeTag = (index: number) => {
        if (disabled) return;
        const newTags = [...value];
        newTags.splice(index, 1);
        onChange(newTags);
    };

    return (
        <div className={`tags-input ${disabled ? 'disabled' : ''}`}>
            <div className="tags-container">
                {value.map((tag, index) => (
                    <span key={tag} className="tag-chip">
                        {tag}
                        {!disabled && (
                            <button
                                type="button"
                                className="tag-remove"
                                onClick={() => removeTag(index)}
                                title="Remove tag"
                            >
                                ×
                            </button>
                        )}
                    </span>
                ))}
                <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    onBlur={addTag}
                    placeholder={value.length === 0 ? placeholder : ''}
                    disabled={disabled}
                    className="tag-input"
                />
            </div>
        </div>
    );
}

export default TagsInput;
