'use client';

import { useState } from 'react';
import Link from 'next/link';

// Completed eval data for Skills Extraction Agent
const skillsEvalResult = {
  eval_id: "eval_skills_001",
  agent: "Skills Extraction Agent",
  run_at: "2026-02-01T14:32:15Z",
  status: "completed",
  duration_ms: 4823,
  weave_trace_id: "weave_trace_skills_abc123",
  input: {
    thread_id: "thread_diagnostic_session_001",
    thread_name: "Full Diagnostic Session",
    message_count: 24,
    tool_call_count: 12
  },
  output: {
    extracted_skills: [
      {
        id: "skill_001",
        name: "Complete Safety Diagnostic",
        description: "Runs hull scan, oxygen check, and atmosphere analysis in sequence",
        confidence: 0.92,
        steps: [
          { id: "s1", tool: "scan_hull", description: "Check hull integrity" },
          { id: "s2", tool: "check_oxygen", description: "Measure O2 levels" },
          { id: "s3", tool: "analyze_atmosphere", description: "Analyze based on O2", args: { o2_level: "$s2.level" }, depends_on: ["s2"] }
        ],
        source_trace_ids: ["trace_1", "trace_2", "trace_3"],
        suggested_triggers: ["full diagnostic", "safety check", "complete scan"]
      },
      {
        id: "skill_002",
        name: "Emergency O2 Protocol",
        description: "Quick oxygen assessment with immediate atmosphere analysis",
        confidence: 0.88,
        steps: [
          { id: "s1", tool: "check_oxygen", description: "Immediate O2 check" },
          { id: "s2", tool: "analyze_atmosphere", description: "Analyze severity", args: { o2_level: "$s1.level" }, depends_on: ["s1"] }
        ],
        source_trace_ids: ["trace_4", "trace_5"],
        suggested_triggers: ["oxygen emergency", "o2 critical", "breathing issue"]
      }
    ],
    total_traces_analyzed: 20,
    patterns_detected: 5,
    skills_saved: 2
  },
  metrics: {
    traces_processed: 20,
    patterns_found: 5,
    avg_confidence: 0.90,
    extraction_time_ms: 3200
  }
};

// Completed eval data for Coding Agent
const codingAgentEvalResult = {
  eval_id: "eval_coding_001",
  agent: "Coding Agent Evaluator",
  run_at: "2026-02-01T14:45:30Z",
  status: "completed",
  duration_ms: 6142,
  weave_trace_id: "weave_trace_coding_def456",
  input: {
    thread_id: "thread_diagnostic_session_001",
    skills_analyzed: 2,
    tool_calls_reviewed: 12,
    system_prompt_hash: "sha256:abc123..."
  },
  output: {
    overall_score: 78,
    summary: "Good tool usage patterns detected. Some opportunities for prompt optimization and tool description clarity.",
    suggestions: [
      {
        id: "suggestion_001",
        type: "system_prompt_update",
        priority: "high",
        title: "Add Emergency Protocol Instructions",
        description: "The system prompt should include explicit instructions for handling critical oxygen levels.",
        rationale: "In 3 out of 5 emergency scenarios, the agent hesitated before triggering intervention.",
        estimated_impact: "Reduce emergency response time by ~40%",
        affected_files: ["server/tools.py"],
        trace_evidence: [
          { trace_id: "trace_emergency_001", delay_ms: 3500, o2_level: 15 },
          { trace_id: "trace_emergency_002", delay_ms: 8200, o2_level: 12 }
        ]
      },
      {
        id: "suggestion_002",
        type: "tool_description_update",
        priority: "medium",
        title: "Clarify analyze_atmosphere Parameter Source",
        description: "Tool description should mention o2_level comes from check_oxygen results.",
        rationale: "Users frequently ask to analyze atmosphere without first checking oxygen.",
        estimated_impact: "Reduce tool chain errors by ~25%",
        affected_files: ["server/tools.py"]
      },
      {
        id: "suggestion_003",
        type: "tool_design_change",
        priority: "high",
        title: "Add Batch Temperature Check Tool",
        description: "Create a new tool that checks all zones in a single call.",
        rationale: "Users frequently want to check all zones, requiring 3 sequential tool calls.",
        estimated_impact: "Reduce multi-zone check time by ~66%",
        affected_files: ["server/tools.py", "marimo_engine/tools/examples.py"]
      }
    ],
    key_metrics: {
      tool_success_rate: 0.94,
      avg_response_time_ms: 4200,
      user_satisfaction: "positive"
    }
  },
  metrics: {
    traces_analyzed: 24,
    suggestions_generated: 3,
    high_priority_count: 2,
    analysis_time_ms: 5800
  }
};

