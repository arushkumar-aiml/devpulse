import { useState } from 'react'
import ActivityFeed   from './components/ActivityFeed.jsx'
import BlockerList    from './components/BlockerList.jsx'
import StandupReport  from './components/StandupReport.jsx'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const s = {
  app:    { minHeight:'100vh', background:'var(--bg)', color:'var(--text)', fontFamily:'var(--font)' },
  nav:    { borderBottom:'1px solid var(--border)', padding:'14px 32px', display:'flex', justifyContent:'space-between', alignItems:'center' },
  logo:   { color:'var(--accent)', fontSize:18, fontWeight:'bold', letterSpacing:3 },
  tag:    { color:'var(--muted)', fontSize:11 },
  main:   { maxWidth:1100, margin:'0 auto', padding:'28px 20px' },
  input:  { width:'100%', background:'var(--surface2)', border:'1px solid var(--border)', borderRadius:6,
            padding:'10px 14px', color:'var(--text)', fontFamily:'var(--font)', fontSize:13, outline:'none',
            marginBottom:10, transition:'border .2s' },
  btn:    (c='var(--accent)', d=false) => ({
            background: d ? 'var(--surface2)' : c, color: d ? 'var(--muted)' : '#000',
            border: `1px solid ${d ? 'var(--border)' : c}`, borderRadius:6,
            padding:'10px 28px', fontFamily:'var(--font)', fontWeight:'bold', fontSize:13,
            cursor: d ? 'not-allowed' : 'pointer', marginRight:10 }),
  row:    { display:'flex', gap:8, marginBottom:14, alignItems:'center', flexWrap:'wrap' },
  error:  { background:'#2d1515', border:'1px solid var(--red)', color:'var(--red)', borderRadius:6, padding:'10px 14px', fontSize:13, marginBottom:12 },
  sum:    { background:'var(--surface)', border:'1px solid var(--accent)', borderRadius:8, padding:16,
            marginBottom:20, fontSize:13, lineHeight:1.8, color:'var(--text)' },
  sumhd:  { color:'var(--accent)', fontWeight:'bold', marginBottom:8, fontSize:11, letterSpacing:2 },
  spinner:{ display:'inline-block', width:12, height:12, border:'2px solid var(--border)',
            borderTop:'2px solid var(--accent)', borderRadius:'50%', animation:'spin 0.7s linear infinite' },
}

