import { forwardRef, useEffect, useImperativeHandle, useState } from 'react';
import {
    Heading1, Heading2, Heading3,
    List, ListOrdered,
    Text,
    Code, Quote, Image, Youtube
} from 'lucide-react';

export const SlashCommandList = forwardRef((props: any, ref) => {
    const [selectedIndex, setSelectedIndex] = useState(0);

    const selectItem = (index: number) => {
        const item = props.items[index];
        if (item) {
            props.command(item);
        }
    };

    const upHandler = () => {
        setSelectedIndex((selectedIndex + props.items.length - 1) % props.items.length);
    };

    const downHandler = () => {
        setSelectedIndex((selectedIndex + 1) % props.items.length);
    };

    const enterHandler = () => {
        selectItem(selectedIndex);
    };

    useEffect(() => setSelectedIndex(0), [props.items]);

    useImperativeHandle(ref, () => ({
        onKeyDown: ({ event }: { event: KeyboardEvent }) => {
            if (event.key === 'ArrowUp') {
                upHandler();
                return true;
            }

            if (event.key === 'ArrowDown') {
                downHandler();
                return true;
            }

            if (event.key === 'Enter') {
                enterHandler();
                return true;
            }

            return false;
        },
    }));

    return (
        <div className="slash-command-menu">
            {props.items.length ? (
                props.items.map((item: any, index: number) => (
                    <button
                        className={`slash-command-item ${index === selectedIndex ? 'is-selected' : ''}`}
                        key={index}
                        onClick={() => selectItem(index)}
                    >
                        {item.icon}
                        <div className="slash-command-label">
                            <span className="title">{item.title}</span>
                            <span className="description">{item.description}</span>
                        </div>
                    </button>
                ))
            ) : (
                <div className="slash-command-empty">No results</div>
            )}
        </div>
    );
});

export const getSuggestionItems = ({ query }: { query: string }) => {
    return [
        {
            title: 'Heading 1',
            description: 'Big section heading',
            icon: <Heading1 size={18} />,
            command: ({ editor, range }: any) => {
                editor.chain().focus().deleteRange(range).setNode('heading', { level: 1 }).run();
            },
        },
        {
            title: 'Heading 2',
            description: 'Medium section heading',
            icon: <Heading2 size={18} />,
            command: ({ editor, range }: any) => {
                editor.chain().focus().deleteRange(range).setNode('heading', { level: 2 }).run();
            },
        },
        {
            title: 'Heading 3',
            description: 'Small section heading',
            icon: <Heading3 size={18} />,
            command: ({ editor, range }: any) => {
                editor.chain().focus().deleteRange(range).setNode('heading', { level: 3 }).run();
            },
        },
        {
            title: 'Text',
            description: 'Just start typing with plain text',
            icon: <Text size={18} />,
            command: ({ editor, range }: any) => {
                editor.chain().focus().deleteRange(range).setParagraph().run();
            },
        },
        {
            title: 'Bullet List',
            description: 'Create a simple bullet list',
            icon: <List size={18} />,
            command: ({ editor, range }: any) => {
                editor.chain().focus().deleteRange(range).toggleBulletList().run();
            },
        },
        {
            title: 'Numbered List',
            description: 'Create a list with numbering',
            icon: <ListOrdered size={18} />,
            command: ({ editor, range }: any) => {
                editor.chain().focus().deleteRange(range).toggleOrderedList().run();
            },
        },
        {
            title: 'Quote',
            description: 'Capture a quote',
            icon: <Quote size={18} />,
            command: ({ editor, range }: any) => {
                editor.chain().focus().deleteRange(range).toggleBlockquote().run();
            },
        },
        {
            title: 'Code Block',
            description: 'Capture a code snippet',
            icon: <Code size={18} />,
            command: ({ editor, range }: any) => {
                editor.chain().focus().deleteRange(range).toggleCodeBlock().run();
            },
        },
        {
            title: 'Image',
            description: 'Insert an image via URL',
            icon: <Image size={18} />,
            command: ({ editor, range }: any) => {
                const url = window.prompt('Image URL');
                if (url) {
                    editor.chain().focus().deleteRange(range).setImage({ src: url }).run();
                }
            },
        },
        {
            title: 'YouTube',
            description: 'Embed a YouTube video',
            icon: <Youtube size={18} />,
            command: ({ editor, range }: any) => {
                const url = window.prompt('YouTube URL');
                if (url) {
                    editor.chain().focus().deleteRange(range).setYoutubeVideo({ src: url }).run();
                }
            },
        },
    ].filter((item) => item.title.toLowerCase().startsWith(query.toLowerCase())).slice(0, 10);
};
