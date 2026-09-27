// src/components/Button.jsx
import { forwardRef } from 'react'
import styles from './Button.module.css'

/**
 * variant: 'primary' | 'secondary' | 'danger'
 * size:    'md' (default) | 'sm'
 */
const Button = forwardRef(function Button(
  { children, variant = 'primary', size = 'md', disabled = false, onClick, type = 'button', className = '', ...rest },
  ref
) {
  return (
    <button
      ref={ref}
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={`${styles.btn} ${styles[variant]} ${styles[size]} ${className}`}
      {...rest}
    >
      {children}
    </button>
  )
})

export default Button
