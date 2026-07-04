import { useState, useRef, useEffect } from 'react';
import Layout from '../components/Layout';
import { useAuth } from '../context/AuthContext';
import styles from './Chat.module.css';

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef();
  const { token } = useAuth();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async () => {
    if (!input.trim() || streaming) return;
    const question = input.trim();
    setInput('');
    setMessages(m => [...m, { role: 'user', text: question }]);
    setStreaming(true);

    const aiIdx = Date.now();
    setMessages(m => [...m, { role: 'ai', text: '', citations: [], id: aiIdx, streaming: true }]);

    try {
      const res = await fetch('http://localhost:8000/api/v1/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ question, limit: 5 }),
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const lines = decoder.decode(value).split('\n').filter(l => l.startsWith('data: '));
        for (const line of lines) {
          const data = JSON.parse(line.slice(6));
          if (data.type === 'citations') {
            setMessages(m => m.map(msg => msg.id === aiIdx ? { ...msg, citations: data.citations } : msg));
          } else if (data.type === 'token') {
            setMessages(m => m.map(msg => msg.id === aiIdx ? { ...msg, text: msg.text + data.content } : msg));
          } else if (data.type === 'done') {
            setMessages(m => m.map(msg => msg.id === aiIdx ? { ...msg, streaming: false } : msg));
          }
        }
      }
    } catch (e) {
      setMessages(m => m.map(msg => msg.id === aiIdx ? { ...msg, text: 'Something went wrong. Please try again.', streaming: false } : msg));
    } finally {
      setStreaming(false);
    }
  };

  const onKey = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } };

  return (
    <Layout>
      <div className={styles.page}>
        <div className={`${styles.chatHeader} fade-up`}>
          <div className={styles.heading}>Ask your <em>knowledge base</em></div>
          <div className={styles.sub}>Powered by Llama 3.2 · Results from your indexed documents</div>
        </div>

        <div className={styles.messages}>
          {messages.length === 0 && (
            <div className={styles.empty}>
              <div className={styles.emptyHeading}>What would you like to know?</div>
              <div className={styles.emptyText}>Ask anything about your uploaded documents.</div>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`${styles.msgBlock} ${i < 3 ? `fade-up-${i + 1}` : 'fade-up'}`}>
              <div className={styles.msgWho}>
                {msg.role === 'user' ? 'You' : 'KnowledgeAI'}
              </div>
              <div className={styles.msgText}>
                {msg.text}
                {msg.streaming && <span className={styles.cursor} />}
              </div>
              {msg.citations?.length > 0 && (
                <div className={styles.citations}>
                  {msg.citations.map((c, j) => (
                    <span key={j} className={styles.cite}>
                      ↗ {c.document_name} · {Math.round(c.similarity * 100)}% match
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        <div className={`${styles.inputBar} fade-up-3`}>
          <div className={styles.inputWrap}>
            <input
              className={styles.input}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={onKey}
              placeholder="Ask anything about your documents…"
              disabled={streaming}
            />
            <span className={styles.kbd}>↵</span>
          </div>
          <button className={styles.sendBtn} onClick={send} disabled={streaming}>↑</button>
        </div>
      </div>
    </Layout>
  );
}