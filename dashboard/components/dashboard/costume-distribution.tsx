'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { AnimatedNumber } from '@/components/ui/animated-number'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { toTitleCase } from '@/lib/string-utils'

interface CostumeData {
  name: string
  fullName: string
  count: number
  percentage: number
  descriptions: string[]
}

interface CostumeDistributionProps {
  costumes: CostumeData[]
}

export function CostumeDistribution({ costumes }: CostumeDistributionProps) {
  const maxCount = Math.max(...costumes.map(c => c.count), 1)
  const [expandedCostume, setExpandedCostume] = useState<string | null>(null)

  const toggleExpanded = (costumeName: string) => {
    setExpandedCostume(expandedCostume === costumeName ? null : costumeName)
  }

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
                key={costume.fullName}
                className="space-y-2"
              >
                <div
                  className="flex items-center justify-between cursor-pointer hover:bg-accent/50 p-2 rounded-lg transition-colors"
                  onClick={() => toggleExpanded(costume.fullName)}
                >
                  <div className="flex items-center gap-2">
                    {costume.descriptions.length > 0 ? (
                      expandedCostume === costume.fullName ? (
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      )
                    ) : (
                      <div className="w-4" />
                    )}
                    <span className="text-sm font-medium">{toTitleCase(costume.name)}</span>
                    <Badge variant="secondary" className="text-xs">
                      <AnimatedNumber value={costume.count} decimals={0} />
                    </Badge>
                  </div>
                  <span className="text-sm text-muted-foreground">
                    <AnimatedNumber value={costume.percentage} decimals={1} suffix="%" />
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
                {expandedCostume === costume.fullName && costume.descriptions.length > 0 && (
                  <div className="ml-6 pl-4 border-l-2 border-border space-y-1 py-2">
                    {costume.descriptions.map((desc, idx) => (
                      <div key={idx} className="text-sm text-muted-foreground">
                        • {desc}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}
