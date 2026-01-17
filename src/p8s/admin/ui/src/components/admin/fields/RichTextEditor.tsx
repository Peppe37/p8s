/**
 * RichTextEditor - Full-featured WYSIWYG editor
 *
 * Features:
 * - Table Support
 * - Drag & Drop Image Upload
 * - Character/Word Count
 * - Full Screen Mode
 * - Media (Image, YouTube)
 * - Basic Formatting & Headings
 * - Font Family & Size
 * - Text & Highlight Color
 */
import { useEditor, EditorContent, ReactNodeViewRenderer, Extension, ReactRenderer } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import Underline from '@tiptap/extension-underline';
import TextAlign from '@tiptap/extension-text-align';
import Link from '@tiptap/extension-link';
import Highlight from '@tiptap/extension-highlight';
import Image from '@tiptap/extension-image';
import Youtube from '@tiptap/extension-youtube';
import { Table } from '@tiptap/extension-table';
import TableRow from '@tiptap/extension-table-row';
import TableCell from '@tiptap/extension-table-cell';
import TableHeader from '@tiptap/extension-table-header';
import CharacterCount from '@tiptap/extension-character-count';
import Suggestion from '@tiptap/suggestion';
import { TextStyle } from '@tiptap/extension-text-style';
import Color from '@tiptap/extension-color';
import FontFamily from '@tiptap/extension-font-family';
import { useState, useRef, useEffect } from 'react';
import tippy from 'tippy.js';
import 'tippy.js/dist/tippy.css';
import {
    Bold, Italic, Underline as UnderlineIcon, Strikethrough, Highlighter,
    AlignLeft, AlignCenter, AlignRight,
    List, ListOrdered,
    Link as LinkIcon, Image as ImageIcon, Youtube as YoutubeIcon,
    Code, Quote, Maximize, Minimize,
    Undo, Redo,
    Upload,
    Table as TableIcon, Trash2,
    ArrowRightFromLine, ArrowDownFromLine, X, Palette
} from 'lucide-react';
import { ResizableImage } from './ResizableImage';
import { SlashCommandList, getSuggestionItems } from './SlashCommandList';

