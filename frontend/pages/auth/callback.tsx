import { useEffect } from 'react'
import { useRouter } from 'next/router'
import { supabase } from '../../lib/supabaseClient'

export default function AuthCallback() {
  const router = useRouter()

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        // Get the session to confirm the user is authenticated
        const { data: { session }, error } = await supabase.auth.getSession()
        
        if (error) {
          console.error('Auth callback error:', error)
        }

        // Always redirect to login page after confirmation
        router.push('/login')
      } catch (error) {
        console.error('Error in auth callback:', error)
        router.push('/login')
      }
    }

    handleAuthCallback()
  }, [router])

  // Show loading state while processing
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="text-center">
        <h2 className="text-2xl font-semibold text-gray-900">
          Confirming your email...
        </h2>
        <p className="mt-2 text-gray-600">
          You will be redirected to login shortly.
        </p>
      </div>
    </div>
  )
} 