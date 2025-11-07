import React from 'react';
import { WorkflowPreview } from '../types';

interface WorkflowVisualizationProps {
  workflow?: WorkflowPreview;
}

const WorkflowVisualization: React.FC<WorkflowVisualizationProps> = ({ workflow }) => {
  const getStepIcon = (type: string) => {
    switch(type) {
      case 'email':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        );
      case 'data':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        );
      case 'process':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        );
      case 'notification':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
        );
      case 'decision':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        );
    }
  };

  const getStepColor = (type: string) => {
    // All step icons use the accent gradient
    return 'from-[#614385] to-[#516395]';
  };

  return (
    <div className="h-full flex flex-col p-6">
      {/* Header */}
      <div className="mb-6 pb-4 border-b border-slate-700/30">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold text-white">Workflow Preview</h2>
          <button className="p-1.5 hover:bg-slate-700 rounded-lg transition-colors">
            <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
            </svg>
          </button>
        </div>
        <p className="text-sm text-slate-400">Your automation blueprint</p>
      </div>

      {/* Workflow Steps or Empty State */}
      {!workflow || !workflow.steps?.length ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-br from-slate-800/50 to-slate-900/50 rounded-2xl flex items-center justify-center border border-slate-600/30">
              <svg className="w-10 h-10 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} 
                      d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <p className="text-slate-300 text-sm font-medium">Start describing your workflow</p>
            <p className="text-slate-500 text-xs mt-1">I'll build it in real-time</p>
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto space-y-4 pr-2 scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-transparent hover:scrollbar-thumb-slate-500">
          {workflow.steps.map((step, index) => (
            <div key={step.id} className="animate-slideIn" style={{ animationDelay: `${index * 100}ms` }}>
              <div className="flex items-start space-x-3">
                {/* Step Icon */}
                <div className={`w-10 h-10 bg-gradient-to-br ${getStepColor(step.type)} rounded-xl flex items-center justify-center text-white flex-shrink-0 shadow-lg`}>
                  {getStepIcon(step.type)}
                </div>
                
                {/* Step Content */}
                <div className="flex-1 bg-slate-800/50 rounded-xl p-4 shadow-lg border border-slate-600/30 hover:border-slate-500/50 transition-all">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="font-medium text-slate-100 mb-1">{step.name}</h4>
                      <p className="text-sm text-slate-300 leading-relaxed">{step.description}</p>

                      {/* Step Details */}
                      {step.details && Object.keys(step.details).length > 0 && (
                        <div className="mt-3 pt-3 border-t border-slate-700/50">
                          <div className="space-y-1.5">
                            {Object.entries(step.details).map(([key, value]) => (
                              <div key={key} className="flex items-start text-xs">
                                <span className="text-slate-400 font-medium min-w-[80px] capitalize">
                                  {key.replace(/_/g, ' ')}:
                                </span>
                                <span className="text-slate-300 ml-2">
                                  {Array.isArray(value) ? value.join(', ') : String(value)}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                    <button className="p-1 hover:bg-slate-600/50 rounded-lg transition-colors flex-shrink-0 ml-2">
                      <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
              
              {/* Connector Line */}
              {index < workflow.steps.length - 1 && (
                <div className="ml-5 my-2">
                  <div className="w-0.5 h-8 bg-gradient-to-b from-slate-500/60 to-transparent"></div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Action Buttons */}
      <div className="mt-6 pt-4 border-t border-gray-600/30 flex space-x-3">
        <button className="flex-1 py-2.5 px-4 bg-gray-700/50 hover:bg-gray-600/50 text-gray-300 border border-gray-600/50 rounded-lg transition-colors text-sm font-medium">
          Save Draft
        </button>
        <button className="flex-1 py-2.5 px-4 bg-gradient-to-r from-[#614385] to-[#516395] hover:from-[#553a75] hover:to-[#465685] text-white rounded-lg transition-colors text-sm font-medium shadow-lg">
          Deploy
        </button>
      </div>

      {/* Quick Stats */}
      {workflow && workflow.steps?.length > 0 && (
        <div className="mt-4 grid grid-cols-2 gap-3">
          <div className="bg-gray-700/50 border border-gray-600/30 rounded-lg p-3">
            <p className="text-xs text-gray-400">Total Steps</p>
            <p className="text-lg font-semibold text-white">{workflow.steps.length}</p>
          </div>
          <div className="bg-gray-700/50 border border-gray-600/30 rounded-lg p-3">
            <p className="text-xs text-gray-400">Est. Runtime</p>
            <p className="text-lg font-semibold text-white">~2min</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowVisualization;