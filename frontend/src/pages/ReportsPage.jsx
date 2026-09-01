import React from 'react';
import { useAuth } from '../context/AuthContext';
import ReportGenerator from '../components/ReportGenerator';
import { FileCheck, ShieldCheck, Download, Award } from 'lucide-react';

export const ReportsPage = () => {
  const { user } = useAuth();
  const role = user?.role || 'STUDENT';

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div>
        <h1 className="text-2xl font-black text-slate-800 tracking-tight">Official Reports & Transcripts</h1>
        <p className="text-xs text-slate-500 mt-1">
          Generate, audit, and download role-authorized PDF attendance reports and predictive risk audits.
        </p>
      </div>

      <ReportGenerator userRole={role} defaultStudentId={user?.student_id || user?.id} />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-1">
          <div className="flex items-center gap-2 text-indigo-600 font-bold text-xs">
            <ShieldCheck className="w-4 h-4" />
            Verified & Authenticated
          </div>
          <p className="text-[11px] text-slate-500 leading-relaxed">
            Reports generated via ReportLab engine contain official metadata timestamps and verification hashes.
          </p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-1">
          <div className="flex items-center gap-2 text-emerald-600 font-bold text-xs">
            <FileCheck className="w-4 h-4" />
            Privacy Protected
          </div>
          <p className="text-[11px] text-slate-500 leading-relaxed">
            All PDF report streams omit passwords, JWT tokens, face embeddings, and biometric raw images.
          </p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-1">
          <div className="flex items-center gap-2 text-purple-600 font-bold text-xs">
            <Award className="w-4 h-4" />
            Role-Based Access Control
          </div>
          <p className="text-[11px] text-slate-500 leading-relaxed">
            Strict IDOR security prevents users from downloading unauthorized reports outside their scope.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ReportsPage;
