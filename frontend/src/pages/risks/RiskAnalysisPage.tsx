import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  AlertTriangle, 
  ShieldAlert, 
  CheckCircle2, 
  Filter, 
  FileText, 
  Info, 
  ShieldCheck,
  ChevronDown,
  ExternalLink,
  Upload
} from 'lucide-react';
import { PageHeader } from '../../components/common/PageHeader';
import { Card, CardHeader, CardContent } from '../../components/common/Card';
import { Badge } from '../../components/common/Badge';
import { Button } from '../../components/common/Button';
import { EmptyState } from '../../components/common/EmptyState';
import { contractsApi } from '../../services/api';
import { RiskAssessment, RiskSeverity } from '../../types';

export const RiskAnalysisPage: React.FC = () => {
  const [risks, setRisks] = useState<RiskAssessment[]>([]);
  const [overallScore, setOverallScore] = useState<number>(0);
  const [riskBand, setRiskBand] = useState<string>('Low');
  const [severityDistribution, setSeverityDistribution] = useState<Record<string, number>>({
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
  });
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRisks = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await contractsApi.listOrganizationRisks({
          severity: selectedSeverity !== 'all' ? selectedSeverity : undefined,
        });
        setRisks(res.items || []);
        setOverallScore(res.overall_risk_score ?? 0);
        setRiskBand(res.risk_band || 'Low');
        if (res.severity_distribution) {
          setSeverityDistribution(res.severity_distribution);
        }
      } catch (err: any) {
        console.error('Failed to load organization risks:', err);
        setError('Failed to load risks from backend. Please ensure contracts have been uploaded and analyzed.');
        setRisks([]);
      } finally {
        setLoading(false);
      }
    };

    fetchRisks();
  }, [selectedSeverity]);

  const filteredRisks = risks.filter((r) => {
    const matchesCat = selectedCategory === 'all' || r.category?.toLowerCase() === selectedCategory.toLowerCase();
    return matchesCat;
  });

  const criticalCount = severityDistribution.critical ?? 0;
  const highCount = severityDistribution.high ?? 0;
  const mediumCount = severityDistribution.medium ?? 0;
  const lowCount = severityDistribution.low ?? 0;

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      <PageHeader
        title="Contract Risk Surveillance"
        subtitle="Deterministic rule evaluations highlighting uncapped liabilities, missing safeguards, and aggressive terms across all organization contracts."
      />

      {/* Legal Screening Disclaimer Banner */}
      <div className="p-4 rounded-xl bg-amber-50/80 border border-amber-200/90 text-xs text-amber-900 flex items-start gap-3">
        <Info className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold block mb-0.5">Mandatory Legal Screening Disclaimer</span>
          LexFlow AI provides deterministic, rule-based legal screening aids to highlight potential contractual risks and obligations. Outputs are not legal advice, binding conclusions, or a substitute for professional legal review by qualified counsel.
        </div>
      </div>

      {/* Portfolio Risk Meter Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Score Meter */}
        <Card className="p-5 bg-gradient-to-br from-slate-900 to-navy-950 text-white lg:col-span-1">
          <p className="text-xs uppercase font-medium text-slate-400">Aggregate Risk Index</p>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-extrabold text-white">{overallScore.toFixed(0)}</span>
            <span className="text-xs text-slate-400">/ 100</span>
          </div>
          <div className="mt-3">
            <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-full border ${
              riskBand === 'Critical'
                ? 'bg-red-500/20 text-red-300 border-red-500/30'
                : riskBand === 'High'
                ? 'bg-rose-500/20 text-rose-300 border-rose-500/30'
                : riskBand === 'Medium'
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
            }`}>
              {riskBand} Risk Band
            </span>
          </div>
          <p className="text-[10px] text-slate-400 mt-2">Critical weight: 10.0 • High: 7.0</p>
        </Card>

        {/* Severity counts */}
        <Card className="p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase">Critical</span>
            <span className="w-2.5 h-2.5 rounded-full bg-red-600" />
          </div>
          <div className="mt-2">
            <span className="text-2xl font-bold text-red-600">{criticalCount}</span>
            <p className="text-[11px] text-slate-400">Immediate redress</p>
          </div>
        </Card>

        <Card className="p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase">High</span>
            <span className="w-2.5 h-2.5 rounded-full bg-orange-500" />
          </div>
          <div className="mt-2">
            <span className="text-2xl font-bold text-orange-600">{highCount}</span>
            <p className="text-[11px] text-slate-400">Material exposure</p>
          </div>
        </Card>

        <Card className="p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase">Medium</span>
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
          </div>
          <div className="mt-2">
            <span className="text-2xl font-bold text-amber-600">{mediumCount}</span>
            <p className="text-[11px] text-slate-400">Operational concern</p>
          </div>
        </Card>

        <Card className="p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase">Low</span>
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
          </div>
          <div className="mt-2">
            <span className="text-2xl font-bold text-blue-600">{lowCount}</span>
            <p className="text-[11px] text-slate-400">Procedural review</p>
          </div>
        </Card>
      </div>

      {/* Filter Row */}
      <div className="flex items-center justify-between bg-white p-3.5 rounded-xl border border-slate-200">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-700">Filter findings:</span>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="text-xs px-3 py-1.5 rounded-lg border border-slate-200 bg-white"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="text-xs px-3 py-1.5 rounded-lg border border-slate-200 bg-white"
          >
            <option value="all">All Categories</option>
            <option value="financial">Financial</option>
            <option value="operational">Operational</option>
            <option value="legal">Legal</option>
          </select>
        </div>
      </div>

      {/* Findings List, Loading, Error, or Empty State */}
      {loading ? (
        <Card className="p-12 text-center text-xs text-slate-500">
          <div className="inline-block animate-spin w-6 h-6 border-2 border-brand-600 border-t-transparent rounded-full mb-3" />
          <p>Analyzing risk assessments across contracts...</p>
        </Card>
      ) : error ? (
        <Card className="p-8 text-center text-xs text-rose-600 bg-rose-50 border-rose-200">
          <p className="font-semibold">{error}</p>
        </Card>
      ) : filteredRisks.length === 0 ? (
        <EmptyState
          title="No Risk Findings Identified"
          description="Either all uploaded contracts are clean of identified risks, or no contracts have been analyzed yet."
          actionText="View Contracts Inventory"
          onAction={() => window.location.href = '/contracts'}
        />
      ) : (
        <div className="space-y-4">
          {filteredRisks.map((risk) => (
            <Card key={risk.id} hoverable className="border-l-4 border-l-red-500">
              <div className="p-5">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-100 pb-3 mb-3">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold px-2.5 py-0.5 rounded bg-rose-100 text-rose-800">
                      {risk.rule_id}
                    </span>
                    <span className="text-xs font-semibold text-slate-700">{risk.category} Risk</span>
                    {risk.contract_title && (
                      <span className="text-xs text-slate-400 hidden sm:inline">
                        • in <Link to={`/contracts/${risk.contract_id}`} className="text-brand-600 hover:underline font-semibold">{risk.contract_title}</Link>
                      </span>
                    )}
                  </div>
                  <Badge
                    variant={
                      risk.severity === 'critical'
                        ? 'critical'
                        : risk.severity === 'high'
                        ? 'danger'
                        : risk.severity === 'medium'
                        ? 'warning'
                        : 'info'
                    }
                    size="md"
                  >
                    {risk.severity.toUpperCase()} (Weight: {risk.risk_score})
                  </Badge>
                </div>

                <h3 className="text-base font-bold text-slate-900">{risk.title}</h3>
                <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">{risk.description}</p>

                {/* Evidence Passage */}
                {risk.evidence_text && (
                  <div className="mt-3 p-3.5 rounded-lg bg-slate-50 border border-slate-200/80 font-mono text-xs text-slate-800">
                    <span className="text-[10px] font-bold text-slate-500 uppercase block mb-1">
                      Matched Contractual Language:
                    </span>
                    "{risk.evidence_text}"
                  </div>
                )}

                {/* Mitigation Action */}
                {risk.mitigation_strategy && (
                  <div className="mt-3 p-3.5 rounded-lg bg-emerald-50/70 border border-emerald-200/80 text-xs text-emerald-950 flex items-start gap-2.5">
                    <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold text-[11px] text-emerald-800 uppercase block mb-0.5">
                        Recommended Counsel Remediation:
                      </span>
                      {risk.mitigation_strategy}
                    </div>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
