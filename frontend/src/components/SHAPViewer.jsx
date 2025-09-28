import React, { useEffect, useState } from 'react';
import axios from 'axios';

/**
 * SHAPViewer
 * - fetches /shap/list
 * - displays list with previews (images) and download links
 * - for HTML fragments, it will fetch and dangerouslySetInnerHTML into an iframe or container (careful: only use with trusted backend)
 */
export default function SHAPViewer() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);

  async function loadList() {
    setLoading(true);
    try {
      const res = await axios.get('/shap/list');
      setFiles(res.data.files || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadList(); }, []);

  return (
    <div>
      <h3>SHAP artifacts</h3>
      <div style={{ marginTop: 8 }}>
        <button className="button" onClick={loadList} disabled={loading}>{loading ? 'Refreshing...' : 'Refresh list'}</button>
      </div>

      <div style={{ marginTop: 12 }}>
        {files.length === 0 && <div style={{ color: 'var(--muted)' }}>No SHAP artifacts yet.</div>}
        {files.map(f => (
          <div key={f.filename} style={{ marginTop: 12, borderBottom: '1px solid rgba(255,255,255,0.03)', paddingBottom: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <div>{f.filename}</div>
              <div>
                <a className="muted" href={f.url} target="_blank" rel="noreferrer">Open</a>
              </div>
            </div>
            {f.filename.match(/\.(png|jpg|jpeg|gif)$/i) ? (
              <img src={f.url} alt={f.filename} style={{ maxWidth: '100%', marginTop: 8 }} />
            ) : f.filename.match(/\.html$/i) ? (
              <iframe src={f.url} title={f.filename} style={{ width: '100%', height: 360, marginTop: 8 }} />
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}