export default function App() {
  const [repos,     setRepos]     = useState('')
  const [autoFix,   setAutoFix]   = useState(false)
  const [loading,   setLoading]   = useState(false)
  const [fixing,    setFixing]    = useState(false)
  const [error,     setError]     = useState('')
  const [analysis,  setAnalysis]  = useState(null)
  const [standups,  setStandups]  = useState(null)
  const [blockers,  setBlockers]  = useState(null)
  const [summary,   setSummary]   = useState('')
  const [tab,       setTab]       = useState('activity')

  const repoList = repos.split(',').map(r => r.trim()).filter(Boolean)

  async function handleAnalyze() {
    if (!repoList.length) { setError('Enter at least one repo (e.g. myorg/myrepo)'); return }
    setLoading(true); setError(''); setAnalysis(null); setStandups(null); setBlockers(null); setSummary('')
    try {
      const res  = await fetch(`${API}/analyze`, {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ repos: repoList, since_days: 7, auto_fix: autoFix }),
      })
      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      const data = await res.json()
      setAnalysis({ contributors: data.contributors, summary: data.summary })
      setSummary(data.agent_summary || '')

      const [sb, ss] = await Promise.all([
        fetch(`${API}/blockers`).then(r => r.json()).catch(() => ({})),
        fetch(`${API}/standup`).then(r => r.json()).catch(() => ({})),
      ])
      setBlockers(sb); setStandups(ss)
    } catch(e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleFix() {
    if (!blockers?.blockers?.length) return
    setFixing(true)
    try {
      const critical = blockers.blockers.filter(b => b.priority >= 7).slice(0, 5)
      await Promise.all(critical.map(b =>
        fetch(`${API}/action`, {
          method: 'POST', headers: {'Content-Type':'application/json'},
          body: JSON.stringify({ action: 'auto_fix_blocker', blocker: b, repo: b.repo }),
        })
      ))
      alert(`✅ Fix actions sent for ${critical.length} blocker(s)!`)
    } catch(e) {
      alert('Action failed: ' + e.message)
    } finally {
      setFixing(false)
    }
  }

  const tabs = ['activity', 'standup', 'blockers']

  return (
    <div style={s.app}>
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>

      {/* NAV */}
      <div style={s.nav}>
        <div>
          <span style={s.logo}>DEVPULSE<span className="blink">_</span></span>
          <span style={{...s.tag, marginLeft:12}}>AI Dev Operations Agent</span>
        </div>
        <span style={s.tag}>Gemini 2.0 Flash · GitLab MCP · LangGraph</span>
      </div>

      <div style={s.main}>

        {/* INPUT */}
        <div style={{marginBottom:20}}>
          <div style={{color:'var(--muted)', fontSize:11, marginBottom:6, letterSpacing:1}}>
            GITLAB REPOS (comma-separated)
          </div>
          <input style={s.input} value={repos}
            onChange={e => setRepos(e.target.value)}
            placeholder="myorg/backend, myorg/frontend, myorg/api"
            onFocus={e => e.target.style.borderColor='var(--accent)'}
            onBlur={e => e.target.style.borderColor='var(--border)'}
          />
          <div style={s.row}>
            <button style={s.btn('var(--accent)', loading)} onClick={handleAnalyze} disabled={loading}>
              {loading ? <><span style={s.spinner}/> &nbsp;Analyzing...</> : '▶ Analyze Team'}
            </button>
            <label style={{fontSize:12, color:'var(--muted)', cursor:'pointer', display:'flex', alignItems:'center', gap:6}}>
              <input type="checkbox" checked={autoFix} onChange={e=>setAutoFix(e.target.checked)}
                style={{accentColor:'var(--accent)'}} />
              Auto-fix critical blockers
            </label>
          </div>
        </div>

        {error && <div style={s.error}>⚠ {error}</div>}

        {/* AGENT SUMMARY */}
        {summary && (
          <div style={s.sum} className="fade-in">
            <div style={s.sumhd}>▸ AGENT SUMMARY</div>
            {summary}
          </div>
        )}

        {/* TABS */}
        {(analysis || blockers || standups) && (
          <>
            <div style={{display:'flex', gap:4, marginBottom:20, borderBottom:'1px solid var(--border)', paddingBottom:0}}>
              {tabs.map(t => (
                <button key={t} onClick={()=>setTab(t)}
                  style={{ background:'none', border:'none', borderBottom: tab===t?'2px solid var(--accent)':'2px solid transparent',
                    color: tab===t?'var(--accent)':'var(--muted)', padding:'8px 18px', cursor:'pointer',
                    fontFamily:'var(--font)', fontSize:12, fontWeight: tab===t?'bold':'normal',
                    textTransform:'uppercase', letterSpacing:1, marginBottom:-1 }}>
                  {t === 'blockers' && blockers?.total_blockers
                    ? `${t} (${blockers.total_blockers})`
                    : t}
                </button>
              ))}
            </div>

            {tab === 'activity' && <ActivityFeed contributors={analysis?.contributors} summary={analysis?.summary} />}
            {tab === 'standup'  && <StandupReport standupResult={standups} />}
            {tab === 'blockers' && <BlockerList blockerResult={blockers} onFix={handleFix} fixing={fixing} />}
          </>
        )}

        {/* EMPTY STATE */}
        {!loading && !analysis && !error && (
          <div style={{textAlign:'center', padding:'60px 0', color:'var(--muted)', fontSize:13}}>
            <div style={{fontSize:32, marginBottom:16}}>⚡</div>
            <div>Enter your GitLab repos above and click <span style={{color:'var(--accent)'}}>Analyze Team</span></div>
            <div style={{marginTop:8, fontSize:11}}>DevPulse will fetch activity, detect blockers, and generate standups</div>
          </div>
        )}
      </div>
    </div>
  )
}
