import React, { useState } from 'react';
import { FileText, FileSpreadsheet } from 'lucide-react';
import * as api from '../../api/client';

export const ExportButtons = () => {
  const [loadingPdf, setLoadingPdf] = useState(false);
  const [loadingExcel, setLoadingExcel] = useState(false);

  const handleDownloadPdf = async () => {
    setLoadingPdf(true);
    try {
      await api.downloadPdf();
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingPdf(false);
    }
  };

  const handleDownloadExcel = async () => {
    setLoadingExcel(true);
    try {
      await api.downloadExcel();
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingExcel(false);
    }
  };

  return (
    <div className="flex items-center space-x-3">
      <button 
        onClick={handleDownloadExcel}
        disabled={loadingExcel}
        className="flex items-center px-4 py-2 bg-dark-800 hover:bg-dark-700 border border-white/10 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
      >
        {loadingExcel ? <div className="w-4 h-4 mr-2 border-2 border-slate-500 border-t-white rounded-full animate-spin"></div> : <FileSpreadsheet className="w-4 h-4 mr-2 text-emerald-400" />}
        Excel
      </button>
      <button 
        onClick={handleDownloadPdf}
        disabled={loadingPdf}
        className="flex items-center px-4 py-2 bg-brand-600 hover:bg-brand-500 border border-brand-500/50 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 shadow-[0_0_15px_rgba(99,102,241,0.3)]"
      >
        {loadingPdf ? <div className="w-4 h-4 mr-2 border-2 border-brand-200 border-t-white rounded-full animate-spin"></div> : <FileText className="w-4 h-4 mr-2" />}
        PDF Report
      </button>
    </div>
  );
};
