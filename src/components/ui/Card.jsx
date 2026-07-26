import React from 'react';
import './Card.css';

const Card = ({ children, className = '', padding = 'md', hover = false, ...props }) => {
  const classes = [
    'card',
    `card-p-${padding}`,
    hover ? 'card-hover' : '',
    className
  ].filter(Boolean).join(' ');

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};

export default Card;
