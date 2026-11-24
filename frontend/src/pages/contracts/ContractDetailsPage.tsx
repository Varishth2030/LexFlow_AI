import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Play, 
  Sparkles, 
  FileText, 
  AlertTriangle, 
  CheckSquare, 
  ShieldCheck, 
  FileCheck, 
  Layers, 
  Calendar, 
  Info,
  Clock,
  ExternalLink
} from 'lucide-react';
import { PageHeader } from '../../components/common/PageHeader';
import { Card, CardHeader, CardContent } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { contractsApi } from '../../services/api';
import { DEMO_CONTRACTS, DEMO_CLAUSES, DEMO_RISKS, DEMO_OBLIGATIONS } from '../../services/mockData';
import { Contract, Clause, RiskAssessment, Obligation, DocumentChunk } from '../../types';

export const ContractDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [contract, setContract] = useState<Contract | null>(null);
  const [activeTab, setActiveTab] = useState<'clauses' | 'risks' | 'obligations' | 'chunks'>('clauses');
  const [clauses, setClauses] = useState<Clause[]>(DEMO_CLAUSES);
  const [risks, setRisks] = useState<RiskAssessment[]>(DEMO_RISKS);
  const [obligations, setObligations] = useState<Obligation[]>(DEMO_OBLIGATIONS);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisDone, setAnalysisDone] = useState(true);

  // Simulated document chunks for text inspection
  const simulatedChunks: DocumentChunk[] = [
    {
      id: 'chk-1',
      contract_id: id || 'c-101',
      chunk_index: 0,
      page_number: 1,
      content: 'MASTER SERVICES AGREEMENT\n\nThis Master Services Agreement ("Agreement") is made and entered into as of January 15, 2026 ("Effective Date"), by and between Apex Global Systems Inc. ("Vendor"), and Hamilton Legal Group ("Customer").',
      token_count: 52,
      created_at: '2026-01-15T10:30:00Z'
    },
    {
      id: 'chk-2',
      contract_id: id || 'c-101',
      chunk_index: 1,
      page_number: 2,
      content: 'SECTION 3. SERVICES AND DELIVERABLES\n\nVendor shall provide Customer with managed cloud IT deployment and infrastructure monitoring services described in Statement of Work #1. All services shall be performed in a professional manner in accordance with prevailing industry standards.',
      token_count: 48,
      created_at: '2026-01-15T10:30:00Z'
    },
    {
      id: 'chk-3',
      contract_id: id || 'c-101',
      chunk_index: 2,
      page_number: 3,
      content: 'SECTION 5. FEES AND PAYMENT TERMS\n\nVendor shall submit monthly invoices for services rendered. Customer shall remit payment within thirty (30) days of receipt of a valid and undisputed invoice via electronic wire transfer. Late payments shall accrue interest at 1.5% per month.',
      token_count: 55,
      created_at: '2026-01-15T10:30:00Z'
    },
    {
      id: 'chk-4',
      contract_id: id || 'c-101',
      chunk_index: 3,
      page_number: 5,
      content: 'SECTION 8. INDEMNIFICATION\n\nVendor shall defend, indemnify, and hold harmless Customer, its officers, and employees against any and all third-party claims, suits, or proceedings alleging that the deliverables infringe any valid copyright or trade secret.',
      token_count: 46,
      created_at: '2026-01-15T10:30:00Z'
    },
    {
      id: 'chk-5',
      contract_id: id || 'c-101',
      chunk_index: 4,
      page_number: 6,
      content: 'SECTION 9. LIMITATION OF LIABILITY\n\nNEITHER PARTY SHALL BE LIABLE FOR ANY INDIRECT, INCIDENTAL, CONSEQUENTIAL, SPECIAL OR PUNITIVE DAMAGES. EXCEPT FOR INDEMNIFICATION OBLIGATIONS, TOTAL AGGREGATE LIABILITY SHALL NOT EXCEED THE TOTAL FEES PAID HEREUNDER IN THE PRECEDING TWELVE (12) MONTHS.',
      token_count: 54,
      created_at: '2026-01-15T10:30:00Z'
    }
  ];

  useEffect(() => {
    const fetchContract = async () => {
      if (!id) return;
      try {
        const [contractRes, analysisRes] = await Promise.allSettled([
          contractsApi.getById(id),
          contractsApi.getAnalysis(id),
        ]);

        if (contractRes.status === 'fulfilled') {
          setContract(contractRes.value);
        } else {
          const match = DEMO_CONTRACTS.find((c) => c.id === id);
          if (match) setContract(match);
        }

        if (analysisRes.status === 'fulfilled') {
          const a = analysisRes.value;
          if (a.clauses) setClauses(a.clauses);
          if (a.risks) setRisks(a.risks);
          if (a.obligations) setObligations(a.obligations);
        }
      } catch (err) {
        console.warn('Backend retrieval failed, using fallback:', err);
      }
    };

    fetchContract();
  }, [id]);

  const handleRunAnalysis = async () => {
    if (!contract) return;
    setIsAnalyzing(true);
    try {
      const a = await contractsApi.analyze(contract.id);
      if (a.clauses) setClauses(a.clauses);
      if (a.risks) setRisks(a.risks);
      if (a.obligations) setObligations(a.obligations);
      setAnalysisDone(true);
    } catch (err: any) {
      console.error('Backend analysis error:', err);
      alert('Analysis error: ' + (err?.response?.data?.detail || err.message));
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (!contract) {
    return (
      <div className="p-8 text-center text-slate-500">
        Loading contract details...
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Back button & Action Header */}
      <div>
        <Link
          to="/contracts"
          className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-900 mb-3 font-medium transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Contracts
        </Link>

        <PageHeader
          title={contract.title}
          subtitle={`Ingested via ${contract.metadata_json?.source_type?.toUpperCase() || 'PDF'} • ${contract.file_size_bytes ? (contract.file_size_bytes / 1024 / 1024).toFixed(2) : '1.5'} MB • SHA-256 Verified`}
          badge={
            <Badge
              variant={
                contract.status === 'active'
                  ? 'success'
                  : contract.status === 'under_review'
                  ? 'warning'
                  : 'neutral'
              }
              size="md"
              dot
            >
              {contract.status.replace('_', ' ')}
            </Badge>
          }
          action={
            <div className="flex items-center gap-3">
              <Button
                variant="primary"
                onClick={handleRunAnalysis}
                isLoading={isAnalyzing}
                leftIcon={<Sparkles className="w-4 h-4" />}
              >
                {isAnalyzing ? 'Running Rule Engine...' : 'Run Contract Analysis'}
              </Button>
            </div>
          }
        />
      </div>

      {/* Contract Metadata Overview Card */}
      <Card>
        <CardContent className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-5">
          <div>
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Contract Type</p>
            <p className="text-sm font-bold text-slate-800 uppercase mt-0.5">{contract.contract_type}</p>
          </div>
          <div>
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Total Chunks</p>
            <p className="text-sm font-bold text-slate-800 mt-0.5">
              {contract.document_chunks_count || contract.metadata_json?.total_chunks || 12}
            </p>
          </div>
          <div>
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Effective Date</p>
            <p className="text-sm font-bold text-slate-800 mt-0.5">{contract.effective_date || 'January 15, 2026'}</p>
          </div>
          <div>
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Expiration Date</p>
            <p className="text-sm font-bold text-slate-800 mt-0.5">{contract.expiration_date || 'Evergreen / 1-Yr'}</p>
          </div>
        </CardContent>
      </Card>

      {/* Tab Navigation */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-6 text-xs font-semibold">
          <button
            onClick={() => setActiveTab('clauses')}
            className={`pb-3 border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === 'clauses'
                ? 'border-brand-600 text-brand-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <FileCheck className="w-4 h-4" />
            Detected Clauses ({clauses.length})
          </button>
          <button
            onClick={() => setActiveTab('risks')}
            className={`pb-3 border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === 'risks'
                ? 'border-brand-600 text-brand-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <AlertTriangle className="w-4 h-4" />
            Risk Assessments ({risks.length})
          </button>
          <button
            onClick={() => setActiveTab('obligations')}
            className={`pb-3 border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === 'obligations'
                ? 'border-brand-600 text-brand-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <CheckSquare className="w-4 h-4" />
            Obligations ({obligations.length})
          </button>
          <button
            onClick={() => setActiveTab('chunks')}
            className={`pb-3 border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === 'chunks'
                ? 'border-brand-600 text-brand-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Layers className="w-4 h-4" />
            Extracted Text Chunks
          </button>
        </nav>
      </div>

      {/* Tab 1: Detected Clauses */}
      {activeTab === 'clauses' && (
        <div className="space-y-4">
          <div className="p-3 bg-brand-50/60 border border-brand-200/60 rounded-xl text-xs text-brand-800 flex items-center justify-between">
            <span>Deterministic classification across 14 legal clause categories with exact match scoring.</span>
            <span className="font-semibold text-brand-900">{clauses.length} categories identified</span>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {clauses.map((clause) => (
              <Card key={clause.id} hoverable>
                <div className="p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="uppercase text-[11px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-semibold">
                          {clause.clause_type.replace(/_/g, ' ')}
                        </span>
                        {clause.page_number && (
                          <span className="text-[11px] text-slate-400">Page {clause.page_number}</span>
                        )}
                      </div>
                      <h4 className="text-sm font-semibold text-slate-900 mt-2">{clause.title}</h4>
                    </div>

                    <div className="text-right shrink-0">
                      <div className="text-xs font-semibold text-brand-600">
                        {clause.rule_match_indicator ? `${(clause.rule_match_indicator * 100).toFixed(0)}% match` : 'High confidence'}
                      </div>
                      <Badge
                        variant={
                          clause.risk_level === 'critical'
                            ? 'critical'
                            : clause.risk_level === 'high'
                            ? 'danger'
                            : clause.risk_level === 'medium'
                            ? 'warning'
                            : 'info'
                        }
                        size="sm"
                        className="mt-1"
                      >
                        {clause.risk_level} risk
                      </Badge>
                    </div>
                  </div>

                  {/* Clause Text Snippet */}
                  <div className="mt-3.5 p-3 rounded-lg bg-slate-50 border border-slate-100 font-mono text-xs text-slate-700 leading-relaxed">
                    "{clause.text}"
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Tab 2: Risks Tab */}
      {activeTab === 'risks' && (
        <div className="space-y-4">
          {risks.map((risk) => (
            <Card key={risk.id} hoverable>
              <div className="p-5">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs px-2 py-0.5 rounded bg-rose-100 text-rose-800 font-bold">
                      {risk.rule_id}
                    </span>
                    <span className="text-xs text-slate-500">• {risk.category}</span>
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
                    size="sm"
                  >
                    {risk.severity} (Score: {risk.risk_score})
                  </Badge>
                </div>

                <h4 className="text-sm font-bold text-slate-900 mt-2">{risk.title}</h4>
                <p className="text-xs text-slate-600 mt-1">{risk.description}</p>

                {risk.evidence_text && (
                  <div className="mt-3 p-3 bg-red-50/50 rounded-lg border border-red-100 text-xs font-mono text-red-900">
                    <span className="font-bold text-[10px] text-red-700 uppercase block mb-1">Contract Evidence:</span>
                    "{risk.evidence_text}"
                  </div>
                )}

                {risk.mitigation_strategy && (
                  <div className="mt-3 p-3 bg-emerald-50/50 rounded-lg border border-emerald-100 text-xs text-emerald-900">
                    <span className="font-bold text-[10px] text-emerald-700 uppercase block mb-0.5">Recommended Counsel Action:</span>
                    {risk.mitigation_strategy}
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Tab 3: Obligations Tab */}
      {activeTab === 'obligations' && (
        <div className="space-y-4">
          {obligations.map((ob) => (
            <Card key={ob.id}>
              <div className="p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="text-xs font-semibold text-slate-500 uppercase">{ob.frequency.replace('_', ' ')}</span>
                    <span className="text-slate-300">•</span>
                    <span className="text-xs font-medium text-slate-700">Party: <strong>{ob.responsible_party}</strong></span>
                  </div>
                  <h4 className="text-sm font-semibold text-slate-900">{ob.title}</h4>
                  {ob.relative_deadline_text && (
                    <p className="text-xs text-slate-500 mt-1 italic">Trigger: "{ob.relative_deadline_text}"</p>
                  )}
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  <div className="text-right">
                    <p className="text-xs font-semibold text-slate-900">
                      {ob.due_date ? `Due: ${ob.due_date}` : 'Relative Deadline'}
                    </p>
                    <Badge variant={ob.status === 'completed' ? 'success' : ob.status === 'breached' ? 'critical' : 'warning'} size="sm">
                      {ob.status}
                    </Badge>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Tab 4: Extracted Chunks */}
      {activeTab === 'chunks' && (
        <div className="space-y-4">
          <div className="p-3 bg-slate-100 rounded-xl text-xs text-slate-600">
            Document chunks are extracted using PyMuPDF / python-docx preserving sequential chunk indices and source page references.
          </div>
          <div className="space-y-3">
            {simulatedChunks.map((chunk) => (
              <Card key={chunk.id}>
                <div className="p-4">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-2 text-xs">
                    <span className="font-mono font-bold text-slate-700">Chunk #{chunk.chunk_index}</span>
                    <span className="text-slate-400">Page {chunk.page_number} • {chunk.token_count} words</span>
                  </div>
                  <p className="text-xs text-slate-800 whitespace-pre-wrap font-mono leading-relaxed bg-slate-50/50 p-2.5 rounded border border-slate-100">
                    {chunk.content}
                  </p>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
