import { useEffect, useState, useRef, useCallback } from 'react';
import Link from 'next/link';

import type { PipecatBaseChildProps } from '@pipecat-ai/voice-ui-kit';
import {
  ConnectButton,
  UserAudioControl,
} from '@pipecat-ai/voice-ui-kit';

import type { TransportType } from '../../config';
import { TransportSelect } from './TransportSelect';
import { ChatMessage, ToolCallDisplay } from './ChatMessage';
import { SpaceshipWireframe, getSectionsFromToolCall, type ActiveScan, type ShipSection } from './SpaceshipWireframe';

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
  error?: string | null;
}

export const App = ({
  client,
  handleConnect,
  handleDisconnect,
  transportType,
  onTransportChange,
  availableTransports,
  error,
}: AppProps) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeScans, setActiveScans] = useState<ActiveScan[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Helper to add active scans from tool calls
  const addActiveScans = useCallback((toolName: string, args?: Record<string, unknown>, status: ActiveScan['status'] = 'scanning') => {
    const sections = getSectionsFromToolCall(toolName, args);
    if (sections.length > 0) {
      setActiveScans(prev => {
        // Remove existing scans for these sections and add new ones
        const filtered = prev.filter(s => !sections.includes(s.section));
        const newScans: ActiveScan[] = sections.map(section => ({
          section,
          status,
          label: status === 'scanning' ? 'Scanning...' : undefined,
        }));
        return [...filtered, ...newScans];
      });
    }
  }, []);

  // Helper to update scan status based on tool result
  const updateScanStatus = useCallback((toolName: string, args: Record<string, unknown>, result: string) => {
    const sections = getSectionsFromToolCall(toolName, args);
    if (sections.length === 0) return;

    try {
      const parsed = JSON.parse(result);
      let status: ActiveScan['status'] = 'ok';
      let label: string | undefined;

      // Determine status based on tool result
      if (parsed.status === 'error') {
        status = 'critical';
        label = 'Error';
      } else if (parsed.result) {
        const res = parsed.result;
        
        // Check for critical conditions
        if (res.breach_detected === true) {
          status = 'critical';
          label = 'Breach detected!';
        } else if (res.status === 'CRITICAL_LOW' || res.status === 'CRITICAL') {
          status = 'critical';
          label = res.level ? `${res.level}%` : 'Critical';
        } else if (res.status === 'WARNING' || res.recommendation === 'ALERT') {
          status = 'warning';
          label = res.level ? `${res.level}%` : 'Warning';
        } else if (res.status === 'NORMAL' || res.status === 'OK' || res.recommendation === 'MONITOR') {
          status = 'ok';
          label = res.level ? `${res.level}%` : res.integrity_percent ? `${res.integrity_percent}` : 'OK';
        }

        // Handle temperature results
        if (res.temperature !== undefined) {
          label = `${res.temperature}°${res.unit?.toUpperCase() || 'C'}`;
          if (res.status === 'WARNING' || res.status === 'HIGH') {
            status = 'warning';
          } else if (res.status === 'CRITICAL') {
            status = 'critical';
          }
        }

        // Handle system scan results
        if (toolName === 'scan_systems') {
          const systems = ['power', 'navigation', 'life_support', 'communications'];
          systems.forEach(sys => {
            const sysStatus = res[sys] || res[sys.replace('_', '')];
            if (sysStatus) {
              let scanStatus: ActiveScan['status'] = 'ok';
              if (sysStatus === 'WARNING' || sysStatus === 'DEGRADED') scanStatus = 'warning';
              if (sysStatus === 'CRITICAL' || sysStatus === 'OFFLINE') scanStatus = 'critical';
              
              setActiveScans(prev => {
                const filtered = prev.filter(s => s.section !== sys);
                return [...filtered, { section: sys as ShipSection, status: scanStatus, label: sysStatus }];
              });
            }
          });
          return; // Don't process further for scan_systems
        }
      }

      // Update the scans for these sections
      setActiveScans(prev => {
        const filtered = prev.filter(s => !sections.includes(s.section));
        const newScans: ActiveScan[] = sections.map(section => ({
          section,
          status,
          label,
        }));
        return [...filtered, ...newScans];
      });

      // Clear scans after 10 seconds
      setTimeout(() => {
        setActiveScans(prev => prev.filter(s => !sections.includes(s.section)));
      }, 10000);

    } catch {
      // If parsing fails, just mark as ok
      setActiveScans(prev => {
        const filtered = prev.filter(s => !sections.includes(s.section));
        const newScans: ActiveScan[] = sections.map(section => ({
          section,
          status: 'ok',
        }));
        return [...filtered, ...newScans];
      });
    }
  }, []);

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
      
      // Trigger spaceship visualization scan
      addActiveScans(data.function_name, data.args, 'scanning');
      
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
      
      // Update spaceship visualization with result status
      updateScanStatus(data.function_name, data.args, data.result);
      
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
    const handleBotStartedSpeaking = () => {
      console.log('📡 Event [botStartedSpeaking]');
    };
    const handleBotStoppedSpeaking = () => {
      console.log('📡 Event [botStoppedSpeaking]');
    };
    
    // Subscribe to additional events for debugging
    client.on('botStartedSpeaking', handleBotStartedSpeaking);
    client.on('botStoppedSpeaking', handleBotStoppedSpeaking);

    return () => {
      client.off('userTranscript', handleUserTranscript);
      client.off('botLlmText', handleBotTranscript);
      client.off('llmFunctionCall', handleFunctionCall);
      client.off('serverMessage', handleServerMessage);
      client.off('botStartedSpeaking', handleBotStartedSpeaking);
      client.off('botStoppedSpeaking', handleBotStoppedSpeaking);
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
      if (handleConnect) {
        await handleConnect();
      }
      // Connection state will be updated by the 'connected' event listener
      console.log('Connect call completed');
      addMessage({
        role: 'assistant',
        content: 'Connecting... I\'m MOTHBOT, your ship diagnostic AI. You can speak or type to interact with me. Try asking me to "check oxygen levels" or "scan the hull".',
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
      if (handleDisconnect) {
        await handleDisconnect();
      }
      // Connection state will be updated by the 'disconnected' event listener
      console.log('Disconnect call completed');
      // Clear active scans on disconnect
      setActiveScans([]);
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
      <header className="flex items-center justify-between gap-4 p-4 border-b border-zinc-800 bg-zinc-900/80 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 via-violet-500 to-fuchsia-500 flex items-center justify-center shadow-lg shadow-violet-500/20">
            <svg className="w-6 h-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M12 2L8 6H4v4l-4 4 4 4v4h4l4 4 4-4h4v-4l4-4-4-4V6h-4L12 2z" strokeLinecap="round" strokeLinejoin="round"/>
              <circle cx="12" cy="12" r="3" fill="currentColor" opacity="0.5"/>
            </svg>
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">MOTHBOT</h1>
            <p className="text-xs text-cyan-400/80 font-mono">Ship Diagnostics • AI Control</p>
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
          <Link
            href="/skills"
            className="flex items-center gap-2 px-3 py-2 text-sm font-medium bg-cyan-500/20 text-cyan-400 rounded-lg border border-cyan-500/30 hover:bg-cyan-500/30 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
            Skills
          </Link>
          <Link
            href="/evals"
            className="flex items-center gap-2 px-3 py-2 text-sm font-medium bg-violet-500/20 text-violet-400 rounded-lg border border-violet-500/30 hover:bg-violet-500/30 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Evals
          </Link>
          <UserAudioControl size="lg" />
          <ConnectButton
            size="lg"
            onConnect={handleConnectClick}
            onDisconnect={handleDisconnectClick}
          />
        </div>
      </header>

      {/* Main Content - Split View */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat Panel */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Error Banner */}
            {error && (
              <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400">
                <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div className="flex-1">
                  <p className="font-medium">Connection Error</p>
                  <p className="text-sm text-red-400/80">{error}</p>
                </div>
              </div>
            )}

            {messages.length === 0 && !error && (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500/20 via-violet-500/20 to-fuchsia-500/20 flex items-center justify-center mb-4 border border-cyan-500/30">
                  <svg className="w-8 h-8 text-cyan-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M12 2L8 6H4v4l-4 4 4 4v4h4l4 4 4-4h4v-4l4-4-4-4V6h-4L12 2z" strokeLinecap="round" strokeLinejoin="round"/>
                    <circle cx="12" cy="12" r="3" fill="currentColor" opacity="0.5"/>
                  </svg>
                </div>
                <h2 className="text-xl font-bold text-white mb-2">Welcome to MOTHBOT</h2>
                <p className="text-zinc-400 max-w-md mb-6">
                  Your AI ship diagnostic companion. Connect to start monitoring your vessel.
                  Speak or type commands to run diagnostics and check system status.
                </p>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="px-4 py-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 hover:bg-cyan-500/20 transition-colors cursor-default">
                    "Check oxygen levels"
                  </div>
                  <div className="px-4 py-2 rounded-lg bg-violet-500/10 border border-violet-500/20 text-violet-300 hover:bg-violet-500/20 transition-colors cursor-default">
                    "Scan the hull"
                  </div>
                  <div className="px-4 py-2 rounded-lg bg-fuchsia-500/10 border border-fuchsia-500/20 text-fuchsia-300 hover:bg-fuchsia-500/20 transition-colors cursor-default">
                    "Run a full diagnostic"
                  </div>
                  <div className="px-4 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 hover:bg-emerald-500/20 transition-colors cursor-default">
                    "Check engine temperature"
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
                  <span className="w-2 h-2 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-violet-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 bg-fuchsia-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span className="text-sm font-mono">Processing...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Spaceship Visualization Panel */}
        <div className="hidden lg:flex w-[400px] flex-col border-l border-zinc-800/50 bg-zinc-950 min-h-0">
          <div className="flex-shrink-0 p-4 border-b border-zinc-800/50">
            <h2 className="text-sm font-bold text-zinc-300 uppercase tracking-wider flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse" />
              Ship Status
            </h2>
            <p className="text-xs text-zinc-500 mt-1 font-mono">Real-time diagnostic visualization</p>
          </div>
          <div className="flex-1 min-h-0 p-4 overflow-hidden">
            <SpaceshipWireframe 
              activeScans={activeScans} 
              className="w-full h-full"
            />
          </div>
        </div>
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-zinc-800/50 bg-zinc-900/80 backdrop-blur-sm">
        <div className="flex items-center gap-3 max-w-4xl mx-auto">
          <div className="flex-1 relative">
            <input
              ref={inputRef}
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={isConnected ? "Type a command or speak..." : "Connect to start diagnostics..."}
              disabled={!isConnected || isProcessing}
              className="w-full px-4 py-3 bg-zinc-800/50 border border-zinc-700/50 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 disabled:opacity-50 disabled:cursor-not-allowed font-mono text-sm"
            />
          </div>
          <button
            onClick={handleSendText}
            disabled={!isConnected || !inputText.trim() || isProcessing}
            className="px-4 py-3 bg-gradient-to-r from-cyan-600 to-violet-600 hover:from-cyan-500 hover:to-violet-500 disabled:from-zinc-700 disabled:to-zinc-700 disabled:cursor-not-allowed rounded-xl text-white font-medium transition-all shadow-lg shadow-cyan-500/20 disabled:shadow-none"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
        <p className="text-center text-xs text-zinc-500 mt-2 font-mono">
          Press Enter to send • Use microphone for voice commands
        </p>
      </div>
    </div>
  );
};
