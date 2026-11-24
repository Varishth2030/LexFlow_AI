import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  Download, 
  FileSpreadsheet, 
  FileText, 
  Printer, 
  CheckCircle2, 
  PieChart as PieIcon,
  TrendingUp,
  ShieldCheck,
  Calendar,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  LineChart, 
  Line 
} from 'recharts';
import { PageHeader } from '../../components/common/PageHeader';
import { Card, CardHeader, CardContent } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { reportsApi } from '../../services/api';
import { ExecutiveReportSummary } from '../../types';

export const ReportsPage: React.FC = () => {
  const [summary, setSummary] = useState<ExecutiveReportSummary | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [downloadSuccess, setDownloadSuccess] = useState<string | null>(null);

  const fetchSummary = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await reportsApi.getSummary();
      setSummary(data);
    } catch (err: any) {
      console.error('Failed to load executive report summary:', err);
      setError(err.response?.data?.detail || 'Failed to retrieve executive report analytics.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const handleExport = async (format: 'CSV' | 'PDF' | 'risks' | 'obligations' | 'compliance') => {
    setIsExporting(true);
    try {
      if (format === 'PDF') {
        await reportsApi.downloadPdf();
        setDownloadSuccess('Generated and downloaded Executive Legal Dossier (PDF).');
      } else {
        const type = format === 'CSV' ? 'executive' : format;
        await reportsApi.downloadCsv(type);
        setDownloadSuccess(`Generated and downloaded ${type.toUpperCase()} Audit Report (CSV).`);
      }
      setTimeout(() => setDownloadSuccess(null), 4000);
    } catch (err: any) {
      console.error('Export download error:', err);
      setError(err.response?.data?.detail || 'Export download failed. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  const contractTypeData = summary?.contract_type_distribution && summary.contract_type_distribution.length > 0
    ? summary.contract_type_distribution
    : [
        { name: 'Master Services (MSA)', count: 0 },
        { name: 'Non-Disclosure (NDA)', count: 0 },
        { name: 'Vendor Agreement', count: 0 },
      ];

  const quarterlyRiskTrend = summary?.risk_trend && summary.risk_trend.length > 0
    ? summary.risk_trend
    : [
        { quarter: 'Q1 2025', critical: 0, high: 0, resolved: 0 },
        { quarter: 'Q2 2025', critical: 0, high: 0, resolved: 0 },
        { quarter: 'Q3 2025', critical: 0, high: 0, resolved: 0 },
        { quarter: 'Q4 2025', critical: 0, high: 0, resolved: 0 },
        { quarter: 'Q1 2026', critical: 0, high: 0, resolved: 0 },
      ];

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      <PageHeader
        title="Executive Intelligence Reports"
        subtitle={`Consolidated compliance audits, contractual obligation schedules, and risk exposure trends for ${summary?.organization_name || 'Organization'}.`}
        action={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={isExporting}
              onClick={() => handleExport('CSV')}
              leftIcon={<FileSpreadsheet className="w-4 h-4" />}
            >
              Export CSV
            </Button>
            <Button
              variant="primary"
              size="sm"
              disabled={isExporting}
              onClick={() => handleExport('PDF')}
              leftIcon={isExporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            >
              Download PDF Report
            </Button>
          </div>
        }
      />

      {downloadSuccess && (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center gap-2 animate-in fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{downloadSuccess}</span>
        </div>
      )}

      {error && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-center justify-between animate-in fade-in">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
          <Button variant="outline" size="sm" onClick={fetchSummary}>
            Retry
          </Button>
        </div>
      )}

      {isLoading ? (
        <div className="p-16 flex flex-col items-center justify-center space-y-3">
          <Loader2 className="w-8 h-8 text-brand-600 animate-spin" />
          <p className="text-xs text-slate-500 font-medium">Aggregating executive legal intelligence...</p>
        </div>
      ) : (
        <>
          {/* Overview Stat Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <Card className="p-5">
              <p className="text-xs font-semibold text-slate-500 uppercase">Total Contracts Processed</p>
              <p className="text-3xl font-extrabold text-slate-900 mt-1">{summary?.total_contracts ?? 0}</p>
              <p className="text-[11px] text-slate-400 mt-1">100% Deterministic Extraction</p>
            </Card>
            <Card className="p-5">
              <p className="text-xs font-semibold text-slate-500 uppercase">Total Clauses Cataloged</p>
              <p className="text-3xl font-extrabold text-brand-600 mt-1">{summary?.total_clauses ?? 0}</p>
              <p className="text-[11px] text-slate-400 mt-1">14 Standard Categories</p>
            </Card>
            <Card className="p-5">
              <p className="text-xs font-semibold text-slate-500 uppercase">Compliance Governance Rate</p>
              <p className="text-3xl font-extrabold text-emerald-600 mt-1">{summary?.compliance_governance_rate ?? 0}%</p>
              <p className="text-[11px] text-slate-400 mt-1">SOC 2 & ISO 27001 Controls</p>
            </Card>
            <Card className="p-5">
              <p className="text-xs font-semibold text-slate-500 uppercase">Identified Risks</p>
              <p className="text-3xl font-extrabold text-slate-900 mt-1">{summary?.total_risks ?? 0}</p>
              <p className="text-[11px] text-rose-500 mt-1 font-medium">{summary?.critical_risks ?? 0} Critical • {summary?.high_risks ?? 0} High</p>
            </Card>
          </div>

          {/* Visual Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Risk Trend over quarters */}
            <Card>
              <CardHeader
                title="Risk Velocity & Resolution Trend"
                subtitle="Identified critical risks vs. counsel remediations"
              />
              <CardContent className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={quarterlyRiskTrend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="quarter" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
                    <Tooltip />
                    <Line type="monotone" dataKey="critical" stroke="#ef4444" strokeWidth={2.5} name="Critical Risks" />
                    <Line type="monotone" dataKey="high" stroke="#f97316" strokeWidth={2} name="High Risks" />
                    <Line type="monotone" dataKey="resolved" stroke="#10b981" strokeWidth={2.5} name="Resolved" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Contract Inventory by Type */}
            <Card>
              <CardHeader
                title="Contract Portfolio Breakdown"
                subtitle="Agreements cataloged across organization"
              />
              <CardContent className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={contractTypeData} layout="vertical" margin={{ top: 10, right: 20, left: 40, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                    <XAxis type="number" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
                    <YAxis dataKey="name" type="category" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} width={130} />
                    <Tooltip cursor={{ fill: '#f8fafc' }} />
                    <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} barSize={20} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Available Export Packages */}
          <Card>
            <CardHeader
              title="Ready-to-Export Audit Packages"
              subtitle="Pre-formatted legal briefing dossiers for executive leadership and external auditors"
            />
            <div className="divide-y divide-slate-100">
              <div className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-blue-50 text-blue-700">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-slate-900">Comprehensive Risk & Liability Dossier</h4>
                    <p className="text-[11px] text-slate-500">Includes uncapped liability carve-outs, unilateral termination clauses, and mitigation recommendations.</p>
                  </div>
                </div>
                <Button variant="outline" size="sm" disabled={isExporting} onClick={() => handleExport('PDF')}>
                  Download PDF
                </Button>
              </div>

              <div className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-emerald-50 text-emerald-700">
                    <ShieldCheck className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-slate-900">SOC 2 & ISO 27001 Control Attestation Package</h4>
                    <p className="text-[11px] text-slate-500">Task completion logs, active controls status, and sub-processor DPA execution records.</p>
                  </div>
                </div>
                <Button variant="outline" size="sm" disabled={isExporting} onClick={() => handleExport('compliance')}>
                  Export CSV
                </Button>
              </div>

              <div className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-purple-50 text-purple-700">
                    <Calendar className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-slate-900">Annual Contractual Obligation Master Calendar</h4>
                    <p className="text-[11px] text-slate-500">Timeline of all SLA rebates, audit deliverables, and renewal opt-out notice windows.</p>
                  </div>
                </div>
                <Button variant="outline" size="sm" disabled={isExporting} onClick={() => handleExport('obligations')}>
                  Export CSV
                </Button>
              </div>
            </div>
          </Card>

          {/* Legal Screening Disclaimer Banner */}
          <div className="p-3.5 rounded-xl bg-slate-100 border border-slate-200 text-xs text-slate-600">
            <span className="font-semibold text-slate-800 block mb-0.5">Automated Legal Screening Notice:</span>
            {summary?.legal_disclaimer || 'Outputs are deterministic legal screening aids and do not constitute formal legal counsel.'}
          </div>
        </>
      )}
    </div>
  );
};
