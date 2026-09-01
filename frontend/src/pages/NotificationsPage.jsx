import React, { useState, useEffect } from 'react';
import NotificationPanel from '../components/NotificationPanel';
import NotificationPreferences from '../components/NotificationPreferences';
import notificationService from '../services/notificationService';

export const NotificationsPage = () => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [preferences, setPreferences] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('inbox');

  const loadData = async () => {
    setLoading(true);
    try {
      const [res, prefs] = await Promise.all([
        notificationService.getNotifications(50),
        notificationService.getPreferences(),
      ]);
      setNotifications(res.notifications || []);
      setUnreadCount(res.unread_count || 0);
      setPreferences(prefs);
    } catch (err) {
      console.error('Failed to load notifications page data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleMarkRead = async (id) => {
    try {
      await notificationService.markAsRead(id);
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationService.markAllAsRead();
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id) => {
    try {
      await notificationService.deleteNotification(id);
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleUpdatePreferences = async (data) => {
    try {
      const updated = await notificationService.updatePreferences(data);
      setPreferences(updated);
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-slate-500 font-semibold animate-pulse">
        Loading Notification Center...
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div>
        <h1 className="text-2xl font-black text-slate-800 tracking-tight">Notification Center</h1>
        <p className="text-xs text-slate-500 mt-1">
          Manage system alerts, low attendance warnings, risk alerts, and delivery preferences.
        </p>
      </div>

      <div className="flex border-b border-slate-200 gap-4">
        <button
          onClick={() => setActiveTab('inbox')}
          className={`pb-3 text-xs font-bold border-b-2 transition-all flex items-center gap-2 ${
            activeTab === 'inbox'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          Notification Inbox
          {unreadCount > 0 && (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-indigo-100 text-indigo-700">
              {unreadCount}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('preferences')}
          className={`pb-3 text-xs font-bold border-b-2 transition-all ${
            activeTab === 'preferences'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          Delivery Preferences
        </button>
      </div>

      {activeTab === 'inbox' ? (
        <NotificationPanel
          notifications={notifications}
          onMarkRead={handleMarkRead}
          onMarkAllRead={handleMarkAllRead}
          onDelete={handleDelete}
        />
      ) : (
        <NotificationPreferences preferences={preferences} onUpdate={handleUpdatePreferences} />
      )}
    </div>
  );
};

export default NotificationsPage;
