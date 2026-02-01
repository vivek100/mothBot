'use client';

import { useEffect, useState, useMemo } from 'react';

// Ship sections that can be highlighted based on tool calls
export type ShipSection = 
  | 'hull'
  | 'oxygen'
  | 'atmosphere'
  | 'main'
  | 'engine'
  | 'cargo'
  | 'power'
  | 'navigation'
  | 'life_support'
  | 'communications';

export interface ActiveScan {
  section: ShipSection;
  status: 'scanning' | 'ok' | 'warning' | 'critical';
  label?: string;
}

interface SpaceshipWireframeProps {
  activeScans: ActiveScan[];
  className?: string;
}

// Map tool names to ship sections
export const toolToSectionMap: Record<string, ShipSection[]> = {
  scan_hull: ['hull'],
  check_oxygen: ['oxygen', 'life_support'],
  analyze_atmosphere: ['atmosphere', 'life_support'],
  check_temperature: ['main', 'engine', 'cargo'], // Will be refined by zone arg
  scan_systems: ['power', 'navigation', 'life_support', 'communications'],
};

// Get sections from tool call
export function getSectionsFromToolCall(
  toolName: string, 
  args?: Record<string, unknown>
): ShipSection[] {
  if (toolName === 'check_temperature' && args?.zone) {
    return [args.zone as ShipSection];
  }
  return toolToSectionMap[toolName] || [];
}

// Status colors for different states
const statusColors = {
  scanning: {
    stroke: '#22d3ee', // cyan-400
    fill: 'rgba(34, 211, 238, 0.15)',
    glow: 'rgba(34, 211, 238, 0.6)',
  },
  ok: {
    stroke: '#10b981', // emerald-500
    fill: 'rgba(16, 185, 129, 0.15)',
    glow: 'rgba(16, 185, 129, 0.5)',
  },
  warning: {
    stroke: '#f59e0b', // amber-500
    fill: 'rgba(245, 158, 11, 0.2)',
    glow: 'rgba(245, 158, 11, 0.6)',
  },
  critical: {
    stroke: '#ef4444', // red-500
    fill: 'rgba(239, 68, 68, 0.25)',
    glow: 'rgba(239, 68, 68, 0.7)',
  },
};

// Star field background component
const StarField = () => {
  const stars = useMemo(() => {
    return Array.from({ length: 60 }, (_, i) => ({
      id: i,
      cx: Math.random() * 100,
      cy: Math.random() * 100,
      r: Math.random() * 1.2 + 0.3,
      opacity: Math.random() * 0.6 + 0.2,
      delay: Math.random() * 3,
    }));
  }, []);

  return (
    <g className="star-field">
      {stars.map((star) => (
        <circle
          key={star.id}
          cx={`${star.cx}%`}
          cy={`${star.cy}%`}
          r={star.r}
          fill="#fff"
          opacity={star.opacity}
          className="animate-twinkle"
          style={{ animationDelay: `${star.delay}s` }}
        />
      ))}
    </g>
  );
};

