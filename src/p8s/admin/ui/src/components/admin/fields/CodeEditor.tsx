/**
 * CodeEditor - Syntax-highlighted code editor using CodeMirror
 */
import CodeMirror from '@uiw/react-codemirror';
import { javascript } from '@codemirror/lang-javascript';
import { python } from '@codemirror/lang-python';

interface CodeEditorProps {
    value?: string;
    onChange: (value: string) => void;
    language?: string;
    disabled?: boolean;
}

const languageExtensions: Record<string, ReturnType<typeof javascript>> = {
    javascript: javascript(),
    js: javascript(),
    typescript: javascript({ typescript: true }),
    ts: javascript({ typescript: true }),
    python: python(),
    py: python(),
};

export function CodeEditor({
    value = '',
    onChange,
    language = 'javascript',
    disabled = false,
}: CodeEditorProps) {
    const extension = languageExtensions[language.toLowerCase()] || javascript();

    return (
        <div className={`code-editor ${disabled ? 'disabled' : ''}`}>
            <div className="code-editor-header">
                <span className="code-language-badge">{language}</span>
            </div>
            <CodeMirror
                value={value}
                onChange={onChange}
                extensions={[extension]}
                editable={!disabled}
                theme="dark"
                height="200px"
                className="code-editor-content"
            />
        </div>
    );
}

export default CodeEditor;
