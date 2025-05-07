import { useEffect } from 'react'
import { useRouter } from 'next/router'
import { supabase } from '../lib/supabaseClient'
import Head from "next/head";
import Image from "next/image";
import { Geist, Geist_Mono } from "next/font/google";
import styles from "@/styles/Home.module.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export default function Home() {
  const router = useRouter()

  useEffect(() => {
    // Check if user is logged in
    const checkUser = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      
      if (session) {
        // If logged in, redirect to chat
        router.push('/chat')
      } else {
        // If not logged in, redirect to login
        router.push('/login')
      }
    }

    checkUser()
  }, [router])

  // Show a loading state while redirecting
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-green-600 mb-4">🌱</h1>
        <h2 className="text-2xl font-semibold text-gray-900">
          Sustainable Agriculture Assistant
        </h2>
        <p className="mt-2 text-gray-600">Loading...</p>
      </div>
    </div>
  )
}

