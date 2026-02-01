'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface SkillSummary {
  id: string;
  name: string;
  description: string;
  when_to_use: string;
  steps_count: number;
  has_intervention: boolean;
  keywords: string[];
  is_dynamic: boolean;
}

interface SkillStep {
  id: string;
  tool: string;
  description: string;
  args?: Record<string, unknown>;
  run_if?: string;
  key_finding: boolean;
  intervention_if?: string;
}

interface SkillDetails {
  id: string;
  name: string;
  description: string;
  when_to_use: string;
  expected_outcome: string;
  debug_tips: string[];
  fallback_tools: string[];
  triggers: {
    keywords?: string[];
    user_intents?: string[];
    avoid_when?: string[];
  };
  is_dynamic: boolean;
  steps: SkillStep[];
}

export default function SkillsPage() {
  const [skills, setSkills] = useState<SkillSummary[]>([]);
  const [selectedSkill, setSelectedSkill] = useState<SkillDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSkills();
  }, []);

  const fetchSkills = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/skills');
      const data = await response.json();
      
      if (data.status === 'error') {
        setError(data.error);
      } else {
        setSkills(data.skills || []);
        setError(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch skills');
    } finally {
      setLoading(false);
    }
  };

  const fetchSkillDetails = async (skillId: string) => {
    try {
      setLoadingDetails(true);
      const response = await fetch(`/api/skills/${skillId}`);
      const data = await response.json();
      
      if (data.status === 'error') {
        setError(data.error);
      } else {
        setSelectedSkill(data.skill);
        setError(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch skill details');
    } finally {
      setLoadingDetails(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-zinc-800 bg-zinc-900/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 via-violet-500 to-fuchsia-500 flex items-center justify-center shadow-lg shadow-violet-500/20">
                <svg className="w-6 h-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M12 2L8 6H4v4l-4 4 4 4v4h4l4 4 4-4h4v-4l4-4-4-4V6h-4L12 2z" strokeLinecap="round" strokeLinejoin="round"/>
                  <circle cx="12" cy="12" r="3" fill="currentColor" opacity="0.5"/>
                </svg>
              </div>
              <div>
                <h1 className="text-lg font-bold text-white tracking-tight">MOTHBOT</h1>
                <p className="text-xs text-cyan-400/80 font-mono">Skills Library</p>
              </div>
            </Link>
          </div>
          
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="flex items-center gap-2 px-3 py-2 text-sm font-medium bg-zinc-800 text-zinc-300 rounded-lg border border-zinc-700 hover:bg-zinc-700 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to Chat
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
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Page Title */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-white mb-2">Available Skills</h2>
          <p className="text-zinc-400">
            Skills are pre-defined tool chains that execute multiple diagnostic tools in sequence.
            Each skill is optimized for specific scenarios.
          </p>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="mb-6 flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400">
            <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div className="flex-1">
              <p className="font-medium">Error</p>
              <p className="text-sm text-red-400/80">{error}</p>
            </div>
            <button 
              onClick={() => setError(null)}
              className="text-red-400 hover:text-red-300"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="flex gap-2">
              <span className="w-3 h-3 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-3 h-3 bg-violet-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-3 h-3 bg-fuchsia-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        )}

        {/* Main Content */}
        {!loading && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Skills List */}
            <div className="lg:col-span-1 space-y-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-wider">
                  {skills.length} Skills Available
                </h3>
                <button
                  onClick={fetchSkills}
                  className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
                >
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Refresh
                </button>
              </div>

              {skills.map((skill) => (
                <button
                  key={skill.id}
                  onClick={() => fetchSkillDetails(skill.id)}
                  className={`w-full text-left p-4 rounded-xl border transition-all ${
                    selectedSkill?.id === skill.id
                      ? 'bg-cyan-500/10 border-cyan-500/50 shadow-lg shadow-cyan-500/10'
                      : 'bg-zinc-900/50 border-zinc-800 hover:border-zinc-700 hover:bg-zinc-900'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h4 className="font-semibold text-white">{skill.name}</h4>
                    <div className="flex gap-1">
                      {skill.is_dynamic && (
                        <span className="px-2 py-0.5 text-xs font-medium bg-emerald-500/20 text-emerald-400 rounded-full">
                          Custom
                        </span>
                      )}
                      {skill.has_intervention && (
                        <span className="px-2 py-0.5 text-xs font-medium bg-amber-500/20 text-amber-400 rounded-full">
                          Alert
                        </span>
                      )}
                    </div>
                  </div>
                  <p className="text-sm text-zinc-400 line-clamp-2 mb-3">{skill.description}</p>
                  <div className="flex items-center gap-3 text-xs text-zinc-500">
                    <span className="flex items-center gap-1">
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" />
                      </svg>
                      {skill.steps_count} steps
                    </span>
                    {skill.keywords.length > 0 && (
                      <span className="flex items-center gap-1">
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                        </svg>
                        {skill.keywords.length} keywords
                      </span>
                    )}
                  </div>
                </button>
              ))}

              {skills.length === 0 && !error && (
                <div className="text-center py-8 text-zinc-500">
                  <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                  </svg>
                  <p>No skills available</p>
                  <p className="text-sm mt-1">Make sure the Skills API is running</p>
                </div>
              )}
            </div>

            {/* Skill Details Panel */}
            <div className="lg:col-span-2">
              {loadingDetails && (
                <div className="flex items-center justify-center py-12 bg-zinc-900/50 rounded-xl border border-zinc-800">
                  <div className="flex gap-2">
                    <span className="w-3 h-3 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-3 h-3 bg-violet-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-3 h-3 bg-fuchsia-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              )}

              {!loadingDetails && selectedSkill && (
                <div className="bg-zinc-900/50 rounded-xl border border-zinc-800 overflow-hidden">
                  {/* Skill Header */}
                  <div className="p-6 border-b border-zinc-800 bg-gradient-to-r from-cyan-500/5 via-violet-500/5 to-fuchsia-500/5">
                    <div className="flex items-start justify-between gap-4 mb-4">
                      <div>
                        <h3 className="text-2xl font-bold text-white mb-1">{selectedSkill.name}</h3>
                        <p className="text-sm font-mono text-zinc-500">ID: {selectedSkill.id}</p>
                      </div>
                      <div className="flex gap-2">
                        {selectedSkill.is_dynamic && (
                          <span className="px-3 py-1 text-sm font-medium bg-emerald-500/20 text-emerald-400 rounded-lg border border-emerald-500/30">
                            Custom Skill
                          </span>
                        )}
                      </div>
                    </div>
                    <p className="text-zinc-300">{selectedSkill.description}</p>
                  </div>

                  {/* Skill Content */}
                  <div className="p-6 space-y-6">
                    {/* When to Use */}
                    {selectedSkill.when_to_use && (
                      <div>
                        <h4 className="text-sm font-bold text-cyan-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          When to Use
                        </h4>
                        <div className="bg-zinc-800/50 rounded-lg p-4 text-sm text-zinc-300 whitespace-pre-line">
                          {selectedSkill.when_to_use}
                        </div>
                      </div>
                    )}

                    {/* Expected Outcome */}
                    {selectedSkill.expected_outcome && (
                      <div>
                        <h4 className="text-sm font-bold text-violet-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          Expected Outcome
                        </h4>
                        <div className="bg-zinc-800/50 rounded-lg p-4 text-sm text-zinc-300 whitespace-pre-line">
                          {selectedSkill.expected_outcome}
                        </div>
                      </div>
                    )}

                    {/* Steps */}
                    <div>
                      <h4 className="text-sm font-bold text-fuchsia-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                        </svg>
                        Execution Steps ({selectedSkill.steps.length})
                      </h4>
                      <div className="space-y-3">
                        {selectedSkill.steps.map((step, index) => (
                          <div
                            key={step.id}
                            className="bg-zinc-800/50 rounded-lg p-4 border-l-2 border-zinc-700 hover:border-cyan-500/50 transition-colors"
                          >
                            <div className="flex items-start justify-between gap-3 mb-2">
                              <div className="flex items-center gap-3">
                                <span className="w-6 h-6 rounded-full bg-zinc-700 flex items-center justify-center text-xs font-bold text-zinc-300">
                                  {index + 1}
                                </span>
                                <div>
                                  <span className="font-mono text-sm text-cyan-400">{step.tool}</span>
                                  <span className="text-zinc-500 text-xs ml-2">({step.id})</span>
                                </div>
                              </div>
                              <div className="flex gap-1">
                                {step.key_finding && (
                                  <span className="px-2 py-0.5 text-xs font-medium bg-amber-500/20 text-amber-400 rounded">
                                    Key Finding
                                  </span>
                                )}
                                {step.intervention_if && (
                                  <span className="px-2 py-0.5 text-xs font-medium bg-red-500/20 text-red-400 rounded">
                                    Can Alert
                                  </span>
                                )}
                              </div>
                            </div>
                            {step.description && (
                              <p className="text-sm text-zinc-400 ml-9">{step.description}</p>
                            )}
                            {step.args && Object.keys(step.args).length > 0 && (
                              <div className="mt-2 ml-9">
                                <span className="text-xs text-zinc-500">Args: </span>
                                <code className="text-xs text-emerald-400 bg-zinc-900/50 px-2 py-0.5 rounded">
                                  {JSON.stringify(step.args)}
                                </code>
                              </div>
                            )}
                            {step.run_if && (
                              <div className="mt-2 ml-9">
                                <span className="text-xs text-zinc-500">Condition: </span>
                                <code className="text-xs text-violet-400 bg-zinc-900/50 px-2 py-0.5 rounded">
                                  {step.run_if}
                                </code>
                              </div>
                            )}
                            {step.intervention_if && (
                              <div className="mt-2 ml-9">
                                <span className="text-xs text-zinc-500">Alert if: </span>
                                <code className="text-xs text-red-400 bg-zinc-900/50 px-2 py-0.5 rounded">
                                  {step.intervention_if}
                                </code>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Keywords */}
                    {selectedSkill.triggers?.keywords && selectedSkill.triggers.keywords.length > 0 && (
                      <div>
                        <h4 className="text-sm font-bold text-emerald-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                          </svg>
                          Trigger Keywords
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {selectedSkill.triggers.keywords.map((keyword) => (
                            <span
                              key={keyword}
                              className="px-3 py-1 text-sm bg-emerald-500/10 text-emerald-400 rounded-lg border border-emerald-500/20"
                            >
                              {keyword}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Debug Tips */}
                    {selectedSkill.debug_tips && selectedSkill.debug_tips.length > 0 && (
                      <div>
                        <h4 className="text-sm font-bold text-amber-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                          </svg>
                          Debug Tips
                        </h4>
                        <ul className="space-y-2">
                          {selectedSkill.debug_tips.map((tip, index) => (
                            <li key={index} className="flex items-start gap-2 text-sm text-zinc-400">
                              <span className="text-amber-500 mt-0.5">•</span>
                              {tip}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Fallback Tools */}
                    {selectedSkill.fallback_tools && selectedSkill.fallback_tools.length > 0 && (
                      <div>
                        <h4 className="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                          Fallback Tools
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {selectedSkill.fallback_tools.map((tool) => (
                            <span
                              key={tool}
                              className="px-3 py-1 text-sm font-mono bg-zinc-800 text-zinc-300 rounded-lg border border-zinc-700"
                            >
                              {tool}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {!loadingDetails && !selectedSkill && (
                <div className="flex flex-col items-center justify-center py-16 bg-zinc-900/50 rounded-xl border border-zinc-800 text-center">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500/20 via-violet-500/20 to-fuchsia-500/20 flex items-center justify-center mb-4 border border-cyan-500/30">
                    <svg className="w-8 h-8 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">Select a Skill</h3>
                  <p className="text-zinc-400 max-w-md">
                    Click on a skill from the list to view its details, execution steps, and usage guidance.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
