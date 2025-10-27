'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

interface PersonDetection {
  id: string
  timestamp: string
  confidence: number
  bounding_box: any
  image_url: string | null
  device_id: string
  costume_classification: string | null
  costume_confidence: number | null
}

export default function Dashboard() {
  const [detections, setDetections] = useState<PersonDetection[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch initial detections
  useEffect(() => {
    async function fetchDetections() {
      try {
        const { data, error } = await supabase
          .from('person_detections')
          .select('*')
          .order('timestamp', { ascending: false })
          .limit(50)

        if (error) throw error
        setDetections(data || [])
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch detections')
      } finally {
        setLoading(false)
      }
    }

    fetchDetections()
  }, [])

  // Subscribe to real-time updates
  useEffect(() => {
    const channel = supabase
      .channel('person_detections')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'person_detections' },
        (payload) => {
          console.log('Received new detection:', payload)
          const newDetection = payload.new as PersonDetection
          setDetections((prev) => [newDetection, ...prev])
        }
      )
      .subscribe((status) => {
        console.log('Subscription status:', status)
        if (status === 'SUBSCRIBED') {
          console.log('Successfully subscribed to person_detections changes')
        }
      })

    return () => {
      console.log('Unsubscribing from channel')
      supabase.removeChannel(channel)
    }
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-xl">Loading detections...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 text-gray-900">Person Detection Dashboard</h1>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            Error: {error}
          </div>
        )}

        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-800">
              Recent Detections ({detections.length})
            </h2>
          </div>

          <div className="divide-y divide-gray-200">
            {detections.length === 0 ? (
              <div className="px-6 py-8 text-center text-gray-500">
                No detections yet. Waiting for real-time updates...
              </div>
            ) : (
              detections.map((detection) => (
                <div key={detection.id} className="px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">
                        Device: {detection.device_id}
                      </div>
                      <div className="text-sm text-gray-500">
                        {new Date(detection.timestamp).toLocaleString()}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-semibold text-gray-900">
                        Confidence: {(detection.confidence * 100).toFixed(1)}%
                      </div>
                      {detection.costume_classification && (
                        <div className="text-sm text-gray-600">
                          Costume: {detection.costume_classification}
                          ({(detection.costume_confidence! * 100).toFixed(1)}%)
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
