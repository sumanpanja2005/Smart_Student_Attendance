import React from 'react';
import { HealthBadge } from '../components/HealthBadge';
import NotificationBell from '../components/NotificationBell';
import { useAuth } from '../context/AuthContext';
import { Menu, GraduationCap, LogOut, User as UserIcon } from 'lucide-react';
import { Button } from '../components/Button';
import { Link } from 'react-router-dom';

export const Header = ({ toggleSidebar }) => {
  const { user, isAuthenticated, logout } = useAuth();

  const roleColors = {
    ADMIN: 'bg-purple-100 text-purple-800 border-purple-200',
    TEACHER: 'bg-blue-100 text-blue-800 border-blue-200',
    STUDENT: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  };

  return (
    <header className="sticky top-0 z-30 bg-white border-b border-gray-200 shadow-2xs">
      <div className="flex items-center justify-between px-4 py-3 sm:px-6">
        {/* Left Section: Brand & Sidebar Toggle */}
        <div className="flex items-center gap-3">
          <button
            onClick={toggleSidebar}
            className="p-2 text-gray-500 rounded-lg lg:hidden hover:bg-gray-100 focus:outline-none"
            aria-label="Toggle Navigation"
          >
            <Menu className="w-5 h-5" />
          </button>

          <Link to="/" className="flex items-center gap-2.5">
            <div className="p-2 bg-indigo-600 rounded-xl text-white shadow-xs">
              <GraduationCap className="w-5 h-5" />
            </div>
            <div>
              <span className="text-base font-bold text-gray-900 leading-none block">Smart Attendance</span>
              <span className="text-xs text-gray-500 hidden sm:block">AI & Student Analytics System</span>
            </div>
          </Link>
        </div>

        {/* Right Section: System Health Badge, Notification Bell & User Profile/Logout */}
        <div className="flex items-center gap-4">
          <HealthBadge />

          {isAuthenticated && <NotificationBell />}

          <div className="h-6 w-px bg-gray-200 hidden md:block" />

          {isAuthenticated && user ? (
            <div className="flex items-center gap-3">
              <div className="hidden sm:flex flex-col text-right">
                <span className="text-xs font-semibold text-gray-900 leading-none">
                  {user.first_name} {user.last_name}
                </span>
                <div className="mt-1">
                  <span
                    className={`inline-block text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border ${
                      roleColors[user.role] || 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    {user.role}
                  </span>
                </div>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={logout}
                icon={LogOut}
                title="Log out of system"
              >
                <span className="hidden sm:inline">Logout</span>
              </Button>
            </div>
          ) : (
            <Link to="/login">
              <Button variant="primary" size="sm" icon={UserIcon}>
                Login
              </Button>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
