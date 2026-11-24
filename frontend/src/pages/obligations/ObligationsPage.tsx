import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  CheckSquare, 
  Search, 
  Filter, 
  Calendar, 
  User, 
  Clock, 
  FileText, 
  CheckCircle2, 
  AlertCircle 
} from 'lucide-react';
import { PageHeader } from '../../components/common/PageHeader';
import { Card } from '../../components/common/Card';
import { Badge } from '../../components/common/Badge';
import { Button } from '../../components/common/Button';
import { EmptyState } from '../../components/common/EmptyState';
import { contractsApi } from '../../services/api';
import { Obligation, ObligationStatus } from '../../types';

export const ObligationsPage: React.FC = () => {
  const [obligations, setObligations] = useState<Obligation[]>([]);
  const [search, setSearch] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedParty, setSelectedParty] = useState<string>('all');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchObligations = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await contractsApi.listOrganizationObligations({
          status: selectedStatus !== 'all' ? selectedStatus : undefined,
          responsible_party: selectedParty !== 'all' ? selectedParty : undefined,
        });
        setObligations(res.items || []);
      } catch (err: any) {
        console.error('Failed to load organization obligations:', err);
        setError('Failed to load obligations from backend. Please ensure contracts have been uploaded and analyzed.');
        setObligations([]);
      } finally {
        setLoading(false);
      }
    };

    fetchObligations();
  }, [selectedStatus, selectedParty]);

  const filteredObligations = obligations.filter((o) => {
    const matchesSearch = o.title.toLowerCase().includes(search.toLowerCase()) ||
      (o.contract_title && o.contract_title.toLowerCase().includes(search.toLowerCase()));
    return matchesSearch;
  });

  const handleToggleStatus = (id: string) => {
    setObligations((prev) =>
      prev.map((o) => {
        if (o.id === id) {
          const nextStatus: ObligationStatus = o.status === 'completed' ? 'pending' : 'completed';
          return { ...o, status: nextStatus };
        }
        return o;
      })
    );
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      <PageHeader
        title="Contractual Obligations & Deliverables"
        subtitle="Tracking actionable deliverables, recurring reporting cycles, and payment milestones across all contracts in your organization."
      />

      {/* Filter and Search Bar */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search obligations or contracts..."
              className="w-full pl-9 pr-3.5 py-2 text-xs rounded-lg border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20"
            />
          </div>

          <div className="flex items-center gap-2.5 w-full sm:w-auto">
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="text-xs px-3 py-2 rounded-lg border border-slate-200 bg-white"
            >
              <option value="all">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="breached">Breached</option>
            </select>

            <select
              value={selectedParty}
              onChange={(e) => setSelectedParty(e.target.value)}
              className="text-xs px-3 py-2 rounded-lg border border-slate-200 bg-white"
            >
              <option value="all">All Parties</option>
              <option value="vendor">Vendor</option>
              <option value="client">Client / Customer</option>
              <option value="each">Each Party</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Obligations Table, Loading, Error, or Empty State */}
      {loading ? (
        <Card className="p-12 text-center text-xs text-slate-500">
          <div className="inline-block animate-spin w-6 h-6 border-2 border-brand-600 border-t-transparent rounded-full mb-3" />
          <p>Loading contractual obligations from organization...</p>
        </Card>
      ) : error ? (
        <Card className="p-8 text-center text-xs text-rose-600 bg-rose-50 border-rose-200">
          <p className="font-semibold">{error}</p>
        </Card>
      ) : filteredObligations.length === 0 ? (
        <EmptyState
          title="No Obligations Found"
          description="Either all obligations have been satisfied, or no uploaded contracts have extracted obligations yet."
          actionText="View Contracts Inventory"
          onAction={() => window.location.href = '/contracts'}
        />
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100">
                <tr>
                  <th className="px-5 py-3.5">Obligation Deliverable</th>
                  <th className="px-4 py-3.5">Responsible Party</th>
                  <th className="px-4 py-3.5">Due Date & Frequency</th>
                  <th className="px-4 py-3.5">Contract Reference</th>
                  <th className="px-4 py-3.5">Status</th>
                  <th className="px-5 py-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {filteredObligations.map((ob) => (
                  <tr key={ob.id} className="hover:bg-slate-50/70 transition-colors">
                    {/* Title */}
                    <td className="px-5 py-4 max-w-sm">
                      <p className="font-semibold text-slate-900">{ob.title}</p>
                      {ob.description && ob.description !== ob.title && (
                        <p className="text-[11px] text-slate-500 line-clamp-2 mt-0.5">
                          {ob.description}
                        </p>
                      )}
                      {ob.relative_deadline_text && (
                        <p className="text-[11px] text-slate-500 italic mt-0.5">
                          Trigger: "{ob.relative_deadline_text}"
                        </p>
                      )}
                    </td>

                    {/* Responsible Party */}
                    <td className="px-4 py-4">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 text-slate-800 font-medium text-[11px]">
                        <User className="w-3 h-3 text-slate-500" />
                        {ob.responsible_party}
                      </span>
                    </td>

                    {/* Due Date & Frequency */}
                    <td className="px-4 py-4">
                      <div className="font-semibold text-slate-800">
                        {ob.due_date ? String(ob.due_date) : 'Relative Deadline'}
                      </div>
                      <span className="uppercase text-[10px] tracking-wider text-slate-400 font-medium">
                        {ob.frequency ? String(ob.frequency).replace('_', ' ') : 'one time'}
                      </span>
                    </td>

                    {/* Contract */}
                    <td className="px-4 py-4 max-w-xs truncate">
                      <Link
                        to={`/contracts/${ob.contract_id}`}
                        className="text-brand-600 hover:underline flex items-center gap-1 truncate font-semibold"
                      >
                        <FileText className="w-3.5 h-3.5 shrink-0" />
                        <span className="truncate">{ob.contract_title || 'Contract Agreement'}</span>
                      </Link>
                    </td>

                    {/* Status */}
                    <td className="px-4 py-4">
                      <Badge
                        variant={
                          ob.status === 'completed'
                            ? 'success'
                            : ob.status === 'in_progress'
                            ? 'primary'
                            : ob.status === 'breached'
                            ? 'critical'
                            : 'warning'
                        }
                        size="sm"
                        dot
                      >
                        {ob.status ? String(ob.status).replace('_', ' ') : 'pending'}
                      </Badge>
                    </td>

                    {/* Mark Completed Toggle */}
                    <td className="px-5 py-4 text-right">
                      <Button
                        variant={ob.status === 'completed' ? 'outline' : 'primary'}
                        size="sm"
                        onClick={() => handleToggleStatus(ob.id)}
                      >
                        {ob.status === 'completed' ? 'Mark Incomplete' : 'Complete'}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};
