import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  FileText, 
  AlertTriangle, 
  CheckSquare, 
  ShieldAlert, 
  Upload, 
  ArrowRight, 
  Clock, 
  CheckCircle2, 
  ExternalLink,
  ShieldCheck,
  TrendingUp
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell, 
  Tooltip, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid 
} from 'recharts';
import { PageHeader } from '../../components/common/PageHeader';
import { MetricCard } from '../../components/common/MetricCard';
import { Card, CardHeader, CardContent } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { contractsApi, complianceApi } from '../../services/api';
import { 
  DEMO_CONTRACTS, 
  DEMO_RISKS, 
  DEMO_OBLIGATIONS, 
  DEMO_TASKS, 
  DEMO_DASHBOARD,
  DEMO_AUDIT_LOGS 
} from '../../services/mockData';
import { Contract, RiskAssessment, Obligation, ComplianceTask } from '../../types';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [contracts, setContracts] = useState<Contract[]>(DEMO_CONTRACTS);
  const [risks, setRisks] = useState<RiskAssessment[]>(DEMO_RISKS);
  const [obligations, setObligations] = useState<Obligation[]>(DEMO_OBLIGATIONS);
  const [tasks, setTasks] = useState<ComplianceTask[]>(DEMO_TASKS);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchLiveStats = async () => {
      try {
        const [contractsRes, compDash, risksRes, obligationsRes] = await Promise.allSettled([
          contractsApi.list({ limit: 5 }),
          complianceApi.getDashboard(),
          contractsApi.listOrganizationRisks({ limit: 10 }),
          contractsApi.listOrganizationObligations({ limit: 10 }),
        ]);
        if (contractsRes.status === 'fulfilled') {
          const list = contractsRes.value.items || contractsRes.value.contracts;
          if (list && list.length > 0) setContracts(list);
        }
        if (risksRes.status === 'fulfilled' && risksRes.value.items?.length > 0) {
          setRisks(risksRes.value.items);
        }
        if (obligationsRes.status === 'fulfilled' && obligationsRes.value.items?.length > 0) {
          setObligations(obligationsRes.value.items);
        }
      } catch (err) {
        console.warn('Dashboard live stats query:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchLiveStats();
  }, []);

  // Compute metrics
  const totalContracts = contracts.length;
  const analyzedContracts = contracts.filter((c) => c.status === 'active' || c.status === 'under_review').length;
  const highRiskFindings = risks.filter((r) => r.severity === 'critical' || r.severity === 'high').length;
  const pendingObligations = obligations.filter((o) => o.status === 'pending' || o.status === 'in_progress').length;
  const overdueTasks = tasks.filter((t) => t.status === 'overdue').length;

  // Chart data: Risk Severity Distribution
  const riskDistributionData = [
    { name: 'Critical', value: risks.filter(r => r.severity === 'critical').length, color: '#ef4444' },
    { name: 'High', value: risks.filter(r => r.severity === 'high').length, color: '#f97316' },
    { name: 'Medium', value: risks.filter(r => r.severity === 'medium').length, color: '#eab308' },
    { name: 'Low', value: risks.filter(r => r.severity === 'low').length, color: '#3b82f6' },
  ];

  // Chart data: Obligation frequency
  const obligationChartData = [
    { name: 'Monthly', count: obligations.filter(o => o.frequency === 'monthly').length },
    { name: 'Quarterly', count: obligations.filter(o => o.frequency === 'quarterly').length },
    { name: 'Annual', count: obligations.filter(o => o.frequency === 'annual').length },
    { name: 'One-Time', count: obligations.filter(o => o.frequency === 'one_time').length },
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Top Banner Notice */}
      <div className="p-4 rounded-xl bg-gradient-to-r from-navy-900 to-slate-900 text-white flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 shadow-sm border border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-brand-500/20 text-brand-300 border border-brand-500/30">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold">Rule-Based Legal Intelligence Engine Active</h3>
            <p className="text-xs text-slate-300">
              14 clause categories, 12 deterministic risk checks, and tenant-scoped compliance automation.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button 
            variant="primary" 
            size="sm" 
            leftIcon={<Upload className="w-4 h-4" />}
            onClick={() => navigate('/contracts')}
          >
            Upload Contract
          </Button>
        </div>
      </div>

      {/* Page Title Header */}
      <PageHeader
        title="Executive Contract Dashboard"
        subtitle="Real-time legal risk surveillance, contractual obligations, and compliance milestones."
        action={
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Clock className="w-4 h-4 text-slate-400" />
            <span>Updated moments ago</span>
          </div>
        }
      />

      {/* 5 Core Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="Total Contracts"
          value={totalContracts}
          change="+2"
          changeType="positive"
          icon={<FileText className="w-5 h-5 text-brand-600" />}
          iconBg="bg-brand-50"
        />
        <MetricCard
          title="Analyzed Agreements"
          value={analyzedContracts}
          subtitle="100% Deterministic"
          icon={<CheckCircle2 className="w-5 h-5 text-emerald-600" />}
          iconBg="bg-emerald-50"
        />
        <MetricCard
          title="High/Critical Risks"
          value={highRiskFindings}
          change="+1 flagged"
          changeType="negative"
          icon={<AlertTriangle className="w-5 h-5 text-rose-600" />}
          iconBg="bg-rose-50"
        />
        <MetricCard
          title="Pending Obligations"
          value={pendingObligations}
          subtitle="Active deliverables"
          icon={<CheckSquare className="w-5 h-5 text-amber-600" />}
          iconBg="bg-amber-50"
        />
        <MetricCard
          title="Overdue Tasks"
          value={overdueTasks}
          change={overdueTasks > 0 ? "Requires action" : "On schedule"}
          changeType={overdueTasks > 0 ? "negative" : "positive"}
          icon={<ShieldAlert className="w-5 h-5 text-red-600" />}
          iconBg="bg-red-50"
        />
      </div>

      {/* Visual Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Distribution Donut */}
        <Card className="lg:col-span-1">
          <CardHeader
            title="Risk Findings by Severity"
            subtitle="Deterministic rule evaluations"
          />
          <CardContent className="h-64 flex flex-col items-center justify-center">
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie
                  data={riskDistributionData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {riskDistributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-xs w-full mt-2">
              {riskDistributionData.map((item) => (
                <div key={item.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-slate-600">{item.name}</span>
                  </div>
                  <span className="font-semibold text-slate-800">{item.value}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Obligations by Frequency Bar Chart */}
        <Card className="lg:col-span-2">
          <CardHeader
            title="Contractual Obligation Cadence"
            subtitle="Extracted recurring deliverables and milestones"
            action={
              <Link to="/obligations" className="text-xs font-semibold text-brand-600 hover:underline">
                View all obligations →
              </Link>
            }
          />
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={obligationChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip cursor={{ fill: '#f8fafc' }} />
                <Bar dataKey="count" fill="#2563eb" radius={[6, 6, 0, 0]} barSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Tables Section: Recent Contracts & Upcoming Deadlines */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Contracts Table */}
        <Card className="lg:col-span-2">
          <CardHeader
            title="Recent Contracts"
            subtitle="Uploaded legal agreements across active organization"
            action={
              <Link to="/contracts" className="text-xs font-semibold text-brand-600 hover:underline">
                All contracts →
              </Link>
            }
          />
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100">
                <tr>
                  <th className="px-5 py-3">Contract Title</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Chunks</th>
                  <th className="px-5 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {contracts.slice(0, 4).map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-5 py-3.5 font-medium text-slate-900 max-w-xs truncate">
                      <Link to={`/contracts`} className="hover:text-brand-600">
                        {c.title}
                      </Link>
                    </td>
                    <td className="px-4 py-3.5 uppercase text-[11px] font-semibold text-slate-500">
                      {c.contract_type}
                    </td>
                    <td className="px-4 py-3.5">
                      <Badge
                        variant={
                          c.status === 'active'
                            ? 'success'
                            : c.status === 'under_review'
                            ? 'warning'
                            : 'neutral'
                        }
                        size="sm"
                        dot
                      >
                        {c.status.replace('_', ' ')}
                      </Badge>
                    </td>
                    <td className="px-4 py-3.5 text-slate-500">
                      {c.document_chunks_count || c.metadata_json?.total_chunks || '—'}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/contracts`)}
                        rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
                      >
                        View
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Upcoming Deadlines & Overdue Tasks */}
        <Card className="lg:col-span-1">
          <CardHeader
            title="Upcoming Deadlines"
            subtitle="Prioritized obligations & compliance tasks"
            action={
              <Link to="/compliance" className="text-xs font-semibold text-brand-600 hover:underline">
                Tasks →
              </Link>
            }
          />
          <CardContent className="p-0">
            <div className="divide-y divide-slate-100">
              {tasks.slice(0, 4).map((task) => (
                <div key={task.id} className="p-4 hover:bg-slate-50 transition-colors">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-xs font-medium text-slate-900 line-clamp-1">{task.title}</p>
                    <Badge
                      variant={
                        task.status === 'overdue'
                          ? 'critical'
                          : task.status === 'completed'
                          ? 'success'
                          : task.priority === 'critical'
                          ? 'danger'
                          : 'primary'
                      }
                      size="sm"
                    >
                      {task.status}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-500 mt-2">
                    <span>Due: {task.due_date || 'No date'}</span>
                    <span className="capitalize font-medium text-slate-600">{task.priority} Priority</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Security & Processing Activity (Audit Log) */}
      <Card>
        <CardHeader
          title="Recent System & Audit Activity"
          subtitle="Non-repudiable log of contract uploads, analysis runs, and task completions"
          action={
            <Link to="/audit" className="text-xs font-semibold text-brand-600 hover:underline">
              View full audit log →
            </Link>
          }
        />
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100">
              <tr>
                <th className="px-5 py-3">Timestamp</th>
                <th className="px-4 py-3">User</th>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Target Entity</th>
                <th className="px-4 py-3">IP Address</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {DEMO_AUDIT_LOGS.slice(0, 4).map((log) => (
                <tr key={log.id} className="hover:bg-slate-50/70">
                  <td className="px-5 py-3 text-slate-500 font-mono text-[11px]">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 font-medium text-slate-900">{log.user_name || 'System User'}</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-0.5 rounded font-mono text-[11px] bg-slate-100 text-slate-800">
                      {log.action}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600 uppercase text-[11px]">
                    {log.entity_type} ({log.entity_id?.substring(0, 8)})
                  </td>
                  <td className="px-4 py-3 text-slate-400 font-mono text-[11px]">{log.ip_address}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
