import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  FileText, 
  Upload, 
  Search, 
  Filter, 
  Eye, 
  Trash2, 
  Play, 
  Sparkles,
  Calendar, 
  Layers,
  ArrowUpDown
} from 'lucide-react';
import { PageHeader } from '../../components/common/PageHeader';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { EmptyState } from '../../components/common/EmptyState';
import { ContractUploadModal } from './ContractUploadModal';
import { contractsApi } from '../../services/api';
import { DEMO_CONTRACTS } from '../../services/mockData';
import { Contract, ContractType, ContractStatus } from '../../types';

export const ContractsPage: React.FC = () => {
  const navigate = useNavigate();
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [search, setSearch] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadContracts = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await contractsApi.list({
          search: search || undefined,
          contract_type: selectedType !== 'all' ? selectedType : undefined,
          status: selectedStatus !== 'all' ? selectedStatus : undefined,
        });
        const list = res.items || res.contracts || [];
        setContracts(list);
      } catch (err: any) {
        console.error('Backend list contracts error:', err);
        setError('Failed to load contracts from backend.');
        setContracts([]);
      } finally {
        setLoading(false);
      }
    };

    loadContracts();
  }, [search, selectedType, selectedStatus]);

  const handleContractUploaded = (newContract: Contract) => {
    setContracts((prev) => [newContract, ...prev]);
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this contract and all extracted clauses?')) {
      return;
    }
    try {
      await contractsApi.delete(id);
    } catch (err) {
      console.warn('Backend delete simulation:', err);
    }
    setContracts((prev) => prev.filter((c) => c.id !== id));
  };

  const handleRowClick = (contractId: string) => {
    navigate(`/contracts/${contractId}`);
  };

  // Filter local state if search query entered
  const filteredContracts = contracts.filter((c) => {
    const matchesSearch = c.title.toLowerCase().includes(search.toLowerCase()) ||
      (c.description && c.description.toLowerCase().includes(search.toLowerCase()));
    const matchesType = selectedType === 'all' || c.contract_type === selectedType;
    const matchesStatus = selectedStatus === 'all' || c.status === selectedStatus;
    return matchesSearch && matchesType && matchesStatus;
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Header */}
      <PageHeader
        title="Contract Inventory"
        subtitle="Manage, inspect, and analyze legal agreements ingested across your organization."
        action={
          <Button
            variant="primary"
            onClick={() => setIsUploadModalOpen(true)}
            leftIcon={<Upload className="w-4 h-4" />}
          >
            Upload Contract
          </Button>
        }
      />

      {/* Filter and Search Bar */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          {/* Search */}
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search contracts by title..."
              className="w-full pl-9 pr-3.5 py-2 text-xs rounded-lg border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
            />
          </div>

          {/* Dropdown Filters */}
          <div className="flex items-center gap-2.5 w-full sm:w-auto">
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="text-xs px-3 py-2 rounded-lg border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
            >
              <option value="all">All Contract Types</option>
              <option value="msa">MSA (Master Services)</option>
              <option value="nda">NDA (Confidentiality)</option>
              <option value="dpa">DPA (Data Processing)</option>
              <option value="sla">SLA (Service Level)</option>
              <option value="vendor">Vendor Agreement</option>
              <option value="license">Software License</option>
            </select>

            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="text-xs px-3 py-2 rounded-lg border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
            >
              <option value="all">All Statuses</option>
              <option value="active">Active</option>
              <option value="under_review">Under Review</option>
              <option value="draft">Draft</option>
              <option value="expired">Expired</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Contracts Table */}
      {loading ? (
        <Card className="p-12 text-center text-xs text-slate-500">
          <div className="inline-block animate-spin w-6 h-6 border-2 border-brand-600 border-t-transparent rounded-full mb-3" />
          <p>Loading organization contracts...</p>
        </Card>
      ) : error ? (
        <Card className="p-8 text-center text-xs text-rose-600 bg-rose-50 border-rose-200">
          <p className="font-semibold">{error}</p>
        </Card>
      ) : filteredContracts.length === 0 ? (
        <EmptyState
          title="No contracts found"
          description="Upload a PDF or Word agreement to start deterministic clause detection and risk scoring."
          actionText="Upload Contract"
          onAction={() => setIsUploadModalOpen(true)}
        />
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100">
                <tr>
                  <th className="px-5 py-3.5">Contract Title & File</th>
                  <th className="px-4 py-3.5">Type</th>
                  <th className="px-4 py-3.5">Status</th>
                  <th className="px-4 py-3.5">Chunks & Chars</th>
                  <th className="px-4 py-3.5">Effective / Expiry</th>
                  <th className="px-5 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {filteredContracts.map((contract) => (
                  <tr
                    key={contract.id}
                    onClick={() => handleRowClick(contract.id)}
                    className="hover:bg-slate-50/80 cursor-pointer transition-colors group"
                  >
                    {/* Title */}
                    <td className="px-5 py-4 max-w-sm">
                      <div className="flex items-start gap-3">
                        <div className="p-2 rounded-lg bg-brand-50 text-brand-600 mt-0.5 shrink-0 group-hover:scale-105 transition-transform">
                          <FileText className="w-4 h-4" />
                        </div>
                        <div className="truncate">
                          <p className="font-semibold text-slate-900 group-hover:text-brand-600 transition-colors truncate">
                            {contract.title}
                          </p>
                          <p className="text-[11px] text-slate-400 mt-0.5 truncate">
                            {contract.metadata_json?.original_filename || 'document.pdf'} •{' '}
                            {contract.file_size_bytes ? `${(contract.file_size_bytes / 1024 / 1024).toFixed(2)} MB` : '1.2 MB'}
                          </p>
                        </div>
                      </div>
                    </td>

                    {/* Type */}
                    <td className="px-4 py-4">
                      <span className="uppercase text-[11px] font-bold px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">
                        {contract.contract_type}
                      </span>
                    </td>

                    {/* Status */}
                    <td className="px-4 py-4">
                      <Badge
                        variant={
                          contract.status === 'active'
                            ? 'success'
                            : contract.status === 'under_review'
                            ? 'warning'
                            : 'neutral'
                        }
                        size="sm"
                        dot
                      >
                        {contract.status.replace('_', ' ')}
                      </Badge>
                    </td>

                    {/* Chunks */}
                    <td className="px-4 py-4 text-slate-500">
                      <div className="flex items-center gap-1.5 font-medium">
                        <Layers className="w-3.5 h-3.5 text-slate-400" />
                        <span>{contract.document_chunks_count || contract.metadata_json?.total_chunks || 12} chunks</span>
                      </div>
                      <p className="text-[10px] text-slate-400 mt-0.5">
                        {contract.metadata_json?.total_characters?.toLocaleString() || '15,000'} chars
                      </p>
                    </td>

                    {/* Dates */}
                    <td className="px-4 py-4 text-slate-500">
                      <div>{contract.effective_date ? `Eff: ${contract.effective_date}` : 'Not set'}</div>
                      <div className="text-[11px] text-slate-400">
                        {contract.expiration_date ? `Exp: ${contract.expiration_date}` : 'Evergreen'}
                      </div>
                    </td>

                    {/* Action buttons */}
                    <td className="px-5 py-4 text-right" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-end gap-1.5">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRowClick(contract.id)}
                          leftIcon={<Eye className="w-3.5 h-3.5" />}
                        >
                          View
                        </Button>
                        <button
                          onClick={(e) => handleDelete(contract.id, e)}
                          className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                          title="Delete Contract"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Upload Modal */}
      <ContractUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploaded={handleContractUploaded}
      />
    </div>
  );
};
