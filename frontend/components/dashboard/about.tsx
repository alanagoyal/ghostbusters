import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
export function About() {
  return <Card><CardHeader><CardTitle>About Ghostbusters</CardTitle><CardDescription>Camera detections and costume guesses</CardDescription></CardHeader><CardContent><p className="text-sm text-muted-foreground">YOLO detects people and possible inflatable costumes. The configured vision model guesses costumes and can make mistakes. This cloud gallery uses Supabase; cloud inference and storage are explicit alternatives to the private local installation. Counts describe detections, not unique visitors.</p></CardContent></Card>
}
