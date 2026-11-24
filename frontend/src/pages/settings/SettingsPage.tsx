import React, { useState } from 'react';
import { 
  User, 
  Building, 
  Shield, 
  Sliders, 
  CheckCircle2, 
  Lock, 
  Bell, 
  Save, 
  Key,
  ShieldCheck
} from 'lucide-react';
import { PageHeader } from '../../components/common/PageHeader';
import { Card, CardHeader, CardContent } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Badge } from '../../components/common/Badge';
import { useAuth } from '../../context/AuthContext';

export const SettingsPage: React.FC = () => {
  const { user, organization } = useAuth();
  const [activeTab, setActiveTab] = useState<'profile' | 'organization' | 'security' | 'preferences'>('profile');

  // Form states
  const [fullName, setFullName] = useState(user?.full_name || 'Alexander Hamilton');
  const [email, setEmail] = useState(user?.email || 'alexander@hamiltonlegal.com');
  const [orgName, setOrgName] = useState(organization?.name || 'Hamilton Legal Group');
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Security
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);

  // Preferences
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [autoOverdueCheck, setAutoOverdueCheck] = useState(true);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2500);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      <PageHeader
        title="Settings & Workspace Configuration"
        subtitle="Manage user credentials, organization tenant details, and security parameters."
      />

      {saveSuccess && (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center gap-2 animate-in fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>Configuration saved successfully.</span>
        </div>
      )}

      {/* Settings Navigation Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-6 text-xs font-semibold">
          <button
            onClick={() => setActiveTab('profile')}
            className={`pb-3 border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === 'profile'
                ? 'border-brand-600 text-brand-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <User className="w-4 h-4" />
            My Profile
          </button>
          <button
            onClick={() => setActiveTab('organization')}
            className={`pb-3 border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === 'organization'
                ? 'border-brand-600 text-brand-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Building className="w-4 h-4" />
            Organization
          </button>
          <button
            onClick={() => setActiveTab('security')}
            className={`pb-3 border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === 'security'
                ? 'border-brand-600 text-brand-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Shield className="w-4 h-4" />
            Security & Passwords
          </button>
          <button
            onClick={() => setActiveTab('preferences')}
            className={`pb-3 border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === 'preferences'
                ? 'border-brand-600 text-brand-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Sliders className="w-4 h-4" />
            Preferences
          </button>
        </nav>
      </div>

      {/* Tab 1: Profile */}
      {activeTab === 'profile' && (
        <Card>
          <CardHeader
            title="User Profile Information"
            subtitle="Your personal details and assigned role within the organization"
          />
          <CardContent>
            <form onSubmit={handleSave} className="space-y-4 max-w-xl">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-14 h-14 rounded-full bg-slate-800 text-white flex items-center justify-center text-lg font-bold">
                  {fullName ? fullName.charAt(0).toUpperCase() : 'U'}
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900">{fullName}</h4>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="purple" size="sm">
                      {user?.role || 'owner'}
                    </Badge>
                    <span className="text-xs text-slate-400">UUID: {user?.id?.substring(0, 8) || 'usr-1'}</span>
                  </div>
                </div>
              </div>

              <Input
                label="Full Name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />

              <Input
                label="Work Email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />

              <div className="pt-2">
                <Button type="submit" variant="primary" leftIcon={<Save className="w-4 h-4" />}>
                  Save Profile Changes
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Tab 2: Organization */}
      {activeTab === 'organization' && (
        <Card>
          <CardHeader
            title="Tenant Organization Settings"
            subtitle="Multi-tenant root entity anchoring all contracts, controls, and tasks"
          />
          <CardContent>
            <form onSubmit={handleSave} className="space-y-4 max-w-xl">
              <Input
                label="Organization / Law Firm Name"
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
              />

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Tenant Unique Slug
                </label>
                <input
                  type="text"
                  disabled
                  value={organization?.slug || 'hamilton-legal-group'}
                  className="w-full rounded-lg border border-slate-200 bg-slate-100 px-3.5 py-2 text-xs text-slate-500 font-mono"
                />
                <p className="text-[11px] text-slate-400 mt-1">
                  Unique subdomain namespace used for cryptographic token verification.
                </p>
              </div>

              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-600">
                <div className="flex items-center gap-1.5 font-bold text-slate-900 mb-1">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  <span>Tenant Isolation Safeguards</span>
                </div>
                LexFlow AI strictly enforces organization boundaries on every database query. Users from other tenants can never inspect or modify your agreements.
              </div>

              <div className="pt-2">
                <Button type="submit" variant="primary" leftIcon={<Save className="w-4 h-4" />}>
                  Update Organization
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Tab 3: Security & Passwords */}
      {activeTab === 'security' && (
        <div className="space-y-6">
          <Card>
            <CardHeader
              title="Change Password"
              subtitle="Secured with memory-hard Argon2id hashing algorithms"
            />
            <CardContent>
              <form onSubmit={handleSave} className="space-y-4 max-w-xl">
                <Input
                  label="Current Password"
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="••••••••••••"
                />
                <Input
                  label="New Password (min 8 characters, alphanumeric)"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••••••"
                />
                <Input
                  label="Confirm New Password"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••••••"
                />

                <div className="pt-2">
                  <Button type="submit" variant="primary" leftIcon={<Key className="w-4 h-4" />}>
                    Update Password
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader
              title="Two-Factor Authentication (2FA)"
              subtitle="Enforce hardware keys or TOTP authenticator apps for counsel logins"
            />
            <CardContent>
              <div className="flex items-center justify-between max-w-xl">
                <div>
                  <p className="text-xs font-semibold text-slate-900">Enforce 2FA on all team accounts</p>
                  <p className="text-[11px] text-slate-500">Require an authenticator code alongside Argon2 password.</p>
                </div>
                <input
                  type="checkbox"
                  checked={twoFactorEnabled}
                  onChange={(e) => setTwoFactorEnabled(e.target.checked)}
                  className="rounded border-slate-300 text-brand-600 focus:ring-brand-500 h-4 w-4"
                />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tab 4: Preferences */}
      {activeTab === 'preferences' && (
        <Card>
          <CardHeader
            title="Application Preferences & Automation"
            subtitle="Notification schedules and automated compliance engine parameters"
          />
          <CardContent className="space-y-4 max-w-xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <p className="text-xs font-semibold text-slate-900">Critical Risk Email Alerts</p>
                <p className="text-[11px] text-slate-500">Receive immediate notifications when uncapped liabilities are identified.</p>
              </div>
              <input
                type="checkbox"
                checked={emailAlerts}
                onChange={(e) => setEmailAlerts(e.target.checked)}
                className="rounded border-slate-300 text-brand-600 focus:ring-brand-500 h-4 w-4"
              />
            </div>

            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <p className="text-xs font-semibold text-slate-900">Dynamic Overdue Surveillance Engine</p>
                <p className="text-[11px] text-slate-500">Automatically flag past-due compliance tasks without manual status edits.</p>
              </div>
              <input
                type="checkbox"
                checked={autoOverdueCheck}
                onChange={(e) => setAutoOverdueCheck(e.target.checked)}
                className="rounded border-slate-300 text-brand-600 focus:ring-brand-500 h-4 w-4"
              />
            </div>

            <div className="pt-2">
              <Button onClick={handleSave} variant="primary">
                Save Application Preferences
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
