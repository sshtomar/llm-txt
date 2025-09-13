# Build a Developer-Focused Frontend for llm.txt Generator Service

Create a modern, developer-centric web interface for a service that crawls documentation sites and generates optimized `llm.txt` files for LLM context windows.

## Core Functionality
- **Input**: URL field for documentation sites (with optional depth/settings)
- **Process**: Async crawling with detailed progress tracking  
- **Output**: Generated `llm.txt` and optional `llms-full.txt` with preview and download capabilities

## Design Requirements

### Typography & Visual Identity
- **Primary font**: Berkeley Mono (with fallbacks: SF Mono, Fira Code, JetBrains Mono, Cascadia Code)
- **Aesthetic**: Clean, terminal-inspired, developer-friendly
- **Style**: Minimal brutalist design with sharp edges, reminiscent of vintage technical documentation
- **Colors**: High contrast, inspired by classic terminal themes

### Theme System
- **Dark mode default** with light mode toggle
- **Dark palette**: Deep blacks (#000, #111), bright accent colors (#00ff00, #ff6b6b, #4ecdc4)  
- **Light palette**: Clean whites (#fff, #f8f9fa), muted accent colors
- **Terminal-style syntax highlighting** for code blocks and previews

### Layout & Components

#### Header
- Clean logo/title with monospace typography
- Theme toggle (terminal-style switch)
- GitHub link, documentation link

#### Main Interface
- **URL input**: Large, prominent text field with validation
- **Advanced options**: Collapsible section for depth, size limits, inclusion/exclusion patterns
- **Generate button**: Terminal-style CTA with hover effects

#### Progress Tracking System (Key Feature)
Since crawling is async and can take 30-90 seconds:

**Progress States**:
1. **Initializing**: "Parsing robots.txt, discovering sitemap..."
2. **Crawling**: "Fetching pages (23/45) - Respecting rate limits..."  
3. **Processing**: "Extracting content, cleaning markdown..."
4. **Composing**: "Assembling llm.txt, applying size budget..."
5. **Complete**: "Generated 847KB llm.txt (+ 2.3MB full version)"

**Progress UI Elements**:
- **Terminal-style progress bars** with ASCII art indicators
- **Real-time log stream** showing crawled URLs, blocked pages, size calculations
- **Live stats**: Pages processed, content extracted, final size estimates
- **Estimated time remaining** with context ("Usually takes 60-90s for docs sites")

#### Results Section (Enhanced)

**File Downloads & Preview Panel**:
- **Download Cards**: 
  - Primary `llm.txt` card with file size, optimized badge
  - Secondary `llms-full.txt` card (if generated) with "Complete Version" label
  - One-click download buttons with progress indicators
  - Copy-to-clipboard buttons for quick access

**Interactive Preview System**:
- **Tabbed interface**: Switch between `llm.txt` and `llms-full.txt` previews
- **Syntax-highlighted preview**: Full markdown rendering with Berkeley Mono
- **Preview controls**:
  - **Scroll to section**: Quick navigation to different doc sections
  - **Search within preview**: Find specific content
  - **Line numbers**: Developer-friendly reference
  - **Raw/rendered toggle**: Switch between markdown source and formatted view
- **Preview window**: Resizable, terminal-style with scroll bars
- **Content stats overlay**: Show character count, estimated tokens, compression ratio

**Preview Features**:
```typescript
interface PreviewState {
  content: string
  totalLines: number
  totalChars: number
  estimatedTokens: number
  sections: Array<{title: string, lineStart: number}>
  searchQuery?: string
  currentView: 'raw' | 'rendered'
}
Stats Dashboard:

Generation summary: Pages crawled, content extracted, final sizes
Comparison metrics: Original size vs. compressed size
Quality indicators: Sections preserved, content types included
Time metrics: Total generation time, pages per second

Error Handling

Robots.txt blocked: Clear message with sitemap upload alternative
Timeout/failures: Actionable error messages with retry options
Validation errors: Inline feedback for malformed URLs
Download errors: Fallback options, retry mechanisms

Technical Implementation
Framework & Stack

Next.js 14 with App Router
TypeScript throughout
Tailwind CSS for styling with custom terminal theme
Framer Motion for smooth progress animations
WebSocket or SSE for real-time progress updates
React Syntax Highlighter for code preview
FileSaver.js for robust download handling

Download Implementation
typescript// Download functionality
interface GeneratedFiles {
  llmTxt: {
    content: string
    size: number
    downloadUrl: string
  }
  llmsFullTxt?: {
    content: string  
    size: number
    downloadUrl: string
  }
}

// Preview functionality  
interface PreviewComponent {
  content: string
  filename: string
  onDownload: () => void
  onCopy: () => void
  searchable: boolean
  navigable: boolean
}
Key Features

Streaming preview: Show content as it's being generated
Lazy loading: Load preview content efficiently for large files
Download with metadata: Include generation timestamp, source URL in filename
Batch download: Option to download both files as ZIP
Share functionality: Generate shareable links to generated content

Responsive Design

Mobile-first: Collapsible preview panel, touch-friendly controls
Desktop optimization: Side-by-side progress/preview layout
Preview responsiveness: Adapts to different screen sizes
Terminal breakpoints: Consistent with monospace layouts

Interactive Elements

URL validation: Real-time feedback with favicon fetching
Copy-to-clipboard: One-click copying of entire files or selected sections
Keyboard shortcuts:

Ctrl+Enter to submit
Ctrl+D to download
Ctrl+C to copy preview
/ to search in preview


Terminal commands: Show equivalent CLI/curl commands

Preview UX Details

Loading preview: Skeleton with typing animation effect
Preview transitions: Smooth fade between different files
Content highlighting: Highlight matching search terms
Section bookmarks: Quick jump to different documentation sections
Preview toolbar: Download, copy, search, navigate controls
Content warnings: Show if content was truncated, sections dropped

Content & Copy

Download buttons: "Download llm.txt (847KB)" with file size
Preview headers: "Preview: docs.example.com/llm.txt"
Status messages: "Ready to download • 2,847 lines • ~15K tokens"
Copy feedback: "Copied to clipboard!" with fade animation
Preview placeholders: "Generated content will appear here..."

Performance & UX

Instant preview: Show content as soon as generation completes
Progressive download: Allow partial downloads if generation is slow
Preview caching: Cache previews for quick re-access
Download optimization: Efficient file serving, resume support
Accessibility: Full keyboard navigation, screen reader support for previews

Advanced Preview Features

Diff view: Compare llm.txt vs llms-full.txt side-by-side
Token estimation: Real-time token count for different models (GPT-4, Claude)
Content analysis: Show content types, section breakdown
Export options: Multiple formats, custom naming conventions

# Analyze Linear.app Design Patterns for llm.txt Generator Frontend

Use Playwright to analyze Linear's website (https://linear.app) and extract design patterns, UI components, and implementation details that we can adapt for our llm.txt generator frontend.

## Analysis Focus Areas

### 1. Visual Design System
**Task**: Visit Linear's homepage and main app interface
- Screenshot key sections: header, navigation, main content areas
- Analyze color palette (dark/light themes)
- Document typography choices (fonts, sizes, weights)
- Note spacing patterns and grid systems
- Examine button styles, form inputs, cards

### 2. Progress & Loading States
**Task**: Look for any progress indicators, loading states, or status displays
- How do they show task progress/completion?
- Loading animations and transitions
- Status badges and indicators
- Timeline/progress visualization patterns

### 3. Terminal/Code Aesthetic Elements
**Task**: Find any code-related or terminal-style UI elements
- Monospace font usage
- Code block styling
- Terminal-like components
- Developer-focused design patterns

### 4. Layout & Navigation
**Task**: Analyze their responsive design and navigation patterns
- Header/navigation structure
- Mobile vs desktop layouts
- Sidebar patterns
- Content organization

### 5. Interactive Elements & Animations
**Task**: Test interactions and document animation patterns
- Hover states and transitions
- Micro-interactions
- Button animations
- Page transitions
- Loading/progress animations

## Specific Playwright Actions
```javascript
// Visit and analyze Linear's design
await page.goto('https://linear.app');

// Take screenshots of key sections
await page.screenshot({ path: 'linear-homepage.png', fullPage: true });

// Test dark/light theme toggle if available
await page.click('[data-theme-toggle]', { timeout: 5000 }).catch(() => {});
await page.screenshot({ path: 'linear-dark-theme.png' });

// Analyze CSS custom properties for design tokens
const designTokens = await page.evaluate(() => {
  const styles = getComputedStyle(document.documentElement);
  const tokens = {};
  for (let i = 0; i < styles.length; i++) {
    const prop = styles[i];
    if (prop.startsWith('--')) {
      tokens[prop] = styles.getPropertyValue(prop);
    }
  }
  return tokens;
});

// Check for specific UI patterns we need
const uiPatterns = await page.evaluate(() => {
  return {
    progressBars: document.querySelectorAll('[role="progressbar"]').length,
    loadingSpinners: document.querySelectorAll('[data-loading]').length,
    codeBlocks: document.querySelectorAll('pre, code').length,
    terminalElements: document.querySelectorAll('[class*="terminal"], [class*="mono"]').length
  };
});