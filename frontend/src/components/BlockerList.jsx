import React from 'react'

const COLORS = { stale_mr:'var(--yellow)', failed_pipeline:'var(--red)', unassigned_issue:'var(--blue)' }
const ICONS  = { stale_mr:'⏳', failed_pipeline:'🔴', unassigned_issue:'👤' }

const s = {
  card: { background:'var(--surface)', border:'1px solid var(--border)', borderRadius:8, padding:20, marginBottom:16 },
  header: { color:'var(--accent)', fontWeight:'bold', fontSize:13, marginBottom:14, letterSpacing:2, textTransform:'uppercase' },
  blocker: { border:'1px solid var(--border)', borderRadius:6, padding:12, marginBottom:10, background:'var(--surface2)' },
  title: { fontSize:13, fontWeight:'bold', marginBottom:6 },
  meta: { display:'flex', gap:12, fontSize:11, color:'var(--muted)', flexWrap:'wrap' },
  badge: (type) => ({ color:COLORS[type]||'var(--text)', border:`1px solid ${COLORS[type]||'var(--border)'}`, borderRadius:4, padding:'2px 7px', fontSize:11 }),
  priority: (n) => ({ color: n>=8?'var(--red)':n>=5?'var(--yellow)':'var(--blue)', fontWeight:'bold', fontSize:13, minWidth:24 }),
  empty: { color:'var(--muted)', textAlign:'center', padding:24, fontSize:13 },
  link: { color:'var(--accent)', textDecoration:'none', fontSize:11 },
}

export default function BlockerList({ blockerResult, onFix, fixing }) {
  const blockers = blockerResult?.blockers || []

  return (
    <div style={s.card} className="fade-in">
      <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:14}}>
        <div style={s.header}>▸ Blockers ({blockers.length})</div>
        {blockers.length > 0 && (
          <button onClick={onFix} disabled={fixing}
            style={{ background:'var(--accent)', color:'#000', border:'none', borderRadius:5,
              padding:'6px 16px', fontFamily:'var(--font)', fontWeight:'bold', fontSize:12,
              cursor: fixing?'not-allowed':'pointer', opacity: fixing?0.6:1 }}>
            {fixing ? '⟳ Fixing...' : '⚡ Fix It'}
          </button>
        )}
      </div>
      {blockers.length === 0
        ? <div style={s.empty}>✅ No blockers detected.</div>
        : blockers.map((b, i) => (
          <div key={i} style={{...s.blocker, borderLeftColor:COLORS[b.type]||'var(--border)', borderLeftWidth:3}}>
            <div style={{display:'flex', gap:10, alignItems:'flex-start'}}>
              <div style={s.priority(b.priority)}>{b.priority}</div>
              <div style={{flex:1}}>
                <div style={{...s.title, color:COLORS[b.type]||'var(--text)'}}>
                  {ICONS[b.type]} {b.title}
                </div>
                <div style={s.meta}>
                  <span style={s.badge(b.type)}>{b.type.replace('_',' ')}</span>
                  <span>{b.repo}</span>
                  {b.age_days && <span>{b.age_days}d old</span>}
                  {b.author && <span>by @{b.author}</span>}
                  {b.url && <a href={b.url} target="_blank" rel="noreferrer" style={s.link}>view →</a>}
                </div>
              </div>
            </div>
          </div>
        ))
      }
    </div>
  )
}
