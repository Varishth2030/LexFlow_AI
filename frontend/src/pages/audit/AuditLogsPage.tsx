import React, { useState, useEffect } from 'react';
import { 
  History, 
  Search, 
  Filter, 
  Eye, 
  ShieldCheck, 
  Clock, 
  User, 
  Code,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { PageHeader } from '../../components/common/PageHeader';
import { Card } from '../../components/common/Card';
import { Badge } from '../../components/common/Badge';
import { Button } from '../../components/common/Button';
import { Modal } from '../../components/common/Modal';
import { auditApi } from '../../services/api';
import { AuditLog } from '../../types';

export const AuditLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [selectedAction, setSelectedAction] = useState<string>('all');
  const [viewingLog, setViewingLog] = useState<AuditLog | null>(null);
  const [page, setPage] = useState<number>(1);
  const limit = 50;

  const fetchLogs = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params: any = {
        skip: (page - 1) * limit,
        limit,
      };
      if (selectedAction && selectedAction !== 'all') {
        params.action = selectedAction;
      }
      const data = await auditApi.list(params);
      const items = data.items || data.logs || [];
      setLogs(items);
      setTotal(data.total || items.length);
    } catch (err: any) {
      console.error('Failed to load audit logs:', err);
      setError(err.response?.data?.detail || 'Failed to load audit records from backend.');
      setLogs([]);
      setTotal(0);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [page, selectedAction]);

  const filteredLogs = logs.filter((log) => {
    if (!search.trim()) return true;
    const s = search.toLowerCase();
    return (
      (log.action && log.action.toLowerCase().includes(s)) ||
      (log.entity_type && log.entity_type.toLowerCase().includes(s)) ||
      (log.user_name && log.user_name.toLowerCase().includes(s)) ||
      (log.user_email && log.user_email.toLowerCase().includes(s)) ||
      (log.entity_id && log.entity_id.toLowerCase().includes(s))
    );
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      <PageHeader
        title="Security & System Audit Trail"
        subtitle="Append-only immutable record of all contract uploads, analysis runs, controls changes, and authentication events."
        badge={
          <Badge variant="success" size="md">
            ISO 27001 Compliant
          </Badge>
        }
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
              placeholder="Search by action, user, entity or ID..."
              className="w-full pl-9 pr-3.5 py-2 text-xs rounded-lg border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20"
            />
          </div>

          <div className="flex items-center gap-2.5 w-full sm:w-auto">
            <span className="text-xs text-slate-500 font-medium">Action:</span>
            <select
              value={selectedAction}
              onChange={(e) => {
                setSelectedAction(e.target.value);
                setPage(1);
              }}
              className="text-xs px-3 py-2 rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20"
            >
              <option value="all">All Actions</option>
              <option value="CREATE">CREATE</option>
              <option value="VIEW">VIEW</option>
              <option value="UPDATE">UPDATE</option>
              <option value="DELETE">DELETE</option>
              <option value="LOGIN">LOGIN</option>
              <option value="LOGOUT">LOGOUT</option>
              <option value="EXPORT">EXPORT</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Error Notice */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
          <Button variant="outline" size="sm" onClick={fetchLogs}>
            Retry
          </Button>
        </div>
      )}

      {/* Audit Log Table */}
      <Card>
        {isLoading ? (
          <div className="p-12 text-center flex flex-col items-center justify-center space-y-3">
            <Loader2 className="w-6 h-6 text-brand-600 animate-spin" />
            <p className="text-xs text-slate-500 font-medium">Loading immutable audit trail...</p>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="p-12 text-center flex flex-col items-center justify-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-400">
              <History className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-semibold text-slate-900">No audit records found</p>
              <p className="text-xs text-slate-500 max-w-sm">
                {search || selectedAction !== 'all'
                  ? 'No records match the current filter criteria.'
                  : 'System and tenant security audit logs will appear here as contract and compliance actions occur.'}
              </p>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100">
                <tr>
                  <th className="px-5 py-3.5">Timestamp (UTC)</th>
                  <th className="px-4 py-3.5">Actor / User</th>
                  <th className="px-4 py-3.5">Event Action</th>
                  <th className="px-4 py-3.5">Target Entity</th>
                  <th className="px-4 py-3.5">Source IP</th>
                  <th className="px-5 py-3.5 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700 font-mono text-[11px]">
                {filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-5 py-4 text-slate-500 font-sans text-xs">
                      {new Date(log.created_at).toLocaleString()}
                    </td>

                    <td className="px-4 py-4 font-sans text-xs font-semibold text-slate-900">
                      <span className="flex items-center gap-1.5">
                        <User className="w-3.5 h-3.5 text-slate-400" />
                        {log.user_name || 'System Actor'}
                      </span>
                    </td>

                    <td className="px-4 py-4">
                      <span className="px-2 py-0.5 rounded font-bold bg-slate-100 text-slate-800 uppercase">
                        {log.action}
                      </span>
                    </td>

                    <td className="px-4 py-4 text-slate-600 uppercase font-sans">
                      {log.entity_type} {log.entity_id ? `(${log.entity_id.substring(0, 8)})` : ''}
                    </td>

                    <td className="px-4 py-4 text-slate-400">{log.ip_address || '127.0.0.1'}</td>

                    <td className="px-5 py-4 text-right font-sans">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setViewingLog(log)}
                        leftIcon={<Eye className="w-3.5 h-3.5" />}
                      >
                        Payload
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {total > limit && (
          <div className="px-5 py-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>
              Showing {(page - 1) * limit + 1} to {Math.min(page * limit, total)} of {total} records
            </span>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={page * limit >= total}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* JSON Payload Inspection Modal */}
      {viewingLog && (
        <Modal
          isOpen={!!viewingLog}
          onClose={() => setViewingLog(null)}
          title={`Audit Payload: ${viewingLog.action}`}
          subtitle={`Event ID: ${viewingLog.id} • Target: ${viewingLog.entity_type}`}
          footer={
            <Button variant="outline" onClick={() => setViewingLog(null)}>
              Close
            </Button>
          }
        >
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-2 text-xs bg-slate-50 p-3 rounded-lg border border-slate-200">
              <div>
                <span className="text-slate-400">Actor:</span> <strong>{viewingLog.user_name || 'System Actor'}</strong>
              </div>
              <div>
                <span className="text-slate-400">IP Address:</span> <strong>{viewingLog.ip_address || '127.0.0.1'}</strong>
              </div>
              <div>
                <span className="text-slate-400">Timestamp:</span> <strong>{new Date(viewingLog.created_at).toLocaleString()}</strong>
              </div>
              <div>
                <span className="text-slate-400">Resource:</span> <strong>{viewingLog.entity_id || viewingLog.entity_type}</strong>
              </div>
            </div>

            <div>
              <p className="text-xs font-semibold text-slate-700 mb-1">Structured JSON Event Details:</p>
              <pre className="p-4 rounded-xl bg-slate-900 text-slate-100 text-xs font-mono overflow-x-auto leading-relaxed border border-slate-800">
                {JSON.stringify(viewingLog.details || {}, null, 2)}
              </pre>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
