import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Lock, User, Eye, EyeOff, Mail } from 'lucide-react';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import { useToast } from '../contexts/ToastContext';
import { useAuth } from '../contexts/AuthContext';

const CreateAccount = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({ fullName: '', username: '', password: '', confirmPassword: '' });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();
  const { addToast } = useToast();
  const { register } = useAuth();

  const handleTogglePassword = () => setShowPassword(!showPassword);

  const getPasswordStrength = (pass) => {
    if (!pass) return 0;
    let strength = 0;
    if (pass.length > 5) strength += 1;
    if (pass.length > 8) strength += 1;
    if (/[A-Z]/.test(pass)) strength += 1;
    if (/[0-9]/.test(pass)) strength += 1;
    return strength;
  };

  const strength = getPasswordStrength(formData.password);

  const validate = () => {
    const newErrors = {};
    if (!formData.fullName) newErrors.fullName = 'Full Name is required';
    if (!formData.username) newErrors.username = 'Username is required';
    if (!formData.password) newErrors.password = 'Password is required';
    else if (formData.password.length < 6) newErrors.password = 'Password must be at least 6 characters';
    if (formData.password !== formData.confirmPassword) newErrors.confirmPassword = 'Passwords must match';
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (validate()) {
      setIsSubmitting(true);
      const result = await register({
        name: formData.fullName,
        username: formData.username,
        password: formData.password,
        confirm_password: formData.confirmPassword
      });
      setIsSubmitting(false);

      if (result.success) {
        addToast('Account Created successfully. Please log in.', 'success');
        navigate('/login');
      } else {
        addToast(result.error || 'Registration failed', 'error');
        setErrors({ submit: result.error || 'Registration failed' });
      }
    }
  };

  return (
    <>
      <div className="auth-header" style={{ marginBottom: '1.5rem' }}>
        <h1 className="auth-title">Create Account</h1>
        <p className="auth-subtitle">Join the Faculty Timetable Extraction System</p>
      </div>

      <form onSubmit={handleSubmit}>
        <Input 
          label="Full Name" 
          placeholder="John Doe" 
          icon={User}
          value={formData.fullName}
          onChange={(e) => setFormData({...formData, fullName: e.target.value})}
          error={errors.fullName}
        />
        
        <Input 
          label="Username" 
          placeholder="johndoe123" 
          icon={Mail}
          value={formData.username}
          onChange={(e) => setFormData({...formData, username: e.target.value})}
          error={errors.username}
        />
        
        <div style={{ position: 'relative', marginBottom: formData.password ? '1.5rem' : '1rem' }}>
          <Input 
            label="Password" 
            type={showPassword ? 'text' : 'password'}
            placeholder="Create a strong password" 
            icon={Lock}
            value={formData.password}
            onChange={(e) => setFormData({...formData, password: e.target.value})}
            error={errors.password}
            style={{ marginBottom: 0 }}
          />
          <button 
            type="button" 
            onClick={handleTogglePassword}
            style={{ position: 'absolute', right: '10px', top: '34px', color: 'var(--text-tertiary)', background: 'none', border: 'none', cursor: 'pointer' }}
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
          
          {formData.password && (
            <div style={{ display: 'flex', gap: '4px', marginTop: '8px' }}>
              <div style={{ height: '4px', flex: 1, borderRadius: '2px', backgroundColor: strength >= 1 ? 'var(--error)' : 'var(--border)' }}></div>
              <div style={{ height: '4px', flex: 1, borderRadius: '2px', backgroundColor: strength >= 2 ? 'var(--warning)' : 'var(--border)' }}></div>
              <div style={{ height: '4px', flex: 1, borderRadius: '2px', backgroundColor: strength >= 3 ? 'var(--success)' : 'var(--border)' }}></div>
              <div style={{ height: '4px', flex: 1, borderRadius: '2px', backgroundColor: strength >= 4 ? 'var(--success)' : 'var(--border)' }}></div>
            </div>
          )}
        </div>

        <Input 
          label="Confirm Password" 
          type={showPassword ? 'text' : 'password'}
          placeholder="Confirm your password" 
          icon={Lock}
          value={formData.confirmPassword}
          onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
          error={errors.confirmPassword}
        />

        <Button type="submit" fullWidth style={{ marginTop: '0.5rem' }} disabled={isSubmitting}>
          {isSubmitting ? 'Creating Account...' : 'Create Account'}
        </Button>
      </form>

      <div style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
        Already have an account? <Link to="/login">Back to Login</Link>
      </div>
    </>
  );
};

export default CreateAccount;
