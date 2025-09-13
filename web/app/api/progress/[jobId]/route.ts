import { NextRequest } from 'next/server'

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000'

export async function GET(
  request: NextRequest,
  { params }: { params: { jobId: string } }
) {
  const encoder = new TextEncoder()

  const stream = new ReadableStream({
    async start(controller) {
      let intervalId: NodeJS.Timeout

      const sendUpdate = async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/v1/generations/${params.jobId}`)
          
          if (!response.ok) {
            controller.enqueue(
              encoder.encode(
                `data: ${JSON.stringify({ state: 'error', message: 'Failed to fetch status' })}\n\n`
              )
            )
            clearInterval(intervalId)
            controller.close()
            return
          }

          const data = await response.json()
          
          // Transform backend response to frontend format
          const update = {
            state: data.status,
            message: data.message || '',
            current: data.progress?.current,
            total: data.progress?.total,
            details: {
              pagesProcessed: data.progress?.pages_processed,
              contentExtracted: data.progress?.content_extracted,
              currentUrl: data.progress?.current_url,
              estimatedSize: data.progress?.estimated_size,
            },
          }

          if (data.status === 'completed') {
            update.result = {
              llmTxt: {
                content: data.result?.llm_txt || '',
                size: data.result?.llm_txt_size || 0,
              },
              llmsFullTxt: data.result?.llms_full_txt ? {
                content: data.result.llms_full_txt,
                size: data.result.llms_full_txt_size || 0,
              } : undefined,
              stats: {
                pagesCrawled: data.stats?.pages_crawled || 0,
                contentExtracted: data.stats?.content_extracted || 0,
                compressionRatio: data.stats?.compression_ratio || 0,
                generationTime: data.stats?.generation_time || 0,
              },
            }
            clearInterval(intervalId)
          }

          controller.enqueue(
            encoder.encode(`data: ${JSON.stringify(update)}\n\n`)
          )

          if (data.status === 'completed' || data.status === 'failed') {
            controller.close()
          }
        } catch (error) {
          console.error('Progress fetch error:', error)
          controller.enqueue(
            encoder.encode(
              `data: ${JSON.stringify({ state: 'error', message: 'Connection error' })}\n\n`
            )
          )
          clearInterval(intervalId)
          controller.close()
        }
      }

      // Send initial update
      await sendUpdate()
      
      // Poll every 2 seconds
      intervalId = setInterval(sendUpdate, 2000)

      // Clean up on close
      request.signal.addEventListener('abort', () => {
        clearInterval(intervalId)
        controller.close()
      })
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  })
}