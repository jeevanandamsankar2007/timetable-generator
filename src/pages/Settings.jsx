import React, { useState } from 'react';
import { User, Lock, Palette, Globe, Download, Bell, Shield } from 'lucide-react';
import Card from '../components/ui/Card';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import { useToast } from '../contexts/ToastContext';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../lib/api';
import './Settings.css';

const Settings = () => {
  const [activeTab, setActiveTab] = useState('profile');
  
  // Password change state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { currentUser } = useAuth();
  const { addToast } = useToast();

  const handleSave = (e) => {
    e.preventDefault();
    addToast('Settings saved successfully (Mock)', 'success');
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    if (!currentPassword || !newPassword || !confirmPassword) {
      addToast('Please fill in all password fields', 'error');
      return;
    }
    if (newPassword !== confirmPassword) {
      addToast('New passwords do not match', 'error');
      return;
    }
    if (newPassword.length < 6) {
      addToast('New password must be at least 6 characters', 'error');
      return;
    }

    try {
      setIsSubmitting(true);
      await api.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword
      });
      
      addToast('Password updated successfully', 'success');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      addToast(error.message || 'Failed to update password', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const tabs = [
    { id: 'profile', label: 'User Profile', icon: User },
    { id: 'security', label: 'Security & Password', icon: Lock },
    { id: 'preferences', label: 'Preferences', icon: Palette },
  ];

  return (
    <div className="settings-page">
      <div className="dashboard-header mb-6">
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle">Manage your account settings and preferences.</p>
      </div>

      <div className="settings-layout">
        <Card padding="none" className="settings-sidebar">
          <ul className="settings-nav">
            {tabs.map(tab => (
              <li key={tab.id}>
                <button 
                  className={`settings-nav-btn ${activeTab === tab.id ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  <tab.icon size={18} />
                  <span>{tab.label}</span>
                </button>
              </li>
            ))}
          </ul>
        </Card>

        <div className="settings-content">
          {activeTab === 'profile' && (
            <Card title="User Profile">
              <div className="card-header border-b mb-6">
                <h2 className="card-title flex items-center gap-2">
                  <User size={20} /> User Profile
                </h2>
              </div>
              <form onSubmit={handleSave} className="p-6 pt-0">
                <div className="avatar-upload mb-6">
                  <div className="avatar-preview">
                    <User size={40} color="white" />
                  </div>
                  <div>
                    <Button variant="outline" type="button" size="sm">Change Avatar</Button>
                    <p className="mt-2 text-tertiary" style={{ fontSize: '0.75rem' }}>JPG, GIF or PNG. Max size of 800K</p>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <Input label="Name" defaultValue={currentUser?.name || currentUser?.username || 'User'} />
                  <Input label="Username" defaultValue={currentUser?.username || 'user'} disabled />
                </div>
                <Input label="Email Address" defaultValue={`${currentUser?.username || 'user'}@university.edu`} />
                <Input label="Role" defaultValue="Administrator" disabled />
                
                <div className="mt-6 flex justify-end">
                  <Button type="submit">Save Changes</Button>
                </div>
              </form>
            </Card>
          )}

          {activeTab === 'security' && (
             <Card title="Security">
              <div className="card-header border-b mb-6">
                <h2 className="card-title flex items-center gap-2">
                  <Shield size={20} /> Change Password
                </h2>
              </div>
              <form onSubmit={handlePasswordSubmit} className="p-6 pt-0">
                <Input 
                  label="Current Password" 
                  type="password" 
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                />
                <Input 
                  label="New Password" 
                  type="password" 
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                />
                <Input 
                  label="Confirm New Password" 
                  type="password" 
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
                
                <div className="mt-6 flex justify-end">
                  <Button type="submit" disabled={isSubmitting}>
                    {isSubmitting ? 'Updating...' : 'Update Password'}
                  </Button>
                </div>
              </form>
            </Card>
          )}

          {activeTab === 'preferences' && (
            <Card title="Preferences">
              <div className="card-header border-b mb-6">
                <h2 className="card-title flex items-center gap-2">
                  <Palette size={20} /> Application Preferences
                </h2>
              </div>
              <form onSubmit={handleSave} className="p-6 pt-0">
                <div className="form-group mb-6">
                  <label className="input-label">Theme</label>
                  <select 
                    className="input-field mt-2"
                    defaultValue={localStorage.getItem('theme') || 'light'}
                    onChange={(e) => {
                      const newTheme = e.target.value;
                      if (newTheme === 'dark' || newTheme === 'light') {
                        localStorage.setItem('theme', newTheme);
                        window.dispatchEvent(new Event('themechange'));
                      }
                    }}
                  >
                    <option value="light">Light Mode</option>
                    <option value="dark">Dark Mode</option>
                  </select>
                </div>
                

                <div className="form-group mb-6">
                  <label className="input-label">Default Export Format</label>
                  <select 
                    className="input-field mt-2" 
                    defaultValue={localStorage.getItem('exportFormat') || 'pdf'}
                    onChange={(e) => {
                      localStorage.setItem('exportFormat', e.target.value);
                      window.dispatchEvent(new Event('exportformatchange'));
                    }}
                  >
                    <option value="pdf">PDF Document</option>
                    <option value="xlsx">Excel Spreadsheet</option>
                  </select>
                </div>
                
                <div className="mt-6 flex justify-end">
                  <Button type="submit">Save Preferences</Button>
                </div>
              </form>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default Settings;
