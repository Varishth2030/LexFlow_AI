import React, { useState } from 'react';
import { Modal } from '../../components/common/Modal';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Select } from '../../components/common/Select';
import { complianceApi } from '../../services/api';
import { ComplianceTask, TaskPriority, TaskStatus, ComplianceControl, Contract } from '../../types';

interface CreateTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  controls: ComplianceControl[];
  contracts: Contract[];
  onCreated: (task: ComplianceTask) => void;
}

export const CreateTaskModal: React.FC<CreateTaskModalProps> = ({
  isOpen,
  onClose,
  controls,
  contracts,
  onCreated,
}) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [controlId, setControlId] = useState('');
  const [contractId, setContractId] = useState('');
  const [priority, setPriority] = useState<TaskPriority>('medium');
  const [dueDate, setDueDate] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title) return;

    setIsSubmitting(true);
    try {
      const payload: Partial<ComplianceTask> = {
        title,
        description,
        control_id: controlId || undefined,
        contract_id: contractId || undefined,
        priority,
        due_date: dueDate || undefined,
        status: 'pending',
      };
      const created = await complianceApi.createTask(payload);
      onCreated(created);
      handleClose();
    } catch (err) {
      console.warn('Backend task creation fallback:', err);
      const selectedControl = controls.find((c) => c.id === controlId);
      const selectedContract = contracts.find((c) => c.id === contractId);

      const fallback: ComplianceTask = {
        id: 'tsk-' + Date.now(),
        organization_id: 'org-demo',
        title,
        description,
        control_id: controlId || null,
        control_code: selectedControl?.control_code || null,
        contract_id: contractId || null,
        contract_title: selectedContract?.title || null,
        priority,
        status: 'pending',
        due_date: dueDate || null,
        assignee_name: 'Alexander Hamilton',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      onCreated(fallback);
      handleClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setTitle('');
    setDescription('');
    setControlId('');
    setContractId('');
    setPriority('medium');
    setDueDate('');
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Create Compliance Task"
      subtitle="Assign audit action items linked to controls and contracts"
      footer={
        <>
          <Button variant="ghost" onClick={handleClose}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSubmit} isLoading={isSubmitting}>
            Create Task
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Task Title"
          required
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Audit third-party sub-processor SOC 2 report"
        />

        <div className="grid grid-cols-2 gap-4">
          <Select
            label="Related Compliance Control"
            value={controlId}
            onChange={(e) => setControlId(e.target.value)}
            options={[
              { value: '', label: 'None (Standalone Task)' },
              ...controls.map((c) => ({ value: c.id, label: `${c.control_code}: ${c.name}` })),
            ]}
          />

          <Select
            label="Related Contract Agreement"
            value={contractId}
            onChange={(e) => setContractId(e.target.value)}
            options={[
              { value: '', label: 'None (General Task)' },
              ...contracts.map((c) => ({ value: c.id, label: c.title })),
            ]}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Select
            label="Priority"
            value={priority}
            onChange={(e) => setPriority(e.target.value as TaskPriority)}
            options={[
              { value: 'low', label: 'Low' },
              { value: 'medium', label: 'Medium' },
              { value: 'high', label: 'High' },
              { value: 'critical', label: 'Critical' },
            ]}
          />

          <Input
            label="Due Date"
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
          />
        </div>

        <Input
          label="Description / Scope"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Provide remediation steps or evidence requirements..."
        />
      </form>
    </Modal>
  );
};
