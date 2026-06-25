import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';

const ToastContext = createContext(null);

const TOAST_COLORS = {
  success: {
    background: 'linear-gradient(135deg, rgba(5,150,105,0.95), rgba(16,185,129,0.95))',
    border: 'rgba(16,185,129,0.4)',
    icon: '✓',
    iconBg: 'rgba(16,185,129,0.2)',
  },
  error: {
    background: 'linear-gradient(135deg, rgba(185,28,28,0.95), rgba(239,68,68,0.95))',
    border: 'rgba(239,68,68,0.4)',
    icon: '✕',
    iconBg: 'rgba(239,68,68,0.2)',
  },
  info: {
    background: 'linear-gradient(135deg, rgba(8,145,178,0.95), rgba(6,182,212,0.95))',
    border: 'rgba(6,182,212,0.4)',
    icon: 'ℹ',
    iconBg: 'rgba(6,182,212,0.2)',
  },
  warning: {
    background: 'linear-gradient(135deg, rgba(180,83,9,0.95), rgba(245,158,11,0.95))',
    border: 'rgba(245,158,11,0.4)',
    icon: '⚠',
    iconBg: 'rgba(245,158,11,0.2)',
  },
};

const INJECT_STYLES = `
  @keyframes toastSlideIn {
    from { opacity: 0; transform: translateX(120%) scale(0.92); }
    to   { opacity: 1; transform: translateX(0)    scale(1); }
  }
  @keyframes toastFadeOut {
    from { opacity: 1; transform: translateX(0)    scale(1); max-height: 120px; margin-bottom: 10px; }
    to   { opacity: 0; transform: translateX(120%) scale(0.92); max-height: 0; margin-bottom: 0; }
  }
  @keyframes toastProgress {
    from { width: 100%; }
    to   { width: 0%; }
  }
`;

if (typeof document !== 'undefined' && !document.getElementById('toast-notification-styles')) {
  const style = document.createElement('style');
  style.id = 'toast-notification-styles';
  style.textContent = INJECT_STYLES;
  document.head.appendChild(style);
}

let toastIdCounter = 0;

function Toast({ id, message, type, onDismiss }) {
  const [exiting, setExiting] = useState(false);
  const timerRef = useRef(null);
  const colors = TOAST_COLORS[type] || TOAST_COLORS.info;

  const dismiss = useCallback(() => {
    setExiting(true);
    setTimeout(() => onDismiss(id), 350);
  }, [id, onDismiss]);

  useEffect(() => {
    timerRef.current = setTimeout(dismiss, 4000);
    return () => clearTimeout(timerRef.current);
  }, [dismiss]);

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '12px 16px',
        borderRadius: '14px',
        background: colors.background,
        border: `1px solid ${colors.border}`,
        boxShadow: '0 8px 32px rgba(0,0,0,0.4), 0 2px 8px rgba(0,0,0,0.3)',
        backdropFilter: 'blur(12px)',
        minWidth: '280px',
        maxWidth: '380px',
        position: 'relative',
        overflow: 'hidden',
        cursor: 'pointer',
        animation: exiting
          ? 'toastFadeOut 0.35s ease-in forwards'
          : 'toastSlideIn 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) forwards',
        marginBottom: '10px',
      }}
      onClick={dismiss}
    >
      {/* Icon */}
      <div style={{
        width: 28,
        height: 28,
        borderRadius: '50%',
        background: colors.iconBg,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '14px',
        fontWeight: 'bold',
        color: '#fff',
        flexShrink: 0,
      }}>
        {colors.icon}
      </div>

      {/* Message */}
      <span style={{
        color: '#fff',
        fontSize: '13px',
        fontWeight: '500',
        lineHeight: '1.4',
        flex: 1,
      }}>
        {message}
      </span>

      {/* Close button */}
      <button
        onClick={(e) => { e.stopPropagation(); dismiss(); }}
        style={{
          background: 'none',
          border: 'none',
          color: 'rgba(255,255,255,0.7)',
          cursor: 'pointer',
          fontSize: '16px',
          lineHeight: '1',
          padding: '0 2px',
          flexShrink: 0,
        }}
      >
        ×
      </button>

      {/* Progress bar */}
      <div style={{
        position: 'absolute',
        bottom: 0,
        left: 0,
        height: '2px',
        background: 'rgba(255,255,255,0.4)',
        animation: `toastProgress 4s linear forwards`,
        borderRadius: '0 0 14px 14px',
      }} />
    </div>
  );
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const showToast = useCallback((message, type = 'info') => {
    const id = ++toastIdCounter;
    setToasts((prev) => [...prev, { id, message, type }]);
  }, []);

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      {/* Toast container */}
      <div
        style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          zIndex: 99999,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-end',
          pointerEvents: 'none',
        }}
      >
        {toasts.map((toast) => (
          <div key={toast.id} style={{ pointerEvents: 'auto' }}>
            <Toast
              id={toast.id}
              message={toast.message}
              type={toast.type}
              onDismiss={dismissToast}
            />
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    // Return a no-op if used outside provider
    return { showToast: () => {} };
  }
  return ctx;
}