type EvalType = 'skills' | 'coding';

// Skills Extraction Visual Component
function SkillsVisual() {
  const skills = skillsEvalResult.output.extracted_skills;
  
  return (
    <div className="space-y-4">
      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="p-3 rounded-lg bg-zinc-800/50 border border-zinc-700">
          <p className="text-2xl font-bold text-amber-400">{skillsEvalResult.output.skills_saved}</p>
          <p className="text-xs text-zinc-400">Skills Extracted</p>
        </div>
        <div className="p-3 rounded-lg bg-zinc-800/50 border border-zinc-700">
          <p className="text-2xl font-bold text-cyan-400">{skillsEvalResult.output.total_traces_analyzed}</p>
          <p className="text-xs text-zinc-400">Traces Analyzed</p>
        </div>
        <div className="p-3 rounded-lg bg-zinc-800/50 border border-zinc-700">
          <p className="text-2xl font-bold text-emerald-400">{Math.round(skillsEvalResult.metrics.avg_confidence * 100)}%</p>
          <p className="text-xs text-zinc-400">Avg Confidence</p>
        </div>
      </div>

      {/* Extracted Skills */}
      <div className="space-y-3">
        <h4 className="text-sm font-medium text-zinc-300">Extracted Skills</h4>
        {skills.map((skill) => (
          <div key={skill.id} className="p-4 rounded-lg bg-zinc-800/30 border border-zinc-700/50">
            <div className="flex items-start justify-between mb-2">
              <div>
                <h5 className="font-medium text-white">{skill.name}</h5>
                <p className="text-sm text-zinc-400">{skill.description}</p>
              </div>
              <span className={`px-2 py-1 text-xs rounded-full ${
                skill.confidence >= 0.9 
                  ? 'bg-emerald-500/20 text-emerald-400' 
                  : 'bg-amber-500/20 text-amber-400'
              }`}>
                {Math.round(skill.confidence * 100)}%
              </span>
            </div>

            {/* Steps Flow */}
            <div className="mt-3 space-y-2">
              <p className="text-xs text-zinc-500 uppercase tracking-wider">Steps</p>
              <div className="flex items-center gap-2 flex-wrap">
                {skill.steps.map((step, idx) => (
                  <div key={step.id} className="flex items-center gap-2">
                    <div className="px-3 py-1.5 rounded bg-cyan-500/10 border border-cyan-500/30">
                      <code className="text-xs text-cyan-400">{step.tool}</code>
                    </div>
                    {idx < skill.steps.length - 1 && (
                      <svg className="w-4 h-4 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Triggers */}
            <div className="mt-3">
              <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1">Triggers</p>
              <div className="flex flex-wrap gap-1">
                {skill.suggested_triggers.map((trigger, idx) => (
                  <span key={idx} className="px-2 py-0.5 text-xs bg-violet-500/10 text-violet-400 rounded border border-violet-500/20">
                    &quot;{trigger}&quot;
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Coding Agent Visual Component
function CodingAgentVisual() {
  const { output } = codingAgentEvalResult;
  
  const priorityColors = {
    high: 'bg-red-500/20 text-red-400 border-red-500/30',
    medium: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    low: 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30'
  };

  const typeIcons: Record<string, JSX.Element> = {
    system_prompt_update: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    tool_description_update: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
      </svg>
    ),
    tool_design_change: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    )
  };

  const typeLabels: Record<string, string> = {
    system_prompt_update: 'Prompt Update',
    tool_description_update: 'Tool Description',
    tool_design_change: 'Tool Design'
  };
  
  return (
    <div className="space-y-4">
      {/* Score */}
      <div className="p-4 rounded-lg bg-zinc-800/50 border border-zinc-700">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-zinc-400">Overall Score</span>
          <span className="text-3xl font-bold text-white">{output.overall_score}<span className="text-lg text-zinc-500">/100</span></span>
        </div>
        <div className="h-2 bg-zinc-700 rounded-full overflow-hidden">
          <div 
            className={`h-full rounded-full ${
              output.overall_score >= 80 ? 'bg-emerald-500' : 
              output.overall_score >= 60 ? 'bg-amber-500' : 'bg-red-500'
            }`}
            style={{ width: `${output.overall_score}%` }}
          />
        </div>
        <p className="mt-2 text-sm text-zinc-400">{output.summary}</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-3 gap-3">
        <div className="p-3 rounded-lg bg-zinc-800/50 border border-zinc-700">
          <p className="text-2xl font-bold text-emerald-400">{Math.round(output.key_metrics.tool_success_rate * 100)}%</p>
          <p className="text-xs text-zinc-400">Tool Success</p>
        </div>
        <div className="p-3 rounded-lg bg-zinc-800/50 border border-zinc-700">
          <p className="text-2xl font-bold text-cyan-400">{(output.key_metrics.avg_response_time_ms / 1000).toFixed(1)}s</p>
          <p className="text-xs text-zinc-400">Avg Response</p>
        </div>
        <div className="p-3 rounded-lg bg-zinc-800/50 border border-zinc-700">
          <p className="text-2xl font-bold text-violet-400">{output.suggestions.length}</p>
          <p className="text-xs text-zinc-400">Suggestions</p>
        </div>
      </div>

      {/* Suggestions */}
      <div className="space-y-3">
        <h4 className="text-sm font-medium text-zinc-300">Improvement Suggestions</h4>
        {output.suggestions.map((suggestion) => (
          <div key={suggestion.id} className="p-4 rounded-lg bg-zinc-800/30 border border-zinc-700/50">
            <div className="flex items-start gap-3">
              <div className={`p-2 rounded-lg ${
                suggestion.type === 'system_prompt_update' ? 'bg-violet-500/20 text-violet-400' :
                suggestion.type === 'tool_description_update' ? 'bg-cyan-500/20 text-cyan-400' :
                'bg-orange-500/20 text-orange-400'
              }`}>
                {typeIcons[suggestion.type]}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h5 className="font-medium text-white">{suggestion.title}</h5>
                  <span className={`px-2 py-0.5 text-xs rounded border ${priorityColors[suggestion.priority as keyof typeof priorityColors]}`}>
                    {suggestion.priority}
                  </span>
                </div>
                <p className="text-sm text-zinc-400 mb-2">{suggestion.description}</p>
                
                <div className="flex items-center gap-4 text-xs">
                  <span className="text-zinc-500">
                    <span className="text-zinc-400">{typeLabels[suggestion.type]}</span>
                  </span>
                  <span className="text-emerald-400">{suggestion.estimated_impact}</span>
                </div>

                {/* Affected Files */}
                <div className="mt-2 flex flex-wrap gap-1">
                  {suggestion.affected_files.map((file, idx) => (
                    <code key={idx} className="px-2 py-0.5 text-xs bg-zinc-800 text-zinc-300 rounded font-mono">
                      {file}
                    </code>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function EvalsPage() {
  const [selectedEval, setSelectedEval] = useState<EvalType>('skills');

  const currentEval = selectedEval === 'skills' ? skillsEvalResult : codingAgentEvalResult;

  return (
    <div className="flex flex-col h-screen bg-zinc-950">
      {/* Header */}
      <header className="flex items-center justify-between gap-4 p-4 border-b border-zinc-800 bg-zinc-900 shrink-0">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="p-2 rounded-lg bg-zinc-800 text-zinc-400 hover:text-white hover:bg-zinc-700 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </Link>
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-500 flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <div>
            <h1 className="text-lg font-semibold text-white">Eval Results</h1>
            <p className="text-xs text-zinc-400">Completed evaluation runs</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="w-2 h-2 bg-emerald-500 rounded-full" />
          <span className="text-xs text-zinc-400">Connected to Weave</span>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex flex-1 min-h-0">
        {/* Left Sidebar - Eval List */}
        <aside className="w-72 border-r border-zinc-800 bg-zinc-900/50 flex flex-col shrink-0">
          <div className="p-4 border-b border-zinc-800">
            <h2 className="text-sm font-medium text-zinc-300">Completed Evals</h2>
          </div>
          
          <div className="flex-1 overflow-y-auto">
            {/* Skills Extraction Eval */}
            <button
              onClick={() => setSelectedEval('skills')}
              className={`w-full p-4 text-left border-b border-zinc-800/50 transition-colors ${
                selectedEval === 'skills'
                  ? 'bg-zinc-800/80 border-l-2 border-l-amber-500'
                  : 'hover:bg-zinc-800/40 border-l-2 border-l-transparent'
              }`}
            >
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center">
                  <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-white text-sm truncate">Skills Extraction</h3>
                  <p className="text-xs text-zinc-500">2 skills extracted</p>
                </div>
              </div>
              <div className="flex items-center gap-2 text-xs text-zinc-500">
                <span className="px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 rounded">Done</span>
                <span>4.8s</span>
                <span>•</span>
                <span>20 traces</span>
              </div>
            </button>

            {/* Coding Agent Eval */}
            <button
              onClick={() => setSelectedEval('coding')}
              className={`w-full p-4 text-left border-b border-zinc-800/50 transition-colors ${
                selectedEval === 'coding'
                  ? 'bg-zinc-800/80 border-l-2 border-l-violet-500'
                  : 'hover:bg-zinc-800/40 border-l-2 border-l-transparent'
              }`}
            >
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-lg bg-violet-500/20 flex items-center justify-center">
                  <svg className="w-4 h-4 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-white text-sm truncate">Coding Agent Eval</h3>
                  <p className="text-xs text-zinc-500">Score: 78/100</p>
                </div>
              </div>
              <div className="flex items-center gap-2 text-xs text-zinc-500">
                <span className="px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 rounded">Done</span>
                <span>6.1s</span>
                <span>•</span>
                <span>3 suggestions</span>
              </div>
            </button>
          </div>
        </aside>

        {/* Middle Panel - Visual Display */}
        <div className="flex-1 flex flex-col min-h-0 min-w-0 border-r border-zinc-800">
          <div className="p-4 border-b border-zinc-800 bg-zinc-900/30 shrink-0">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-white">{currentEval.agent}</h2>
                <p className="text-xs text-zinc-500 font-mono">{currentEval.eval_id}</p>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className="text-zinc-500">Weave:</span>
                <code className="text-cyan-400">{currentEval.weave_trace_id}</code>
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {selectedEval === 'skills' ? <SkillsVisual /> : <CodingAgentVisual />}
          </div>
        </div>

        {/* Right Panel - JSON Output */}
        <div className="w-[480px] flex flex-col min-h-0 shrink-0 bg-zinc-900/30">
          <div className="p-4 border-b border-zinc-800 shrink-0">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-zinc-300">Raw JSON Output</h3>
              <span className="text-xs text-zinc-500">{currentEval.duration_ms}ms</span>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            <pre className="p-4 bg-black/50 rounded-lg border border-zinc-800 text-xs text-zinc-400 overflow-x-auto font-mono whitespace-pre">
{JSON.stringify(currentEval, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
