import React, { useState } from 'react';
import ChatInterface from './components/ChatInterface.tsx';
import WorkflowVisualization from './components/WorkflowVisualization.tsx';
import ExecutionDashboard from './components/ExecutionDashboard.tsx';
import AnalyticsDashboard from './components/AnalyticsDashboard.tsx';
import SchedulerUI from './components/SchedulerUI.tsx';
import { WorkflowPreview } from './types';
import './app.styles.css';

type ViewType = 'builder' | 'executions' | 'analytics' | 'scheduler';

function App() {
  const [currentWorkflow, setCurrentWorkflow] = useState<WorkflowPreview | undefined>();
  const [currentView, setCurrentView] = useState<ViewType>('builder');

  const NavButton = ({ view, icon, label }: { view: ViewType; icon: React.ReactNode; label: string }) => (
    <button
      onClick={() => setCurrentView(view)}
      className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all ${
        currentView === view
          ? 'bg-gradient-to-r from-[#614385] to-[#516395] text-white shadow-lg'
          : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
      }`}
    >
      {icon}
      <span className="font-medium">{label}</span>
    </button>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-slate-900 to-gray-950 p-4">
      <div className="max-w-7xl mx-auto h-screen flex flex-col">
        {/* Header */}
        <div className="text-center mb-4 flex-shrink-0">
          <img src="/Logo3.png" alt="AgentFlow Logo" className="mx-auto h-32 w-auto" />
        </div>

        {/* Navigation */}
        <div className="flex justify-center space-x-2 mb-4 flex-shrink-0">
          <NavButton
            view="builder"
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            }
            label="Workflow Builder"
          />
          <NavButton
            view="executions"
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            }
            label="Executions"
          />
          <NavButton
            view="analytics"
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            }
            label="Analytics"
          />
          <NavButton
            view="scheduler"
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
            label="Scheduler"
          />
        </div>

        {/* Main Content */}
        <div className="flex-1 min-h-0">
          {currentView === 'builder' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full">
              {/* Chat Interface */}
              <div className="bg-slate-900/40 backdrop-blur-xl border border-slate-700/30 rounded-2xl shadow-2xl overflow-hidden">
                <ChatInterface onWorkflowUpdate={setCurrentWorkflow} />
              </div>

              {/* Workflow Visualization */}
              <div className="bg-slate-900/40 backdrop-blur-xl border border-slate-700/30 rounded-2xl shadow-2xl overflow-hidden">
                <WorkflowVisualization workflow={currentWorkflow} />
              </div>
            </div>
          )}

          {currentView === 'executions' && (
            <div className="bg-slate-900/40 backdrop-blur-xl border border-slate-700/30 rounded-2xl shadow-2xl overflow-hidden h-full">
              <ExecutionDashboard />
            </div>
          )}

          {currentView === 'analytics' && (
            <div className="bg-slate-900/40 backdrop-blur-xl border border-slate-700/30 rounded-2xl shadow-2xl overflow-hidden h-full">
              <AnalyticsDashboard />
            </div>
          )}

          {currentView === 'scheduler' && (
            <div className="bg-slate-900/40 backdrop-blur-xl border border-slate-700/30 rounded-2xl shadow-2xl overflow-hidden h-full">
              <SchedulerUI />
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center mt-4 flex-shrink-0">
          <p className="text-slate-500 text-sm">
            {currentView === 'builder' && 'Describe your automation needs and watch your workflow come to life'}
            {currentView === 'executions' && 'Monitor and control active workflow executions'}
            {currentView === 'analytics' && 'Track performance metrics and system health'}
            {currentView === 'scheduler' && 'Schedule and automate workflow executions'}
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
