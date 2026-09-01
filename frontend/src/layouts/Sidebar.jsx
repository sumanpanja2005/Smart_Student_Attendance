import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  GraduationCap,
  Users,
  BookOpen,
  Layers,
  UserCog,
  Camera,
  Scan,
  ShieldAlert,
  Calendar,
  BarChart3,
  Bell,
  FileText,
  Shield,
  Activity,
} from 'lucide-react';

export const Sidebar = () => {
  const { user } = useAuth();
  const role = user?.role;

  const adminLinks = [
    { to: '/admin', label: 'Overview', icon: LayoutDashboard },
    { to: '/admin/analytics', label: 'Analytics & Risk', icon: BarChart3 },
    { to: '/admin/attendance', label: 'Attendance Management', icon: Calendar },
    { to: '/notifications', label: 'Notifications', icon: Bell },
    { to: '/reports', label: 'Reports & PDF', icon: FileText },
    { to: '/admin/audit', label: 'Audit Trail', icon: Shield },
    { to: '/admin/system', label: 'System Monitoring', icon: Activity },
    { to: '/admin/students', label: 'Students', icon: GraduationCap },
    { to: '/admin/teachers', label: 'Teachers', icon: Users },
    { to: '/admin/subjects', label: 'Subjects', icon: BookOpen },
    { to: '/admin/classes', label: 'Classes', icon: Layers },
    { to: '/admin/users', label: 'User Accounts', icon: UserCog },
    { to: '/admin/face-recognition', label: 'Face Recognition Test', icon: Scan },
  ];

  const teacherLinks = [
    { to: '/teacher', label: 'Faculty Dashboard', icon: LayoutDashboard },
    { to: '/teacher/analytics', label: 'Class Analytics', icon: BarChart3 },
    { to: '/teacher/attendance', label: 'Attendance Manager', icon: Calendar },
    { to: '/notifications', label: 'Notifications', icon: Bell },
    { to: '/reports', label: 'Reports & PDF', icon: FileText },
    { to: '/teacher/students', label: 'My Students', icon: GraduationCap },
    { to: '/teacher/face-recognition', label: 'Verify Face', icon: Scan },
  ];

  const studentLinks = [
    { to: '/student', label: 'Student Portal', icon: LayoutDashboard },
    { to: '/student/analytics', label: 'My Analytics', icon: BarChart3 },
    { to: '/student/attendance', label: 'My Attendance', icon: Calendar },
    { to: '/notifications', label: 'Notifications', icon: Bell },
    { to: '/reports', label: 'Reports & PDF', icon: FileText },
    { to: '/student/register-face', label: 'Register Face Profile', icon: Camera },
  ];

  const links = role === 'ADMIN' ? adminLinks : role === 'TEACHER' ? teacherLinks : role === 'STUDENT' ? studentLinks : [];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 hidden md:flex flex-col flex-shrink-0">
      <div className="p-4 border-b border-slate-800">
        <h2 className="text-xs uppercase tracking-wider text-slate-400 font-bold">
          {role ? `${role} MENU` : 'NAVIGATION'}
        </h2>
      </div>

      <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
        {links.map((link) => {
          const Icon = link.icon;
          return (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === '/admin' || link.to === '/teacher' || link.to === '/student'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              <span>{link.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Role Badge Indicator */}
      <div className="p-4 border-t border-slate-800 text-xs">
        <div className="p-3 bg-slate-800/60 rounded-xl border border-slate-700 flex items-center gap-2 text-slate-300">
          <ShieldAlert className="w-4 h-4 text-indigo-400 shrink-0" />
          <div className="truncate">
            <p className="font-bold text-white text-[11px] uppercase">{role || 'GUEST'}</p>
            <p className="text-[10px] text-slate-400 truncate">{user?.email || 'Not logged in'}</p>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
