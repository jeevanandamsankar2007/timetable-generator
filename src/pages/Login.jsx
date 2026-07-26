import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Lock, User, Eye, EyeOff } from 'lucide-react';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import { useToast } from '../contexts/ToastContext';
import { useAuth } from '../contexts/AuthContext';

const Login = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();
  const { addToast } = useToast();
  const { login } = useAuth();

  const handleTogglePassword = () => setShowPassword(!showPassword);

  const validate = () => {
    const newErrors = {};
    if (!formData.username) newErrors.username = 'Username is required';
    if (!formData.password) newErrors.password = 'Password is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (validate()) {
      setIsSubmitting(true);
      const result = await login(formData.username, formData.password);
      setIsSubmitting(false);
      
      if (result.success) {
        addToast('Login Successful', 'success');
        navigate('/');
      } else {
        addToast(result.error || 'Login failed', 'error');
        setErrors({ submit: result.error || 'Login failed' });
      }
    }
  };

  return (
    <>
      <div className="auth-header">
        <div className="auth-logo">
          <LayoutDashboard size={48} />
        </div>
        <h1 className="auth-title">Faculty Timetable Extraction System</h1>
        <p className="auth-subtitle">Extract Individual Faculty Timetables from Master Timetables</p>
      </div>

      <form onSubmit={handleSubmit}>
        <Input 
          label="Username" 
          placeholder="Enter your username" 
          icon={User}
          value={formData.username}
          onChange={(e) => setFormData({...formData, username: e.target.value})}
          error={errors.username}
        />
        
        <div style={{ position: 'relative' }}>
          <Input 
            label="Password" 
            type={showPassword ? 'text' : 'password'}
            placeholder="Enter your password" 
            icon={Lock}
            value={formData.password}
            onChange={(e) => setFormData({...formData, password: e.target.value})}
            error={errors.password}
          />
          <button 
            type="button" 
            onClick={handleTogglePassword}
            style={{ position: 'absolute', right: '10px', top: '34px', color: 'var(--text-tertiary)', background: 'none', border: 'none', cursor: 'pointer' }}
            title={showPassword ? "Hide Password" : "Show Password"}
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        </div>

        <div className="flex items-center justify-between" style={{ marginBottom: '1.5rem', marginTop: '0.5rem' }}>
          <label className="flex items-center" style={{ gap: '0.5rem', fontSize: '0.875rem', cursor: 'pointer' }}>
            <input type="checkbox" />
            <span style={{ color: 'var(--text-secondary)' }}>Remember Me</span>
          </label>
          <a href="#" style={{ fontSize: '0.875rem' }}>Forgot password?</a>
        </div>

        <Button type="submit" fullWidth disabled={isSubmitting}>
          {isSubmitting ? 'Logging in...' : 'Login'}
        </Button>
      </form>

      <div style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
        Don't have an account? <Link to="/register">Create Account</Link>
      </div>
    </>
  );
};

export default Login;
