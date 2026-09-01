import React, { useState } from 'react';
import { Settings, Shield, Mail, BellRing, FileText } from 'lucide-react';

const NotificationPreferences = ({ preferences, onUpdate }) => {
  const [prefs, setPrefs] = useState({
    in_app_enabled: preferences?.in_app_enabled ?? true,
    email_enabled: preferences?.email_enabled ?? true,
    low_attendance_enabled: preferences?.low_attendance_enabled ?? true,
    risk_alert_enabled: preferences?.risk_alert_enabled ?? true,
    report_notifications_enabled: preferences?.report_notifications_enabled ?? true,
  });

  const [saving, setSaving] = useState(false);

  const handleToggle = async (key) => {
    const updated = { ...prefs, [key]: !prefs[key] };
    setPrefs(updated);
    setSaving(true);
    try {
      if (onUpdate) {
        await onUpdate({ [key]: updated[key] });
      }
    } catch (err) {
      console.error('Failed to update preference:', err);
    } finally {
      setSaving(false);
    }
  };

  const options = [
    {
      key: 'in_app_enabled',
      title: 'In-App Alerts',
      desc: 'Receive real-time alerts in the application header bell menu.',
      icon: BellRing,
    },
    {
      key: 'email_enabled',
      title: 'Email Notifications (Stub Abstraction)',
      desc: 'Receive digest notifications to your registered email address.',
      icon: Mail,
    },
    {
      key: 'low_attendance_enabled',
      title: 'Low Attendance Warnings',
      desc: 'Trigger notifications when overall attendance drops below 75%.',
      icon: Shield,
    },
    {
      key: 'risk_alert_enabled',
      title: 'Predictive Risk Notifications',
      desc: 'Receive notifications when attendance risk status reaches High or Critical level.',
      icon: Shield,
    },
    {
      key: 'report_notifications_enabled',
      title: 'Report Download Alerts',
      desc: 'Notify when PDF attendance or analytics reports are generated and ready.',
      icon: FileText,
    },
  ];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
          <Settings className="w-5 h-5 text-indigo-600" />
          Notification Preferences & Rules
        </h3>
        {saving && <span className="text-xs text-indigo-600 font-semibold animate-pulse">Saving...</span>}
      </div>

      <div className="space-y-3">
        {options.map((opt) => {
          const Icon = opt.icon;
          const isChecked = prefs[opt.key] ?? true;

          return (
            <div
              key={opt.key}
              className="p-3.5 rounded-xl border border-slate-200/80 hover:border-slate-300 flex items-center justify-between gap-4 transition-all"
            >
              <div className="flex items-center gap-3">
                <div className="p-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-600">
                  <Icon className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-800">{opt.title}</h4>
                  <p className="text-[11px] text-slate-500">{opt.desc}</p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => handleToggle(opt.key)}
                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                  isChecked ? 'bg-indigo-600' : 'bg-slate-200'
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                    isChecked ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default NotificationPreferences;
