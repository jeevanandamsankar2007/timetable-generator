import React, { useState, useEffect } from 'react';
import { FileText, Users, Calendar, CheckCircle, Clock } from 'lucide-react';
import Card from '../components/ui/Card';
import Modal from '../components/ui/Modal';
import { api } from '../lib/api';
import './Dashboard.css';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Faculty Modal State
  const [isFacultyModalOpen, setIsFacultyModalOpen] = useState(false);
  const [facultyList, setFacultyList] = useState([]);
  const [loadingFaculty, setLoadingFaculty] = useState(false);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await api.get('/dashboard/statistics');
        setStats(data);
      } catch (error) {
        console.error('Failed to fetch dashboard stats:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  const handleFacultyCardClick = async () => {
    setIsFacultyModalOpen(true);
    if (facultyList.length === 0) {
      setLoadingFaculty(true);
      try {
        const data = await api.get('/faculty?per_page=1000');
        setFacultyList(data.items || []);
      } catch (error) {
        console.error('Failed to fetch faculty list:', error);
      } finally {
        setLoadingFaculty(false);
      }
    }
  };

  if (loading) {
    return <div className="p-8 text-center">Loading dashboard...</div>;
  }

  const statCards = [
    { label: 'Total Uploaded PDFs', value: stats?.total_pdfs || 0, icon: FileText, color: 'var(--primary)' },
    { label: 'Total Faculty', value: stats?.total_faculty || 0, icon: Users, color: 'var(--success)', onClick: handleFacultyCardClick },
    { label: 'Total Classes', value: stats?.total_classes || 0, icon: Calendar, color: 'var(--warning)' },
    { label: 'Generated Timetables', value: stats?.total_timetables || 0, icon: CheckCircle, color: '#8B5CF6' },
  ];

  return (
    <div className="dashboard-page">
      <div className="dashboard-header mb-6">
        <h1 className="page-title">Dashboard Overview</h1>
        <p className="page-subtitle">Welcome back! Here is a summary of the system activity.</p>
      </div>

      <div className="stats-grid mb-8">
        {statCards.map((stat, idx) => (
          <Card 
            key={idx} 
            hover 
            padding="sm" 
            className={`stat-card ${stat.onClick ? 'cursor-pointer' : ''}`}
            onClick={stat.onClick}
          >
            <div className="stat-icon-wrapper" style={{ backgroundColor: `${stat.color}15`, color: stat.color }}>
              <stat.icon size={24} />
            </div>
            <div className="stat-info">
              <h3 className="stat-value">{stat.value}</h3>
              <p className="stat-label">{stat.label}</p>
            </div>
          </Card>
        ))}
      </div>

      <div className="dashboard-grid">
        <Card title="Recent Activity" className="flex-col h-full">
          <div className="card-header border-b">
            <h2 className="card-title flex items-center gap-2">
              <Clock size={18} /> Recent Uploads
            </h2>
          </div>
          <div className="activity-list p-4">
            {stats?.recent_uploads?.length > 0 ? (
              stats.recent_uploads.map((upload, idx) => (
                <div key={idx} className="activity-item" style={{ marginBottom: '1rem' }}>
                  <div className="activity-bullet" style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--primary)', marginTop: 6, marginRight: 12 }}></div>
                  <div className="activity-content">
                    <p className="activity-action" style={{ fontWeight: 500 }}>Uploaded {upload.filename}</p>
                    <p className="activity-meta" style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                      Status: {upload.status} • {new Date(upload.upload_date).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <p style={{ color: 'var(--text-secondary)' }}>No recent uploads.</p>
            )}
          </div>
        </Card>

        <Card title="Quick Actions" className="flex-col h-full">
           <div className="card-header border-b">
            <h2 className="card-title">Quick Actions</h2>
          </div>
          <div className="quick-actions-grid p-4">
             <button className="quick-action-btn" onClick={() => window.location.href = '/upload'}>
                <FileText size={24} />
                <span>Upload Master Timetable</span>
             </button>
             <button className="quick-action-btn outline" onClick={() => window.location.href = '/faculty'}>
                <Users size={24} />
                <span>Search Faculty</span>
             </button>
          </div>
        </Card>
      </div>

      {/* Faculty List Modal */}
      <Modal 
        isOpen={isFacultyModalOpen} 
        onClose={() => setIsFacultyModalOpen(false)} 
        title="Faculty List"
        contentClassName="faculty-list-modal-light"
      >
        <div style={{ maxHeight: '60vh', overflowY: 'auto', padding: '0.5rem' }}>
          {loadingFaculty ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>Loading faculty...</div>
          ) : facultyList.length > 0 ? (
            <ul style={{ listStyleType: 'none', padding: 0, margin: 0 }}>
              {facultyList.map(faculty => (
                <li 
                  key={faculty.id} 
                  style={{ 
                    padding: '0.75rem', 
                    borderBottom: '1px solid var(--border)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem'
                  }}
                >
                  <div style={{
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    backgroundColor: 'var(--primary)',
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 'bold',
                    fontSize: '14px'
                  }}>
                    {faculty.faculty_name ? faculty.faculty_name.charAt(0) : '?'}
                  </div>
                  <div>
                    <div style={{ fontWeight: 500, color: '#000' }}>{faculty.faculty_name || ''}</div>
                    {faculty.department && <div style={{ fontSize: '12px', color: '#555' }}>{faculty.department}</div>}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>No faculty found.</div>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default Dashboard;
