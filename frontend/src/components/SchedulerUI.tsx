import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ScheduledJob } from '../types';

const SchedulerUI: React.FC = () => {
  const [jobs, setJobs] = useState<ScheduledJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    fetchScheduledJobs();
  }, []);

  const fetchScheduledJobs = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/execution/schedule');
      setJobs(response.data.jobs || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching scheduled jobs:', error);
      setLoading(false);
    }
  };

  const toggleJobStatus = async (jobId: string, enable: boolean) => {
    try {
      const action = enable ? 'enable' : 'disable';
      await axios.post(`http://localhost:8000/api/execution/schedule/${jobId}/${action}`);
      fetchScheduledJobs();
    } catch (error) {
      console.error(`Error ${enable ? 'enabling' : 'disabling'} job:`, error);
    }
  };

  const deleteJob = async (jobId: string) => {
    if (!window.confirm('Are you sure you want to delete this scheduled job?')) {
      return;
    }
    try {
      await axios.delete(`http://localhost:8000/api/execution/schedule/${jobId}`);
      fetchScheduledJobs();
    } catch (error) {
      console.error('Error deleting job:', error);
    }
  };

  const getScheduleTypeLabel = (type: string) => {
    switch (type) {
      case 'cron':
        return 'Cron';
      case 'interval':
        return 'Interval';
      case 'one_time':
        return 'One-Time';
      default:
        return type;
    }
  };

  const getScheduleTypeColor = (type: string) => {
    switch (type) {
      case 'cron':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'interval':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      case 'one_time':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      default:
        return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-slate-400">Loading scheduled jobs...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Workflow Scheduler</h2>
          <p className="text-slate-400">Manage scheduled workflow executions</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-gradient-to-r from-[#614385] to-[#516395] hover:from-[#553a75] hover:to-[#465685] text-white rounded-lg transition-all shadow-lg flex items-center space-x-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          <span>New Schedule</span>
        </button>
      </div>

      {/* Jobs List */}
      {jobs.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-br from-slate-800/50 to-slate-900/50 rounded-2xl flex items-center justify-center border border-slate-600/30">
              <svg className="w-10 h-10 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-slate-300 text-sm font-medium">No scheduled jobs</p>
            <p className="text-slate-500 text-xs mt-1">Create a schedule to automate workflow execution</p>
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto space-y-4">
          {jobs.map((job) => (
            <div
              key={job.id}
              className="bg-slate-800/50 rounded-xl p-5 border border-slate-600/30 hover:border-slate-500/50 transition-all"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-white font-medium text-lg">{job.workflow_name || job.workflow_id}</h3>
                    <span className={`px-2 py-1 rounded-md text-xs font-medium border ${getScheduleTypeColor(job.schedule_type)}`}>
                      {getScheduleTypeLabel(job.schedule_type)}
                    </span>
                    <span className={`px-2 py-1 rounded-md text-xs font-medium ${
                      job.is_enabled
                        ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                        : 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
                    }`}>
                      {job.is_enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                  <p className="text-slate-400 text-sm mb-3">
                    <span className="text-purple-400 font-mono">{job.schedule}</span>
                  </p>

                  {/* Stats */}
                  <div className="flex items-center space-x-6 text-sm">
                    <div>
                      <span className="text-slate-500">Executions:</span>
                      <span className="text-white ml-2 font-medium">{job.execution_count}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Success:</span>
                      <span className="text-green-400 ml-2 font-medium">{job.success_count}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Failed:</span>
                      <span className="text-red-400 ml-2 font-medium">{job.failure_count}</span>
                    </div>
                    {job.success_count + job.failure_count > 0 && (
                      <div>
                        <span className="text-slate-500">Success Rate:</span>
                        <span className="text-blue-400 ml-2 font-medium">
                          {((job.success_count / (job.success_count + job.failure_count)) * 100).toFixed(0)}%
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Next/Last Run */}
                  <div className="flex items-center space-x-6 mt-3 text-xs text-slate-500">
                    {job.next_run && (
                      <div>
                        Next run: <span className="text-slate-400">{new Date(job.next_run).toLocaleString()}</span>
                      </div>
                    )}
                    {job.last_run && (
                      <div>
                        Last run: <span className="text-slate-400">{new Date(job.last_run).toLocaleString()}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => toggleJobStatus(job.id, !job.is_enabled)}
                    className={`p-2 rounded-lg transition-colors ${
                      job.is_enabled
                        ? 'bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-400'
                        : 'bg-green-500/20 hover:bg-green-500/30 text-green-400'
                    }`}
                    title={job.is_enabled ? 'Disable' : 'Enable'}
                  >
                    {job.is_enabled ? (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    )}
                  </button>
                  <button
                    onClick={() => deleteJob(job.id)}
                    className="p-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors"
                    title="Delete"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal Placeholder */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setShowCreateModal(false)}>
          <div className="bg-slate-800 rounded-2xl p-6 max-w-md w-full mx-4 border border-slate-600/30" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-xl font-bold text-white mb-4">Create Schedule</h3>
            <p className="text-slate-400 mb-6">Schedule creation form coming soon. Use the API directly for now.</p>
            <button
              onClick={() => setShowCreateModal(false)}
              className="w-full py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SchedulerUI;
