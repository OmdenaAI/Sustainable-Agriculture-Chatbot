import { useState, useEffect, useRef, KeyboardEvent } from 'react'
import { useRouter } from 'next/router'
import { supabase } from '../lib/supabaseClient'
import { User } from '@supabase/supabase-js'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export default function Chat() {
  const [prompt, setPrompt] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [debugMode, setDebugMode] = useState(false)
  const [bypassChatAuth, setBypassChatAuth] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const router = useRouter()

  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Check environment variables on load
  useEffect(() => {
    console.log('Environment check:')
    console.log('NEXT_PUBLIC_BACKEND_URL:', process.env.NEXT_PUBLIC_BACKEND_URL || 'not set')
    
    // Add a welcome message if there are no messages
    if (messages.length === 0) {
      setMessages([{
        role: 'assistant',
        content: 'Hello! I\'m your Sustainable Agriculture Assistant. How can I help you today?'
      }])
    }
  }, [messages.length])

  useEffect(() => {
    const checkAuth = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) {
        router.push('/login')
      } else {
        setUser(session.user)
      }
    }
    checkAuth()
  }, [router])

  const handlePrompt = async () => {
    if (!prompt.trim() || loading) return

    const userMessage: ChatMessage = { role: 'user', content: prompt }
    setMessages(prev => [...prev, userMessage])
    const userInput = prompt.trim() // Save for error recovery
    setPrompt('')
    setLoading(true)
    setError(null)

    try {
      // Check if backend URL is configured
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'
      
      // Get session
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) {
        throw new Error('No session found. Please log in again.')
      }
      
      // Only include auth header if not bypassing chat auth
      const authHeader = bypassChatAuth ? {} : { 'Authorization': `Bearer ${session.access_token}` }
      
      // Format messages for the API
      const messageHistory = messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }))

      // Log the request for debugging
      console.log('Backend URL:', backendUrl)
      console.log('Sending request to:', `${backendUrl}/api/chat`)
      console.log('Request payload:', {
        message: userInput,
        history: messageHistory
        // No session_id sent - let backend handle it
      })
      console.log('Chat auth bypass:', bypassChatAuth)
      
      // Make the request with the correct endpoint and format
      const response = await fetch(`${backendUrl}/api/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...authHeader
        },
        body: JSON.stringify({
            message: userInput,
            history: messageHistory
        })
    });
    

      console.log('Response status:', response.status)

      // Handle non-OK responses
      if (!response.ok) {
        const errorText = await response.text()
        console.error('Backend error response:', {
          status: response.status,
          statusText: response.statusText,
          body: errorText
        })
        
        // Try to parse the error as JSON
        let errorDetail = `Status ${response.status}: ${response.statusText}`
        try {
          const errorJson = JSON.parse(errorText)
          if (errorJson.detail) {
            errorDetail = errorJson.detail
          } else if (errorJson.message) {
            errorDetail = errorJson.message
          } else if (errorJson.error) {
            errorDetail = errorJson.error
          }
        } catch (e) {
          // Not JSON, use status text
        }
        
        throw new Error(`Failed to get response: ${errorDetail}`)
      }

      // Parse the response
      const data = await response.json()
      console.log('Response data:', data)
      
      // Extract the response content
      let content = ''
      
      if (data.response) {
        content = data.response
      } else if (data.message) {
        content = data.message
      } else if (data.text) {
        content = data.text
      } else if (data.content) {
        content = data.content
      } else {
        // If we can't find a known format, stringify the whole response
        content = 'Received response in unknown format: ' + JSON.stringify(data)
      }
      
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: content
      }
      
      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Chat error:', error)
      
      // Set the error state
      setError(error instanceof Error ? error.message : 'Unknown error occurred')
      
      // Also add an error message to the chat
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  // Try a direct fetch to test the connection
  const testBackendConnection = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'
      
      // Get session
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) {
        throw new Error('No session found. Please log in first.')
      }
      
      // Only include auth header if not bypassing chat auth
      const authHeader = bypassChatAuth ? {} : { 'Authorization': `Bearer ${session.access_token}` }
      
      // Test with a simple message
      const response = await fetch(`${backendUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeader
        },
        body: JSON.stringify({
          message: 'Hello, this is a test message',
          history: []
          // No session_id field - removed completely
        })
      })
      
      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Backend test failed: ${response.status} - ${errorText}`)
      }
      
      const data = await response.json()
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Backend connection test successful! Response: ' + JSON.stringify(data)
      }])
    } catch (error) {
      console.error('Connection test error:', error)
      setError(`Connection test failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handlePrompt()
    }
  }

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'inherit'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }

  return (
    <div className="flex h-screen flex-col bg-gray-50">
      {/* Header */}
      <header className="fixed top-0 z-10 w-full border-b bg-white shadow-sm">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-3">
          <div className="flex items-center space-x-2">
            <span className="text-green-600 text-2xl">🌱</span>
            <h1 className="text-xl font-semibold text-gray-800">
              Sustainable Agriculture Assistant
            </h1>
          </div>
          <div className="flex items-center space-x-4">
            {user && (
              <span className="text-xs text-gray-500">
                User: {user.email}
              </span>
            )}
            <button
              onClick={() => setDebugMode(!debugMode)}
              className="rounded-md bg-gray-200 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-300 transition-colors"
            >
              {debugMode ? 'Hide Debug' : 'Debug'}
            </button>
            <button
              onClick={async () => {
                await supabase.auth.signOut()
                router.push('/login')
              }}
              className="rounded-md bg-red-500 px-3 py-1.5 text-sm text-white hover:bg-red-600 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto pt-16 pb-36">
        <div className="mx-auto max-w-4xl">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`px-4 py-6 ${
                message.role === 'assistant' ? 'bg-white' : 'bg-gray-50'
              }`}
            >
              <div className="mx-auto max-w-4xl">
                <div className="flex items-start space-x-2">
                  <span className="mt-1 text-xl">
                    {message.role === 'assistant' ? '🌱' : '👤'}
                  </span>
                  <div className="prose prose-green max-w-none">
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  </div>
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="px-4 py-6 bg-white">
              <div className="mx-auto max-w-4xl">
                <div className="flex items-start space-x-2">
                  <span className="mt-1 text-xl">🌱</span>
                  <div className="flex space-x-2">
                    <div className="h-2 w-2 animate-bounce rounded-full bg-green-600"></div>
                    <div className="h-2 w-2 animate-bounce rounded-full bg-green-600" style={{ animationDelay: '0.2s' }}></div>
                    <div className="h-2 w-2 animate-bounce rounded-full bg-green-600" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          {error && (
            <div className="px-4 py-4 bg-red-50 border-l-4 border-red-500">
              <div className="mx-auto max-w-4xl">
                <div className="flex items-start space-x-2">
                  <span className="mt-1 text-xl">⚠️</span>
                  <div>
                    <p className="font-medium text-red-800">Error</p>
                    <p className="text-sm text-red-700">{error}</p>
                  </div>
                </div>
              </div>
            </div>
          )}
          {debugMode && (
            <div className="px-4 py-4 bg-gray-100 border-l-4 border-gray-500">
              <div className="mx-auto max-w-4xl">
                <div className="flex flex-col space-y-2">
                  <p className="font-medium">Debug Information</p>
                  <p className="text-sm">Backend URL: {process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'}</p>
                  <p className="text-sm">User: {user?.email || 'Not logged in'}</p>
                  <div className="flex items-center space-x-4 mt-2">
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id="bypass-chat-auth"
                        checked={bypassChatAuth}
                        onChange={(e) => setBypassChatAuth(e.target.checked)}
                        className="rounded border-gray-300 text-green-600 focus:ring-green-500"
                      />
                      <label htmlFor="bypass-chat-auth" className="text-sm text-gray-700">
                        Bypass Chat Auth
                      </label>
                    </div>
                  </div>
                  <div className="flex space-x-2 mt-2">
                    <button 
                      onClick={testBackendConnection}
                      className="rounded-md bg-blue-500 px-3 py-1.5 text-sm text-white hover:bg-blue-600 transition-colors"
                    >
                      Test Backend Connection
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="fixed bottom-0 w-full border-t bg-white px-4 py-4">
        <div className="mx-auto max-w-4xl">
          <div className="relative flex items-end space-x-2">
            <textarea
              ref={textareaRef}
              value={prompt}
              onChange={(e) => {
                setPrompt(e.target.value)
                adjustTextareaHeight()
              }}
              onKeyDown={handleKeyDown}
              placeholder="Ask about sustainable agriculture..."
              className="flex-1 resize-none rounded-lg border border-gray-200 p-3 pr-12 focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
              rows={1}
              style={{ maxHeight: '200px' }}
            />
            <button
              onClick={handlePrompt}
              disabled={loading || !prompt.trim()}
              className="rounded-lg bg-green-600 px-4 py-2 text-white hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}