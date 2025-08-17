'use client'

import { CheckCircle, Circle, Loader2, AlertCircle } from 'lucide-react'

interface JobStep {
  id: string
  title: string
  description: string
  status: 'pending' | 'running' | 'completed' | 'failed'
}

interface JobStepsProps {
  currentStatus: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  message: string
}

export function JobSteps({ currentStatus, progress, message }: JobStepsProps) {
  const getSteps = (): JobStep[] => {
    const steps: JobStep[] = [
      {
        id: 'queued',
        title: 'Queued',
        description: 'Job added to processing queue',
        status: 'completed',
      },
      {
        id: 'crawling',
        title: 'Crawling',
        description: 'Discovering and crawling pages',
        status:
          progress > 0.2
            ? 'completed'
            : currentStatus === 'running'
              ? 'running'
              : 'pending',
      },
      {
        id: 'extracting',
        title: 'Extracting',
        description: 'Converting HTML to clean markdown',
        status:
          progress > 0.6 ? 'completed' : progress > 0.2 ? 'running' : 'pending',
      },
      {
        id: 'composing',
        title: 'Composing',
        description: 'Generating final llm.txt content',
        status:
          progress > 0.8 ? 'completed' : progress > 0.6 ? 'running' : 'pending',
      },
      {
        id: 'done',
        title: 'Done',
        description: 'Ready for download',
        status:
          currentStatus === 'completed'
            ? 'completed'
            : currentStatus === 'failed'
              ? 'failed'
              : 'pending',
      },
    ]

    if (currentStatus === 'failed') {
      // Mark all incomplete steps as failed
      steps.forEach((step) => {
        if (step.status === 'pending' || step.status === 'running') {
          step.status = 'failed'
        }
      })
    }

    return steps
  }

  const steps = getSteps()

  const getStepIcon = (step: JobStep) => {
    switch (step.status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'running':
        return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-500" />
      default:
        return <Circle className="h-5 w-5 text-gray-300" />
    }
  }

  const getStepColor = (step: JobStep) => {
    switch (step.status) {
      case 'completed':
        return 'text-green-700 border-green-200 bg-green-50'
      case 'running':
        return 'text-blue-700 border-blue-200 bg-blue-50'
      case 'failed':
        return 'text-red-700 border-red-200 bg-red-50'
      default:
        return 'text-gray-500 border-gray-200 bg-gray-50'
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">Processing Steps</h3>
        <div className="text-sm text-muted-foreground">
          {Math.round(progress * 100)}% complete
        </div>
      </div>

      <div className="space-y-3">
        {steps.map((step, index) => (
          <div
            key={step.id}
            className={`flex items-start space-x-3 rounded-lg border p-3 transition-colors ${getStepColor(step)}`}
          >
            <div className="mt-0.5">{getStepIcon(step)}</div>

            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between">
                <p className="font-medium">{step.title}</p>
                {step.status === 'running' && (
                  <div className="rounded-full bg-blue-100 px-2 py-1 text-xs text-blue-800">
                    In Progress
                  </div>
                )}
              </div>
              <p className="text-sm opacity-75">{step.description}</p>
            </div>
          </div>
        ))}
      </div>

      {message && (
        <div className="mt-4 rounded-md bg-muted/50 p-3">
          <p className="text-sm text-muted-foreground">{message}</p>
        </div>
      )}
    </div>
  )
}
