import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import client from '../api/client';
import styles from './Documents.module.css';

export default function Documents() {
  const [docs, setDocs] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [startingChat, setStartingChat] = useState(null);
  const fileRef = useRef();
  const navigate = useNavigate();

  const load = () => client.get('/documents/').then(r => setDocs(r.data)).catch(() => {});
  useEffect(() => { load(); const t = setInterval(load, 4000); return () => clearInterval(t); }, []);

  const upload = async (file) => {
    if (!file) return;
    setUploading(true);
    const form = new FormData();
    form.append('file', file);
    try { await client.post('/documents/upload', form); await load(); }
    catch (e) { alert(e.response?.data?.detail || 'Upload failed'); }
    finally { setUploading(false); }
  };

  const onDrop = (e) => {
    e.preventDefault(); setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) upload(file);
  };

  const deleteDoc = async (id) => {
    if (!window.confirm('Delete this document? This cannot be undone.')) return;
    try { await client.delete(`/documents/${id}`); await load(); }
    catch (e) { alert('Failed to delete document'); }
  };

  const startChat = async (doc) => {
    if (doc.status !== 'completed') return;
    setStartingChat(doc.id);
    try {
      const { data } = await client.post('/conversations/', {
        document_id: doc.id,
        title: `Chat about ${doc.name}`,
      });
      navigate(`/chat/${data.id}`);
    } catch (e) {
      alert('Failed to start chat');
    } finally {
      setStartingChat(null);
    }
  };

  const statusLabel = (s) => {
    if (s === 'completed') return { label: 'Indexed', cls: styles.sDone };
    if (s === 'processing') return { label: 'Processing', cls: styles.sProc };
    if (s === 'pending') return { label: 'Pending', cls: styles.sPend };
    return { label: 'Failed', cls: styles.sFail };
  };

  return (
    <Layout>
      <div className={styles.page}>
        <div className={`${styles.pageHeader} fade-up`}>
          <div>
            <h1 className={styles.heading}>Document index</h1>
            <p className={styles.sub}>{docs.length} documents · {docs.filter(d => d.status === 'completed').length} indexed</p>
          </div>
          <button className={styles.uploadBtn} onClick={() => fileRef.current.click()} disabled={uploading}>
            {uploading ? 'Uploading…' : 'Upload ↑'}
          </button>
          <input ref={fileRef} type="file" accept=".pdf,.docx,.txt" style={{ display: 'none' }} onChange={e => upload(e.target.files[0])} />
        </div>

        <div
          className={`${styles.dropZone} ${dragging ? styles.dragging : ''} fade-up-1`}
          onDragOver={e => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => fileRef.current.click()}
        >
          <span className={styles.dropIcon}>↑</span>
          <span className={styles.dropText}>Drop a file here or click to browse</span>
          <span className={styles.dropSub}>PDF · DOCX · TXT</span>
        </div>

        <div className={`${styles.tableHeader} fade-up-2`}>
          <span>Index</span>
          <span>Name</span>
          <span>Type</span>
          <span>Uploaded</span>
          <span>Status</span>
          <span></span>
          <span></span>
        </div>

        <div className={styles.docList}>
          {docs.map((doc, i) => {
            const { label, cls } = statusLabel(doc.status);
            return (
              <div key={doc.id} className={styles.docRow} style={{ animationDelay: `${0.1 + i * 0.04}s` }}>
                <span className={styles.idx}>{String(i + 1).padStart(2, '0')}</span>
                <span className={styles.name}>{doc.name}</span>
                <span className={styles.type}>{doc.file_type.toUpperCase()}</span>
                <span className={styles.date}>{new Date(doc.created_at).toLocaleDateString()}</span>
                <span className={`${styles.status} ${cls}`}>{label}</span>
                <button
                  className={styles.chatBtn}
                  onClick={() => startChat(doc)}
                  disabled={doc.status !== 'completed' || startingChat === doc.id}
                >
                  {startingChat === doc.id ? '…' : 'Chat →'}
                </button>
                <button className={styles.deleteBtn} onClick={() => deleteDoc(doc.id)}>✕</button>
              </div>
            );
          })}
        </div>
      </div>
    </Layout>
  );
}