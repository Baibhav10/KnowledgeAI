import { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { useAuth } from '../context/AuthContext';
import client from '../api/client';
import styles from './Chat.module.css';

const SUMMARY_PROMPT = `Please provide a concise summary (under 200 words) of our conversation so far, 
including: the main topics discussed, key findings from the documents, and any conclusions reached. 
This summary will be used to continue the conversation in a new chat session.`;

export default function Chat() {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();

  const [conversations, setConversations] = useState([]);
  const [messages, setMessages] = useState([]);
  const [activeConv, setActiveConv] = useState(null);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [showSummaryBanner, setShowSummaryBanner] = useState(false);
  const [summary, setSummary] = useState('');
  const [copied, setCopied] = useState(false);
  const bottomRef = useRef();

  // Load all conversations for sidebar
  const loadConversations = () =>
    client.get('/conversations/').then(r => setConversations(r.data)).catch(() => {});

  useEffect(() => { loadConversations(); }, []);

  // Load specific conversation when URL changes
  useEffect(() => {
    if (!conversationId) return;
    client.get(`/conversations/${conversationId}`).then(r => {
      setActiveConv(r.data);
      setMessages(r.data.messages.map(m => ({
        role: m.role === 'assistant' ? 'ai' : 'user',
        text: m.content,
      })));
    }).catch(() => navigate('/chat'));
  }, [conversationId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const getHistory = () =>
    messages
      .filter(m => !m.streaming)
      .map(m => ({ role: m.role === 'ai' ? 'assistant' : 'user', content: m.text }));

  const sendMessage = async (question, isSystemSummary = false) => {
    if (!question.trim() || streaming || !conversationId) return;

    if (!isSystemSummary) {
      setMessages(m => [...m, { role: 'user', text: question }]);
    }
    setStreaming(true);

    const aiIdx = Date.now();
    if (!isSystemSummary) {
      setMessages(m => [...m, { role: 'ai', text: '', citations: [], id: aiIdx, streaming: true }]);
    }

    let fullText = '';

    try {
      const res = await fetch('http://localhost:8000/api/v1/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          question,
          messages: getHistory(),
          limit: 5,
          conversation_id: conversationId,
          document_id: activeConv?.document_id,
        }),
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const lines = decoder.decode(value).split('\n').filter(l => l.startsWith('data: '));
        for (const line of lines) {
          const data = JSON.parse(line.slice(6));
          if (data.type === 'citations' && !isSystemSummary) {
            setMessages(m => m.map(msg => msg.id === aiIdx ? { ...msg, citations: data.citations } : msg));
          } else if (data.type === 'token') {
            fullText += data.content;
            if (!isSystemSummary) {
              setMessages(m => m.map(msg => msg.id === aiIdx ? { ...msg, text: msg.text + data.content } : msg));
            }
          } else if (data.type === 'approaching_limit') {
            setShowSummaryBanner(true);
          } else if (data.type === 'done') {
            if (!isSystemSummary) {
              setMessages(m => m.map(msg => msg.id === aiIdx ? { ...msg, streaming: false } : msg));
            }
            loadConversations();
          }
        }
      }
    } catch (e) {
      if (!isSystemSummary) {
        setMessages(m => m.map(msg =>
          msg.id === aiIdx ? { ...msg, text: 'Something went wrong.', streaming: false } : msg
        ));
      }
    } finally {
      setStreaming(false);
    }

    return fullText;
  };

  const send = async () => {
    const question = input.trim();
    setInput('');
    await sendMessage(question);
  };

  const generateSummary = async () => {
    setShowSummaryBanner(false);
    const result = await sendMessage(SUMMARY_PROMPT, true);
    setSummary(result);
  };

  const copySummary = () => {
    navigator.clipboard.writeText(
      `[Conversation summary]\n\n${summary}`
    );
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const deleteConv = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('Delete this conversation?')) return;
    await client.delete(`/conversations/${id}`);
    await loadConversations();
    if (id === conversationId) navigate('/chat');
  };

  const onKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  };

  return (
    <Layout>
      <div className={styles.page}>
        {/* Sidebar */}
        <div className={styles.sidebar}>
          <div className={styles.sidebarHeader}>
            <span className={styles.sidebarTitle}>History</span>
            <button className={styles.newChatBtn} onClick={() => navigate('/documents')}>
              + New
            </button>
          </div>
          <div className={styles.convList}>
            {conversations.length === 0 && (
              <p className={styles.noConvs}>No conversations yet.</p>
            )}
            {conversations.map(conv => (
              <div
                key={conv.id}
                className={`${styles.convItem} ${conv.id === conversationId ? styles.convActive : ''}`}
                onClick={() => navigate(`/chat/${conv.id}`)}
              >
                <div className={styles.convTitle}>{conv.title}</div>
                <div className={styles.convMeta}>
                  {conv.document_name} · {new Date(conv.updated_at).toLocaleDateString()}
                </div>
                <button className={styles.convDelete} onClick={(e) => deleteConv(conv.id, e)}>✕</button>
              </div>
            ))}
          </div>
        </div>

        {/* Main chat area */}
        <div className={styles.chatArea}>
          {!conversationId ? (
            <div className={styles.noChatSelected}>
              <div className={styles.emptyHeading}>Select a conversation</div>
              <div className={styles.emptyText}>
                Or go to <span onClick={() => navigate('/documents')}>Documents →</span> to start a new chat
              </div>
            </div>
          ) : (
            <>
              <div className={`${styles.chatHeader} fade-up`}>
                <div className={styles.heading}>
                  {activeConv?.document_name || 'Loading…'}
                </div>
                <div className={styles.sub}>Powered by Llama 3.2 · Conversation memory active</div>
              </div>

              {showSummaryBanner && (
                <div className={styles.limitBanner}>
                  <span>This conversation is getting long.</span>
                  <button className={styles.summaryBtn} onClick={generateSummary} disabled={streaming}>
                    Generate summary →
                  </button>
                </div>
              )}

              {summary && (
                <div className={styles.summaryBox}>
                  <div className={styles.summaryLabel}>Summary — paste into a new chat to continue</div>
                  <p className={styles.summaryText}>{summary}</p>
                  <button className={styles.copyBtn} onClick={copySummary}>
                    {copied ? '✓ Copied' : 'Copy summary'}
                  </button>
                </div>
              )}

              <div className={styles.messages}>
                {messages.length === 0 && (
                  <div className={styles.empty}>
                    <div className={styles.emptyHeading}>Start the conversation</div>
                    <div className={styles.emptyText}>Ask anything about this document.</div>
                  </div>
                )}
                {messages.map((msg, i) => (
                  <div key={i} className={`${styles.msgBlock} fade-up`}>
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

              <div className={styles.inputBar}>
                <div className={styles.inputWrap}>
                  <input
                    className={styles.input}
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={onKey}
                    placeholder="Ask anything about this document…"
                    disabled={streaming}
                  />
                  <span className={styles.kbd}>↵</span>
                </div>
                <button className={styles.sendBtn} onClick={send} disabled={streaming}>↑</button>
              </div>
            </>
          )}
        </div>
      </div>
    </Layout>
  );
}