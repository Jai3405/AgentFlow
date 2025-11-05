import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Message, ChatResponse } from '../types';

interface ChatInterfaceProps {
  onWorkflowUpdate?: (workflow: any) => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onWorkflowUpdate }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "Hi! I'm AgentFlow, your AI workflow builder. I can help you create automation workflows just by talking to me. What business process would you like to automate?",
      timestamp: new Date().toISOString()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [workflowProgress, setWorkflowProgress] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await axios.post<ChatResponse>('http://localhost:8000/api/chat', {
        message: inputValue,
        conversation_id: conversationId
      });

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMessage]);
      setConversationId(response.data.conversation_id);
      setWorkflowProgress(response.data.workflow_progress);

      if (response.data.workflow_preview && onWorkflowUpdate) {
        onWorkflowUpdate(response.data.workflow_preview);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-slate-700/30">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-[#614385] to-[#516395] rounded-full flex items-center justify-center shadow-lg">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                      d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-white">New Workflow</h1>
              <p className="text-sm text-slate-500">Building by conversation</p>
            </div>
          </div>
          <button className="p-2 hover:bg-slate-700 rounded-lg transition-colors">
            <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {workflowProgress > 0 && (
          <div className="bg-slate-800 rounded-full h-2 overflow-hidden">
            <div 
              className="bg-gradient-to-r from-[#614385] to-[#516395] h-full transition-all duration-500 rounded-full shadow-sm"
              style={{ width: `${workflowProgress * 100}%` }}
            />
          </div>
        )}
      </div>

      {/* Messages Area - Fixed overflow */}
      <div className="flex-1 overflow-y-auto px-4 py-2">
        <div className="space-y-4 min-h-full">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              } animate-fadeIn`}
            >
              {message.role === 'assistant' && (
                <div className="w-8 h-8 bg-gradient-to-br from-[#614385] to-[#516395] rounded-full flex items-center justify-center mr-3 flex-shrink-0 shadow-lg">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
              )}
              <div
                className={`max-w-md px-4 py-3 rounded-2xl shadow-lg ${
                  message.role === 'user'
                    ? 'bg-gradient-to-r from-[#614385] to-[#516395] text-white'
                    : 'bg-slate-800/60 text-slate-100 border border-slate-600/40'
                }`}
              >
                <p className={`${message.role === 'user' ? 'text-white' : 'text-slate-100'} leading-relaxed`}>
                  {message.content}
                </p>
                <p className={`text-xs mt-2 ${message.role === 'user' ? 'text-slate-200' : 'text-slate-400'}`}>
                  {new Date(message.timestamp).toLocaleTimeString()}
                </p>
              </div>
              {message.role === 'user' && (
                <div className="w-8 h-8 bg-slate-700 rounded-full ml-3 flex-shrink-0 flex items-center justify-center">
                  <svg className="w-4 h-4 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
              )}
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start animate-fadeIn">
              <div className="w-8 h-8 bg-gradient-to-br from-[#614385] to-[#516395] rounded-full flex items-center justify-center mr-3 shadow-lg">
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div className="bg-slate-800/60 border border-slate-600/40 shadow-lg px-4 py-3 rounded-2xl">
                <div className="typing-dots flex space-x-1">
                  <span className="w-2 h-2 bg-slate-400 rounded-full"></span>
                  <span className="w-2 h-2 bg-slate-400 rounded-full"></span>
                  <span className="w-2 h-2 bg-slate-400 rounded-full"></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="flex-shrink-0 p-4 border-t border-slate-700/30">
        <div className="flex items-end space-x-3">
          <button className="p-2 hover:bg-slate-700 rounded-lg transition-colors group">
            <svg className="w-5 h-5 text-slate-400 group-hover:text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
            </svg>
          </button>
          <div className="flex-1">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Describe your workflow needs..."
              className="w-full resize-none outline-none bg-slate-800/50 text-white placeholder-slate-400 leading-relaxed p-3 rounded-lg border border-slate-600/40 focus:border-slate-500 transition-colors"
              rows={1}
              style={{ minHeight: '44px', maxHeight: '120px' }}
              disabled={isLoading}
            />
          </div>
          <button
            onClick={sendMessage}
            disabled={isLoading || !inputValue.trim()}
            className="p-3 bg-gradient-to-r from-[#614385] to-[#516395] hover:from-[#553a75] hover:to-[#465685] disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-all shadow-lg"
          >
            {isLoading ? (
              <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                      d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
          </button>
        </div>

        {/* Quick Actions */}
        <div className="flex items-center space-x-4 mt-3 pt-3 border-t border-slate-700/30">
          <button className="flex items-center space-x-2 text-sm text-slate-400 hover:text-slate-300 transition-colors">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
            <span>Templates</span>
          </button>
          <button className="flex items-center space-x-2 text-sm text-slate-400 hover:text-slate-300 transition-colors">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span>Examples</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;