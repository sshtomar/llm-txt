import { z } from 'zod'

export const urlSchema = z
  .string()
  .min(1, 'URL is required')
  .transform((url) => {
    // Auto-prefix with https:// if no protocol is provided
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      return `https://${url}`
    }
    return url
  })
  .pipe(
    z.string().url('Please enter a valid URL (e.g., https://docs.example.com)')
  )
  .refine(
    (url) => {
      try {
        const parsed = new URL(url)
        return parsed.protocol === 'http:' || parsed.protocol === 'https:'
      } catch {
        return false
      }
    },
    { message: 'URL must use http or https protocol' }
  )

export const generateRequestSchema = z.object({
  url: urlSchema,
  max_pages: z.number().int().min(1).max(1000).optional().default(100),
  max_depth: z.number().int().min(1).max(10).optional().default(3),
  full_version: z.boolean().optional().default(false),
  respect_robots: z.boolean().optional().default(true),
})

export type GenerateRequest = z.infer<typeof generateRequestSchema>
