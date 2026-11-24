import React, { useState } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle, X, ShieldCheck } from 'lucide-react';
import { Modal } from '../../components/common/Modal';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Select } from '../../components/common/Select';
import { contractsApi } from '../../services/api';
import { Contract, ContractType } from '../../types';

interface ContractUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploaded: (contract: Contract) => void;
}

export const ContractUploadModal: React.FC<ContractUploadModalProps> = ({
  isOpen,
  onClose,
  onUploaded,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [contractType, setContractType] = useState<ContractType>('msa');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      validateAndSetFile(selected);
    }
  };

  const validateAndSetFile = (selected: File) => {
    setError(null);
    const validExtensions = ['.pdf', '.docx'];
    const hasValidExt = validExtensions.some(ext => selected.name.toLowerCase().endsWith(ext));
    if (!hasValidExt) {
      setError('Unsupported file type. Please upload a .pdf or .docx document.');
      return;
    }
    if (selected.size > 15 * 1024 * 1024) {
      setError('File size exceeds the 15 MB limit.');
      return;
    }
    setFile(selected);
    if (!title) {
      // Auto-populate title from filename
      const cleanName = selected.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' ');
      setTitle(cleanName);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a PDF or DOCX file to upload.');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      if (title) formData.append('title', title);
      if (description) formData.append('description', description);
      if (contractType) formData.append('contract_type', contractType);

      const created = await contractsApi.upload(formData);
      onUploaded(created);
      handleClose();
    } catch (err: any) {
      console.error('Backend upload error:', err);
      setError(err?.response?.data?.detail || 'File upload failed. Please verify format and size.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleClose = () => {
    setFile(null);
    setTitle('');
    setDescription('');
    setContractType('msa');
    setError(null);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Upload Legal Contract"
      subtitle="Supported formats: PDF and Word (.docx) up to 15 MB"
      maxWidth="lg"
      footer={
        <>
          <Button variant="ghost" onClick={handleClose} disabled={isUploading}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleSubmit}
            isLoading={isUploading}
            disabled={!file}
            leftIcon={<Upload className="w-4 h-4" />}
          >
            {isUploading ? 'Extracting & Ingesting...' : 'Upload & Process'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Drag and Drop Box */}
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-6 text-center transition-all ${
            dragActive
              ? 'border-brand-500 bg-brand-50/50'
              : file
              ? 'border-emerald-400 bg-emerald-50/20'
              : 'border-slate-300 hover:border-slate-400 bg-slate-50/50'
          }`}
        >
          {file ? (
            <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-emerald-200 shadow-xs">
              <div className="flex items-center gap-3 truncate">
                <div className="p-2 bg-emerald-100 text-emerald-700 rounded-lg shrink-0">
                  <FileText className="w-5 h-5" />
                </div>
                <div className="text-left truncate">
                  <p className="text-xs font-semibold text-slate-800 truncate">{file.name}</p>
                  <p className="text-[11px] text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setFile(null)}
                className="p-1 text-slate-400 hover:text-rose-500 rounded-md"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div>
              <div className="w-10 h-10 mx-auto rounded-full bg-brand-50 text-brand-600 flex items-center justify-center mb-2">
                <Upload className="w-5 h-5" />
              </div>
              <p className="text-xs font-semibold text-slate-800">
                Drag and drop your document here, or{' '}
                <label className="text-brand-600 hover:underline cursor-pointer">
                  browse file
                  <input
                    type="file"
                    className="hidden"
                    accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    onChange={handleFileChange}
                  />
                </label>
              </p>
              <p className="text-[11px] text-slate-400 mt-1">PDF or DOCX documents up to 15 MB</p>
            </div>
          )}
        </div>

        {/* Contract Title */}
        <Input
          label="Contract Title"
          required
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Master Services Agreement (Vendor 2026)"
        />

        {/* Contract Type & Description */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Select
            label="Contract Type"
            value={contractType}
            onChange={(e) => setContractType(e.target.value as ContractType)}
            options={[
              { value: 'msa', label: 'Master Services Agreement (MSA)' },
              { value: 'nda', label: 'Non-Disclosure Agreement (NDA)' },
              { value: 'dpa', label: 'Data Processing Addendum (DPA)' },
              { value: 'sla', label: 'Service Level Agreement (SLA)' },
              { value: 'vendor', label: 'Vendor Agreement' },
              { value: 'license', label: 'Software License' },
              { value: 'employment', label: 'Employment Agreement' },
              { value: 'other', label: 'Other Agreement' },
            ]}
          />

          <Input
            label="Description / Purpose (Optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g. IT services renewal"
          />
        </div>

        {/* Privacy & Anti-Path Traversal Guarantee */}
        <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-[11px] text-slate-500 flex items-start gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
          <span>
            <strong>Local Processing Guarantee:</strong> Files are stored with randomized UUID filenames in tenant-isolated directories. Text extraction is performed entirely in-process using PyMuPDF and python-docx without external AI exposure.
          </span>
        </div>
      </form>
    </Modal>
  );
};
