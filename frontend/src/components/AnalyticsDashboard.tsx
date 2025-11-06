import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { AnalyticsMetrics } from '../types';

const AnalyticsDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<AnalyticsMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/monitoring/metrics');
      setMetrics(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching metrics:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-slate-400">Loading analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col p-6 overflow-y-auto">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">Analytics Dashboard</h2>
        <p className="text-slate-400">Performance metrics and insights</p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {/* Total Executions */}
        <div className="bg-gradient-to-br from-blue-500/10 to-blue-600/10 border border-blue-500/30 rounded-xl p-6">
          <div className="flex items-center justify-between mb-3">
            <div className="p-3 bg-blue-500/20 rounded-lg">
              <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <span className="text-sm text-blue-400 font-medium">Total</span>
          </div>
          <p className="text-3xl font-bold text-white mb-1">{metrics?.total_executions || 0}</p>
          <p className="text-sm text-slate-400">Workflow executions</p>
        </div>

        {/* Success Rate */}
        <div className="bg-gradient-to-br from-green-500/10 to-green-600/10 border border-green-500/30 rounded-xl p-6">
          <div className="flex items-center justify-between mb-3">
            <div className="p-3 bg-green-500/20 rounded-lg">
              <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <span className="text-sm text-green-400 font-medium">Success</span>
          </div>
          <p className="text-3xl font-bold text-white mb-1">
            {metrics?.success_rate ? `${(metrics.success_rate * 100).toFixed(1)}%` : '0%'}
          </p>
          <p className="text-sm text-slate-400">Success rate</p>
        </div>

        {/* Average Duration */}
        <div className="bg-gradient-to-br from-purple-500/10 to-purple-600/10 border border-purple-500/30 rounded-xl p-6">
          <div className="flex items-center justify-between mb-3">
            <div className="p-3 bg-purple-500/20 rounded-lg">
              <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <span className="text-sm text-purple-400 font-medium">Speed</span>
          </div>
          <p className="text-3xl font-bold text-white mb-1">
            {metrics?.average_duration ? `${metrics.average_duration.toFixed(1)}s` : '0s'}
          </p>
          <p className="text-sm text-slate-400">Avg. duration</p>
        </div>

        {/* Active Executions */}
        <div className="bg-gradient-to-br from-yellow-500/10 to-yellow-600/10 border border-yellow-500/30 rounded-xl p-6">
          <div className="flex items-center justify-between mb-3">
            <div className="p-3 bg-yellow-500/20 rounded-lg">
              <svg className="w-6 h-6 text-yellow-400 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </div>
            <span className="text-sm text-yellow-400 font-medium">Running</span>
          </div>
          <p className="text-3xl font-bold text-white mb-1">{metrics?.active_executions || 0}</p>
          <p className="text-sm text-slate-400">Active now</p>
        </div>

        {/* Failed Executions */}
        <div className="bg-gradient-to-br from-red-500/10 to-red-600/10 border border-red-500/30 rounded-xl p-6">
          <div className="flex items-center justify-between mb-3">
            <div className="p-3 bg-red-500/20 rounded-lg">
              <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <span className="text-sm text-red-400 font-medium">Failed</span>
          </div>
          <p className="text-3xl font-bold text-white mb-1">{metrics?.failed_executions || 0}</p>
          <p className="text-sm text-slate-400">Failed executions</p>
        </div>

        {/* System Health */}
        <div className="bg-gradient-to-br from-cyan-500/10 to-cyan-600/10 border border-cyan-500/30 rounded-xl p-6">
          <div className="flex items-center justify-between mb-3">
            <div className="p-3 bg-cyan-500/20 rounded-lg">
              <svg className="w-6 h-6 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0121 12c0 5.523-4.477 10-10 10S1 17.523 1 12 5.477 2 11 2c1.568 0 3.047.328 4.382.896" />
              </svg>
            </div>
            <span className="text-sm text-cyan-400 font-medium">Status</span>
          </div>
          <p className="text-3xl font-bold text-white mb-1">Healthy</p>
          <p className="text-sm text-slate-400">System status</p>
        </div>
      </div>

      {/* Performance Chart Placeholder */}
      <div className="bg-slate-800/50 border border-slate-600/30 rounded-xl p-6 mb-6">
        <h3 className="text-lg font-semibold text-white mb-4">Execution Trends</h3>
        <div className="h-48 flex items-center justify-center">
          <div className="text-center">
            <svg className="w-16 h-16 text-slate-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
            </svg>
            <p className="text-slate-500 text-sm">Chart visualization coming soon</p>
            <p className="text-slate-600 text-xs mt-1">Real-time execution trends</p>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-slate-800/50 border border-slate-600/30 rounded-xl p-4">
          <p className="text-sm text-slate-400 mb-2">This Hour</p>
          <p className="text-2xl font-bold text-white">--</p>
        </div>
        <div className="bg-slate-800/50 border border-slate-600/30 rounded-xl p-4">
          <p className="text-sm text-slate-400 mb-2">Today</p>
          <p className="text-2xl font-bold text-white">--</p>
        </div>
        <div className="bg-slate-800/50 border border-slate-600/30 rounded-xl p-4">
          <p className="text-sm text-slate-400 mb-2">This Week</p>
          <p className="text-2xl font-bold text-white">--</p>
        </div>
        <div className="bg-slate-800/50 border border-slate-600/30 rounded-xl p-4">
          <p className="text-sm text-slate-400 mb-2">This Month</p>
          <p className="text-2xl font-bold text-white">--</p>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
