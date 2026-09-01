import React, { useState, useEffect } from 'react';
import { FileText, Download, Calendar, Layers, BookOpen, User, RefreshCw, AlertCircle } from 'lucide-react';
import reportService from '../services/reportService';
import { getClasses } from '../services/classService';
import { getSubjects } from '../services/subjectService';

const ReportGenerator = ({ userRole, defaultStudentId = null }) => {
  const [reportType, setReportType] = useState(
    userRole === 'STUDENT' ? 'STUDENT_ATTENDANCE' : 'CLASS_ATTENDANCE'
  );

  const [classesList, setClassesList] = useState([]);
  const [subjectsList, setSubjectsList] = useState([]);
  const [selectedClass, setSelectedClass] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const [isGenerating, setIsGenerating] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    const loadMetadata = async () => {
      if (userRole === 'ADMIN' || userRole === 'TEACHER') {
        try {
          const [cls, subs] = await Promise.all([getClasses(), getSubjects()]);
          setClassesList(cls);
          setSubjectsList(subs);
          if (cls.length > 0) setSelectedClass(cls[0].id || cls[0]._id);
        } catch (err) {
          console.error('Failed to load classes/subjects for reporting:', err);
        }
      }
    };
    loadMetadata();
  }, [userRole]);

  const handleGenerateReport = async (e) => {
    e.preventDefault();
    setIsGenerating(true);
    setErrorMsg('');
    setSuccessMsg('');

    try {
      let result = null;

      if (reportType === 'STUDENT_ATTENDANCE') {
        result = await reportService.generateStudentReport({
          student_id: defaultStudentId,
          date_from: dateFrom || null,
          date_to: dateTo || null,
          subject_id: selectedSubject || null,
        });
      } else if (reportType === 'CLASS_ATTENDANCE') {
        if (!selectedClass) throw new Error('Please select a class section.');
        result = await reportService.generateClassReport({
          class_id: selectedClass,
          subject_id: selectedSubject || null,
          date_from: dateFrom || null,
          date_to: dateTo || null,
        });
      } else if (reportType === 'SUBJECT_ATTENDANCE') {
        if (!selectedClass || !selectedSubject) throw new Error('Please select both class and subject.');
        result = await reportService.generateSubjectReport({
          class_id: selectedClass,
          subject_id: selectedSubject,
          date_from: dateFrom || null,
          date_to: dateTo || null,
        });
      } else if (reportType === 'ANALYTICS_RISK') {
        result = await reportService.generateAnalyticsReport({
          class_id: selectedClass || null,
          student_id: defaultStudentId || null,
        });
      }

      if (result && result.id) {
        setSuccessMsg(`PDF Report '${result.file_name}' generated successfully.`);
        // Trigger file download
        await reportService.downloadReportFile(result.id, result.file_name);
      }
    } catch (err) {
      console.error('Report generation error:', err);
      setErrorMsg(err.response?.data?.detail || err.message || 'Failed to generate PDF report.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-5">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
          <FileText className="w-5 h-5 text-indigo-600" />
          Generate Official Attendance PDF Report
        </h3>
        <span className="text-xs font-semibold bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded-full border border-indigo-100">
          ReportLab PDF Engine
        </span>
      </div>

      {errorMsg && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 p-3.5 rounded-xl text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />
          {errorMsg}
        </div>
      )}

      {successMsg && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-700 p-3.5 rounded-xl text-xs flex items-center gap-2 font-medium">
          <Download className="w-4 h-4 text-emerald-600 shrink-0" />
          {successMsg}
        </div>
      )}

      <form onSubmit={handleGenerateReport} className="space-y-4 text-xs">
        {/* Report Type Selector */}
        <div>
          <label className="block font-bold text-slate-700 mb-1.5 uppercase tracking-wider">Select Report Type</label>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2">
            {userRole === 'STUDENT' ? (
              <>
                <button
                  type="button"
                  onClick={() => setReportType('STUDENT_ATTENDANCE')}
                  className={`p-3 rounded-xl border text-left font-semibold transition-all ${
                    reportType === 'STUDENT_ATTENDANCE'
                      ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                      : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  My Attendance Report
                </button>
                <button
                  type="button"
                  onClick={() => setReportType('ANALYTICS_RISK')}
                  className={`p-3 rounded-xl border text-left font-semibold transition-all ${
                    reportType === 'ANALYTICS_RISK'
                      ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                      : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  My Risk Analytics Report
                </button>
              </>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => setReportType('CLASS_ATTENDANCE')}
                  className={`p-3 rounded-xl border text-left font-semibold transition-all ${
                    reportType === 'CLASS_ATTENDANCE'
                      ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                      : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  Class Roster Report
                </button>
                <button
                  type="button"
                  onClick={() => setReportType('SUBJECT_ATTENDANCE')}
                  className={`p-3 rounded-xl border text-left font-semibold transition-all ${
                    reportType === 'SUBJECT_ATTENDANCE'
                      ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                      : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  Subject Statistics Report
                </button>
                <button
                  type="button"
                  onClick={() => setReportType('STUDENT_ATTENDANCE')}
                  className={`p-3 rounded-xl border text-left font-semibold transition-all ${
                    reportType === 'STUDENT_ATTENDANCE'
                      ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                      : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  Student Transcript Report
                </button>
                <button
                  type="button"
                  onClick={() => setReportType('ANALYTICS_RISK')}
                  className={`p-3 rounded-xl border text-left font-semibold transition-all ${
                    reportType === 'ANALYTICS_RISK'
                      ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                      : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  Predictive Risk Report
                </button>
              </>
            )}
          </div>
        </div>

        {/* Filters Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          {(userRole === 'ADMIN' || userRole === 'TEACHER') && reportType !== 'STUDENT_ATTENDANCE' && (
            <div>
              <label className="block font-bold text-slate-700 mb-1.5 uppercase">Class Section</label>
              <select
                value={selectedClass}
                onChange={(e) => setSelectedClass(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">Select Class...</option>
                {classesList.map((cls) => (
                  <option key={cls.id || cls._id} value={cls.id || cls._id}>
                    {cls.name || cls.class_name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {(userRole === 'ADMIN' || userRole === 'TEACHER') && (
            <div>
              <label className="block font-bold text-slate-700 mb-1.5 uppercase">Subject (Optional)</label>
              <select
                value={selectedSubject}
                onChange={(e) => setSelectedSubject(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">All Subjects</option>
                {subjectsList.map((sub) => (
                  <option key={sub.id || sub._id} value={sub.id || sub._id}>
                    {sub.subject_code} - {sub.subject_name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="block font-bold text-slate-700 mb-1.5 uppercase">Date From</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block font-bold text-slate-700 mb-1.5 uppercase">Date To</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        {/* Submit Button */}
        <div className="pt-2 flex justify-end">
          <button
            type="submit"
            disabled={isGenerating}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-xl font-bold transition-colors flex items-center gap-2 shadow-xs"
          >
            {isGenerating ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Generating PDF Report...
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                Generate & Download PDF
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ReportGenerator;
