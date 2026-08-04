import React, { useEffect } from 'react';
import { X } from 'lucide-react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  fullScreen?: boolean;
}

export const Modal: React.FC<ModalProps> = ({ isOpen, onClose, title, children, fullScreen = false }) => {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => { document.body.style.overflow = 'unset'; };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
      <div className="absolute inset-0 bg-dark-950/80 backdrop-blur-sm transition-opacity" onClick={onClose}></div>
      <div className={`relative w-full ${fullScreen ? 'h-full max-w-none' : 'max-w-4xl max-h-[90vh]'} glass-card flex flex-col animate-slide-up shadow-2xl`}>
        {title && (
          <div className="flex items-center justify-between p-4 border-b border-white/10 shrink-0">
            <h2 className="text-lg font-bold text-white">{title}</h2>
            <button onClick={onClose} className="p-1 text-slate-400 hover:text-white hover:bg-white/10 rounded transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>
        )}
        {!title && (
          <button onClick={onClose} className="absolute top-4 right-4 z-10 p-1.5 text-slate-400 hover:text-white hover:bg-white/10 rounded-full transition-colors bg-dark-900/50 backdrop-blur-md">
            <X className="w-5 h-5" />
          </button>
        )}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 custom-scrollbar">
          {children}
        </div>
      </div>
    </div>
  );
};
