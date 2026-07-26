import React, { useState, useEffect } from 'react';
import { X, CheckCircle, AlertTriangle, AlertCircle, Save, Check } from 'lucide-react';
import Button from './Button';
import { api } from '../../lib/api';
import { useToast } from '../../contexts/ToastContext';
import './PreviewModal.css';

const SummaryModal = ({ uploadId, onClose }) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const { addToast } = useToast();

  useEffect(() => {
    fetchSummaryData();
  }, [uploadId]);

  const fetchSummaryData = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/upload/${uploadId}/summary`);
      setData(res);
    } catch (error) {
      addToast('Failed to load summary data: ' + error.message, 'error');
      onClose();
    } finally {
      setLoading(false);
    }
  };

  const [activeTab, setActiveTab] = useState('summary'); // 'summary', 'validation', 'debug'

  if (loading) {
    return (
      <div className="modal-overlay">
        <div className="modal-content" style={{ width: '400px', height: '200px', alignItems: 'center', justifyContent: 'center' }}>
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="mt-4 text-secondary">Loading summary report...</p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ maxWidth: '90vw', width: '1000px' }}>
        <div className="modal-header">
          <h2>Processing Summary <span style={{ fontSize: '1rem', color: 'var(--text-secondary)', marginLeft: '1rem' }}>(Upload #{uploadId})</span></h2>
          <button className="modal-close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body" style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', gap: '1rem', borderBottom: '1px solid var(--border-color)', marginBottom: '1rem' }}>
            <button 
              onClick={() => setActiveTab('summary')}
              style={{ padding: '0.5rem 1rem', borderBottom: activeTab === 'summary' ? '2px solid var(--primary-color)' : 'none', fontWeight: activeTab === 'summary' ? '600' : 'normal', background: 'none', borderTop: 'none', borderLeft: 'none', borderRight: 'none', cursor: 'pointer' }}
            >
              Processing Summary
            </button>
            <button 
              onClick={() => setActiveTab('validation')}
              style={{ padding: '0.5rem 1rem', borderBottom: activeTab === 'validation' ? '2px solid var(--primary-color)' : 'none', fontWeight: activeTab === 'validation' ? '600' : 'normal', background: 'none', borderTop: 'none', borderLeft: 'none', borderRight: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
            >
              Validation Report <span style={{ background: 'var(--bg-secondary)', padding: '2px 6px', borderRadius: '4px', fontSize: '12px' }}>{data.validation_logs?.length || 0}</span>
            </button>
            <button 
              onClick={() => setActiveTab('debug')}
              style={{ padding: '0.5rem 1rem', borderBottom: activeTab === 'debug' ? '2px solid var(--primary-color)' : 'none', fontWeight: activeTab === 'debug' ? '600' : 'normal', background: 'none', borderTop: 'none', borderLeft: 'none', borderRight: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
            >
              Subject Master Debug <span style={{ background: 'var(--bg-secondary)', padding: '2px 6px', borderRadius: '4px', fontSize: '12px' }}>{data.master_debug_log?.length || 0}</span>
            </button>
          </div>

          {activeTab === 'summary' && (
            <div style={{ flex: 1, padding: '2rem 4rem' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '1.1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}><CheckCircle color="var(--success-color)" size={24} /> PDF Read: ✅</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}><CheckCircle color="var(--success-color)" size={24} /> Timetable Grid Parsed: ✅</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}><CheckCircle color="var(--success-color)" size={24} /> Subject Master Parsed: ✅</div>
                
                <hr style={{ margin: '1rem 0', borderColor: 'var(--border-color)' }} />
                
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '8px' }}>
                  <span>Mappings Created:</span>
                  <strong>{data?.total_extracted || 0}</strong>
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '1rem', background: 'rgba(245, 158, 11, 0.1)', color: '#b45309', borderRadius: '8px' }}>
                  <span>Warnings:</span>
                  <strong>{data?.warning_count || 0}</strong>
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', color: '#b91c1c', borderRadius: '8px' }}>
                  <span>Failed Records:</span>
                  <strong>{data?.error_count || 0}</strong>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '1rem', background: 'rgba(34, 197, 94, 0.1)', color: '#15803d', borderRadius: '8px', fontSize: '1.25rem', fontWeight: 'bold' }}>
                  <span>Records Successfully Saved:</span>
                  <span>{data.saved_records}</span>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'validation' && (
            <div className="preview-table-wrapper" style={{ flex: 1, minHeight: '400px' }}>
              {!data.validation_logs || data.validation_logs.length === 0 ? (
                <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                  <CheckCircle size={48} color="var(--success-color)" style={{ margin: '0 auto 1rem auto' }} />
                  <h3>No warnings or errors!</h3>
                  <p>All mapped records were perfectly valid.</p>
                </div>
              ) : (
                <table className="preview-table">
                  <thead>
                    <tr>
                      <th>Status</th>
                      <th>Cell Reference</th>
                      <th>Message</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.validation_logs.map((log) => (
                      <tr key={log.id}>
                        <td>
                          <span className={`status-indicator ${log.status}`}></span>
                          {log.status}
                        </td>
                        <td><strong>{log.cell_reference}</strong></td>
                        <td style={{ color: log.status === 'error' ? '#ef4444' : '#f59e0b' }}>
                          {log.message}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {activeTab === 'debug' && (
            <div className="preview-table-wrapper" style={{ flex: 1, minHeight: '400px' }}>
              {!data.master_debug_log ? (
                <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>No debug log available for this upload.</div>
              ) : (
                <table className="preview-table">
                  <thead>
                    <tr>
                      <th style={{ width: '40%' }}>Raw PDF Array (What the parser saw)</th>
                      <th>Code</th>
                      <th>Subject</th>
                      <th>Faculty</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.master_debug_log.map((log, i) => (
                      <tr key={i} style={{ background: log.validation_status !== 'Valid' ? 'var(--error-bg)' : 'inherit' }}>
                        <td style={{ fontFamily: 'monospace', fontSize: '11px', whiteSpace: 'pre-wrap' }}>
                          {JSON.stringify(log.raw_row)}
                        </td>
                        <td><strong>{log.extracted_code}</strong></td>
                        <td>{log.extracted_subject}</td>
                        <td>{log.extracted_faculty.join(', ')}</td>
                        <td>
                           <span className={`status-indicator ${log.validation_status === 'Valid' ? 'valid' : 'error'}`}></span>
                           <span style={{ color: log.validation_status !== 'Valid' ? '#ef4444' : 'inherit' }}>{log.validation_status}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <Button variant="primary" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
};

export default SummaryModal;
