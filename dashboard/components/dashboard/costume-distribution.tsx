'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface CostumeData {
  name: string
  count: number
  percentage: number
}

interface CostumeDistributionProps {
  costumes: CostumeData[]
}

export function CostumeDistribution({ costumes }: CostumeDistributionProps) {
  const maxCount = Math.max(...costumes.map(c => c.count), 1)

  return (
    <Card className="col-span-2 flex flex-col h-[500px]">
      <CardHeader className="flex-shrink-0">
        <CardTitle>Popular Costumes</CardTitle>
        <CardDescription>Most spotted trick-or-treater costumes</CardDescription>
      </CardHeader>
      <CardContent className="flex-1 overflow-y-auto">
        <div className="space-y-4">
          {costumes.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              No costume data available yet
            </p>
          ) : (
            costumes.map((costume, index) => (
              <div
                key={costume.name}
                className="space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{costume.name}</span>
                    <Badge variant="secondary" className="text-xs">
                      {costume.count}
                    </Badge>
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {costume.percentage.toFixed(1)}%
                  </span>
                </div>
                <div className="h-2 rounded-full bg-secondary overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all duration-500 animate-grow-width"
                    style={{
                      width: `${(costume.count / maxCount) * 100}%`,
                      animationDelay: `${(index + 1) * 150}ms`
                    }}
                  />
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}
