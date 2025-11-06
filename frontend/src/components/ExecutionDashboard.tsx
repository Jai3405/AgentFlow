import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { WorkflowExecution } from '../types';

const ExecutionDashboard: React.FC = () => {
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchActiveExecutions();
    const interval = setInterval(fetchActiveExecutions, 3000); // Refresh every 3 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchActiveExecutions = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/execution/active');
      setExecutions(response.data.executions || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching executions:', error);
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-blue-500';
      case 'completed':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      case 'paused':
        return 'bg-yellow-500';
      case 'cancelled':
        return 'bg-gray-500';
      default:
        return 'bg-slate-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return (
          <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        );
      case 'completed':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        );
      case 'failed':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
      case 'paused':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  const handleControlAction = async (executionId: string, action: 'cancel' | 'pause' | 'resume') => {
    try {
      await axios.post(`http://localhost:8000/api/execution/${action}/${executionId}`);
      fetchActiveExecutions();
    } catch (error) {
      console.error(`Error ${action}ing execution:`, error);
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-slate-400">Loading executions...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">Workflow Executions</h2>
        <p className="text-slate-400">Monitor real-time workflow execution status</p>
      </div>

      {/* Executions List */}
      {executions.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-br from-slate-800/50 to-slate-900/50 rounded-2xl flex items-center justify-center border border-slate-600/30">
              <svg className="w-10 h-10 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <p className="text-slate-300 text-sm font-medium">No active executions</p>
            <p className="text-slate-500 text-xs mt-1">Execute a workflow to see it here</p>
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto space-y-4">
          {executions.map((execution) => (
            <div
              key={execution.execution_id}
              className="bg-slate-800/50 rounded-xl p-4 border border-slate-600/30 hover:border-slate-500/50 transition-all"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-start space-x-3 flex-1">
                  <div className={`${getStatusColor(execution.status)} p-2 rounded-lg text-white`}>
                    {getStatusIcon(execution.status)}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-white font-medium">{execution.workflow_name || execution.workflow_id}</h3>
                    <p className="text-sm text-slate-400 mt-1">
                      Started {new Date(execution.started_at).toLocaleString()}
                    </p>
                    {execution.current_step && (
                      <p className="text-sm text-purple-400 mt-1">Current: {execution.current_step}</p>
                    )}
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex space-x-2">
                  {execution.status === 'running' && (
                    <>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleControlAction(execution.execution_id, 'pause');
                        }}
                        className="p-2 bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-400 rounded-lg transition-colors"
                        title="Pause"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleControlAction(execution.execution_id, 'cancel');
                        }}
                        className="p-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors"
                        title="Cancel"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </>
                  )}
                  {execution.status === 'paused' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleControlAction(execution.execution_id, 'resume');
                      }}
                      className="p-2 bg-green-500/20 hover:bg-green-500/30 text-green-400 rounded-lg transition-colors"
                      title="Resume"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>

              {/* Progress Bar */}
              <div className="bg-slate-700/50 rounded-full h-2 overflow-hidden">
                <div
                  className={`${getStatusColor(execution.status)} h-full transition-all duration-500`}
                  style={{ width: `${execution.progress * 100}%` }}
                />
              </div>
              <div className="flex justify-between items-center mt-2">
                <span className="text-xs text-slate-400 capitalize">{execution.status}</span>
                <span className="text-xs text-slate-400">{Math.round(execution.progress * 100)}%</span>
              </div>

              {execution.error_message && (
                <div className="mt-3 p-2 bg-red-500/10 border border-red-500/30 rounded-lg">
                  <p className="text-sm text-red-400">{execution.error_message}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ExecutionDashboard;
