'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Clock } from 'lucide-react'
import { truncateString, toTitleCase } from '@/lib/string-utils'

interface Detection {
  id: string
  timestamp: string
  confidence: number
  device_id: string
  costume_classification: string | null
  costume_confidence: number | null
  costume_description: string | null
}

interface LiveFeedProps {
  detections: Detection[]
  limit?: number
}

export function LiveFeed({ detections, limit = 5 }: LiveFeedProps) {
  const recentDetections = detections.slice(0, limit)

  return (
    <Card className="feed-section flex flex-col">
      <CardHeader className="flex-shrink-0">
        <CardTitle>Live Feed</CardTitle>
        <CardDescription>Most recent trick-or-treaters</CardDescription>
      </CardHeader>
      <CardContent className="flex-1">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {recentDetections.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              Waiting for visitors...
            </p>
          ) : (
            recentDetections.map((detection, index) => (
              <div
                key={detection.id}
                className="flex items-start gap-3 py-3 border-t border-border"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex flex-col gap-1.5">
                    <div className="flex items-center justify-between gap-2">
                      {detection.costume_classification && (
                        <Badge variant="default" className="bg-foreground text-background hover:bg-foreground/80 text-xs max-w-[180px] sm:max-w-[220px] truncate" title={toTitleCase(detection.costume_classification) || ''}>
                          {truncateString(toTitleCase(detection.costume_classification), 25)}
                        </Badge>
                      )}
                      <span className="text-xs text-muted-foreground">
                        {(detection.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    {detection.costume_description && (
                      <p className="text-sm text-foreground">
                        {detection.costume_description}
                      </p>
                    )}
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      {new Date(detection.timestamp).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}
