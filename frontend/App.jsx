import React, {useState} from 'react'
import { generate } from './api'

export default function App(){
  const [query, setQuery] = useState('Write a short blog about intermittent fasting')
  const [tone, setTone] = useState('friendly')
  const [output, setOutput] = useState('')
  const [loading, setLoading] = useState(false)

  async function onGenerate(){
    setLoading(true)
    const res = await generate(query, {tone, length:'short'})
    setOutput(res.output || JSON.stringify(res))
    setLoading(false)
  }

  return (
    <div style={{padding:20,fontFamily:'sans-serif'}}>
      <h2>TextGen-RAG Demo</h2>
      <div>
        <textarea value={query} onChange={e=>setQuery(e.target.value)} rows={4} cols={60} />
      </div>
      <div style={{marginTop:8}}>
        Tone: <select value={tone} onChange={e=>setTone(e.target.value)}><option>friendly</option><option>neutral</option><option>formal</option></select>
      </div>
      <div style={{marginTop:8}}>
        <button onClick={onGenerate} disabled={loading}>{loading? 'Generating...':'Generate'}</button>
      </div>
      <pre style={{marginTop:12,background:'#f7f7f7',padding:12}}>{output}</pre>
    </div>
  )
}
