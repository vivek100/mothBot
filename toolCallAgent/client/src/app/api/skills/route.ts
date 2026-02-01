import { NextResponse } from 'next/server';

const SKILLS_API_URL = process.env.SKILLS_API_URL || 'http://localhost:7861';

export async function GET() {
  try {
    const response = await fetch(`${SKILLS_API_URL}/skills`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      // Don't cache skills - they can be dynamically added
      cache: 'no-store',
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch skills: ${response.statusText}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Skills API error:', error);
    return NextResponse.json(
      { 
        status: 'error',
        error: `Failed to fetch skills: ${error instanceof Error ? error.message : 'Unknown error'}`,
        skills: [],
      },
      { status: 500 }
    );
  }
}
