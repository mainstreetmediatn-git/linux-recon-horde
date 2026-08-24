import { useMemo, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  Bot,
  ChevronDown,
  ChevronRight,
  CircleDot,
  Cpu,
  FileText,
  Gauge,
  Play,
  ShieldCheck,
  SlidersHorizontal,
  TerminalSquare,
  Wrench,
  Zap,
} from 'lucide-react'

type Risk = 'Low' | 'Medium' | 'High'

type Module = {
  id: string
  name: string
  description: string
  risk: Risk
  category: string
  impact: string
}

const modules: Module[] = [
  {
    id: 'dns',
    name: 'DNS Intelligence',
    description: 'Resolve and summarize authorized hostname metadata.',
    risk: 'Low',
    category: 'Discovery',
    impact: 'Passive metadata inspection with minimal system impact.',
  },
  {
    id: 'tls',
    name: 'TLS Certificate Review',
    description: 'Inspect certificate identity, issuer, and validity window.',
    risk: 'Low',
    category: 'Discovery',
    impact: 'Low-volume connection to the selected authorized target.',
  },
  {
    id: 'headers',
    name: 'HTTP Security Headers',
    description: 'Analyze supplied or collected headers for defensive posture.',
    risk: 'Low',
    category: 'Web',
    impact: 'Read-only analysis; no state-changing request is represented in this UI.',
  },
  {
    id: 'service-meta',
    name: 'Service Metadata',
    description: 'Prepare bounded service-identification checks for approved labs.',
    risk: 'Medium',
    category: 'Network',
    impact: 'May create noticeable connection volume depending on future backend policy.',
  },
  {
    id: 'udp-meta',
    name: 'Bounded UDP Metadata',
    description: 'Represent constrained UDP discovery with explicit load policy.',
    risk: 'High',
    category: 'Network',
    impact: 'Potentially noisy. Must remain rate-limited, authorized, and operator-reviewed.',
  },
]

const terminalLines = [
  '[11:48:02] HORDE console initialized',
  '[11:48:02] policy mode: human authority required',
  '[11:48:03] execution adapter: UI preview only',
  '[11:48:03] no live target selected',
  '[11:48:03] awaiting operator configuration…',
]

const runbook = [
  'Confirm written authorization and exact target scope.',
  'Review selected modules and risk classification.',
  'Validate rate/load constraints before any external execution.',
  'Create evidence record and timestamp before starting.',
  'Execute only through an approved environment and tool admission.',
  'Review findings, contradictions, and audit history after completion.',
]

export function RiskBadge({ risk }: { risk: Risk }) {
  return <span className={`risk-badge risk-${risk.toLowerCase()}`}>{risk}</span>
}

export function ModuleCard({
  module,
  checked,
  onToggle,
}: {
  module: Module
  checked: boolean
  onToggle: () => void
}) {
  return (
    <button className={`module-card ${checked ? 'selected' : ''}`} onClick={onToggle} type="button">
      <span className="module-check" aria-hidden="true">{checked ? '✓' : ''}</span>
      <span className="module-copy">
        <span className="module-heading">
          <strong>{module.name}</strong>
          <RiskBadge risk={module.risk} />
        </span>
        <span className="module-description">{module.description}</span>
        <span className="module-meta">{module.category}</span>
      </span>
    </button>
  )
}

