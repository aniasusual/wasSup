import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";

interface ProperMarkdownRendererProps {
  content: string;
  className?: string;
}

// A robust markdown renderer with GFM support and syntax highlighting.
export const ProperMarkdownRenderer: React.FC<ProperMarkdownRendererProps> = ({
  content,
  className = "",
}) => {
  // Some upstream responses may contain JSON-escaped newlines ("\n")
  // which prevents markdown from rendering headings and paragraphs.
  // Normalize these to actual characters before rendering.
  const normalizeMarkdown = (text: string) => {
    if (!text) return "";
    let t = text;
    t = t
      .replace(/\\r\\n/g, "\n")
      .replace(/\\n/g, "\n")
      .replace(/\\t/g, "\t")
      .replace(/\\r/g, "\r");
    // Ensure headings that arrive mid-line from streaming get their own line
    // e.g., "... last_hour ## Heading" -> "... last_hour\n## Heading"
    t = t.replace(/(\S)\s+(#{1,6}\s)/g, "$1\n$2");
    // Collapse more than 3 consecutive blank lines for nicer spacing
    t = t.replace(/(\n\s*){4,}/g, "\n\n\n");
    return t.trim();
  };

  const normalized = normalizeMarkdown(content);
  return (
    <div
      className={
        `prose prose-slate prose-invert max-w-none ` +
        `prose-headings:text-white prose-headings:font-bold ` +
        `prose-p:text-slate-200 prose-p:leading-relaxed ` +
        `prose-strong:text-blue-200 prose-a:text-blue-400 ` +
        `prose-code:text-purple-300 prose-code:bg-slate-800/60 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded ` +
        `prose-blockquote:border-l-blue-500 prose-blockquote:bg-slate-800/30 prose-blockquote:rounded-r-xl ` +
        `prose-pre:bg-slate-900/60 prose-pre:border prose-pre:border-slate-700/50 prose-pre:rounded-xl ` +
        `prose-table:overflow-hidden prose-th:text-slate-200 prose-td:text-slate-200 ` +
        className
      }
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ node, ...props }) => (
            <h1 className="text-3xl font-bold text-white mt-8 mb-4" {...props} />
          ),
          h2: ({ node, ...props }) => (
            <h2 className="text-2xl font-bold text-white mt-7 mb-3" {...props} />
          ),
          h3: ({ node, ...props }) => (
            <h3 className="text-xl font-bold text-white mt-6 mb-3" {...props} />
          ),
          h4: ({ node, ...props }) => (
            <h4 className="text-lg font-bold text-white mt-5 mb-2" {...props} />
          ),
          p: ({ node, ...props }) => (
            <p
              className="text-slate-200 leading-relaxed my-3 whitespace-pre-wrap"
              {...props}
            />
          ),
          a: ({ node, ...props }) => (
            <a
              {...props}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300 underline decoration-slate-500/60 hover:decoration-blue-400 transition-colors"
            />
          ),
          ul: ({ node, ...props }) => (
            <ul className="list-disc pl-6 space-y-1" {...props} />
          ),
          ol: ({ node, ...props }) => (
            <ol className="list-decimal pl-6 space-y-1" {...props} />
          ),
          li: ({ node, ...props }) => (
            <li className="text-slate-200" {...props} />
          ),
          blockquote: ({ node, ...props }) => (
            <blockquote
              className="border-l-4 border-blue-500/70 bg-slate-800/40 pl-4 pr-3 py-2 rounded-r-xl my-4"
              {...props}
            />
          ),
          table: ({ node, ...props }) => (
            <div className="my-4 overflow-x-auto">
              <table
                className="w-full text-sm border-collapse rounded-xl overflow-hidden"
                {...props}
              />
            </div>
          ),
          th: ({ node, ...props }) => (
            <th
              className="bg-slate-800/60 text-slate-200 font-semibold px-3 py-2 border border-slate-700/50"
              {...props}
            />
          ),
          td: ({ node, ...props }) => (
            <td
              className="px-3 py-2 border border-slate-800/50 text-slate-200"
              {...props}
            />
          ),
          code({ node, inline, className, children, ...props }: any) {
            const match = /language-(\w+)/.exec(className || "");
            if (!inline) {
              const language = match?.[1] || "text";
              return (
                <div className="my-4 rounded-xl border border-slate-700/50 overflow-hidden">
                  <SyntaxHighlighter
                    style={vscDarkPlus as any}
                    language={language}
                    PreTag="div"
                    customStyle={{
                      margin: 0,
                      background: "transparent",
                      fontSize: "0.875rem",
                      lineHeight: 1.6,
                    }}
                    wrapLongLines
                    showLineNumbers={(String(children || "").split("\n").length || 0) > 5}
                    {...props}
                  >
                    {String(children).replace(/\n$/, "")}
                  </SyntaxHighlighter>
                </div>
              );
            }
            return (
              <code
                className="px-1.5 py-0.5 bg-slate-800/70 text-purple-300 rounded-md text-sm font-mono border border-purple-700/40"
                {...props}
              >
                {children}
              </code>
            );
          },
        }}
      >
        {normalized}
      </ReactMarkdown>
    </div>
  );
};

export default ProperMarkdownRenderer;