export const SpaceshipWireframe = ({ activeScans, className = '' }: SpaceshipWireframeProps) => {
  const [pulsePhase, setPulsePhase] = useState(0);

  // Animate pulse effect
  useEffect(() => {
    const interval = setInterval(() => {
      setPulsePhase((prev) => (prev + 1) % 360);
    }, 50);
    return () => clearInterval(interval);
  }, []);

  // Get active status for a section
  const getSectionStatus = (section: ShipSection) => {
    const scan = activeScans.find((s) => s.section === section);
    return scan?.status || null;
  };

  // Get style for a section based on its status
  const getSectionStyle = (section: ShipSection) => {
    const status = getSectionStatus(section);
    if (!status) {
      return {
        stroke: '#3f3f46', // zinc-700
        fill: 'transparent',
        filter: 'none',
      };
    }
    const colors = statusColors[status];
    return {
      stroke: colors.stroke,
      fill: colors.fill,
      filter: status === 'scanning' ? `drop-shadow(0 0 8px ${colors.glow})` : `drop-shadow(0 0 4px ${colors.glow})`,
    };
  };

  // Check if section is being scanned
  const isScanning = (section: ShipSection) => {
    return activeScans.some((s) => s.section === section && s.status === 'scanning');
  };

  return (
    <div className={`relative overflow-hidden ${className}`} style={{ maxHeight: '100%' }}>
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-zinc-950 via-zinc-900/50 to-zinc-950 rounded-2xl" />
      
      {/* Grid overlay */}
      <div 
        className="absolute inset-0 opacity-10 rounded-2xl"
        style={{
          backgroundImage: `
            linear-gradient(rgba(34, 211, 238, 0.3) 1px, transparent 1px),
            linear-gradient(90deg, rgba(34, 211, 238, 0.3) 1px, transparent 1px)
          `,
          backgroundSize: '20px 20px',
        }}
      />

      <svg
        viewBox="0 0 400 600"
        className="relative w-full h-full"
        preserveAspectRatio="xMidYMid meet"
        style={{ maxHeight: '100%', maxWidth: '100%' }}
      >
        <defs>
          {/* Scanning animation gradient */}
          <linearGradient id="scanGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#22d3ee" stopOpacity="0" />
            <stop offset={`${(pulsePhase % 100)}%`} stopColor="#22d3ee" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#22d3ee" stopOpacity="0" />
          </linearGradient>

          {/* Glow filter */}
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          {/* Scan line filter */}
          <filter id="scanLine">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* Star field background */}
        <StarField />

        {/* Ship outline - Main body */}
        <g className="ship-body">
          {/* Hull - outer shell */}
          <path
            d={`
              M 200 50
              C 280 80, 320 150, 320 200
              L 340 280
              L 350 380
              C 350 420, 340 480, 320 520
              L 280 560
              L 120 560
              L 80 520
              C 60 480, 50 420, 50 380
              L 60 280
              L 80 200
              C 80 150, 120 80, 200 50
              Z
            `}
            style={getSectionStyle('hull')}
            strokeWidth="2"
            className={isScanning('hull') ? 'animate-pulse' : ''}
          />

          {/* Cockpit / Navigation */}
          <ellipse
            cx="200"
            cy="100"
            rx="50"
            ry="30"
            style={getSectionStyle('navigation')}
            strokeWidth="2"
            className={isScanning('navigation') ? 'animate-pulse' : ''}
          />
          <text x="200" y="105" textAnchor="middle" fill="#71717a" fontSize="10" fontFamily="monospace">
            NAV
          </text>

          {/* Main Section */}
          <rect
            x="100"
            y="150"
            width="200"
            height="120"
            rx="10"
            style={getSectionStyle('main')}
            strokeWidth="2"
            className={isScanning('main') ? 'animate-pulse' : ''}
          />
          <text x="200" y="215" textAnchor="middle" fill="#71717a" fontSize="12" fontFamily="monospace">
            MAIN DECK
          </text>

          {/* Life Support / Oxygen / Atmosphere - Center module */}
          <g>
            <rect
              x="140"
              y="180"
              width="120"
              height="60"
              rx="5"
              style={{
                ...getSectionStyle('life_support'),
                ...(getSectionStatus('oxygen') ? getSectionStyle('oxygen') : {}),
                ...(getSectionStatus('atmosphere') ? getSectionStyle('atmosphere') : {}),
              }}
              strokeWidth="1.5"
              className={
                isScanning('life_support') || isScanning('oxygen') || isScanning('atmosphere')
                  ? 'animate-pulse'
                  : ''
              }
            />
            <text x="200" y="200" textAnchor="middle" fill="#71717a" fontSize="8" fontFamily="monospace">
              LIFE SUPPORT
            </text>
            <text x="200" y="215" textAnchor="middle" fill="#71717a" fontSize="8" fontFamily="monospace">
              O₂ / ATMO
            </text>
            {/* Oxygen indicator circles */}
            <circle cx="160" cy="225" r="6" style={getSectionStyle('oxygen')} strokeWidth="1" />
            <circle cx="200" cy="225" r="6" style={getSectionStyle('atmosphere')} strokeWidth="1" />
            <circle cx="240" cy="225" r="6" style={getSectionStyle('life_support')} strokeWidth="1" />
          </g>

          {/* Cargo Bay */}
          <rect
            x="90"
            y="290"
            width="220"
            height="100"
            rx="8"
            style={getSectionStyle('cargo')}
            strokeWidth="2"
            className={isScanning('cargo') ? 'animate-pulse' : ''}
          />
          <text x="200" y="345" textAnchor="middle" fill="#71717a" fontSize="12" fontFamily="monospace">
            CARGO BAY
          </text>
          {/* Cargo grid lines */}
          <line x1="150" y1="290" x2="150" y2="390" stroke="#3f3f46" strokeWidth="0.5" />
          <line x1="200" y1="290" x2="200" y2="390" stroke="#3f3f46" strokeWidth="0.5" />
          <line x1="250" y1="290" x2="250" y2="390" stroke="#3f3f46" strokeWidth="0.5" />

          {/* Engine Section */}
          <path
            d={`
              M 100 410
              L 300 410
              L 320 480
              L 280 540
              L 120 540
              L 80 480
              Z
            `}
            style={getSectionStyle('engine')}
            strokeWidth="2"
            className={isScanning('engine') ? 'animate-pulse' : ''}
          />
          <text x="200" y="470" textAnchor="middle" fill="#71717a" fontSize="12" fontFamily="monospace">
            ENGINE
          </text>

          {/* Engine thrusters */}
          <rect x="130" y="520" width="30" height="30" rx="3" style={getSectionStyle('engine')} strokeWidth="1" />
          <rect x="185" y="520" width="30" height="30" rx="3" style={getSectionStyle('engine')} strokeWidth="1" />
          <rect x="240" y="520" width="30" height="30" rx="3" style={getSectionStyle('engine')} strokeWidth="1" />

          {/* Power Systems - Side modules */}
          <rect
            x="55"
            y="320"
            width="30"
            height="80"
            rx="5"
            style={getSectionStyle('power')}
            strokeWidth="1.5"
            className={isScanning('power') ? 'animate-pulse' : ''}
          />
          <text x="70" y="365" textAnchor="middle" fill="#71717a" fontSize="7" fontFamily="monospace" transform="rotate(-90, 70, 365)">
            PWR
          </text>

          <rect
            x="315"
            y="320"
            width="30"
            height="80"
            rx="5"
            style={getSectionStyle('power')}
            strokeWidth="1.5"
            className={isScanning('power') ? 'animate-pulse' : ''}
          />
          <text x="330" y="365" textAnchor="middle" fill="#71717a" fontSize="7" fontFamily="monospace" transform="rotate(90, 330, 365)">
            PWR
          </text>

          {/* Communications Array - Top antenna */}
          <g style={getSectionStyle('communications')} className={isScanning('communications') ? 'animate-pulse' : ''}>
            <line x1="200" y1="50" x2="200" y2="20" strokeWidth="2" />
            <circle cx="200" cy="15" r="8" strokeWidth="1.5" />
            <circle cx="200" cy="15" r="4" strokeWidth="1" />
          </g>
          <text x="200" y="8" textAnchor="middle" fill="#71717a" fontSize="7" fontFamily="monospace">
            COMMS
          </text>

          {/* Wing details */}
          <path
            d="M 80 250 L 40 300 L 40 380 L 60 400 L 80 380"
            style={getSectionStyle('hull')}
            strokeWidth="1.5"
            fill="transparent"
          />
          <path
            d="M 320 250 L 360 300 L 360 380 L 340 400 L 320 380"
            style={getSectionStyle('hull')}
            strokeWidth="1.5"
            fill="transparent"
          />
        </g>

        {/* Scanning line effect */}
        {activeScans.some((s) => s.status === 'scanning') && (
          <rect
            x="40"
            y={50 + (pulsePhase % 100) * 5}
            width="320"
            height="4"
            fill="url(#scanGradient)"
            filter="url(#scanLine)"
            opacity="0.8"
          />
        )}
      </svg>

      {/* Status Legend - Only show when there are active scans */}
      {activeScans.length > 0 && (
        <div className="absolute bottom-2 left-2 right-2 flex flex-wrap gap-2 justify-center max-h-20 overflow-y-auto">
          {activeScans.map((scan, idx) => (
            <div
              key={`${scan.section}-${idx}`}
              className="flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-mono"
              style={{
                backgroundColor: statusColors[scan.status].fill,
                borderColor: statusColors[scan.status].stroke,
                borderWidth: 1,
                color: statusColors[scan.status].stroke,
              }}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${scan.status === 'scanning' ? 'animate-ping' : ''}`}
                style={{ backgroundColor: statusColors[scan.status].stroke }}
              />
              <span className="uppercase text-[10px]">{scan.section.replace('_', ' ')}</span>
              {scan.label && <span className="opacity-70 text-[10px]">: {scan.label}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SpaceshipWireframe;
