import { useState } from 'react';
import type { Message } from './App';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage = ({ message }: ChatMessageProps) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-gradient-to-r from-cyan-600 to-violet-600 text-white shadow-lg shadow-cyan-500/10'
            : 'bg-zinc-800/80 text-zinc-100 border border-zinc-700/50'
        }`}
      >
        {!isUser && (
          <div className="flex items-center gap-2 mb-1">
            <div className="w-5 h-5 rounded-md bg-gradient-to-br from-cyan-500 via-violet-500 to-fuchsia-500 flex items-center justify-center">
              <svg className="w-3 h-3 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2L8 6H4v4l-4 4 4 4v4h4l4 4 4-4h4v-4l4-4-4-4V6h-4L12 2z" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <span className="text-xs font-bold text-cyan-400 tracking-wide">MOTHBOT</span>
          </div>
        )}
        <p className="whitespace-pre-wrap">{message.content}</p>
        <p className={`text-xs mt-1 font-mono ${isUser ? 'text-cyan-200/70' : 'text-zinc-500'}`}>
          {message.timestamp.toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
};

interface ToolCallDisplayProps {
  message: Message;
}

export const ToolCallDisplay = ({ message }: ToolCallDisplayProps) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const toolCall = message.toolCall!;

  const statusColors = {
    pending: 'text-cyan-400 bg-cyan-400/10 border-cyan-400/30',
    success: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/30',
    error: 'text-red-400 bg-red-400/10 border-red-400/30',
  };

  const statusIcons = {
    pending: (
      <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
      </svg>
    ),
    success: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    ),
    error: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    ),
  };

  // Parse result if it's JSON
  let parsedResult: Record<string, unknown> | null = null;
  if (toolCall.result) {
    try {
      parsedResult = JSON.parse(toolCall.result);
    } catch {
      // Not JSON, use as string
    }
  }

  return (
    <div className="flex justify-start">
      <div className={`max-w-[90%] rounded-xl border ${statusColors[toolCall.status]} overflow-hidden`}>
        {/* Header */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-between gap-3 px-4 py-3 hover:bg-white/5 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-zinc-800 flex items-center justify-center">
              <svg className="w-4 h-4 text-zinc-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <div className="text-left">
              <p className="font-mono text-sm font-medium">{toolCall.name}</p>
              <p className="text-xs opacity-70">
                {toolCall.status === 'pending' ? 'Executing...' : 
                 toolCall.status === 'success' ? 'Completed' : 'Failed'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {statusIcons[toolCall.status]}
            <svg
              className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </button>

        {/* Expanded Content */}
        {isExpanded && (
          <div className="border-t border-current/20 px-4 py-3 space-y-3 bg-black/20">
            {/* Arguments */}
            {Object.keys(toolCall.arguments).length > 0 && (
              <div>
                <p className="text-xs font-medium mb-1 opacity-70">Arguments</p>
                <pre className="text-xs bg-black/30 rounded-lg p-2 overflow-x-auto">
                  {JSON.stringify(toolCall.arguments, null, 2)}
                </pre>
              </div>
            )}

            {/* Result */}
            {toolCall.result && (
              <div>
                <p className="text-xs font-medium mb-1 opacity-70">Result</p>
                {parsedResult ? (
                  <div className="space-y-2">
                    {/* Summary if available */}
                    {parsedResult.summary && (
                      <p className="text-sm bg-black/30 rounded-lg p-2">
                        {String(parsedResult.summary)}
                      </p>
                    )}
                    {/* Full result */}
                    <details className="text-xs">
                      <summary className="cursor-pointer opacity-70 hover:opacity-100">
                        View full response
                      </summary>
                      <pre className="bg-black/30 rounded-lg p-2 mt-1 overflow-x-auto">
                        {JSON.stringify(parsedResult, null, 2)}
                      </pre>
                    </details>
                  </div>
                ) : (
                  <pre className="text-xs bg-black/30 rounded-lg p-2 overflow-x-auto whitespace-pre-wrap">
                    {toolCall.result}
                  </pre>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
