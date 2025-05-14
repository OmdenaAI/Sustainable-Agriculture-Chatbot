// pages/api/chat.js
export default async function handler(req, res) {
    // Only allow POST requests
    if (req.method !== 'POST') {
      return res.status(405).json({ error: 'Method not allowed' });
    }
  
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000';
      const response = await fetch(`${backendUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': req.headers.authorization
        },
        body: JSON.stringify(req.body),
      });
  
      if (!response.ok) {
        const errorText = await response.text();
        return res.status(response.status).json({ 
          error: `Backend error: ${response.status}`,
          details: errorText
        });
      }
  
      const data = await response.json();
      return res.status(200).json(data);
    } catch (error) {
      console.error('Error forwarding request to backend:', error);
      return res.status(500).json({ error: 'Failed to connect to backend service' });
    }
  }