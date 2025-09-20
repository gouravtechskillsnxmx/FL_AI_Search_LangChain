const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API_KEY = 'dev-key-123'

export async function generate(query, options={}){
  const res = await fetch(`${API_URL}/v1/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${API_KEY}` },
    body: JSON.stringify({ query, options })
  })
  return res.json()
}
