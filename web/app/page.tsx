import { Navigation } from '@/components/navigation'
import { Hero } from '@/components/hero'
import { JobSteps } from '@/components/job-steps'

export default function HomePage() {
  return (
    <div className="min-h-screen">
      <Navigation />
      <main>
        <Hero />
        
        {/* Features Section */}
        <section className="border-t py-20">
          <div className="container">
            <div className="mx-auto max-w-4xl">
              <h2 className="mb-12 text-center text-3xl font-bold">How it works</h2>
              <JobSteps />
              
              <div className="mt-16 grid gap-8 md:grid-cols-3">
                <div className="text-center">
                  <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100 text-blue-600">
                    <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <h3 className="mb-2 text-lg font-semibold">Fast Generation</h3>
                  <p className="text-sm text-muted-foreground">
                    P50 processing time under 90 seconds for most documentation sites
                  </p>
                </div>
                
                <div className="text-center">
                  <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-green-100 text-green-600">
                    <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="mb-2 text-lg font-semibold">Smart Filtering</h3>
                  <p className="text-sm text-muted-foreground">
                    Automatically removes redundant content and focuses on core documentation
                  </p>
                </div>
                
                <div className="text-center">
                  <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-purple-100 text-purple-600">
                    <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                  </div>
                  <h3 className="mb-2 text-lg font-semibold">Multiple Formats</h3>
                  <p className="text-sm text-muted-foreground">
                    Download llm.txt and optional llms-full.txt for comprehensive coverage
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}