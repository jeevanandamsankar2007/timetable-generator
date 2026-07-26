import React, { useEffect } from 'react';
import { CheckCircle, AlertTriangle, XCircle, X } from 'lucide-react';
import './Toast.css';

const Toast = ({ message, type = 'success', duration = 3000, onClose }) => {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  const icons = {
    success: <CheckCircle size={20} className="toast-icon toast-success-icon" />,
    warning: <AlertTriangle size={20} className="toast-icon toast-warning-icon" />,
    error: <XCircle size={20} className="toast-icon toast-error-icon" />
  };

  return (
    <div className={`toast animate-slide-right`}>
      {icons[type]}
      <span className="toast-message">{message}</span>
      <button onClick={onClose} className="toast-close">
        <X size={16} />
      </button>
    </div>
  );
};

export default Toast;
