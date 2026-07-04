import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import client from '../api/client';
import styles from './Dashboard.module.css';

export default function Dashboard() {
  const [docs, setDocs] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    client.get('/documents/').then(r => setDocs(r.data)).catch(() => {});
  }, []);

  const statusDot = (s) => {
    if (s === 'completed') return styles.dotDone;
    if (s === 'processing') return styles.dotProc;
    return styles.dotWait;
  };

  return (
    <Layout>
      <div className={styles.workspace}>
        <div className={styles.left}>
          <div className={`${styles.statsRail} fade-up-1`}>
            <div className={styles.stat}>
              <div className={styles.statN}>{docs.length}</div>
              <div className={styles.statLabel}>Documents</div>
            </div>
            <div className={styles.stat}>
              <div className={styles.statN}>{docs.filter(d => d.status === 'completed').length}</div>
              <div className={styles.statLabel}>Indexed</div>
            </div>
            <div className={styles.stat}>
              <div className={styles.statN}>{docs.filter(d => d.status === 'processing' || d.status === 'pending').length}</div>
              <div className={styles.statLabel}>Processing</div>
            </div>
          </div>

          <div className={styles.docSection}>
            <div className={`${styles.sectionLabel} fade-up-2`}>Document index</div>
            <div className={styles.docIndex}>
              {docs.length === 0 && (
                <p className={styles.empty}>No documents yet — upload one to get started.</p>
              )}
              {docs.map((doc, i) => (
                <div
                  key={doc.id}
                  className={styles.docRow}
                  style={{ animationDelay: `${0.2 + i * 0.05}s` }}
                  onClick={() => navigate('/documents')}
                >
                  <span className={styles.docIdx}>{String(i + 1).padStart(2, '0')}</span>
                  <span className={styles.docTitle}>{doc.name}</span>
                  <span className={styles.docExt}>{doc.file_type.toUpperCase()}</span>
                  <span className={`${styles.dot} ${statusDot(doc.status)}`} />
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className={styles.right}>
          <div className={`${styles.chatTop} fade-up-1`}>
            <div className={styles.chatHeading}>Ask your <em>knowledge base</em></div>
            <div className={styles.chatSub}>{docs.filter(d => d.status === 'completed').length} documents indexed · Llama 3.2</div>
          </div>
          <div className={styles.chatPrompt}>
            <p className={styles.chatPromptText}>
              Go to the <span onClick={() => navigate('/chat')}>Chat →</span> page to start asking questions about your documents.
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
}