function App() {
  const [agentOnline, setAgentOnline] = useState(true)
  const [mode, setMode] = useState<'Auto' | 'Manual'>('Auto')
  const [target, setTarget] = useState('')
  const [intensity, setIntensity] = useState('Balanced')
  const [openModules, setOpenModules] = useState(true)
  const [selected, setSelected] = useState<string[]>(['dns', 'tls', 'headers'])
  const [view, setView] = useState<'Terminal' | 'Runbook'>('Terminal')
  const [riskAck, setRiskAck] = useState(false)

  const selectedModules = useMemo(
    () => modules.filter((item) => selected.includes(item.id)),
    [selected],
  )

  const highestRisk: Risk = selectedModules.some((m) => m.risk === 'High')
    ? 'High'
    : selectedModules.some((m) => m.risk === 'Medium')
      ? 'Medium'
      : 'Low'

  const warningModule = selectedModules.find((m) => m.risk === highestRisk) ?? modules[0]

  const toggleModule = (id: string) => {
    setSelected((current) => current.includes(id) ? current.filter((value) => value !== id) : [...current, id])
    setRiskAck(false)
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <div className="brand-mark"><ShieldCheck size={20} /></div>
          <div>
            <div className="eyebrow">AUTHORIZED SECURITY ORCHESTRATION</div>
            <h1>Linux Recon Horde</h1>
          </div>
        </div>

        <div className="header-controls">
          <button className="status-chip" type="button" onClick={() => setAgentOnline(!agentOnline)}>
            <span className={`status-dot ${agentOnline ? 'online' : 'offline'}`} />
            <span>AI Agent:</span>
            <strong>{agentOnline ? 'Online' : 'Offline'}</strong>
          </button>
          <div className="mode-toggle" role="group" aria-label="Execution mode">
            {(['Auto', 'Manual'] as const).map((item) => (
              <button key={item} className={mode === item ? 'active' : ''} type="button" onClick={() => setMode(item)}>
                {item === 'Auto' ? <Bot size={15} /> : <Wrench size={15} />}
                {item}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="workspace">
        <section className="panel config-panel">
          <div className="panel-title-row">
            <div>
              <div className="eyebrow">01 / CONFIGURE</div>
              <h2>Target & Modules</h2>
            </div>
            <SlidersHorizontal size={19} />
          </div>

          <label className="field-group">
            <span>Target</span>
            <div className="input-shell">
              <CircleDot size={16} />
              <input value={target} onChange={(e) => setTarget(e.target.value)} placeholder="IP address or domain" />
            </div>
            <small>UI preview only — no request is sent from this screen.</small>
          </label>

          <div className="field-grid">
            <label className="field-group">
              <span>Scan intensity</span>
              <select value={intensity} onChange={(e) => setIntensity(e.target.value)}>
                <option>Passive</option>
                <option>Balanced</option>
                <option>Thorough</option>
              </select>
            </label>
            <div className="metric-card compact">
              <span>Selected</span>
              <strong>{selected.length}</strong>
              <small>modules</small>
            </div>
          </div>

          <div className="quick-options">
            <label><input type="checkbox" defaultChecked /> Preserve evidence</label>
            <label><input type="checkbox" defaultChecked /> Human review gate</label>
            <label><input type="checkbox" /> Verbose telemetry</label>
          </div>

          <div className="accordion">
            <button className="accordion-trigger" type="button" onClick={() => setOpenModules(!openModules)}>
              <span><Cpu size={17} /> Module & Payload Selector</span>
              {openModules ? <ChevronDown size={17} /> : <ChevronRight size={17} />}
            </button>
            {openModules && (
              <div className="module-list">
                {modules.map((module) => (
                  <ModuleCard key={module.id} module={module} checked={selected.includes(module.id)} onToggle={() => toggleModule(module.id)} />
                ))}
              </div>
            )}
          </div>
        </section>

        <section className="right-stack">
          <div className="panel execution-panel">
            <div className="panel-title-row execution-header">
              <div>
                <div className="eyebrow">02 / EXECUTION VIEW</div>
                <h2>{view === 'Terminal' ? 'Terminal Preview' : 'Manual Runbook'}</h2>
              </div>
              <div className="view-switch">
                <button type="button" className={view === 'Terminal' ? 'active' : ''} onClick={() => setView('Terminal')}>
                  <TerminalSquare size={15} /> Terminal
                </button>
                <button type="button" className={view === 'Runbook' ? 'active' : ''} onClick={() => setView('Runbook')}>
                  <FileText size={15} /> Runbook
                </button>
              </div>
            </div>

            <div className="console-window">
              <div className="console-bar">
                <span className="window-dot" /><span className="window-dot" /><span className="window-dot" />
                <span>horde://operator-session</span>
                <span className="ui-only-tag">UI ONLY</span>
              </div>
              {view === 'Terminal' ? (
                <pre className="terminal-output">{terminalLines.join('\n')}</pre>
              ) : (
                <ol className="runbook-list">
                  {runbook.map((step, index) => (
                    <li key={step}><span>{String(index + 1).padStart(2, '0')}</span><p>{step}</p></li>
                  ))}
                </ol>
              )}
            </div>

            <div className="telemetry-row">
              <div><Activity size={16} /><span>Mode</span><strong>{mode}</strong></div>
              <div><Gauge size={16} /><span>Intensity</span><strong>{intensity}</strong></div>
              <div><Cpu size={16} /><span>Modules</span><strong>{selected.length}</strong></div>
            </div>
          </div>

          <aside className={`warning-card warning-${highestRisk.toLowerCase()}`}>
            <div className="warning-icon"><AlertTriangle size={22} /></div>
            <div className="warning-content">
              <div className="warning-heading">
                <div>
                  <div className="eyebrow">RISK REVIEW</div>
                  <h3>{warningModule.name}</h3>
                </div>
                <RiskBadge risk={highestRisk} />
              </div>
              <p>{warningModule.description}</p>
              <div className="impact-box">
                <strong>Potential system impact</strong>
                <span>{warningModule.impact}</span>
              </div>
              <label className="acknowledge-row">
                <input type="checkbox" checked={riskAck} onChange={(e) => setRiskAck(e.target.checked)} />
                <span>I acknowledge the displayed risk and understand this interface does not itself authorize execution.</span>
              </label>
            </div>
          </aside>
        </section>
      </main>

      <footer className="action-bar">
        <div className="scope-summary">
          <span className="status-dot online" />
          <div><strong>Operator preview</strong><small>{target || 'No target entered'} · {selected.length} modules · Highest risk {highestRisk}</small></div>
        </div>
        <div className="action-buttons">
          <button className="secondary-action" type="button" onClick={() => setView('Runbook')}>
            <Wrench size={17} /> Generate Manual Runbook
          </button>
          <button className="primary-action" type="button" disabled={!riskAck} title="UI-only control">
            <Zap size={17} /> Run with AI Agent
          </button>
        </div>
      </footer>
    </div>
  )
}

export default App
