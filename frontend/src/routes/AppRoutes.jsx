import React from 'react';
import { Routes, Route } from 'react-router-dom';
import MainLayout from '../layouts/MainLayout';
import ProtectedRoute from './ProtectedRoute';

import HomeDashboard from '../pages/HomeDashboard';
import Login from '../pages/Login';
import AdminDashboard from '../pages/AdminDashboard';
import StudentsPage from '../pages/StudentsPage';
import TeachersPage from '../pages/TeachersPage';
import SubjectsPage from '../pages/SubjectsPage';
import ClassesPage from '../pages/ClassesPage';
import UsersPage from '../pages/UsersPage';

import TeacherDashboard from '../pages/TeacherDashboard';
import StudentDashboard from '../pages/StudentDashboard';

import FaceRegistrationPage from '../pages/FaceRegistrationPage';
import FaceRecognitionPage from '../pages/FaceRecognitionPage';

import TeacherAttendancePage from '../pages/TeacherAttendancePage';
import AttendanceSessionPage from '../pages/AttendanceSessionPage';
import AdminAttendancePage from '../pages/AdminAttendancePage';
import MyAttendancePage from '../pages/MyAttendancePage';

import AdminAnalyticsPage from '../pages/AdminAnalyticsPage';
import TeacherAnalyticsPage from '../pages/TeacherAnalyticsPage';
import StudentAnalyticsPage from '../pages/StudentAnalyticsPage';

import NotificationsPage from '../pages/NotificationsPage';
import ReportsPage from '../pages/ReportsPage';

import AdminAuditPage from '../pages/AdminAuditPage';
import SystemMonitoringPage from '../pages/SystemMonitoringPage';

import NotFound from '../pages/NotFound';

export const AppRoutes = () => {
  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={<HomeDashboard />} />
        <Route path="/login" element={<Login />} />

        {/* COMMON AUTHENTICATED ROUTES */}
        <Route
          path="/notifications"
          element={
            <ProtectedRoute allowedRoles={['ADMIN', 'TEACHER', 'STUDENT']}>
              <NotificationsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/reports"
          element={
            <ProtectedRoute allowedRoles={['ADMIN', 'TEACHER', 'STUDENT']}>
              <ReportsPage />
            </ProtectedRoute>
          }
        />

        {/* ADMIN PROTECTED ROUTES */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/audit"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <AdminAuditPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/system"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <SystemMonitoringPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/analytics"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <AdminAnalyticsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/attendance"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <AdminAttendancePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/attendance/:sessionId"
          element={
            <ProtectedRoute allowedRoles={['ADMIN', 'TEACHER']}>
              <AttendanceSessionPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/students"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <StudentsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/students/:studentId/register-face"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <FaceRegistrationPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/face-recognition"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <FaceRecognitionPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/teachers"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <TeachersPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/subjects"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <SubjectsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/classes"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <ClassesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/users"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <UsersPage />
            </ProtectedRoute>
          }
        />

        {/* TEACHER PROTECTED ROUTES */}
        <Route
          path="/teacher"
          element={
            <ProtectedRoute allowedRoles={['TEACHER']}>
              <TeacherDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/teacher/analytics"
          element={
            <ProtectedRoute allowedRoles={['TEACHER']}>
              <TeacherAnalyticsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/teacher/attendance"
          element={
            <ProtectedRoute allowedRoles={['TEACHER']}>
              <TeacherAttendancePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/teacher/attendance/:sessionId"
          element={
            <ProtectedRoute allowedRoles={['TEACHER', 'ADMIN']}>
              <AttendanceSessionPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/teacher/students"
          element={
            <ProtectedRoute allowedRoles={['ADMIN', 'TEACHER']}>
              <StudentsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/teacher/face-recognition"
          element={
            <ProtectedRoute allowedRoles={['ADMIN', 'TEACHER']}>
              <FaceRecognitionPage />
            </ProtectedRoute>
          }
        />

        {/* STUDENT PROTECTED ROUTES */}
        <Route
          path="/student"
          element={
            <ProtectedRoute allowedRoles={['STUDENT']}>
              <StudentDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/student/analytics"
          element={
            <ProtectedRoute allowedRoles={['STUDENT']}>
              <StudentAnalyticsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/student/attendance"
          element={
            <ProtectedRoute allowedRoles={['STUDENT']}>
              <MyAttendancePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/student/register-face"
          element={
            <ProtectedRoute allowedRoles={['STUDENT']}>
              <FaceRegistrationPage />
            </ProtectedRoute>
          }
        />

        <Route path="*" element={<NotFound />} />
      </Routes>
    </MainLayout>
  );
};

export default AppRoutes;
