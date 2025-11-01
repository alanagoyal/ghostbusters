import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

const linkClassName = "relative text-muted-foreground font-medium after:absolute after:bottom-0 after:left-0 after:h-[2px] after:w-0 after:bg-muted-foreground after:transition-all after:duration-300 hover:after:w-full";

export function About() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>About</CardTitle>
        <CardDescription>How this works</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground leading-relaxed">
          This is a live feed from my front door in Noe Valley that identifies the costumes of trick-or-treaters in real time. The video stream is sent over{' '}
          <a href="https://en.wikipedia.org/wiki/Real_Streaming_Protocol" target="_blank" rel="noopener noreferrer" className={linkClassName}>RTSP</a> to a{' '}
          <a href="https://www.raspberrypi.org/" target="_blank" rel="noopener noreferrer" className={linkClassName}>Raspberry Pi</a>, which runs{' '}
          <a href="https://github.com/ultralytics/ultralytics" target="_blank" rel="noopener noreferrer" className={linkClassName}>YOLOv8</a> to detect people. The frames are then classified for costumes using{' '}
          <a href="https://baseten.co/" target="_blank" rel="noopener noreferrer" className={linkClassName}>Baseten</a>, the detections are stored in{' '}
          <a href="https://supabase.com/" target="_blank" rel="noopener noreferrer" className={linkClassName}>Supabase</a> using real-time listeners, and this dashboard displays the results as they happen. It's fully open-source and available on{' '}
          <a href="https://github.com/alanagoyal/costume-classifier" target="_blank" rel="noopener noreferrer" className={linkClassName}>GitHub</a>.
        </p>
      </CardContent>
    </Card>
  )
}
