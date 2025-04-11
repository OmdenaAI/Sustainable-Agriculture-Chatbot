import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabaseClient'
import { useRouter } from 'next/router'

interface AuthError {
  message: string;
}

interface AuthResponse {
  email: string;
  token?: string;
  message: string;
}

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const router = useRouter()

  // Add authentication state tracking
  useEffect(() => {
    const checkSession = async () => {
      try {
        console.log('=== Checking Initial Session ===')
        const { data: { session }, error } = await supabase.auth.getSession()
        
        if (error) {
          console.error('Initial session check error:', error)
          return
        }
        
        if (session) {
          console.log('Initial session found:', {
            user: session.user.email,
            sessionId: session.access_token.slice(-10), // Log last 10 chars for security
          })
          router.push('/chat')
        } else {
          console.log('No initial session found')
        }
      } catch (error) {
        console.error('Error in initial session check:', error)
      }
    }
    
    // Track auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      console.log('=== Auth State Change ===')
      console.log('Event:', event)
      console.log('Session exists:', !!session)
      if (session) {
        console.log('User:', session.user.email)
      }
    })

    checkSession()

    return () => {
      subscription.unsubscribe()
    }
  }, [router])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      console.log('=== Login Attempt ===')
      console.log('Attempting login for email:', email)
      
      setLoading(true)
      setMessage(null)

      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })
      
      console.log('Sign in response received')
      
      if (error) {
        console.error('Login error:', {
          message: error.message,
          status: error.status,
          name: error.name
        })
        
        switch (error.message) {
          case 'Invalid login credentials':
            setMessage('Email or password incorrect. Please try again.')
            break
          case 'Email not confirmed':
            setMessage('This account needs to be confirmed first. Please check your email for the confirmation link sent during signup.')
            break
          default:
            setMessage(error.message)
        }
        return
      }

      if (data?.session) {
        console.log('Session created successfully')
        router.push('/chat')
      } else {
        console.error('No session data after successful login:', data)
        setMessage('Login succeeded but no session was created. Please try again.')
      }
      
    } catch (error: unknown) {
      console.error('Unexpected login error:', error)
      setMessage('An unexpected error occurred. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      console.log('=== Signup Attempt ===')
      console.log('Attempting signup for email:', email)
      
      setLoading(true)
      setMessage(null)

      if (password.length < 6) {
        console.log('Password too short')
        setMessage('Password must be at least 6 characters long')
        return
      }
      
      // Add emailRedirectTo option to redirect to login page after confirmation
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: `${window.location.origin}/login`
        }
      })
      
      if (error) {
        console.error('Signup error:', {
          message: error.message,
          status: error.status,
          name: error.name
        })
        
        switch (error.message) {
          case 'User already registered':
            setMessage('This email is already registered. Try logging in instead.')
            break
          default:
            setMessage(error.message)
        }
        return
      }
      
      console.log('Signup response:', {
        hasData: !!data,
        hasUser: !!data?.user,
        userEmail: data?.user?.email,
      })
      
      // Clear form and show confirmation message
      setMessage('Account created! Please check your email to confirm your account (check spam folder if needed). After confirming, you can log in.')
      setEmail('')
      setPassword('')
      
    } catch (error: unknown) {
      console.error('Unexpected signup error:', error)
      setMessage('Unable to create account at this time. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md space-y-8 rounded-lg bg-white p-6 shadow-md">
        <div>
          <h2 className="text-center text-3xl font-bold tracking-tight text-gray-900">
            🌱 Sustainable Agriculture Chatbot
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Sign in to your account
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleLogin}>
          <div className="space-y-4 rounded-md shadow-sm">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email address
              </label>
              <input
                id="email"
                type="email"
                required
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-green-500 focus:outline-none focus:ring-green-500"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-green-500 focus:outline-none focus:ring-green-500"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <div className="flex gap-4">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Sign in'}
            </button>
            
            <button
              type="button"
              onClick={handleSignUp}
              disabled={loading}
              className="flex-1 rounded-md bg-gray-600 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Sign up'}
            </button>
          </div>

          {message && (
            <p className={`text-center text-sm ${
              message.includes('successful') ? 'text-green-600' : 'text-red-600'
            }`}>
              {message}
            </p>
          )}
        </form>
      </div>
    </div>
  )
}