// Custom FontSize extension
const FontSize = Extension.create({
    name: 'fontSize',
    addOptions() {
        return {
            types: ['textStyle'],
        };
    },
    addGlobalAttributes() {
        return [
            {
                types: this.options.types,
                attributes: {
                    fontSize: {
                        default: null,
                        parseHTML: element => element.style.fontSize.replace(/['"]+/g, ''),
                        renderHTML: attributes => {
                            if (!attributes.fontSize) {
                                return {};
                            }
                            return {
                                style: `font-size: ${attributes.fontSize}`,
                            };
                        },
                    },
                },
            },
        ];
    },
    addCommands() {
        return {
            setFontSize: (fontSize: string) => ({ chain }: any) => {
                return chain()
                    .setMark('textStyle', { fontSize })
                    .run();
            },
            unsetFontSize: () => ({ chain }: any) => {
                return chain()
                    .setMark('textStyle', { fontSize: null })
                    .removeEmptyTextStyle()
                    .run()
            },
        }
    },
});

interface RichTextEditorProps {
    value?: string | object;
    onChange: (value: object) => void;
    placeholder?: string;
    disabled?: boolean;
}

const SlashCommands = Extension.create({
    name: 'slash-commands',
    addOptions() {
        return {
            suggestion: {
                char: '/',
                command: ({ editor, range, props }: any) => {
                    props.command({ editor, range });
                },
            },
        };
    },
    addProseMirrorPlugins() {
        return [
            Suggestion({
                editor: this.editor,
                ...this.options.suggestion,
            }),
        ];
    },
});

// Font and Size options
const FONT_FAMILIES = [
    { label: 'Sans Serif', value: 'Inter, sans-serif' },
    { label: 'Serif', value: 'Georgia, serif' },
    { label: 'Monospace', value: 'monospace' },
    { label: 'Arial', value: 'Arial, sans-serif' },
    { label: 'Times New Roman', value: 'Times New Roman, serif' },
];

const FONT_SIZES = ['12px', '14px', '16px', '18px', '20px', '24px', '30px', '36px'];

export function RichTextEditor({
    value,
    onChange,
    placeholder = 'Start writing...',
    disabled = false,
}: RichTextEditorProps) {
    const [mediaPopup, setMediaPopup] = useState<{
        isOpen: boolean;
        type: 'link' | 'image' | 'video';
        activeTab: 'url' | 'upload';
        url: string;
    }>({
        isOpen: false,
        type: 'link',
        activeTab: 'url',
        url: ''
    });
    const [isFullScreen, setIsFullScreen] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const dropZoneInputRef = useRef<HTMLInputElement>(null);

    const getInitialContent = (): object | string => {
        if (!value) return '';

        let content = value;

        // If it's a string, try to parse it as JSON
        if (typeof content === 'string') {
            if (content.trim() === '') return '';
            try {
                content = JSON.parse(content);
            } catch {
                // If it's not valid JSON, treat it as plain text/HTML
                return content;
            }
        }

        // Now content should be an object
        if (typeof content === 'object' && content !== null) {
            const obj = content as Record<string, unknown>;

            // Handle nested/double-encoded JSON (where content is stored as a string inside text nodes)
            // Check if this looks like a valid Tiptap document
            if (obj.type === 'doc' && Array.isArray(obj.content)) {
                return content;
            }

            // Empty object
            if (Object.keys(obj).length === 0) {
                return '';
            }
        }

        return '';
    };

    const editor = useEditor({
        extensions: [
            StarterKit.configure({
                heading: { levels: [1, 2, 3] },
            }),
            Placeholder.configure({ placeholder }),
            Underline,
            TextStyle,
            Color,
            FontFamily,
            FontSize,
            TextAlign.configure({ types: ['heading', 'paragraph', 'image'] }),
            Link.configure({
                openOnClick: false,
                HTMLAttributes: { class: 'editor-link' },
            }),
            Highlight.configure({ multicolor: true }),
            Image.configure({
                inline: true,
                allowBase64: true,
            }).extend({
                addAttributes() {
                    return {
                        src: { default: null },
                        alt: { default: null },
                        title: { default: null },
                        width: { default: null },
                        height: { default: null },
                        textAlign: { default: 'left' },
                    };
                },
                addNodeView() {
                    return ReactNodeViewRenderer(ResizableImage);
                },
            }),
            Youtube.configure({
                controls: true,
                nocookie: true,
            }),
            Table.configure({
                resizable: true,
                HTMLAttributes: { class: 'editor-table' },
            }),
            TableRow,
            TableHeader,
            TableCell,
            CharacterCount.configure({
                limit: null,
            }),
            SlashCommands.configure({
                suggestion: {
                    items: getSuggestionItems,
                    render: () => {
                        let reactRenderer: ReactRenderer;
                        let popup: any;

                        return {
                            onStart: (props: any) => {
                                reactRenderer = new ReactRenderer(SlashCommandList, {
                                    props,
                                    editor: props.editor,
                                });

                                popup = tippy('body', {
                                    getReferenceClientRect: props.clientRect,
                                    appendTo: () => document.body,
                                    content: reactRenderer.element,
                                    showOnCreate: true,
                                    interactive: true,
                                    trigger: 'manual',
                                    placement: 'bottom-start',
                                });
                            },
                            onUpdate(props: any) {
                                reactRenderer.updateProps(props);
                                if (!popup) return;
                                popup[0].setProps({
                                    getReferenceClientRect: props.clientRect,
                                });
                            },
                            onKeyDown(props: any) {
                                if (props.event.key === 'Escape') {
                                    popup?.[0].hide();
                                    return true;
                                }
                                return (reactRenderer?.ref as any)?.onKeyDown(props);
                            },
                            onExit() {
                                popup?.[0].destroy();
                                reactRenderer?.destroy();
                            },
                        };
                    }
                }
            })
        ],
        content: getInitialContent(),
        editable: !disabled,
        onUpdate: ({ editor }) => {
            onChange(editor.getJSON());
        },
        editorProps: {
            handleDrop: (view, event, _slice, moved) => {
                if (!moved && event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0]) {
                    const file = event.dataTransfer.files[0];
                    if (file.type.startsWith('image/')) {
                        event.preventDefault();
                        const reader = new FileReader();
                        reader.onload = (e) => {
                            const src = e.target?.result as string;
                            const { schema } = view.state;
                            const node = schema.nodes.image.create({ src });
                            const transaction = view.state.tr.replaceSelectionWith(node);
                            view.dispatch(transaction);
                        };
                        reader.readAsDataURL(file);
                        return true;
                    }
                }
                return false;
            }
        }
    });

    useEffect(() => {
        if (editor && disabled) {
            editor.setEditable(false);
        } else if (editor && !disabled) {
            editor.setEditable(true);
        }
    }, [editor, disabled]);

    const openPopup = (type: 'link' | 'image' | 'video') => {
        let currentUrl = '';
        if (type === 'link') {
            currentUrl = editor?.getAttributes('link').href || '';
        }
        setMediaPopup({
            isOpen: true,
            type,
            activeTab: 'url', // Default to URL tab
            url: currentUrl
        });
    };

    const handleApplyMedia = () => {
        if (!editor) return;
        const { type, url } = mediaPopup;

        if (url) {
            if (type === 'link') {
                editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run();
            } else if (type === 'image') {
                editor.chain().focus().setImage({ src: url }).run();
            } else if (type === 'video') {
                editor.chain().focus().setYoutubeVideo({ src: url }).run();
            }
        } else if (type === 'link') {
            editor.chain().focus().extendMarkRange('link').unsetLink().run();
        }

        setMediaPopup({ ...mediaPopup, isOpen: false, url: '' });
    };

    const handleFileUploadChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        insertImageFile(file);
        // Reset input
        e.target.value = '';
    };

    const insertImageFile = (file?: File) => {
        if (!file || !editor) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            const src = event.target?.result as string;
            editor.chain().focus().setImage({ src }).run();
            setMediaPopup(prev => ({ ...prev, isOpen: false }));
        };
        reader.readAsDataURL(file);
    }

    const toggleFullScreen = () => {
        setIsFullScreen(!isFullScreen);
    };

    const insertTable = () => {
        editor?.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run();
    }

    // preventDefault onMouseDown ensures focus isn't lost from editor when clicking toolbar buttons
    const preventFocusLoss = (e: React.MouseEvent) => {
        e.preventDefault();
    };

    if (!editor) return null;

    return (
        <div className={`richtext-editor modern ${disabled ? 'disabled' : ''} ${isFullScreen ? 'fullscreen' : ''}`}>
            <input
                type="file"
                ref={fileInputRef}
                style={{ display: 'none' }}
                accept="image/*"
                onChange={handleFileUploadChange}
            />

            {/* Toolbar */}
            <div className="richtext-toolbar" onMouseDown={preventFocusLoss}>
                {/* Font Family & Size Dropdowns */}
                <div className="toolbar-group">
                    <select
                        className="font-select"
                        onMouseDown={(e) => e.stopPropagation()}
                        value={editor.getAttributes('textStyle').fontFamily || ''}
                        onChange={(e) => {
                            if (e.target.value) {
                                editor.chain().focus().setFontFamily(e.target.value).run();
                            } else {
                                editor.chain().focus().unsetFontFamily().run();
                            }
                        }}
                        disabled={disabled}
                        title="Font Family"
                    >
                        <option value="">Default</option>
                        {FONT_FAMILIES.map((f) => (
                            <option key={f.value} value={f.value}>{f.label}</option>
                        ))}
                    </select>
                    <select
                        className="size-select"
                        onMouseDown={(e) => e.stopPropagation()}
                        value={editor.getAttributes('textStyle').fontSize || ''}
                        onChange={(e) => {
                            if (e.target.value) {
                                (editor.chain().focus() as any).setFontSize(e.target.value).run();
                            } else {
                                (editor.chain().focus() as any).unsetFontSize().run();
                            }
                        }}
                        disabled={disabled}
                        title="Font Size"
                    >
                        <option value="">Size</option>
                        {FONT_SIZES.map((size) => (
                            <option key={size} value={size}>{size}</option>
                        ))}
                    </select>
                </div>

                <div className="toolbar-divider" />

                {/* Text Color & Highlight Color */}
                <div className="toolbar-group color-pickers">
                    <div className="color-picker-wrapper" title="Text Color">
                        <Palette size={16} style={{ pointerEvents: 'none', position: 'absolute', left: '6px', top: '50%', transform: 'translateY(-50%)', color: '#1e293b' }} />
                        <input
                            type="color"
                            className="color-input"
                            value={editor.getAttributes('textStyle').color || '#000000'}
                            onChange={(e) => editor.chain().focus().setColor(e.target.value).run()}
                            disabled={disabled}
                        />
                    </div>
                    <div className="color-picker-wrapper highlight-picker" title="Highlight Color">
                        <Highlighter size={16} style={{ pointerEvents: 'none', position: 'absolute', left: '6px', top: '50%', transform: 'translateY(-50%)', color: '#1e293b' }} />
                        <input
                            type="color"
                            className="color-input"
                            value={editor.getAttributes('highlight').color || '#FEFF00'}
                            onChange={(e) => editor.chain().focus().toggleHighlight({ color: e.target.value }).run()}
                            disabled={disabled}
                        />
                    </div>
                </div>

                <div className="toolbar-divider" />

                <div className="toolbar-group">
                    <select
                        className="heading-select"
                        onMouseDown={(e) => e.stopPropagation()}
                        value={
                            editor.isActive('heading', { level: 1 }) ? '1' :
                                editor.isActive('heading', { level: 2 }) ? '2' :
                                    editor.isActive('heading', { level: 3 }) ? '3' : '0'
                        }
                        onChange={(e) => {
                            const level = parseInt(e.target.value);
                            if (level === 0) editor.chain().focus().setParagraph().run();
                            else editor.chain().focus().toggleHeading({ level: level as 1 | 2 | 3 }).run();
                        }}
                        disabled={disabled}
                    >
                        <option value="0">Normal</option>
                        <option value="1">Heading 1</option>
                        <option value="2">Heading 2</option>
                        <option value="3">Heading 3</option>
                    </select>
                </div>

                <div className="toolbar-divider" />

                <div className="toolbar-group">
                    <ToolbarButton
                        isActive={editor.isActive('bold')}
                        onClick={() => editor.chain().focus().toggleBold().run()}
                        disabled={disabled}
                        icon={<Bold size={18} />}
                        title="Bold (Ctrl+B)"
                    />
                    <ToolbarButton
                        isActive={editor.isActive('italic')}
                        onClick={() => editor.chain().focus().toggleItalic().run()}
                        disabled={disabled}
                        icon={<Italic size={18} />}
                        title="Italic (Ctrl+I)"
                    />
                    <ToolbarButton
                        isActive={editor.isActive('underline')}
                        onClick={() => editor.chain().focus().toggleUnderline().run()}
                        disabled={disabled}
                        icon={<UnderlineIcon size={18} />}
                        title="Underline (Ctrl+U)"
                    />
                    <ToolbarButton
                        isActive={editor.isActive('strike')}
                        onClick={() => editor.chain().focus().toggleStrike().run()}
                        disabled={disabled}
                        icon={<Strikethrough size={18} />}
                        title="Strikethrough"
                    />
                    <ToolbarButton
                        isActive={editor.isActive('highlight')}
                        onClick={() => editor.chain().focus().toggleHighlight().run()}
                        disabled={disabled}
                        icon={<Highlighter size={18} />}
                        title="Highlight"
                        highlight
                    />
                </div>

                <div className="toolbar-divider" />

                <div className="toolbar-group">
                    <ToolbarButton
                        isActive={editor.isActive({ textAlign: 'left' })}
                        onClick={() => editor.chain().focus().setTextAlign('left').run()}
                        disabled={disabled}
                        icon={<AlignLeft size={18} />}
                        title="Align Left"
                    />
                    <ToolbarButton
                        isActive={editor.isActive({ textAlign: 'center' })}
                        onClick={() => editor.chain().focus().setTextAlign('center').run()}
                        disabled={disabled}
                        icon={<AlignCenter size={18} />}
                        title="Align Center"
                    />
                    <ToolbarButton
                        isActive={editor.isActive({ textAlign: 'right' })}
                        onClick={() => editor.chain().focus().setTextAlign('right').run()}
                        disabled={disabled}
                        icon={<AlignRight size={18} />}
                        title="Align Right"
                    />
                </div>

                <div className="toolbar-divider" />

                <div className="toolbar-group">
                    <ToolbarButton
                        isActive={editor.isActive('bulletList')}
                        onClick={() => editor.chain().focus().toggleBulletList().run()}
                        disabled={disabled}
                        icon={<List size={18} />}
                        title="Bullet List"
                    />
                    <ToolbarButton
                        isActive={editor.isActive('orderedList')}
                        onClick={() => editor.chain().focus().toggleOrderedList().run()}
                        disabled={disabled}
                        icon={<ListOrdered size={18} />}
                        title="Numbered List"
                    />
                </div>

                <div className="toolbar-divider" />

                <div className="toolbar-group">
                    <ToolbarButton
                        isActive={editor.isActive('table')}
                        onClick={insertTable}
                        disabled={disabled}
                        icon={<TableIcon size={18} />}
                        title="Insert Table"
                    />
                    {editor.isActive('table') && (
                        <>
                            <ToolbarButton
                                isActive={false}
                                onClick={() => editor.chain().focus().addColumnAfter().run()}
                                disabled={disabled}
                                icon={<ArrowRightFromLine size={16} />}
                                title="Add Column After"
                            />
                            <ToolbarButton
                                isActive={false}
                                onClick={() => editor.chain().focus().addRowAfter().run()}
                                disabled={disabled}
                                icon={<ArrowDownFromLine size={16} />}
                                title="Add Row After"
                            />
                            <ToolbarButton
                                isActive={false}
                                onClick={() => editor.chain().focus().deleteTable().run()}
                                disabled={disabled}
                                icon={<Trash2 size={16} color="red" />}
                                title="Delete Table"
                            />
                        </>
                    )}
                </div>

                <div className="toolbar-divider" />

                <div className="toolbar-group">
                    <ToolbarButton
                        isActive={editor.isActive('link')}
                        onClick={() => openPopup('link')}
                        disabled={disabled}
                        icon={<LinkIcon size={18} />}
                        title="Link"
                    />
                    <ToolbarButton
                        isActive={editor.isActive('image')}
                        onClick={() => openPopup('image')}
                        disabled={disabled}
                        icon={<ImageIcon size={18} />}
                        title="Insert Image"
                    />
                    <ToolbarButton
                        isActive={editor.isActive('youtube')}
                        onClick={() => openPopup('video')}
                        disabled={disabled}
                        icon={<YoutubeIcon size={18} />}
                        title="Insert YouTube Video"
                    />
                </div>

                <div className="toolbar-divider" />

                <div className="toolbar-group">
                    <ToolbarButton
                        isActive={editor.isActive('codeBlock')}
                        onClick={() => editor.chain().focus().toggleCodeBlock().run()}
                        disabled={disabled}
                        icon={<Code size={18} />}
                        title="Code Block"
                    />
                    <ToolbarButton
                        isActive={editor.isActive('blockquote')}
                        onClick={() => editor.chain().focus().toggleBlockquote().run()}
                        disabled={disabled}
                        icon={<Quote size={18} />}
                        title="Quote"
                    />
                </div>

                <div style={{ flex: 1 }} />

                <div className="toolbar-group">
                    <ToolbarButton
                        isActive={false}
                        onClick={() => editor.chain().focus().undo().run()}
                        disabled={disabled || !editor.can().undo()}
                        icon={<Undo size={18} />}
                        title="Undo"
                    />
                    <ToolbarButton
                        isActive={false}
                        onClick={() => editor.chain().focus().redo().run()}
                        disabled={disabled || !editor.can().redo()}
                        icon={<Redo size={18} />}
                        title="Redo"
                    />

                    <div className="toolbar-divider" />

                    <ToolbarButton
                        isActive={isFullScreen}
                        onClick={toggleFullScreen}
                        disabled={disabled}
                        icon={isFullScreen ? <Minimize size={18} /> : <Maximize size={18} />}
                        title={isFullScreen ? "Exit Full Screen" : "Full Screen"}
                    />
                </div>
            </div>

            {/* Unified Media Popup */}
            {mediaPopup.isOpen && (
                <div className="editor-popup-backdrop" onClick={() => setMediaPopup({ ...mediaPopup, isOpen: false })}>
                    <div className="editor-popup" onClick={(e) => e.stopPropagation()}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <h3 className="popup-header">
                                {mediaPopup.type === 'link' ? 'Insert Link' :
                                    mediaPopup.type === 'image' ? 'Insert Image' : 'Insert Video'}
                            </h3>
                            <button
                                type="button"
                                onClick={() => setMediaPopup({ ...mediaPopup, isOpen: false })}
                                style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}
                            >
                                <X size={20} />
                            </button>
                        </div>

                        {/* Tabs for Image */}
                        {mediaPopup.type === 'image' && (
                            <div className="popup-tabs">
                                <button
                                    type="button"
                                    className={`popup-tab ${mediaPopup.activeTab === 'url' ? 'active' : ''}`}
                                    onClick={() => setMediaPopup({ ...mediaPopup, activeTab: 'url' })}
                                >
                                    From URL
                                </button>
                                <button
                                    type="button"
                                    className={`popup-tab ${mediaPopup.activeTab === 'upload' ? 'active' : ''}`}
                                    onClick={() => setMediaPopup({ ...mediaPopup, activeTab: 'upload' })}
                                >
                                    Upload File
                                </button>
                            </div>
                        )}

                        {/* URL Input */}
                        {(mediaPopup.type !== 'image' || mediaPopup.activeTab === 'url') && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                <label className="popup-label">
                                    {mediaPopup.type === 'link' ? 'URL' :
                                        mediaPopup.type === 'image' ? 'Image URL' : 'YouTube URL'}
                                </label>
                                <input
                                    type="url"
                                    className="popup-input"
                                    placeholder="https://..."
                                    value={mediaPopup.url}
                                    onChange={(e) => setMediaPopup({ ...mediaPopup, url: e.target.value })}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter') { e.preventDefault(); handleApplyMedia(); }
                                    }}
                                    autoFocus
                                />
                            </div>
                        )}

                        {/* Upload Input */}
                        {mediaPopup.type === 'image' && mediaPopup.activeTab === 'upload' && (
                            <div
                                className="drop-zone"
                                onClick={() => dropZoneInputRef.current?.click()}
                                onDragOver={(e) => e.preventDefault()}
                                onDrop={(e) => {
                                    e.preventDefault();
                                    const file = e.dataTransfer.files?.[0];
                                    if (file && file.type.startsWith('image/')) insertImageFile(file);
                                }}
                            >
                                <input
                                    type="file"
                                    ref={dropZoneInputRef}
                                    style={{ display: 'none' }}
                                    accept="image/*"
                                    onChange={handleFileUploadChange}
                                />
                                <Upload size={32} style={{ marginBottom: '8px', opacity: 0.5 }} />
                                <p style={{ margin: 0, fontSize: '0.9rem' }}>Click or drag image to upload</p>
                            </div>
                        )}

                        <div className="popup-actions">
                            <button type="button" onClick={() => setMediaPopup({ ...mediaPopup, isOpen: false })} className="btn-popup-secondary">Cancel</button>
                            {(mediaPopup.type !== 'image' || mediaPopup.activeTab === 'url') && (
                                <button type="button" onClick={handleApplyMedia} className="btn-popup-primary">Apply</button>
                            )}
                        </div>
                    </div>
                </div>
            )}

            <EditorContent editor={editor} className="richtext-content" />

            {/* Status Footer */}
            <div className="richtext-footer">
                <span className="char-count">
                    {editor.storage.characterCount.words()} words • {editor.storage.characterCount.characters()} characters
                </span>
            </div>
        </div>
    );
}

// Helper component for cleaner code
interface ToolbarButtonProps {
    isActive: boolean;
    onClick: () => void;
    disabled: boolean;
    icon: React.ReactNode;
    title: string;
    highlight?: boolean;
}

function ToolbarButton({ isActive, onClick, disabled, icon, title, highlight }: ToolbarButtonProps) {
    return (
        <button
            type="button"
            onClick={onClick}
            // Important: prevent focus loss from editor
            onMouseDown={(e) => e.preventDefault()}
            className={`toolbar-btn ${isActive ? 'active' : ''}`}
            disabled={disabled}
            title={title}
        >
            <span style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: highlight ? '#fef08a' : 'transparent',
                borderRadius: highlight ? '2px' : '0',
                color: highlight ? '#000' : 'currentColor'
            }}>
                {icon}
            </span>
        </button>
    );
}

export default RichTextEditor;
