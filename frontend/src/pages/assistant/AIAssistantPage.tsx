import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  Bot, 
  Search, 
  Send, 
  FileText, 
  ShieldCheck, 
  ExternalLink, 
  Info, 
  Sparkles,
  Layers,
  ArrowRight,
  HelpCircle,
  AlertCircle
} from 'lucide-react';
import { PageHeader } from '../../components/common/PageHeader';
import { Card, CardHeader, CardContent } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { contractsApi } from '../../services/api';
import { SearchResultPassage } from '../../types';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  query?: string;
  results?: SearchResultPassage[];
  noResults?: boolean;
  welcome?: boolean;
  error?: string;
  disclaimer?: string;
  timestamp: string;
}

export const AIAssistantPage: React.FC = () => {
  const [inputQuery, setInputQuery] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-init',
      sender: 'assistant',
      welcome: true,
      timestamp: 'Ready',
    },
  ]);
  const [isSearching, setIsSearching] = useState(false);

  const sampleQueries = [
    'What is our aggregate limitation of liability cap?',
    'What are our notice requirements for a data breach?',
    'Does the customer have unilateral termination rights?',
    'What are the confidentiality obligations upon agreement termination?',
  ];

  const handleSearch = async (queryText: string) => {
    if (!queryText.trim() || isSearching) return;

    const userMsg: ChatMessage = {
      id: 'usr-' + Date.now(),
      sender: 'user',
      query: queryText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setIsSearching(true);

    try {
      const response = await contractsApi.search({ query: queryText });
      const items = response.items || response.results || [];
      const assistantMsg: ChatMessage = {
        id: 'ast-' + Date.now(),
        sender: 'assistant',
        results: items.length > 0 ? items : undefined,
        noResults: items.length === 0,
        disclaimer: response.legal_disclaimer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      console.error('Contract search error:', err);
      const errorMsg: ChatMessage = {
        id: 'ast-err-' + Date.now(),
        sender: 'assistant',
        error: err.response?.data?.detail || 'An error occurred while searching contracts. Ensure contracts are uploaded and try again.',
        noResults: true,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      <PageHeader
        title="Contract Search Assistant"
        subtitle="Deterministic keyword & clause locator with exact document and page citations."
        badge={
          <Badge variant="info" size="md">
            Non-Generative Search
          </Badge>
        }
      />

      {/* Non-Generative Clarification Alert */}
      <div className="p-4 rounded-xl bg-slate-100 border border-slate-200 text-xs text-slate-700 flex items-start gap-3">
        <Info className="w-4 h-4 text-brand-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-900 block mb-0.5">
            Deterministic Contract Search Engine (Zero LLM / No Generative Hallucinations)
          </span>
          This assistant locates verbatim text passages, chunk indices, and page references across your ingested PDF and DOCX files. It does not fabricate text or summarize with external AI APIs.
        </div>
      </div>

      {/* Main Chat Interface */}
      <Card className="h-[650px] flex flex-col">
        <CardHeader
          title="Interactive Contract Clause Query"
          subtitle="Search contracts for clauses, covenants, and restrictions"
          action={
            <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Tenant Isolated</span>
            </div>
          }
        />

        {/* Message Thread */}
        <div className="flex-1 p-6 overflow-y-auto space-y-5 bg-slate-50/40">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.sender === 'assistant' && (
                <div className="w-8 h-8 rounded-xl bg-navy-900 text-brand-400 flex items-center justify-center shrink-0 mt-1 shadow-xs">
                  <Bot className="w-4.5 h-4.5" />
                </div>
              )}

              <div
                className={`max-w-2xl rounded-2xl p-4.5 text-xs ${
                  msg.sender === 'user'
                    ? 'bg-brand-600 text-white shadow-xs rounded-tr-xs'
                    : 'bg-white border border-slate-200 shadow-xs text-slate-800 rounded-tl-xs'
                }`}
              >
                {msg.sender === 'user' ? (
                  <p className="font-medium text-sm leading-relaxed">{msg.query}</p>
                ) : msg.welcome ? (
                  <div className="space-y-3">
                    <p className="font-semibold text-slate-900 flex items-center gap-1.5 text-sm">
                      <Sparkles className="w-4 h-4 text-brand-600" />
                      Deterministic Contract Search Assistant
                    </p>
                    <p className="text-slate-600 leading-relaxed text-xs">
                      Ask questions about provisions, deadlines, liabilities, or indemnities. This engine executes SQL pattern and keyword matching across your organization's ingested contract chunks.
                    </p>
                    <div className="p-3 bg-brand-50/60 rounded-xl border border-brand-100 text-[11px] text-brand-900 space-y-1">
                      <p className="font-semibold">Key Capabilities:</p>
                      <ul className="list-disc list-inside space-y-0.5 text-brand-800">
                        <li>Locates verbatim clauses across all tenant contracts</li>
                        <li>Identifies page numbers, chunk references, and responsible parties</li>
                        <li>Zero generative AI, zero hallucinations, zero external API exposure</li>
                      </ul>
                    </div>
                  </div>
                ) : msg.error ? (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-rose-600 font-semibold text-xs">
                      <AlertCircle className="w-4 h-4 shrink-0" />
                      <span>Search Failed</span>
                    </div>
                    <p className="text-slate-600 text-xs">{msg.error}</p>
                  </div>
                ) : (
                  <div className="space-y-3.5">
                    {msg.results && msg.results.length > 0 ? (
                      <>
                        <p className="font-semibold text-slate-900 flex items-center gap-1.5">
                          <Sparkles className="w-3.5 h-3.5 text-brand-600" />
                          Found {msg.results.length} verbatim contractual matches:
                        </p>

                        <div className="space-y-3">
                          {msg.results.map((res) => (
                            <div
                              key={res.id}
                              className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/90 text-xs"
                            >
                              <div className="flex items-center justify-between border-b border-slate-200 pb-2 mb-2">
                                <Link
                                  to={`/contracts/${res.contract_id}`}
                                  className="font-semibold text-brand-700 hover:text-brand-900 hover:underline flex items-center gap-1.5"
                                >
                                  {res.contract_title}
                                  <ExternalLink className="w-3 h-3 text-brand-500" />
                                </Link>
                                <div className="flex items-center gap-2">
                                  <span className="font-mono text-[10px] bg-slate-200 px-1.5 py-0.5 rounded text-slate-700">
                                    {res.source_reference || `Chunk #${res.chunk_index}`}
                                  </span>
                                  {res.page_number && (
                                    <span className="text-slate-500 font-medium text-[11px]">
                                      Page {res.page_number}
                                    </span>
                                  )}
                                </div>
                              </div>

                              <div className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider mb-1">
                                {res.matched_clause_type || 'Clause Passage'}
                              </div>

                              <p className="font-mono text-slate-800 bg-white p-2.5 rounded-lg border border-slate-200/70 leading-relaxed text-[11px] select-text">
                                {res.snippet}
                              </p>

                              <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-500">
                                <span>Responsible: <strong>{res.responsible_party || 'Both Parties'}</strong></span>
                                <span className="text-brand-600 font-medium">Deterministic Score: {(res.exact_match_score * 100).toFixed(0)}%</span>
                              </div>
                            </div>
                          ))}
                        </div>

                        {/* Verbatim Disclaimer Banner */}
                        <div className="p-2.5 bg-slate-100 rounded-lg text-[10px] text-slate-600 border border-slate-200">
                          {msg.disclaimer || 'LexFlow AI deterministic search retrieves verbatim passages directly from stored document chunks. Results are not legal advice, binding conclusions, or AI-generated answers.'}
                        </div>
                      </>
                    ) : (
                      <div className="p-4 bg-slate-50 rounded-xl text-center space-y-1.5">
                        <p className="font-semibold text-slate-800">No matching contract language found.</p>
                        <p className="text-slate-500 text-xs">
                          No passages in your organization's contracts matched the query. Try searching for specific legal keywords such as <em>indemnity</em>, <em>liability</em>, <em>notice</em>, <em>cure</em>, or <em>confidential</em>.
                        </p>
                      </div>
                    )}
                  </div>
                )}
                <span className={`block text-[10px] mt-2 ${msg.sender === 'user' ? 'text-brand-200 text-right' : 'text-slate-400'}`}>
                  {msg.timestamp}
                </span>
              </div>
            </div>
          ))}

          {isSearching && (
            <div className="flex gap-3 items-center text-xs text-slate-500 italic">
              <Bot className="w-5 h-5 text-brand-600 animate-pulse" />
              <span>Scanning document chunks across tenant contracts...</span>
            </div>
          )}
        </div>

        {/* Suggested Queries Pill Bar */}
        <div className="px-6 py-2.5 border-t border-slate-100 bg-white flex items-center gap-2 overflow-x-auto">
          <span className="text-[11px] text-slate-400 font-semibold shrink-0">Sample queries:</span>
          {sampleQueries.map((q, idx) => (
            <button
              key={idx}
              onClick={() => handleSearch(q)}
              className="text-[11px] px-2.5 py-1 rounded-full bg-slate-100 hover:bg-brand-50 hover:text-brand-700 text-slate-600 border border-slate-200 shrink-0 transition-colors"
            >
              {q}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-200 bg-white">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSearch(inputQuery);
            }}
            className="flex items-center gap-2"
          >
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                placeholder="Ask about contract provisions, deadlines, liabilities, or indemnities..."
                className="w-full pl-10 pr-4 py-2.5 text-xs rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all text-slate-900"
              />
            </div>
            <Button
              type="submit"
              variant="primary"
              disabled={!inputQuery.trim() || isSearching}
              rightIcon={<Send className="w-4 h-4" />}
            >
              Search
            </Button>
          </form>
        </div>
      </Card>
    </div>
  );
};
