import React, { useState, useRef, useEffect } from 'react';
import { UploadCloud, X, File as FileIcon, Trash2, Eye, RefreshCw, FileText } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Table from '../components/ui/Table';
import Input from '../components/ui/Input';
import PreviewModal from '../components/ui/PreviewModal';
import SummaryModal from '../components/ui/SummaryModal';
import { useToast } from '../contexts/ToastContext';
import { api } from '../lib/api';
import './Upload.css';

const Upload = () => {
  const [dragActive, setDragActive] = useState(false);
  const [files, setFiles] = useState([]);
  const [metadata, setMetadata] = useState({ department: '', semester: '', academic_year: '' });
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [recentUploads, setRecentUploads] = useState([]);
  const inputRef = useRef(null);
  const { addToast } = useToast();
  const [previewUploadId, setPreviewUploadId] = useState(null);
  const [summaryUploadId, setSummaryUploadId] = useState(null);

  useEffect(() => {
    fetchUploads();
  }, []);

  useEffect(() => {
    let interval;
    const hasActiveUploads = recentUploads.some(u => u.status === 'processing' || u.status === 'uploaded');
    if (hasActiveUploads) {
      interval = setInterval(() => {
        fetchUploads();
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [recentUploads]);

  const fetchUploads = async () => {
    try {
      const data = await api.get('/uploads');
      setRecentUploads(data);
    } catch (error) {
      console.error('Failed to fetch uploads:', error);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };

  const handleFiles = (newFiles) => {
    const fileArray = Array.from(newFiles).map(file => ({
      id: Date.now() + Math.random(),
      file,
      name: file.name,
      size: (file.size / (1024 * 1024)).toFixed(2) + ' MB',
      status: 'pending' // pending, uploading, success, error
    }));
    setFiles([...files, ...fileArray]);
  };

  const removeFile = (id) => {
    setFiles(files.filter(f => f.id !== id));
  };

  const uploadFiles = async () => {
    if (!files || files.length === 0) return;
    if (!metadata.department || !metadata.semester || !metadata.academic_year) {
      addToast('Please fill all metadata fields', 'error');
      return;
    }

    setIsUploading(true);
    setUploadProgress(20);

    for (let f of files) {
      try {
        const formData = new FormData();
        // Extract actual native File object from our wrapper
        const nativeFile = f.file || f; 
        formData.append('file', nativeFile);
        formData.append('department', metadata.department);
        formData.append('semester', metadata.semester);
        formData.append('academic_year', metadata.academic_year);

        await api.post('/upload', formData);
        setUploadProgress(100);
        addToast(`File ${f.name || 'uploaded'} processing started`, 'success');
        
        // Remove uploaded file from list safely
        setFiles(prev => prev.filter(item => item.id !== f.id));
      } catch (error) {
        addToast(`Failed to upload ${f.name || 'file'}: ${error?.message || error}`, 'error');
      }
    }
    
    setIsUploading(false);
    setUploadProgress(0);
    fetchUploads();
  };

  const handleDeleteUpload = async (id) => {
    if (!id) return;
    try {
      await api.delete(`/uploads/${id}`);
      addToast('Upload deleted successfully', 'success');
      fetchUploads();
    } catch (error) {
      addToast(`Failed to delete: ${error?.message || error}`, 'error');
    }
  };

  const columns = [
    { header: 'File Name', accessor: 'original_filename' },
    { header: 'Department', accessor: 'department' },
    { header: 'Semester', accessor: 'semester' },
    { 
      header: 'Upload Date', 
      accessor: 'upload_date', 
      render: (row) => row?.upload_date ? new Date(row.upload_date).toLocaleDateString() : 'N/A' 
    },
    { 
      header: 'Status', 
      render: (row) => (
        <div style={{ width: '150px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: '12px' }}>
            <span className={`status-badge status-${(row?.status || 'pending').toLowerCase().replace(/ /g, '_')}`}>
              {row?.status ? row.status.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ') : 'Pending'}
            </span>
            {row?.status === 'processing' && (
              <span style={{ color: 'var(--text-secondary)' }}>{row?.processing_progress || 0}%</span>
            )}
          </div>
          {row?.status === 'processing' && (
            <div>
              <div style={{ height: '4px', backgroundColor: 'var(--bg-secondary)', borderRadius: '2px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${row?.processing_progress || 0}%`, backgroundColor: 'var(--primary-color)', transition: 'width 0.3s ease' }}></div>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                {row?.processing_stage || 'Processing...'}
              </div>
            </div>
          )}
        </div>
      )
    },
    {
      header: 'Actions',
      render: (row) => (
        <div style={{ display: 'flex', gap: '8px' }}>
          {row?.status === 'pending_approval' && (
            <Button 
              variant="primary" 
              size="sm" 
              onClick={() => setPreviewUploadId(row?.id)}
              icon={Eye}
            >
              Review Mapping
            </Button>
          )}
          {row?.status !== 'pending_approval' && row?.status !== 'processing' && row?.status !== 'uploaded' && (
            <>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setSummaryUploadId(row?.id)}
                icon={FileText}
              >
                View Summary
              </Button>
              {row?.status === 'approved' && (
                <>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => {
                      api.download(`/export/${row.id}/excel`, `timetable_export_${row.id}.xlsx`)
                        .catch(err => addToast(`Download failed: ${err.message}`, 'error'));
                    }}
                  >
                    Excel
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => {
                      api.download(`/export/${row.id}/pdf`, `timetable_export_${row.id}.pdf`)
                        .catch(err => addToast(`Download failed: ${err.message}`, 'error'));
                    }}
                  >
                    PDF
                  </Button>
                </>
              )}
            </>
          )}
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => handleDeleteUpload(row?.id)}
            style={{ color: 'var(--error-color)', padding: '0.25rem 0.5rem' }}
          >
            <Trash2 size={16} />
          </Button>
        </div>
      )
    }
  ];



  return (
    <div className="upload-page">
      <div className="dashboard-header mb-6">
        <h1 className="page-title">Upload Timetable</h1>
        <p className="page-subtitle">Upload master timetables in PDF format to extract individual faculty schedules.</p>
      </div>

      <Card padding="lg" className="mb-8">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
          <Input 
            label="Department" 
            placeholder="e.g. Computer Science" 
            value={metadata.department} 
            onChange={e => setMetadata({...metadata, department: e.target.value})} 
          />
          <Input 
            label="Semester" 
            placeholder="e.g. 4" 
            value={metadata.semester} 
            onChange={e => setMetadata({...metadata, semester: e.target.value})} 
          />
          <Input 
            label="Academic Year" 
            placeholder="e.g. 2026-2027" 
            value={metadata.academic_year} 
            onChange={e => setMetadata({...metadata, academic_year: e.target.value})} 
          />
        </div>

        <div 
          className={`drop-zone ${dragActive ? 'active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => inputRef.current.click()}
        >
          <input 
            type="file" 
            ref={inputRef} 
            onChange={handleChange} 
            accept=".pdf" 
            multiple 
            className="hidden-input"
          />
          <div className="drop-zone-content">
            <div className="upload-icon-wrapper">
              <UploadCloud size={40} className="upload-icon" />
            </div>
            <h3 className="drop-title">Click or drag file to this area to upload</h3>
            <p className="drop-desc">Support for a single or bulk upload. Strictly prohibit from uploading company data or other band files.</p>
          </div>
        </div>

        {files.length > 0 && (
          <div className="selected-files mt-6">
            <h4 className="section-subtitle">Selected Files</h4>
            <div className="file-list">
              {files.map(f => (
                <div key={f.id} className="file-item">
                  <div className="file-info">
                    <FileIcon size={24} className="text-primary" />
                    <div>
                      <p className="file-name">{f.name}</p>
                      <p className="file-size">{f.size}</p>
                    </div>
                  </div>
                  <button className="remove-btn" onClick={() => removeFile(f.id)} disabled={isUploading}>
                    <X size={18} />
                  </button>
                </div>
              ))}
            </div>

            {isUploading && (
              <div className="progress-container mt-4">
                <div className="progress-bar-bg">
                  <div className="progress-bar-fill animate-pulse" style={{ width: `${uploadProgress}%` }}></div>
                </div>
                <p className="progress-text">{uploadProgress}% Uploading...</p>
              </div>
            )}

            <div className="upload-actions mt-6 flex justify-end gap-4">
               <Button variant="secondary" onClick={() => setFiles([])} disabled={isUploading}>Cancel</Button>
               <Button variant="primary" onClick={uploadFiles} disabled={isUploading}>
                 {isUploading ? 'Uploading...' : 'Upload Files'}
               </Button>
            </div>
          </div>
        )}
      </Card>

      <Card title="Recent Uploads">
        <div className="card-header border-b">
          <h2 className="card-title">Recent Uploads</h2>
        </div>
        <div className="p-4">
          {recentUploads.length > 0 ? (
            <Table 
              columns={columns} 
              data={recentUploads} 
            />
          ) : (
            <p style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem 0' }}>No recent uploads.</p>
          )}
        </div>
      </Card>

      {previewUploadId && (
        <PreviewModal 
          uploadId={previewUploadId}
          onClose={() => setPreviewUploadId(null)}
          onComplete={fetchUploads}
        />
      )}

      {summaryUploadId && (
        <SummaryModal 
          uploadId={summaryUploadId}
          onClose={() => setSummaryUploadId(null)}
        />
      )}
    </div>
  );
};

export default Upload;
