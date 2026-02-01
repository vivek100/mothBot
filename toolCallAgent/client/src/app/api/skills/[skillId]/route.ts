import { NextResponse } from 'next/server';

const SKILLS_API_URL = process.env.SKILLS_API_URL || 'http://localhost:7861';

export async function GET(
  request: Request,
  { params }: { params: Promise<{ skillId: string }> }
) {
  const { skillId } = await params;
  
  try {
    const response = await fetch(`${SKILLS_API_URL}/skills/${skillId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      cache: 'no-store',
    });

    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json(
          { status: 'error', error: `Skill '${skillId}' not found` },
          { status: 404 }
        );
      }
      throw new Error(`Failed to fetch skill: ${response.statusText}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Skills API error:', error);
    return NextResponse.json(
      { 
        status: 'error',
        error: `Failed to fetch skill: ${error instanceof Error ? error.message : 'Unknown error'}`,
      },
      { status: 500 }
    );
  }
}
