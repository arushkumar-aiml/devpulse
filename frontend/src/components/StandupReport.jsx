import React, { useState } from 'react'

const s = {
  card: { background:'var(--surface)', border:'1px solid var(--border)', borderRadius:8, padding:20, marginBottom:16 },
  header: { color:'var(--accent)', fontWeight:'bold', fontSize:13, marginBottom:14, letterSpacing:2, textTransform:'uppercase' },
  team: { background:'var(--surface2)', border:'1px solid var(--accent)', borderRadius:6, padding:14, marginBottom:16, fontSize:13, lineHeight:1.7, color:'var(--text)' },
  tabs: { display:'flex', gap:8, marginBottom:14, flexWrap:'wrap' },
  tab: (active) => ({ background: active?'var(--accent)':'var(--surface2)', color: active?'#000':'var(--muted)',
    border:`1px solid ${active?'var(--accent)':'var(--border)'}`, borderRadius:4, padding:'4px 12px',
    fontSize:11, cursor:'pointer', fontFamily:'var(--font)', fontWeight: active?'bold':'normal' }),
  standup: { background:'var(--surface2)', borderRadius:6, padding:14, fontSize:13, lineHeight:1.8, whiteSpace:'pre-wrap', color:'var(--text)' },
  empty: { color:'var(--muted)', textAlign:'center', padding:24, fontSize:13 },
  date: { color:'var(--muted)', fontSize:11, marginBottom:12 },
}

export default function StandupReport({ standupResult }) {
  const [active, setActive] = useState(0)
  const standups = standupResult?.standups || []

  return (
    <div style={s.card} className="fade-in">
      <div style={s.header}>▸ AI Standup Report</div>
      {standupResult?.date && <div style={s.date}>Generated: {standupResult.date}</div>}
      {standupResult?.team_summary && (
        <div style={s.team}>📋 {standupResult.team_summary}</div>
      )}
      {standups.length === 0
        ? <div style={s.empty}>No standup data yet. Run analysis first.</div>
        : <>
            <div style={s.tabs}>
              {standups.map((s2, i) => (
                <button key={i} style={s.tab(active===i)} onClick={() => setActive(i)}>
                  @{s2.username} <span style={{opacity:0.7}}>({s2.stats?.activity_score}/100)</span>
                </button>
              ))}
            </div>
            {standups[active] && (
              <div style={s.standup}>{standups[active].standup}</div>
            )}
          </>
      }
    </div>
  )
}
