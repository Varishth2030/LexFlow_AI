import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  CheckSquare, 
  Plus, 
  AlertTriangle, 
  Clock, 
  CheckCircle2, 
  Layers, 
  Search,
  Filter,
  Trash2,
  Calendar
} from 'lucide-react';
import { PageHeader } from '../../components/common/PageHeader';
import { MetricCard } from '../../components/common/MetricCard';
import { Card, CardHeader, CardContent } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { CreateControlModal } from './CreateControlModal';
import { CreateTaskModal } from './CreateTaskModal';
import { DEMO_CONTROLS, DEMO_TASKS, DEMO_CONTRACTS, DEMO_DASHBOARD } from '../../services/mockData';
import { complianceApi } from '../../services/api';
import { ComplianceControl, ComplianceTask, TaskStatus } from '../../types';

export const CompliancePage: React.FC = () => {
  const [controls, setControls] = useState<ComplianceControl[]>(DEMO_CONTROLS);
  const [tasks, setTasks] = useState<ComplianceTask[]>(DEMO_TASKS);
  const [activeTab, setActiveTab] = useState<'tasks' | 'controls'>('tasks');

  const [isControlModalOpen, setIsControlModalOpen] = useState(false);
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);

  const [taskFilterStatus, setTaskFilterStatus] = useState<string>('all');
  const [taskFilterPriority, setTaskFilterPriority] = useState<string>('all');

  useEffect(() => {
    const fetchCompliance = async () => {
      try {
        const [controlsRes, tasksRes] = await Promise.allSettled([
          complianceApi.listControls(),
          complianceApi.listTasks(),
        ]);
        if (controlsRes.status === 'fulfilled') {
          const cList = (controlsRes.value as any).items || (controlsRes.value as any).controls;
          if (cList && cList.length > 0) setControls(cList);
        }
        if (tasksRes.status === 'fulfilled') {
          const tList = (tasksRes.value as any).items || (tasksRes.value as any).tasks;
          if (tList && tList.length > 0) setTasks(tList);
        }
      } catch (err) {
        console.warn('Compliance data fetch error:', err);
      }
    };
    fetchCompliance();
  }, []);

  // Dashboard metrics
  const totalTasks = tasks.length;
  const pendingTasks = tasks.filter((t) => t.status === 'pending').length;
  const inProgressTasks = tasks.filter((t) => t.status === 'in_progress').length;
  const completedTasks = tasks.filter((t) => t.status === 'completed').length;
  const overdueTasks = tasks.filter((t) => t.status === 'overdue').length;
  const completionPercentage = totalTasks > 0 ? ((completedTasks / totalTasks) * 100).toFixed(0) : '0';

  const handleTaskStatusChange = async (taskId: string, newStatus: TaskStatus) => {
    setTasks((prev) =>
      prev.map((t) => {
        if (t.id === taskId) {
          return {
            ...t,
            status: newStatus,
            completed_at: newStatus === 'completed' ? new Date().toISOString() : undefined,
          };
        }
        return t;
      })
    );
    try {
      await complianceApi.updateTask(taskId, { status: newStatus });
    } catch (err) {
      console.warn('Backend update task:', err);
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    setTasks((prev) => prev.filter((t) => t.id !== taskId));
    try {
      await complianceApi.deleteTask(taskId);
    } catch (err) {
      console.warn('Backend delete task:', err);
    }
  };

  const handleDeleteControl = async (controlId: string) => {
    setControls((prev) => prev.filter((c) => c.id !== controlId));
    try {
      await complianceApi.deleteControl(controlId);
    } catch (err) {
      console.warn('Backend delete control:', err);
    }
  };

  const filteredTasks = tasks.filter((t) => {
    const matchesStatus = taskFilterStatus === 'all' || t.status === taskFilterStatus;
    const matchesPriority = taskFilterPriority === 'all' || t.priority === taskFilterPriority;
    return matchesStatus && matchesPriority;
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      <PageHeader
        title="Compliance & Audit Management"
        subtitle="Operational controls mapping, automated overdue surveillance, and audit evidence."
        action={
          <div className="flex items-center gap-2.5">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsControlModalOpen(true)}
              leftIcon={<Plus className="w-4 h-4" />}
            >
              New Control
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsTaskModalOpen(true)}
              leftIcon={<Plus className="w-4 h-4" />}
            >
              New Task
            </Button>
          </div>
        }
      />

      {/* Compliance Metrics Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
        <Card className="p-4">
          <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Total Tasks</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">{totalTasks}</p>
        </Card>
        <Card className="p-4">
          <p className="text-[11px] font-semibold text-amber-600 uppercase tracking-wider">Pending</p>
          <p className="text-2xl font-bold text-amber-600 mt-1">{pendingTasks}</p>
        </Card>
        <Card className="p-4">
          <p className="text-[11px] font-semibold text-blue-600 uppercase tracking-wider">In Progress</p>
          <p className="text-2xl font-bold text-blue-600 mt-1">{inProgressTasks}</p>
        </Card>
        <Card className="p-4">
          <p className="text-[11px] font-semibold text-emerald-600 uppercase tracking-wider">Completed</p>
          <p className="text-2xl font-bold text-emerald-600 mt-1">{completedTasks}</p>
        </Card>
        <Card className="p-4">
          <p className="text-[11px] font-semibold text-rose-600 uppercase tracking-wider">Overdue</p>
          <p className="text-2xl font-bold text-rose-600 mt-1">{overdueTasks}</p>
        </Card>
        <Card className="p-4 bg-brand-50 border-brand-200">
          <p className="text-[11px] font-semibold text-brand-700 uppercase tracking-wider">Completion</p>
          <p className="text-2xl font-bold text-brand-700 mt-1">{completionPercentage}%</p>
        </Card>
      </div>

      {/* Tab Switcher */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-6 text-xs font-semibold">
          <button
            onClick={() => setActiveTab('tasks')}
            className={`pb-3 border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === 'tasks'
                ? 'border-brand-600 text-brand-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <CheckSquare className="w-4 h-4" />
            Compliance Tasks ({tasks.length})
          </button>
          <button
            onClick={() => setActiveTab('controls')}
            className={`pb-3 border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === 'controls'
                ? 'border-brand-600 text-brand-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            Governance Controls ({controls.length})
          </button>
        </nav>
      </div>

      {/* Tab Content: Tasks */}
      {activeTab === 'tasks' && (
        <div className="space-y-4">
          {/* Filters Bar */}
          <Card className="p-3.5">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2">
                <Filter className="w-4 h-4 text-slate-400" />
                <span className="font-semibold text-slate-700">Filter tasks:</span>
              </div>
              <div className="flex items-center gap-2.5">
                <select
                  value={taskFilterStatus}
                  onChange={(e) => setTaskFilterStatus(e.target.value)}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white"
                >
                  <option value="all">All Statuses</option>
                  <option value="pending">Pending</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                  <option value="overdue">Overdue</option>
                </select>

                <select
                  value={taskFilterPriority}
                  onChange={(e) => setTaskFilterPriority(e.target.value)}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white"
                >
                  <option value="all">All Priorities</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
            </div>
          </Card>

          {/* Tasks Table */}
          <Card>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100">
                  <tr>
                    <th className="px-5 py-3.5">Task Title & Details</th>
                    <th className="px-4 py-3.5">Linked Control</th>
                    <th className="px-4 py-3.5">Priority</th>
                    <th className="px-4 py-3.5">Due Date</th>
                    <th className="px-4 py-3.5">Status</th>
                    <th className="px-5 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {filteredTasks.map((t) => (
                    <tr key={t.id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="px-5 py-4 max-w-sm">
                        <p className="font-semibold text-slate-900">{t.title}</p>
                        {t.description && (
                          <p className="text-[11px] text-slate-500 line-clamp-1 mt-0.5">{t.description}</p>
                        )}
                        {t.contract_title && (
                          <p className="text-[10px] text-brand-600 font-medium mt-1">
                            Contract: {t.contract_title}
                          </p>
                        )}
                      </td>

                      <td className="px-4 py-4">
                        {t.control_code ? (
                          <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-slate-100 text-slate-800 font-bold">
                            {t.control_code}
                          </span>
                        ) : (
                          <span className="text-slate-400">None</span>
                        )}
                      </td>

                      <td className="px-4 py-4">
                        <Badge
                          variant={
                            t.priority === 'critical'
                              ? 'critical'
                              : t.priority === 'high'
                              ? 'danger'
                              : t.priority === 'medium'
                              ? 'warning'
                              : 'info'
                          }
                          size="sm"
                        >
                          {t.priority}
                        </Badge>
                      </td>

                      <td className="px-4 py-4">
                        <span className={`font-medium ${t.status === 'overdue' ? 'text-red-600 font-bold' : 'text-slate-800'}`}>
                          {t.due_date || 'No due date'}
                        </span>
                        {t.status === 'overdue' && (
                          <span className="block text-[10px] text-red-500 font-semibold">PAST DUE</span>
                        )}
                      </td>

                      <td className="px-4 py-4">
                        <select
                          value={t.status}
                          onChange={(e) => handleTaskStatusChange(t.id, e.target.value as TaskStatus)}
                          className={`text-[11px] font-semibold px-2.5 py-1 rounded-full border ${
                            t.status === 'completed'
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
                              : t.status === 'overdue'
                              ? 'bg-red-50 text-red-700 border-red-300'
                              : t.status === 'in_progress'
                              ? 'bg-blue-50 text-blue-700 border-blue-300'
                              : 'bg-amber-50 text-amber-700 border-amber-300'
                          }`}
                        >
                          <option value="pending">Pending</option>
                          <option value="in_progress">In Progress</option>
                          <option value="completed">Completed</option>
                          <option value="overdue">Overdue</option>
                        </select>
                      </td>

                      <td className="px-5 py-4 text-right">
                        <button
                          onClick={() => handleDeleteTask(t.id)}
                          className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                          title="Delete task"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* Tab Content: Controls */}
      {activeTab === 'controls' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {controls.map((ctl) => (
              <Card key={ctl.id} hoverable>
                <div className="p-5 flex flex-col justify-between h-full">
                  <div>
                    <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-2 mb-2">
                      <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-brand-50 text-brand-700">
                        {ctl.control_code}
                      </span>
                      <div className="flex items-center gap-2">
                        <Badge variant="purple" size="sm">
                          {ctl.framework || 'Internal'}
                        </Badge>
                        <Badge variant={ctl.status === 'active' ? 'success' : 'neutral'} size="sm">
                          {ctl.status}
                        </Badge>
                      </div>
                    </div>

                    <h4 className="text-sm font-bold text-slate-900">{ctl.name}</h4>
                    <p className="text-xs text-slate-600 mt-1">{ctl.description}</p>

                    {ctl.requirement && (
                      <div className="mt-3 p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-[11px] text-slate-700">
                        <span className="font-semibold text-slate-800">Requirement: </span>
                        {ctl.requirement}
                      </div>
                    )}
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                    <span>Category: <strong>{ctl.category}</strong></span>
                    <button
                      onClick={() => handleDeleteControl(ctl.id)}
                      className="text-slate-400 hover:text-rose-600 p-1 rounded"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Modals */}
      <CreateControlModal
        isOpen={isControlModalOpen}
        onClose={() => setIsControlModalOpen(false)}
        onCreated={(newCtl) => setControls((prev) => [newCtl, ...prev])}
      />

      <CreateTaskModal
        isOpen={isTaskModalOpen}
        onClose={() => setIsTaskModalOpen(false)}
        controls={controls}
        contracts={DEMO_CONTRACTS}
        onCreated={(newTask) => setTasks((prev) => [newTask, ...prev])}
      />
    </div>
  );
};
