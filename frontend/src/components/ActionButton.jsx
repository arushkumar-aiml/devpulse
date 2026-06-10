import React, { useState } from 'react'

const s = {
  card: { background:'var(--surface)', border:'1px solid var(--border)', borderRadius:8, padding:20, marginBottom:16 },
  header: { color:'var(--accent)', fontWeight:'bold', fontSize:13, marginBottom:14, letterSpacing:2, textTransform:'uppercase' },
  input: { width:'100%', background:'var(--surface2)', border:'1px solid var(--border)', borderRadius:5,
           padding:'8px 12px', color:'var(--text)', fontFamily:'var(--font)', fontSize:12,
           outline:'none', marginBottom:8 },
  btn: (disabled) => ({ background: disabled?'var(--surface2)':'var(--accent)', color: disabled?'var(--muted)':'#000',
        border:'none', borderRadius:5, padding:'8px 20px', fontFamily:'var(--font)',
        fontWeight:'bold', fontSize:12, cursor: disabled?'not-allowed':'pointer', marginRight:8 }),
  result: (ok) => ({ background: ok?'#0d2b1e':'#2b0d0d', border:`1px solid ${ok?'var(--accent)':'var(--red)'}`,
           borderRadius:5, padding:'10px 14px', fontSize:12, marginTop:10, color:'var(--text)' }),
}

export default function ActionButton({ repos = [] }) {
  const [action,   setAction]   = useState('create_issue')
  const [repo,     setRepo]     = useState(repos[0] || '')
  const [title,    setTitle]    = useState('')
  const [assignee, setAssignee] = useState('')
  const [issueId,  setIssueId]  = useState('')
  const [comment,  setComment]  = useState('')
  const [loading,  setLoading]  = useState(false)
  const [result,   setResult]   = useState(null)

  async function handleSubmit() {
    if (!repo) return
    setLoading(true); setResult(null)
    const payload = { action, repo }
    if (action === 'create_issue') { payload.title = title; payload.body = `Created via DevPulse`; payload.assignee = assignee || undefined }
    if (action === 'assign_issue') { payload.issue_id = parseInt(issueId); payload.assignee = assignee }
    if (action === 'post_comment') { payload.issue_id = parseInt(issueId); payload.comment = comment }
    try {
      const res  = await fetch('/api/action', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) })
      const data = await res.json()
      setResult(data)
    } catch(e) {
      setResult({ success: false, error: e.message })
    } finally { setLoading(false) }
  }

  return (
    <div style={s.card} className="fade-in">
      <div style={s.header}>▸ Manual Action Executor</div>
      <select value={action} onChange={e=>setAction(e.target.value)}
        style={{...s.input, marginBottom:10}}>
        <option value="create_issue">Create Issue</option>
        <option value="assign_issue">Assign Issue</option>
        <option value="post_comment">Post Comment</option>
      </select>
      <input style={s.input} placeholder="Repo (e.g. org/repo)" value={repo} onChange={e=>setRepo(e.target.value)} />
      {action === 'create_issue' && <>
        <input style={s.input} placeholder="Issue title" value={title} onChange={e=>setTitle(e.target.value)} />
        <input style={s.input} placeholder="Assignee username (optional)" value={assignee} onChange={e=>setAssignee(e.target.value)} />
      </>}
      {(action === 'assign_issue' || action === 'post_comment') && <>
        <input style={s.input} placeholder="Issue ID (number)" value={issueId} onChange={e=>setIssueId(e.target.value)} />
        {action === 'assign_issue' && <input style={s.input} placeholder="Assignee username" value={assignee} onChange={e=>setAssignee(e.target.value)} />}
        {action === 'post_comment' && <textarea style={{...s.input, height:70, resize:'vertical'}} placeholder="Comment text" value={comment} onChange={e=>setComment(e.target.value)} />}
      </>}
      <button style={s.btn(loading)} onClick={handleSubmit} disabled={loading}>
        {loading ? '⟳ Running...' : '▶ Execute Action'}
      </button>
      {result && (
        <div style={s.result(result.success)}>
          {result.success ? `✅ ${result.action} successful!` : `❌ ${result.error}`}
          {result.issue_url && <div style={{marginTop:4}}><a href={result.issue_url} target="_blank" rel="noreferrer" style={{color:'var(--accent)'}}>View on GitLab →</a></div>}
        </div>
      )}
    </div>
  )
}
