import React from 'react';
import { Outlet } from 'react-router-dom';
import './AuthLayout.css';

const AuthLayout = () => {
  return (
    <div className="auth-layout animate-fade-in">
      <div className="auth-container">
        <div className="auth-card animate-slide-up">
          <Outlet />
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;
