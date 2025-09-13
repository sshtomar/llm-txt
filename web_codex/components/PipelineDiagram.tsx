export default function PipelineDiagram() {
  return (
    <div className="text-[var(--fg)]">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 960 540"
        role="img"
        aria-label="LLM‑TXT project pipeline in TX‑02 box‑drawing style"
        className="block w-full h-auto"
      >
        <defs>
          <style>{`
            .stroke{stroke:currentColor;fill:none}
            .thin{stroke-width:1}
            .mid{stroke-width:2}
            .bold{stroke-width:3}
            .label{fill:currentColor;font-family:'Berkeley Mono','SF Mono','Fira Code','JetBrains Mono','Cascadia Code',ui-monospace,Menlo,Monaco,Consolas,'Liberation Mono',monospace;letter-spacing:.06em}
            .t11{font-size:11px}
            .t13{font-size:13px}
            .t16{font-size:16px}
            .subtle{opacity:.55}
          `}</style>
          <pattern id="dots" x="0" y="0" width="6" height="6" patternUnits="userSpaceOnUse">
            <circle cx="1" cy="1" r="1" fill="currentColor" opacity=".15" />
          </pattern>
        </defs>

        {/* outer frame */}
        <rect x="32" y="24" width="896" height="512" rx="2" className="stroke bold"/>

        {/* corner ticks */}
        <path className="stroke mid" d="M40 40h18M40 40v18M920 40h-18M920 40v18M40 520h18M40 520v-18M920 520h-18M920 520v-18"/>

        {/* title band */}
        <rect x="320" y="64" width="320" height="28" className="stroke mid"/>
        <text x="480" y="82" textAnchor="middle" className="label t13">LLM‑TXT • PIPELINE OVERVIEW</text>

        {/* row 1: inputs */}
        {/* INPUT URL */}
        <g transform="translate(72,104)">
          <rect x="12" y="12" width="220" height="64" fill="url(#dots)"/>
          <rect x="0" y="0" width="220" height="64" className="stroke mid"/>
          <text x="110" y="22" textAnchor="middle" className="label t13">INPUT URL</text>
          <text x="110" y="42" textAnchor="middle" className="label t11 subtle">https://docs.example.com</text>
          <text x="110" y="56" textAnchor="middle" className="label t11 subtle">validate • normalize</text>
        </g>

        {/* robots */}
        <g transform="translate(352,104)">
          <rect x="12" y="12" width="220" height="64" fill="url(#dots)"/>
          <rect x="0" y="0" width="220" height="64" className="stroke mid"/>
          <text x="110" y="22" textAnchor="middle" className="label t13">robots.txt</text>
          <text x="110" y="42" textAnchor="middle" className="label t11 subtle">respect • crawl‑delay</text>
          <text x="110" y="56" textAnchor="middle" className="label t11 subtle">permissions check</text>
        </g>

        {/* sitemap */}
        <g transform="translate(632,104)">
          <rect x="12" y="12" width="220" height="64" fill="url(#dots)"/>
          <rect x="0" y="0" width="220" height="64" className="stroke mid"/>
          <text x="110" y="22" textAnchor="middle" className="label t13">sitemap discovery</text>
          <text x="110" y="42" textAnchor="middle" className="label t11 subtle">/sitemap.xml • links</text>
          <text x="110" y="56" textAnchor="middle" className="label t11 subtle">dedupe • same‑origin</text>
        </g>

        {/* arrows top row */}
        <text x="320" y="140" className="label t16" textAnchor="middle">→</text>
        <text x="600" y="140" className="label t16" textAnchor="middle">→</text>

        {/* row 2: crawl → extract → compose */}
        <g transform="translate(72,224)">
          <rect x="12" y="12" width="260" height="88" fill="url(#dots)"/>
          <rect x="0" y="0" width="260" height="88" className="stroke mid"/>
          <text x="130" y="22" textAnchor="middle" className="label t13">ASYNC CRAWLER</text>
          <text x="130" y="42" textAnchor="middle" className="label t11 subtle">polite • rate‑limited</text>
          <text x="130" y="58" textAnchor="middle" className="label t11 subtle">progress</text>
        </g>

        <text x="372" y="268" className="label t16" textAnchor="middle">→</text>

        <g transform="translate(392,224)">
          <rect x="12" y="12" width="260" height="88" fill="url(#dots)"/>
          <rect x="0" y="0" width="260" height="88" className="stroke mid"/>
          <text x="130" y="22" textAnchor="middle" className="label t13">EXTRACT + CLEAN</text>
          <text x="130" y="42" textAnchor="middle" className="label t11 subtle">Markdown‑first • code preserved</text>
          <text x="130" y="58" textAnchor="middle" className="label t11 subtle">remove nav/boilerplate</text>
        </g>

        <text x="692" y="268" className="label t16" textAnchor="middle">→</text>

        <g transform="translate(712,224)">
          <rect x="12" y="12" width="176" height="88" fill="url(#dots)"/>
          <rect x="0" y="0" width="176" height="88" className="stroke mid"/>
          <text x="88" y="22" textAnchor="middle" className="label t13">COMPOSE</text>
          <text x="88" y="42" textAnchor="middle" className="label t11 subtle">high‑signal first</text>
          <text x="88" y="58" textAnchor="middle" className="label t11 subtle">size budget • deterministic</text>
        </g>

        {/* down arrow to outputs */}
        <text x="800" y="332" className="label t16" textAnchor="middle">↓</text>

        {/* outputs */}
        <g transform="translate(712,352)">
          <rect x="12" y="12" width="176" height="84" fill="url(#dots)"/>
          <rect x="0" y="0" width="176" height="84" className="stroke mid"/>
          <text x="88" y="22" textAnchor="middle" className="label t13">DELIVERABLES</text>
          <g transform="translate(14,36)">
            <rect x="0" y="0" width="70" height="26" className="stroke thin" rx="10" ry="10"/>
            <text x="35" y="18" textAnchor="middle" className="label t11">llm.txt</text>
          </g>
          <g transform="translate(90,36)">
            <rect x="0" y="0" width="92" height="26" className="stroke thin" rx="10" ry="10"/>
            <text x="46" y="18" textAnchor="middle" className="label t11">llms‑full.txt</text>
          </g>
        </g>

        {/* footer badges */}
        <g transform="translate(72,476)">
          <rect x="0" y="0" width="112" height="26" className="stroke thin" rx="12" ry="12"/>
          <text x="56" y="18" textAnchor="middle" className="label t11">robots‑aware</text>
          <g transform="translate(132,0)">
            <rect x="0" y="0" width="112" height="26" className="stroke thin" rx="12" ry="12"/>
            <text x="56" y="18" textAnchor="middle" className="label t11">deterministic</text>
          </g>
          <g transform="translate(264,0)">
            <rect x="0" y="0" width="132" height="26" className="stroke thin" rx="12" ry="12"/>
            <text x="66" y="18" textAnchor="middle" className="label t11">size‑optimized</text>
          </g>
        </g>
      </svg>
    </div>
  )
}

