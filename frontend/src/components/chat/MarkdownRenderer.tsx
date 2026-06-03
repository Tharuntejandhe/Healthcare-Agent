import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import styles from '@/app/chat/chat.module.css';

export default function MarkdownRenderer({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        table: ({ node, ...props }) => (
          <div className={styles.tableScroll}>
            <table className={styles.mdTable} {...props} />
          </div>
        ),
        th: ({ node, ...props }) => <th className={styles.mdTh} {...props} />,
        td: ({ node, ...props }) => <td className={styles.mdTd} {...props} />,
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
