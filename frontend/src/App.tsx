import React, { useState } from 'react';
import ChatInterface from './components/ChatInterface.tsx';
import WorkflowVisualization from './components/WorkflowVisualization.tsx';
import { WorkflowPreview } from './types';
import './app.styles.css';

function App() {
  const [currentWorkflow, setCurrentWorkflow] = useState<WorkflowPreview | undefined>();

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-slate-900 to-gray-950 p-4">
      <div className="max-w-7xl mx-auto h-screen flex flex-col">
        {/* Header */}
        <div className="text-center mb-6 flex-shrink-0">
          <img src="https://i.ibb.co/gLsr9YVF/Agent-Flow.png" alt="AgentFlow Logo" className="mx-auto h-48 w-auto" />

        </div>

        {/* Main Content - Fixed height with proper overflow */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-0">
          {/* Chat Interface */}
          <div className="bg-slate-900/40 backdrop-blur-xl border border-slate-700/30 rounded-2xl shadow-2xl overflow-hidden">
            <ChatInterface onWorkflowUpdate={setCurrentWorkflow} />
          </div>

          {/* Workflow Visualization */}
          <div className="bg-slate-900/40 backdrop-blur-xl border border-slate-700/30 rounded-2xl shadow-2xl overflow-hidden">
            <WorkflowVisualization workflow={currentWorkflow} />
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-6 flex-shrink-0">
          <p className="text-slate-500">Describe your automation needs and watch your workflow come to life</p>
        </div>
      </div>
    </div>
  );
}

export default App;
