import React from "react";

interface StreamingMarkdownRendererProps {
  content: string;
}

export const StreamingMarkdownRenderer: React.FC<StreamingMarkdownRendererProps> = ({
  content
}) => {
  const parseMarkdown = (text: string) => {
    if (!text) return null;

    // Split by lines and process each line
    const lines = text.split('\n');
    const elements: React.ReactNode[] = [];
    let currentIndex = 0;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // Skip empty lines
      if (!line.trim()) {
        elements.push(<br key={currentIndex++} />);
        continue;
      }

      // Headers
      if (line.startsWith('## ')) {
        elements.push(
          <h2 key={currentIndex++} className="text-2xl font-bold text-white mb-4 mt-8 first:mt-0 flex items-center gap-3">
            {parseInlineFormatting(line.substring(3))}
          </h2>
        );
      } else if (line.startsWith('# ')) {
        elements.push(
          <h1 key={currentIndex++} className="text-3xl font-bold text-white mb-6 mt-8 first:mt-0 flex items-center gap-3">
            {parseInlineFormatting(line.substring(2))}
          </h1>
        );
      } else if (line.startsWith('### ')) {
        elements.push(
          <h3 key={currentIndex++} className="text-xl font-bold text-white mb-3 mt-6 first:mt-0 flex items-center gap-3">
            {parseInlineFormatting(line.substring(4))}
          </h3>
        );
      } else if (line.startsWith('#### ')) {
        elements.push(
          <h4 key={currentIndex++} className="text-lg font-bold text-white mb-3 mt-5 first:mt-0 flex items-center gap-3">
            {parseInlineFormatting(line.substring(5))}
          </h4>
        );
      } else if (line.startsWith('- ') || line.startsWith('• ')) {
        // List items
        elements.push(
          <div key={currentIndex++} className="flex items-start gap-3 mb-3 pl-2">
            <span className="text-blue-400 mt-1.5 text-lg">•</span>
            <span className="text-slate-200 leading-relaxed">
              {parseInlineFormatting(line.substring(2))}
            </span>
          </div>
        );
      } else if (line.match(/^\d+\.\s/)) {
        // Numbered list items
        const match = line.match(/^(\d+)\.\s(.+)/);
        if (match) {
          elements.push(
            <div key={currentIndex++} className="flex items-start gap-3 mb-3 pl-2">
              <span className="text-blue-400 mt-1.5 font-bold text-lg">{match[1]}.</span>
              <span className="text-slate-200 leading-relaxed">
                {parseInlineFormatting(match[2])}
              </span>
            </div>
          );
        }
      } else {
        // Regular paragraph
        elements.push(
          <p key={currentIndex++} className="text-slate-200 mb-4 leading-relaxed text-base">
            {parseInlineFormatting(line)}
          </p>
        );
      }
    }

    return elements;
  };

  const parseInlineFormatting = (text: string): React.ReactNode => {
    if (!text) return null;

    const elements: React.ReactNode[] = [];
    let currentIndex = 0;

    // Parse bold text
    const boldRegex = /\*\*(.*?)\*\*/g;
    let match;
    let lastIndex = 0;

    while ((match = boldRegex.exec(text)) !== null) {
      // Add text before the match
      if (match.index > lastIndex) {
        const textContent = text.slice(lastIndex, match.index);
        elements.push(parseInlineCode(textContent, currentIndex));
        currentIndex++;
      }

      // Add bold text
      elements.push(
        <strong key={currentIndex++} className="font-bold text-blue-200 bg-blue-900/20 px-1 rounded">
          {match[1]}
        </strong>
      );

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      const textContent = text.slice(lastIndex);
      elements.push(parseInlineCode(textContent, currentIndex));
    }

    return elements.length === 1 ? elements[0] : <span>{elements}</span>;
  };

  const parseInlineCode = (text: string, startIndex: number): React.ReactNode => {
    const elements: React.ReactNode[] = [];
    let currentIndex = startIndex;

    // Parse inline code
    const inlineCodeRegex = /`([^`]+)`/g;
    let match;
    let lastIndex = 0;

    while ((match = inlineCodeRegex.exec(text)) !== null) {
      // Add text before the match
      if (match.index > lastIndex) {
        const textContent = text.slice(lastIndex, match.index);
        elements.push(textContent);
      }

      // Add inline code
      elements.push(
        <code
          key={currentIndex++}
          className="px-2 py-1 bg-slate-800/70 text-purple-300 rounded-md text-sm font-mono border border-purple-700/50 shadow-sm"
        >
          {match[1]}
        </code>
      );

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      const textContent = text.slice(lastIndex);
      elements.push(textContent);
    }

    return elements.length === 1 ? elements[0] : <span>{elements}</span>;
  };

  return (
    <div className="streaming-markdown">
      {parseMarkdown(content)}
    </div>
  );
};
