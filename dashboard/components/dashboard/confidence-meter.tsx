'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useMemo } from 'react'

interface ConfidenceMeterProps {
  detections: Array<{ confidence: number }>
}

export function ConfidenceMeter({ detections }: ConfidenceMeterProps) {
  const avgConfidence = useMemo(() => {
    if (detections.length === 0) return 0
    const sum = detections.reduce((acc, d) => acc + d.confidence, 0)
    return (sum / detections.length) * 100
  }, [detections])


  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 90) return 'Excellent'
    if (confidence >= 75) return 'Good'
    if (confidence >= 60) return 'Fair'
    return 'Needs Review'
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Detection Quality</CardTitle>
        <CardDescription>Average confidence score</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center justify-center py-4">
          <div className="text-5xl font-bold animate-scale-in">
            {avgConfidence.toFixed(1)}%
          </div>
          <div className="text-sm text-muted-foreground mt-2 animate-fade-in" style={{ animationDelay: '200ms' }}>
            {getConfidenceLabel(avgConfidence)}
          </div>
          <div className="w-full mt-4">
            <div className="h-2 rounded-full bg-secondary overflow-hidden">
              <div
                className="h-full bg-primary transition-all duration-500 animate-grow-width"
                style={{ width: `${avgConfidence}%`, animationDelay: '400ms' }}
              />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
