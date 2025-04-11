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
  const [user, setUser] = useState<User | null>(null)
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
    if (!prompt.trim()) return

    const userMessage: ChatMessage = { role: 'user', content: prompt }
    setMessages(prev => [...prev, userMessage])
    setPrompt('')
    setLoading(true)

    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) throw new Error('No session found')

      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/chat/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({ prompt: prompt.trim() })
      })

      if (!response.ok) {
        throw new Error('Failed to get response')
      }

      const data = await response.json()
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: data.choices[0].message.content
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.'
      }
      setMessages(prev => [...prev, errorMessage])
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
