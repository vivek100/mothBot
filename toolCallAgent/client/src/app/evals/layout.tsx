import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Thread Evaluations - Diagnostic Agent',
  description: 'Extract skills from Weave traces and run coding agent evaluations',
};

export default function EvalsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
