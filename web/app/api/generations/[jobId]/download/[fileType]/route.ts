import { NextRequest, NextResponse } from 'next/server'

export async function GET(
  request: NextRequest,
  { params }: { params: { jobId: string; fileType: string } }
) {
  try {
    const { jobId, fileType } = params

    // Validate file type
    if (!['llm.txt', 'llms-full.txt'].includes(fileType)) {
      return NextResponse.json({ detail: 'Invalid file type' }, { status: 400 })
    }

    // Proxy to backend API
    const response = await fetch(
      `http://localhost:8000/v1/generations/${jobId}/download/${fileType}`,
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || 'Download failed' },
        { status: response.status }
      )
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error('API proxy error:', error)
    return NextResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    )
  }
}
