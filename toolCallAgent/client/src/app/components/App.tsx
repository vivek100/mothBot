import { useEffect, useState, useRef, useCallback } from 'react';

import type { PipecatBaseChildProps } from '@pipecat-ai/voice-ui-kit';
import {
  ConnectButton,
  UserAudioControl,
} from '@pipecat-ai/voice-ui-kit';

import type { TransportType } from '../../config';
import { TransportSelect } from './TransportSelect';
import { ChatMessage, ToolCallDisplay } from './ChatMessage';

// Message types for our chat
export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'tool';
  content: string;
  timestamp: Date;
  toolCall?: {
    name: string;
    arguments: Record<string, unknown>;
    result?: string;
    status: 'pending' | 'success' | 'error';
  };
}

interface AppProps extends PipecatBaseChildProps {
  transportType: TransportType;
  onTransportChange: (type: TransportType) => void;
  availableTransports: TransportType[];
}

export const App = ({
  client,
  handleConnect,
  handleDisconnect,
  transportType,
  onTransportChange,
  availableTransports,
}: AppProps) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when messages change
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    client?.initDevices();
  }, [client]);

  // Track connection state from client
  useEffect(() => {
    if (!client) return;

    const handleConnected = () => {
      console.log('Client connected event received');
      setIsConnected(true);
    };

    const handleBotReady = () => {
      console.log('Bot ready event received - enabling text input');
      setIsConnected(true);
    };

    const handleDisconnected = () => {
      console.log('Client disconnected event received');
      setIsConnected(false);
    };

    const handleError = (error: unknown) => {
      console.error('Client error:', error);
      setIsConnected(false);
    };

    const handleTransportStateChanged = (state: string) => {
      console.log('Transport state changed:', state);
      if (state === 'ready' || state === 'connected') {
        setIsConnected(true);
      } else if (state === 'disconnected' || state === 'error') {
        setIsConnected(false);
      }
    };

    // Listen for connection state changes
    // botReady is the key event that indicates the bot is ready to receive messages
    client.on('connected', handleConnected);
    client.on('botReady', handleBotReady);
    client.on('disconnected', handleDisconnected);
    client.on('error', handleError);
    client.on('transportStateChanged', handleTransportStateChanged);

    // Check if already connected
    if (client.connected) {
      console.log('Client already connected on mount');
      setIsConnected(true);
    }

    // Also check state
    if (client.state === 'ready') {
      console.log('Client state is ready on mount');
      setIsConnected(true);
    }

    return () => {
      client.off('connected', handleConnected);
      client.off('botReady', handleBotReady);
      client.off('disconnected', handleDisconnected);
      client.off('error', handleError);
      client.off('transportStateChanged', handleTransportStateChanged);
    };
  }, [client]);

  // Listen for RTVI events
  useEffect(() => {
    if (!client) return;

    // Handle transcript events (user speech)
    const handleUserTranscript = (data: { text: string; final: boolean }) => {
      if (data.final && data.text.trim()) {
        addMessage({
          role: 'user',
          content: data.text,
        });
      }
    };

    // Handle bot responses
    const handleBotTranscript = (data: { text: string }) => {
      if (data.text.trim()) {
        // Update or add assistant message
        setMessages(prev => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg?.role === 'assistant' && !lastMsg.toolCall) {
            // Append to existing assistant message
            return [
              ...prev.slice(0, -1),
              { ...lastMsg, content: lastMsg.content + data.text },
            ];
          }
          // New assistant message
          return [
            ...prev,
            {
              id: crypto.randomUUID(),
              role: 'assistant',
              content: data.text,
              timestamp: new Date(),
            },
          ];
        });
      }
    };

    // Handle function calls (LLMFunctionCallData from @pipecat-ai/client-js)
    const handleFunctionCall = (data: { 
      function_name: string; 
      tool_call_id: string;
      args: Record<string, unknown>;  // Note: it's 'args' not 'arguments'
    }) => {
      console.log('🔧 Function call received:', data);
      addMessage({
        role: 'tool',
        content: `Calling ${data.function_name}...`,
        toolCall: {
          name: data.function_name,
          arguments: data.args || {},
          status: 'pending',
        },
      });
    };

    // Handle function call results (custom RTVI message from our backend)
    const handleFunctionCallResult = (data: {
      function_name: string;
      tool_call_id: string;
      args: Record<string, unknown>;
      result: string;
    }) => {
      console.log('✅ Function call result received:', data);
      setMessages(prev => {
        // Find the pending tool call message
        const idx = prev.findIndex(
          m => m.toolCall?.name === data.function_name && m.toolCall?.status === 'pending'
        );
        if (idx !== -1) {
          const updated = [...prev];
          updated[idx] = {
            ...updated[idx],
            content: `Tool: ${data.function_name}`,
            toolCall: {
              ...updated[idx].toolCall!,
              result: data.result,
              status: 'success',
            },
          };
          return updated;
        }
        return prev;
      });
    };

    // Handle server messages (for custom RTVI messages like function call results)
    const handleServerMessage = (data: unknown) => {
      console.log('📨 Server message received:', data);
      // The data is the payload directly (not wrapped in a message object)
      const payload = data as { type?: string; function_name?: string; tool_call_id?: string; args?: Record<string, unknown>; result?: string };
      if (payload.type === 'function-call-result' && payload.function_name) {
        handleFunctionCallResult({
          function_name: payload.function_name,
          tool_call_id: payload.tool_call_id || '',
          args: payload.args || {},
          result: payload.result || '',
        });
      }
    };

    // Subscribe to events (using RTVIEvent names from @pipecat-ai/client-js)
    client.on('userTranscript', handleUserTranscript);
    client.on('botLlmText', handleBotTranscript);  // Use botLlmText for streamed LLM output
    client.on('llmFunctionCall', handleFunctionCall);
    client.on('serverMessage', handleServerMessage);  // Listen for custom server messages

    // Log all events for debugging
    const logAllEvents = (eventName: string) => (data: unknown) => {
      console.log(`📡 Event [${eventName}]:`, data);
    };
    
    // Subscribe to additional events for debugging
    client.on('botStartedSpeaking', logAllEvents('botStartedSpeaking'));
    client.on('botStoppedSpeaking', logAllEvents('botStoppedSpeaking'));

    return () => {
      client.off('userTranscript', handleUserTranscript);
      client.off('botLlmText', handleBotTranscript);
      client.off('llmFunctionCall', handleFunctionCall);
      client.off('serverMessage', handleServerMessage);
      client.off('botStartedSpeaking', logAllEvents('botStartedSpeaking'));
      client.off('botStoppedSpeaking', logAllEvents('botStoppedSpeaking'));
    };
  }, [client]);

  const addMessage = (msg: Omit<Message, 'id' | 'timestamp'>) => {
    setMessages(prev => [
      ...prev,
      {
        ...msg,
        id: crypto.randomUUID(),
        timestamp: new Date(),
      },
    ]);
  };

  const handleSendText = async () => {
    if (!inputText.trim() || !client || !isConnected) return;

    const text = inputText.trim();
    setInputText('');
    setIsProcessing(true);

    // Add user message to chat
    addMessage({
      role: 'user',
      content: text,
    });

    try {
      // Use the Pipecat client's sendText method
      // This sends text to the LLM and triggers a response
      await client.sendText(text, {
        run_immediately: true,  // Process immediately
        audio_response: true,   // Get audio response from TTS
      });
    } catch (error) {
      console.error('Failed to send message:', error);
      addMessage({
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to send message'}`,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendText();
    }
  };

  const handleConnectClick = async () => {
    try {
      console.log('Attempting to connect...');
      await handleConnect();
      // Connection state will be updated by the 'connected' event listener
      console.log('Connect call completed');
      addMessage({
        role: 'assistant',
        content: 'Connecting... I\'m your Diagnostic Agent. You can speak or type to interact with me. Try asking me to "check oxygen levels" or "run a full diagnostic".',
      });
    } catch (error) {
      console.error('Connection failed:', error);
      setIsConnected(false);
      addMessage({
        role: 'assistant',
        content: `Connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      });
    }
  };

  const handleDisconnectClick = async () => {
    try {
      console.log('Attempting to disconnect...');
      await handleDisconnect();
      // Connection state will be updated by the 'disconnected' event listener
      console.log('Disconnect call completed');
      addMessage({
        role: 'assistant',
        content: 'Disconnected. Click Connect to start a new session.',
      });
    } catch (error) {
      console.error('Disconnect failed:', error);
    }
  };

  const showTransportSelector = availableTransports.length > 1;

  return (
    <div className="flex flex-col w-full h-full bg-zinc-950">
      {/* Header */}
      <header className="flex items-center justify-between gap-4 p-4 border-b border-zinc-800 bg-zinc-900">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
            </svg>
          </div>
          <div>
            <h1 className="text-lg font-semibold text-white">Diagnostic Agent</h1>
            <p className="text-xs text-zinc-400">Speech-to-Speech • Tool Calling</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          {showTransportSelector && (
            <TransportSelect
              transportType={transportType}
              onTransportChange={onTransportChange}
              availableTransports={availableTransports}
            />
          )}
          <UserAudioControl size="lg" />
          <ConnectButton
            size="lg"
            onConnect={handleConnectClick}
            onDisconnect={handleDisconnectClick}
          />
        </div>
      </header>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">Welcome to Diagnostic Agent</h2>
            <p className="text-zinc-400 max-w-md mb-6">
              Connect to start a conversation. You can speak or type to interact with me.
              I can run diagnostics, check system status, and execute multi-step plans.
            </p>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="px-4 py-2 rounded-lg bg-zinc-800/50 text-zinc-300">
                "Check oxygen levels"
              </div>
              <div className="px-4 py-2 rounded-lg bg-zinc-800/50 text-zinc-300">
                "Scan the hull"
              </div>
              <div className="px-4 py-2 rounded-lg bg-zinc-800/50 text-zinc-300">
                "Run a full diagnostic"
              </div>
              <div className="px-4 py-2 rounded-lg bg-zinc-800/50 text-zinc-300">
                "What plans are available?"
              </div>
            </div>
          </div>
        )}

        {messages.map((message) => (
          message.toolCall ? (
            <ToolCallDisplay key={message.id} message={message} />
          ) : (
            <ChatMessage key={message.id} message={message} />
          )
        ))}

        {isProcessing && (
          <div className="flex items-center gap-2 text-zinc-400">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
            <span className="text-sm">Processing...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-zinc-800 bg-zinc-900">
        <div className="flex items-center gap-3 max-w-4xl mx-auto">
          <div className="flex-1 relative">
            <input
              ref={inputRef}
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={isConnected ? "Type a message or speak..." : "Connect to start chatting..."}
              disabled={!isConnected || isProcessing}
              className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>
          <button
            onClick={handleSendText}
            disabled={!isConnected || !inputText.trim() || isProcessing}
            className="px-4 py-3 bg-emerald-600 hover:bg-emerald-500 disabled:bg-zinc-700 disabled:cursor-not-allowed rounded-xl text-white font-medium transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
        <p className="text-center text-xs text-zinc-500 mt-2">
          Press Enter to send • Use microphone for voice input
        </p>
      </div>
    </div>
  );
};
