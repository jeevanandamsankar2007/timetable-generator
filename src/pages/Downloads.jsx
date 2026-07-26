import React, { useState, useEffect } from 'react';
import { Download as DownloadIcon, Search, Filter, FileText, FileSpreadsheet } from 'lucide-react';
import Card from '../components/ui/Card';
import Table from '../components/ui/Table';
import Button from '../components/ui/Button';
import { useToast } from '../contexts/ToastContext';
import { api } from '../lib/api';

const Downloads = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [facultyList, setFacultyList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [defaultFormat, setDefaultFormat] = useState(localStorage.getItem('exportFormat') || 'pdf');
  const { addToast } = useToast();

  useEffect(() => {
    fetchFaculty();
  }, []);

  useEffect(() => {
    const handleFormatChange = () => setDefaultFormat(localStorage.getItem('exportFormat') || 'pdf');
    window.addEventListener('exportformatchange', handleFormatChange);
    return () => window.removeEventListener('exportformatchange', handleFormatChange);
  }, []);

  const fetchFaculty = async () => {
    try {
      const data = await api.get('/faculty?per_page=1000');
      setFacultyList(data.items || []);
    } catch (error) {
      console.error('Failed to fetch faculty:', error);
      addToast('Failed to load faculty list', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (id, format, name) => {
    addToast(`Generating ${format.toUpperCase()} for ${name}...`, 'info');
    try {
      await api.download(`/download/${format}/${id}`, `${name.replace(/ /g, '_')}_Timetable.${format === 'excel' ? 'xlsx' : 'pdf'}`);
      addToast(`Downloaded ${format.toUpperCase()} for ${name}`, 'success');
    } catch (error) {
      console.error(`Failed to download ${format}:`, error);
      addToast(`Failed to download ${format.toUpperCase()}`, 'error');
    }
  };

  const handleDownloadAll = async () => {
    addToast(`Generating all faculty timetables as ${defaultFormat.toUpperCase()}... This might take a moment.`, 'info');
    try {
      await api.download(`/download/${defaultFormat}/all`, `All_Faculty_Timetables.${defaultFormat === 'excel' ? 'xlsx' : 'pdf'}`);
      addToast(`Successfully downloaded all timetables!`, 'success');
    } catch (error) {
      console.error(`Failed to download all as ${defaultFormat}:`, error);
      addToast(`Failed to generate ${defaultFormat.toUpperCase()} for all faculty`, 'error');
    }
  };

  const columns = [
    { 
      header: 'Faculty Name', 
      render: (row) => (
        <div className="flex items-center gap-3">
          <div style={{ backgroundColor: 'rgba(37, 99, 235, 0.1)', padding: '8px', borderRadius: '8px', color: 'var(--primary)' }}>
            <FileText size={16} />
          </div>
          <span style={{ fontWeight: 500 }}>{row.faculty_name}</span>
        </div>
      )
    },
    { header: 'Total Classes', accessor: 'total_classes' },
    { header: 'Weekly Hours', accessor: 'weekly_hours' },
  ];

  const renderActions = (row) => (
    <div className="flex justify-end gap-2">
      <Button variant={defaultFormat === 'pdf' ? 'primary' : 'outline'} size="sm" icon={DownloadIcon} onClick={() => handleDownload(row.id, 'pdf', row.faculty_name)}>
        PDF
      </Button>
      <Button variant={defaultFormat === 'xlsx' ? 'primary' : 'outline'} size="sm" icon={FileSpreadsheet} onClick={() => handleDownload(row.id, 'excel', row.faculty_name)}>
        Excel
      </Button>
    </div>
  );

  const filteredDownloads = facultyList.filter(d => d.faculty_name.toLowerCase().includes(searchTerm.toLowerCase()));

  return (
    <div className="max-w-6xl mx-auto">
      <div className="dashboard-header mb-6">
        <h1 className="page-title">Downloads</h1>
        <p className="page-subtitle">Access and download previously generated individual faculty timetables.</p>
      </div>

      <Card padding="none">
        <div className="flex justify-between items-center p-4 border-b border-[var(--border)]">
          <div className="topbar-search" style={{ width: '300px' }}>
            <Search size={18} className="search-icon" />
            <input 
              type="text" 
              placeholder="Search faculty name..." 
              className="search-input"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="flex gap-3">
            <Button variant="secondary" icon={DownloadIcon} onClick={handleDownloadAll}>
              Download All {defaultFormat === 'xlsx' ? 'Excel' : 'PDF'}
            </Button>
          </div>
        </div>
        <div className="p-4">
          <Table 
            columns={columns} 
            data={filteredDownloads} 
            actions={renderActions}
          />
        </div>
      </Card>
    </div>
  );
};

export default Downloads;
