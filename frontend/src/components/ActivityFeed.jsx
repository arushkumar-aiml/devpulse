import React from 'react'

const s = {
  card: { background:'var(--surface)', border:'1px solid var(--border)', borderRadius:8, padding:20, marginBottom:16 },
  header: { color:'var(--accent)', fontWeight:'bold', fontSize:13, marginBottom:14, letterSpacing:2, textTransform:'uppercase' },
  row: { display:'flex', justifyContent:'space-between', alignItems:'center', padding:'10px 0', borderBottom:'1px solid var(--border)' },
  user: { color:'var(--accent)', fontSize:13, fontWeight:'bold' },
  stat: { display:'flex', gap:16, fontSize:12, color:'var(--muted)' },
  badge: { background:'var(--surface2)', border:'1px solid var(--border)', borderRadius:4, padding:'2px 8px', color:'var(--text)', fontSize:11 },
  score: (n) => ({ color: n>=70?'var(--accent)':n>=40?'var(--yellow)':'var(--red)', fontWeight:'bold', fontSize:13 }),
  empty: { color:'var(--muted)', textAlign:'center', padding:24, fontSize:13 },
}

export default function ActivityFeed({ contributors, summary }) {
  if (!contributors || Object.keys(contributors).length === 0) {
    return <div style={s.card}><div style={s.empty}>No contributor data yet. Run analysis first.</div></div>
  }

  const sorted = Object.values(contributors).sort((a,b) => b.activity_score - a.activity_score)

  return (
    <div style={s.card} className="fade-in">
      <div style={s.header}>▸ Team Activity Feed</div>
      {summary && (
        <div style={{...s.row, borderBottom:'1px solid var(--accent)', marginBottom:8}}>
          <span style={{color:'var(--muted)', fontSize:12}}>
            {summary.total_commits} commits · {summary.total_mrs} MRs · top: <span style={{color:'var(--accent)'}}>{summary.top_contributor}</span>
          </span>
        </div>
      )}
      {sorted.map(u => (
        <div key={u.username} style={s.row}>
          <div>
            <div style={s.user}>@{u.username}</div>
            <div style={s.stat}>
              <span>{u.commits} commits</span>
              <span>+{u.lines_added} / -{u.lines_removed} lines</span>
              <span>{u.mrs_merged} MRs merged</span>
            </div>
          </div>
          <div style={{textAlign:'right'}}>
            <div style={s.score(u.activity_score)}>{u.activity_score}/100</div>
            <div style={{...s.badge, marginTop:4}}>{u.repos_touched?.length || 0} repos</div>
          </div>
        </div>
      ))}
    </div>
  )
}
