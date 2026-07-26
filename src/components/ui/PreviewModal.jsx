import React, { useState, useEffect } from 'react';
import { X, CheckCircle, AlertTriangle, AlertCircle, Save, Edit2, Search, Filter, Download } from 'lucide-react';
import Button from './Button';
import { api } from '../../lib/api';
import { useToast } from '../../contexts/ToastContext';
import './PreviewModal.css';

const PreviewModal = ({ uploadId, onClose, onComplete }) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({});
  const { addToast } = useToast();
  const [isApproving, setIsApproving] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);

  useEffect(() => {
    fetchPreviewData();
  }, [uploadId]);

  const fetchPreviewData = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/preview/${uploadId}`);
      setData(res);
    } catch (error) {
      addToast('Failed to load mapping preview: ' + error.message, 'error');
      onClose();
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    try {
      setIsApproving(true);
      await api.post(`/preview/${uploadId}/approve`, { approve_all: true });
      addToast('Mapping approved and saved successfully!', 'success');
      if (onComplete) onComplete();
      onClose();
    } catch (error) {
      addToast('Failed to approve mapping: ' + error.message, 'error');
      setIsApproving(false);
    }
  };

  const handleReject = async () => {
    if (!window.confirm("Are you sure you want to reject this extraction? This will delete all temporary data.")) return;
    try {
      setIsRejecting(true);
      await api.post(`/preview/${uploadId}/reject`);
      addToast('Extraction rejected and data wiped.', 'success');
      if (onComplete) onComplete();
      onClose();
    } catch (error) {
      addToast('Failed to reject mapping: ' + error.message, 'error');
      setIsRejecting(false);
    }
  };

  const startEdit = (item) => {
    setEditingId(item.id);
    setEditForm({
      subject_code: item.subject_code || '',
      subject_name: item.subject_name || '',
      faculty_name: item.faculty_name || '',
      room: item.room || '',
      day: item.day || '',
      period: item.period || ''
    });
  };

  const saveEdit = async (id) => {
    try {
      await api.post(`/preview/${uploadId}/edit`, { item_id: id, ...editForm });
      setEditingId(null);
      addToast('Row updated and re-validated.', 'success');
      fetchPreviewData(); // Refresh to get new validation status
    } catch (error) {
      addToast('Failed to save edit: ' + error.message, 'error');
    }
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditForm({});
  };

  const handleExportCSV = () => {
    if (!data || !data.items) return;
    const headers = ['Day', 'Hour', 'Department', 'Semester', 'Class', 'Subject Code', 'Subject Name', 'Faculty', 'Status'];
    const csvRows = [headers.join(',')];
    
    data.items.forEach(item => {
      const values = [
        item.day, item.period, item.department, item.semester, item.class_name,
        item.subject_code, `"${item.subject_name || ''}"`, `"${item.faculty_name || ''}"`, item.validation_status
      ];
      csvRows.push(values.join(','));
    });
    
    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `preview_${uploadId}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="preview-modal-overlay">
        <div className="preview-modal-content" style={{ width: '400px', height: '200px', alignItems: 'center', justifyContent: 'center', display: 'flex', flexDirection: 'column' }}>
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
          <p className="mt-4 text-secondary">Loading Admin Preview...</p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const total = data.total_entries || 0;
  const mapped = data.valid_count || 0;
  const warnings = data.warning_count || 0;
  const errors = data.error_count || 0;
  const accuracy = total > 0 ? ((mapped / total) * 100).toFixed(2) : 0;

  let filteredItems = data.items || [];
  
  if (filterStatus !== 'all') {
    filteredItems = filteredItems.filter(i => i.validation_status === filterStatus);
  }
  
  if (searchTerm) {
    const lower = searchTerm.toLowerCase();
    filteredItems = filteredItems.filter(i => 
      (i.subject_code || '').toLowerCase().includes(lower) ||
      (i.subject_name || '').toLowerCase().includes(lower) ||
      (i.faculty_name || '').toLowerCase().includes(lower) ||
      (i.department || '').toLowerCase().includes(lower) ||
      (i.day || '').toLowerCase().includes(lower)
    );
  }

  return (
    <div className="preview-modal-overlay">
      <div className="preview-modal-content full-screen">
        <div className="preview-modal-header">
          <div>
            <h2>Admin Mapping Preview <span className="upload-id-badge">Upload #{uploadId}</span></h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Review the extracted data before committing to the database.</p>
          </div>
          <div className="preview-header-actions">
             <Button variant="outline" onClick={handleExportCSV} icon={Download}>Export CSV</Button>
             <Button variant="danger" onClick={handleReject} disabled={isRejecting || isApproving}>Reject Mapping</Button>
             <Button variant="primary" onClick={handleApprove} disabled={isApproving || isRejecting} icon={CheckCircle}>
               {isApproving ? 'Approving...' : 'Approve Mapping'}
             </Button>
             <button className="preview-close-btn" onClick={onClose}><X size={24} /></button>
          </div>
        </div>

        <div className="preview-summary-panel">
          <div className="summary-stat">
            <span className="stat-label">Total Cells</span>
            <span className="stat-value">{total}</span>
          </div>
          <div className="summary-stat">
            <span className="stat-label">Successfully Mapped</span>
            <span className="stat-value text-success">{mapped}</span>
          </div>
          <div className="summary-stat">
            <span className="stat-label">Warnings</span>
            <span className="stat-value text-warning">{warnings}</span>
          </div>
          <div className="summary-stat">
            <span className="stat-label">Errors</span>
            <span className="stat-value text-error">{errors}</span>
          </div>
          <div className="summary-stat">
            <span className="stat-label">Accuracy</span>
            <span className="stat-value" style={{ color: accuracy > 95 ? 'var(--success-color)' : 'var(--warning-color)' }}>
              {accuracy}%
            </span>
          </div>
        </div>

        <div className="preview-workspace">

          {/* Right Panel: Data Grid */}
          <div className="preview-right-panel">
            <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3>Extracted Mapping</h3>
              <div className="grid-controls">
                <div className="search-box">
                  <Search size={16} />
                  <input 
                    type="text" 
                    placeholder="Search..." 
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                  />
                </div>
                <div className="filter-box">
                  <Filter size={16} />
                  <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
                    <option value="all">All Statuses</option>
                    <option value="valid">✅ Correct</option>
                    <option value="warning">⚠️ Warning</option>
                    <option value="error">❌ Error</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="table-container">
              <table className="mapping-table">
                <thead>
                  <tr>
                    <th>Day</th>
                    <th>Hour</th>
                    <th>Class</th>
                    <th>Code</th>
                    <th>Subject Name</th>
                    <th>Faculty Name(s)</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredItems.map(item => {
                    const isEditing = editingId === item.id;
                    return (
                      <tr key={item.id} className={`status-row-${item.validation_status}`}>
                        {isEditing ? (
                          <>
                            <td><input className="edit-input" value={editForm.day} onChange={e => setEditForm({...editForm, day: e.target.value})} /></td>
                            <td><input className="edit-input" value={editForm.period} onChange={e => setEditForm({...editForm, period: e.target.value})} /></td>
                            <td>{item.class_name}</td>
                            <td><input className="edit-input" value={editForm.subject_code} onChange={e => setEditForm({...editForm, subject_code: e.target.value})} /></td>
                            <td><input className="edit-input" value={editForm.subject_name} onChange={e => setEditForm({...editForm, subject_name: e.target.value})} /></td>
                            <td><input className="edit-input" value={editForm.faculty_name} onChange={e => setEditForm({...editForm, faculty_name: e.target.value})} /></td>
                            <td>-</td>
                            <td>
                              <div style={{ display: 'flex', gap: '4px' }}>
                                <button className="action-icon-btn save-btn" onClick={() => saveEdit(item.id)}><Save size={16}/></button>
                                <button className="action-icon-btn cancel-btn" onClick={cancelEdit}><X size={16}/></button>
                              </div>
                            </td>
                          </>
                        ) : (
                          <>
                            <td>{item.day}</td>
                            <td>{item.period}</td>
                            <td>
                              <div style={{ fontSize: '11px', fontWeight: 'bold' }}>{item.class_name}</div>
                              <div style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>{item.department} Sem {item.semester}</div>
                            </td>
                            <td><strong>{item.subject_code}</strong></td>
                            <td style={{ maxWidth: '200px', whiteSpace: 'normal' }}>{item.subject_name}</td>
                            <td style={{ maxWidth: '150px', whiteSpace: 'normal' }}>{item.faculty_name}</td>
                            <td>
                              <div className={`status-indicator-pill ${item.validation_status}`}>
                                {item.validation_status === 'valid' && <><CheckCircle size={12} /> Correct</>}
                                {item.validation_status === 'warning' && <><AlertTriangle size={12} /> Warning</>}
                                {item.validation_status === 'error' && <><AlertCircle size={12} /> Error</>}
                              </div>
                              {item.validation_message && (
                                <div style={{ fontSize: '10px', marginTop: '4px', color: 'var(--text-secondary)' }}>
                                  {item.validation_message}
                                </div>
                              )}
                            </td>
                            <td>
                              <button className="action-icon-btn edit-btn" onClick={() => startEdit(item)} title="Edit Row"><Edit2 size={16}/></button>
                            </td>
                          </>
                        )}
                      </tr>
                    );
                  })}
                  {filteredItems.length === 0 && (
                    <tr>
                      <td colSpan="8" style={{ textAlign: 'center', padding: '2rem' }}>No records found matching filters.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PreviewModal;
