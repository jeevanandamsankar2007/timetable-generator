import React, { useState, useEffect } from 'react';
import { Eye, RefreshCw, Trash2, Search, Filter } from 'lucide-react';
import Card from '../components/ui/Card';
import Table from '../components/ui/Table';
import Modal from '../components/ui/Modal';
import Button from '../components/ui/Button';
import { useToast } from '../contexts/ToastContext';
import { api } from '../lib/api';

const UploadedFiles = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isDeleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploads, setUploads] = useState([]);
  const [loading, setLoading] = useState(true);
  const { addToast } = useToast();

  useEffect(() => {
    fetchUploads();
  }, []);

  const fetchUploads = async () => {
    try {
      const data = await api.get('/uploads');
      setUploads(data);
    } catch (error) {
      console.error('Failed to fetch uploads:', error);
      addToast('Failed to load uploads', 'error');
    } finally {
      setLoading(false);
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
    { header: 'Faculty Count', accessor: 'saved_count', align: 'center' },
    { 
      header: 'Status', 
      render: (row) => (
        <span className={`status-badge status-${(row?.status || 'pending').toLowerCase().replace(/ /g, '_')}`}>
          {row?.status ? row.status.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ') : 'Pending'}
        </span>
      )
    },
  ];

  const handleDeleteClick = (file) => {
    setSelectedFile(file);
    setDeleteModalOpen(true);
  };

  const confirmDelete = async () => {
    try {
      await api.delete(`/uploads/${selectedFile.id}`);
      addToast(`${selectedFile.original_filename} deleted successfully`, 'success');
      setDeleteModalOpen(false);
      setSelectedFile(null);
      fetchUploads();
    } catch (error) {
      addToast(`Failed to delete: ${error?.message || error}`, 'error');
    }
  };

  const renderActions = (row) => (
    <div className="flex justify-end gap-2">
      <button className="action-icon-btn text-danger" title="Delete" onClick={() => handleDeleteClick(row)}>
        <Trash2 size={16} />
      </button>
    </div>
  );

  const filteredFiles = uploads.filter(f => f.original_filename?.toLowerCase().includes(searchTerm.toLowerCase()));

  return (
    <div className="max-w-6xl mx-auto">
      <div className="dashboard-header mb-6">
        <h1 className="page-title">Uploaded Files</h1>
        <p className="page-subtitle">Manage all master timetables uploaded to the system.</p>
      </div>

      <Card padding="none">
        <div className="flex justify-between items-center p-4 border-b border-[var(--border)]">
          <div className="topbar-search" style={{ width: '300px' }}>
            <Search size={18} className="search-icon" />
            <input 
              type="text" 
              placeholder="Search files..." 
              className="search-input"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <Button variant="outline" icon={Filter}>Filter</Button>
        </div>
        <div className="p-4">
          <Table 
            columns={columns} 
            data={filteredFiles} 
            actions={renderActions}
          />
        </div>
      </Card>

      <Modal 
        isOpen={isDeleteModalOpen} 
        onClose={() => setDeleteModalOpen(false)}
        title={<span style={{ color: '#111827' }}>Confirm Deletion</span>}
        contentStyle={{ backgroundColor: '#f9fafb', color: '#111827' }}
      >
        <div className="flex flex-col gap-4">
          <p style={{ color: '#374151' }}>
            Are you sure you want to delete <strong>{selectedFile?.original_filename}</strong>? This action cannot be undone and will remove all generated faculty timetables associated with this master file.
          </p>
          <div className="flex justify-end gap-3 mt-4">
            <Button variant="secondary" onClick={() => setDeleteModalOpen(false)}>Cancel</Button>
            <Button variant="danger" onClick={confirmDelete}>Delete File</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default UploadedFiles;
