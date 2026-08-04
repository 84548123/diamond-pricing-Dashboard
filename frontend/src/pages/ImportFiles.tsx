import React, { useState } from 'react';
import { Upload, FileSpreadsheet, CheckCircle2, AlertCircle, RefreshCw, ArrowRight, Database, KeyRound } from 'lucide-react';
import { uploadAnyFiles, generateSampleData, getAdminKey, setAdminKey, getImportStatus } from '../api/client';
import { useNavigate } from 'react-router-dom';

export const ImportFiles: React.FC = () => {
  const navigate = useNavigate();
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [adminKey, setAdminKeyValue] = useState(getAdminKey());
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const upload = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!files.length) { setError('Choose the VDB, inventory, and sales files. They can be selected in any order.'); return; }
    if (!adminKey.trim()) { setError('Enter the administrator key to replace shared dashboard data.'); return; }
    setAdminKey(adminKey);
    setUploading(true); setError(null); setMessage('Inspecting file columns and building your dashboard…');
    try {
      const result = await uploadAnyFiles(files);
      if (result.status === 'processing') {
        setMessage(result.message);
        const until = Date.now() + 20 * 60 * 1000;
        while (Date.now() < until) {
          await new Promise(resolve => setTimeout(resolve, 3000));
          const status = await getImportStatus();
          setMessage(status.import_message || 'Building your dashboard…');
          if (status.import_state === 'complete') {
            const sources = Object.entries(status.detected_sources || {}).map(([name, count]) => `${name.toUpperCase()}: ${Number(count).toLocaleString()}`).join(' · ');
            setMessage(`${status.import_message} ${sources}`);
            setTimeout(() => navigate('/'), 1100);
            return;
          }
          if (status.import_state === 'failed') throw new Error(status.import_message || 'The files could not be processed.');
        }
        throw new Error('Analysis is still running. Keep this page open and refresh shortly to check the dashboard.');
      }
      const sources = Object.entries(result.detected_sources || {}).map(([name, count]) => `${name.toUpperCase()}: ${Number(count).toLocaleString()}`).join(' · ');
      setMessage(`${result.message} ${sources}`);
      setTimeout(() => navigate('/'), 1100);
    } catch (err: any) { setError(err.response?.data?.detail || err.message || 'The files could not be processed.'); }
    finally { setUploading(false); }
  };

  const sample = async () => {
    if (!adminKey.trim()) { setError('Enter the administrator key before generating shared sample data.'); return; }
    setAdminKey(adminKey);
    setGenerating(true); setError(null);
    try { await generateSampleData(1500000, 40000); navigate('/'); }
    catch (err: any) { setError(err.response?.data?.detail || err.message || 'Sample data could not be generated.'); }
    finally { setGenerating(false); }
  };

  return <div className="max-w-5xl mx-auto p-6 text-white animate-fade-in">
    <header className="text-center max-w-3xl mx-auto mb-8"><div className="inline-flex p-3 rounded-2xl bg-brand-500/20 text-brand-400 mb-3"><Database className="w-8 h-8" /></div><h1 className="text-3xl font-black">Build your intelligence dashboard</h1><p className="text-sm text-slate-400 mt-2">Upload supplier exports in any order. The system recognises VDB market, inventory, and sales files from their columns—rather than their file names.</p></header>
    <form onSubmit={upload} className="rounded-2xl border border-white/10 bg-slate-900/80 p-6">
      <input id="any-file" className="hidden" type="file" multiple accept=".csv,.xlsx,.xlsm" onChange={event => setFiles(Array.from(event.target.files || []))} />
      <label htmlFor="any-file" className="block cursor-pointer rounded-2xl border-2 border-dashed border-cyan-400/30 bg-cyan-500/5 px-6 py-10 text-center hover:bg-cyan-500/10"><FileSpreadsheet className="mx-auto h-9 w-9 text-cyan-300" /><p className="mt-3 font-bold">Choose files to analyse</p><p className="mt-1 text-xs text-slate-400">CSV or XLSX · multiple files · any order</p></label>
      {files.length > 0 && <div className="mt-4 grid gap-2 sm:grid-cols-2">{files.map(file => <div key={`${file.name}-${file.size}`} className="flex items-center gap-2 rounded-lg bg-slate-800 px-3 py-2 text-xs"><FileSpreadsheet className="h-4 w-4 text-cyan-300" /><span className="truncate">{file.name}</span><span className="ml-auto text-slate-500">{Math.ceil(file.size / 1024).toLocaleString()} KB</span></div>)}</div>}
      <label className="mt-4 flex items-center gap-3 rounded-xl border border-amber-400/20 bg-amber-400/5 px-4 py-3 text-xs">
        <KeyRound className="h-4 w-4 shrink-0 text-amber-300" />
        <span className="shrink-0 font-bold text-amber-100">Administrator key</span>
        <input value={adminKey} onChange={event => setAdminKeyValue(event.target.value)} type="password" autoComplete="current-password" placeholder="Required to upload or generate data" className="min-w-0 flex-1 bg-transparent text-white outline-none placeholder:text-slate-500" />
      </label>
      <p className="mt-2 text-[11px] text-slate-500">Dashboard viewing is public. This key is kept only for this browser session and protects shared data changes.</p>
      <div className="mt-5 flex flex-col gap-4 md:flex-row md:items-center md:justify-between"><div><h2 className="font-bold">Automatic source detection</h2><p className="text-xs text-slate-400 mt-1">Recognises VDB/Evermine, current inventory/Diamax, and sales/invoice reports using headers such as Stone ID, Packet, Invoice, Price, Shape, Carat, Color and Clarity.</p></div><button disabled={uploading || generating} className="flex shrink-0 items-center justify-center gap-2 rounded-xl bg-brand-500 px-6 py-3 text-xs font-black hover:bg-brand-400 disabled:opacity-50">{uploading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}{uploading ? 'Building dashboard…' : 'Build dashboard'}<ArrowRight className="w-4 h-4" /></button></div>
      {message && <p className="mt-4 flex gap-2 text-xs text-emerald-300"><CheckCircle2 className="w-4 h-4 shrink-0" />{message}</p>}{error && <p className="mt-4 flex gap-2 text-xs text-rose-300"><AlertCircle className="w-4 h-4 shrink-0" />{error}</p>}
    </form>
    <div className="mt-5 flex items-center justify-between rounded-xl border border-emerald-500/20 bg-emerald-950/30 p-4"><p className="text-xs text-slate-300">Want to explore first? Generate test data and see the pricing workflow.</p><button onClick={sample} disabled={uploading || generating} className="text-xs font-bold text-emerald-300 hover:text-emerald-200">{generating ? 'Generating…' : 'Use sample data'}</button></div>
  </div>;
};
