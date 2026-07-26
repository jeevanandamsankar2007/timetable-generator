import React, { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Upload, 
  Files, 
  Users, 
  Download, 
  Settings, 
  HelpCircle, 
  LogOut,
  Menu,
  Bell,
  Moon,
  Sun,
  User,
  Search,
  ChevronLeft
} from 'lucide-react';
import Modal from '../components/ui/Modal';
import './DashboardLayout.css';

const DashboardLayout = () => {
  const [isSidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(() => localStorage.getItem('theme') === 'dark');
  const [isHelpOpen, setHelpOpen] = useState(false);
  const navigate = useNavigate();

  const toggleSidebar = () => setSidebarCollapsed(!isSidebarCollapsed);

  React.useEffect(() => {
    const applyTheme = () => {
      const isDark = localStorage.getItem('theme') === 'dark';
      setIsDarkMode(isDark);
      if (isDark) {
        document.documentElement.setAttribute('data-theme', 'dark');
      } else {
        document.documentElement.removeAttribute('data-theme');
      }
    };
    
    // Apply on mount
    applyTheme();

    // Listen for changes from Settings page
    window.addEventListener('themechange', applyTheme);
    return () => window.removeEventListener('themechange', applyTheme);
  }, []);

  const toggleTheme = () => {
    const newTheme = !isDarkMode ? 'dark' : 'light';
    localStorage.setItem('theme', newTheme);
    window.dispatchEvent(new Event('themechange'));
  };

  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/upload', icon: Upload, label: 'Upload Timetable' },
    { path: '/files', icon: Files, label: 'Uploaded Files' },
    { path: '/faculty', icon: Users, label: 'Faculty Search' },
    { path: '/downloads', icon: Download, label: 'Downloads' },
    { path: '/settings', icon: Settings, label: 'Settings' },
  ];

  const handleLogout = () => {
    navigate('/login');
  };

  return (
    <div className="dashboard-layout">
      {/* Sidebar */}
      <aside className={`sidebar ${isSidebarCollapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-header">
          <div className="logo-container">
            <LayoutDashboard className="logo-icon" size={28} />
            {!isSidebarCollapsed && <span className="logo-text">Timetable Pro</span>}
          </div>
          <button className="collapse-btn" onClick={toggleSidebar}>
            {isSidebarCollapsed ? <Menu size={20} /> : <ChevronLeft size={20} />}
          </button>
        </div>

        <nav className="sidebar-nav">
          <ul>
            {navItems.map((item) => (
              <li key={item.path}>
                <NavLink 
                  to={item.path} 
                  className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                  title={isSidebarCollapsed ? item.label : ''}
                >
                  <item.icon size={20} />
                  {!isSidebarCollapsed && <span>{item.label}</span>}
                </NavLink>
              </li>
            ))}
          </ul>

          <div className="nav-divider"></div>

          <ul>
            <li>
              <button 
                className="nav-link w-full text-left" 
                onClick={() => setHelpOpen(true)}
                title={isSidebarCollapsed ? 'Help' : ''}
              >
                <HelpCircle size={20} />
                {!isSidebarCollapsed && <span>Help</span>}
              </button>
            </li>
            <li>
              <button 
                className="nav-link w-full text-left text-danger" 
                onClick={handleLogout}
                title={isSidebarCollapsed ? 'Logout' : ''}
              >
                <LogOut size={20} />
                {!isSidebarCollapsed && <span>Logout</span>}
              </button>
            </li>
          </ul>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {/* Top Navbar */}
        <header className="topbar">
          <div className="topbar-search">
            <Search size={18} className="search-icon" />
            <input type="text" placeholder="Global Search..." className="search-input" />
          </div>

          <div className="topbar-actions">
            <button className="action-btn" onClick={toggleTheme}>
              {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
            </button>
            <div className="user-profile">
              <div className="avatar">
                <User size={20} />
              </div>
              <div className="user-info">
                <span className="user-name">Admin User</span>
                <span className="user-role">Administrator</span>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="page-content animate-fade-in">
          <Outlet />
        </div>
      </main>

      <Modal 
        isOpen={isHelpOpen} 
        onClose={() => setHelpOpen(false)}
        title="Help & Information"
        contentClassName="help-modal-override"
      >
        <div className="flex flex-col gap-4" style={{ color: 'darkblue' }}>
          <div>
            <h4 style={{ color: 'darkblue', marginBottom: '0.5rem' }}>About Timetable Pro</h4>
            <p>
              Timetable Pro is an automated timetable extraction and generation system. It takes your master timetable PDF, intelligently processes and extracts the schedules for every department and class, and maps them to individual faculty members.
            </p>
          </div>
          <div>
            <h4 style={{ color: 'darkblue', marginBottom: '0.5rem' }}>How It Works</h4>
            <ul style={{ listStyleType: 'disc', paddingLeft: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              <li><strong>Upload:</strong> Navigate to "Upload Timetable" and upload your master PDF. Ensure the PDF contains the schedule grid and the subject master table.</li>
              <li><strong>Review & Approve:</strong> The system automatically extracts data using AI and OCR. You can review and edit any conflicts or warnings before approving.</li>
              <li><strong>Generate:</strong> Once approved, the system automatically builds conflict-free, beautifully formatted individual timetables for every faculty member.</li>
              <li><strong>Download:</strong> Go to the "Downloads" page to export individual timetables as PDF or Excel files, or download them all at once!</li>
            </ul>
          </div>
          <div style={{ marginTop: '1rem', borderTop: '1px solid darkblue', paddingTop: '1rem', fontSize: '0.875rem' }}>
            Version: 1.0.0
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default DashboardLayout;
