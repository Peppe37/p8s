import { NodeViewWrapper } from '@tiptap/react';
import { useCallback, useEffect, useRef, useState } from 'react';

// Resizable Image Component
export const ResizableImage = (props: any) => {
    const { node, updateAttributes, selected } = props;
    const [width, setWidth] = useState(node.attrs.width || '100%');
    const imageRef = useRef<HTMLImageElement>(null);
    const resizingRef = useRef(false);
    const startXRef = useRef(0);
    const startWidthRef = useRef(0);

    useEffect(() => {
        setWidth(node.attrs.width || '100%');
    }, [node.attrs.width]);

    const handleMouseDown = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        resizingRef.current = true;
        startXRef.current = e.clientX;
        // Get current width in pixels
        if (imageRef.current) {
            startWidthRef.current = imageRef.current.offsetWidth;
        }

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    };

    const handleMouseMove = useCallback((e: MouseEvent) => {
        if (!resizingRef.current) return;

        const diff = e.clientX - startXRef.current;
        const newWidth = Math.max(100, startWidthRef.current + diff); // Min 100px
        setWidth(`${newWidth}px`);
    }, []);

    const handleMouseUp = useCallback(() => {
        if (resizingRef.current) {
            resizingRef.current = false;
            updateAttributes({ width: parseInt(String(width)) ? width : `${parseInt(String(width))}px` }); // Save final width
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        }
    }, [width, updateAttributes]);

    return (
        <NodeViewWrapper className="resizable-image-wrapper" style={{
            textAlign: node.attrs.textAlign || 'left',
            position: 'relative',
            display: 'inline-block', // Allow alignment to work
            maxWidth: '100%'
        }}>
            <div style={{ position: 'relative', display: 'inline-block' }}>
                <img
                    ref={imageRef}
                    src={node.attrs.src}
                    alt={node.attrs.alt}
                    style={{
                        width: width,
                        maxWidth: '100%',
                        display: 'block',
                        borderRadius: '4px',
                        border: selected ? '2px solid #3b82f6' : '2px solid transparent'
                    }}
                />

                {selected && (
                    <div
                        className="resize-handle"
                        onMouseDown={handleMouseDown}
                        style={{
                            position: 'absolute',
                            right: '-6px',
                            bottom: '-6px',
                            width: '12px',
                            height: '12px',
                            background: '#3b82f6',
                            cursor: 'nwse-resize',
                            borderRadius: '50%',
                            border: '2px solid white',
                            zIndex: 10
                        }}
                    />
                )}
            </div>
        </NodeViewWrapper>
    );
};
