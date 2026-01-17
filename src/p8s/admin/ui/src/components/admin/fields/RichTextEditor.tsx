/**
 * RichTextEditor - Tiptap-based WYSIWYG editor
 */
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';

interface RichTextEditorProps {
    value?: string | object;
    onChange: (value: object) => void;
    placeholder?: string;
    disabled?: boolean;
}

export function RichTextEditor({
    value,
    onChange,
    placeholder = 'Start writing...',
    disabled = false,
}: RichTextEditorProps) {
    const editor = useEditor({
        extensions: [
            StarterKit,
            Placeholder.configure({ placeholder }),
        ],
        content: typeof value === 'string' ? value : (value as { content?: unknown })?.content || '',
        editable: !disabled,
        onUpdate: ({ editor }) => {
            onChange(editor.getJSON());
        },
    });

    if (!editor) return null;

    return (
        <div className={`richtext-editor ${disabled ? 'disabled' : ''}`}>
            {/* Toolbar */}
            <div className="richtext-toolbar">
                <button
                    type="button"
                    onClick={() => editor.chain().focus().toggleBold().run()}
                    className={editor.isActive('bold') ? 'active' : ''}
                    disabled={disabled}
                    title="Bold"
                >
                    <strong>B</strong>
                </button>
                <button
                    type="button"
                    onClick={() => editor.chain().focus().toggleItalic().run()}
                    className={editor.isActive('italic') ? 'active' : ''}
                    disabled={disabled}
                    title="Italic"
                >
                    <em>I</em>
                </button>
                <button
                    type="button"
                    onClick={() => editor.chain().focus().toggleStrike().run()}
                    className={editor.isActive('strike') ? 'active' : ''}
                    disabled={disabled}
                    title="Strikethrough"
                >
                    <s>S</s>
                </button>
                <span className="toolbar-divider" />
                <button
                    type="button"
                    onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
                    className={editor.isActive('heading', { level: 2 }) ? 'active' : ''}
                    disabled={disabled}
                    title="Heading"
                >
                    H2
                </button>
                <button
                    type="button"
                    onClick={() => editor.chain().focus().toggleBulletList().run()}
                    className={editor.isActive('bulletList') ? 'active' : ''}
                    disabled={disabled}
                    title="Bullet List"
                >
                    •
                </button>
                <button
                    type="button"
                    onClick={() => editor.chain().focus().toggleOrderedList().run()}
                    className={editor.isActive('orderedList') ? 'active' : ''}
                    disabled={disabled}
                    title="Numbered List"
                >
                    1.
                </button>
                <span className="toolbar-divider" />
                <button
                    type="button"
                    onClick={() => editor.chain().focus().toggleCodeBlock().run()}
                    className={editor.isActive('codeBlock') ? 'active' : ''}
                    disabled={disabled}
                    title="Code Block"
                >
                    {'</>'}
                </button>
                <button
                    type="button"
                    onClick={() => editor.chain().focus().toggleBlockquote().run()}
                    className={editor.isActive('blockquote') ? 'active' : ''}
                    disabled={disabled}
                    title="Quote"
                >
                    "
                </button>
            </div>

            {/* Editor Content */}
            <EditorContent editor={editor} className="richtext-content" />
        </div>
    );
}

export default RichTextEditor;
