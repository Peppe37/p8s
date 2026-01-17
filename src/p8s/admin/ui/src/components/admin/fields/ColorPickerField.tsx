/**
 * ColorPickerField - Color picker with hex input
 */
import { useState } from 'react';
import { HexColorPicker, HexColorInput } from 'react-colorful';

interface ColorPickerFieldProps {
    value?: string;
    onChange: (value: string) => void;
    disabled?: boolean;
}

export function ColorPickerField({
    value = '#3b82f6',
    onChange,
    disabled = false,
}: ColorPickerFieldProps) {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className={`color-picker-field ${disabled ? 'disabled' : ''}`}>
            <div className="color-picker-input">
                <button
                    type="button"
                    className="color-swatch"
                    style={{ backgroundColor: value }}
                    onClick={() => !disabled && setIsOpen(!isOpen)}
                    disabled={disabled}
                    title="Click to pick color"
                />
                <HexColorInput
                    color={value}
                    onChange={onChange}
                    disabled={disabled}
                    className="form-input color-hex-input"
                    prefixed
                />
            </div>

            {isOpen && !disabled && (
                <div className="color-picker-popover">
                    <div
                        className="color-picker-cover"
                        onClick={() => setIsOpen(false)}
                    />
                    <HexColorPicker color={value} onChange={onChange} />
                </div>
            )}
        </div>
    );
}

export default ColorPickerField;
