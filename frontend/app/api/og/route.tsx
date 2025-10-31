import { ImageResponse } from 'next/og';

export const runtime = 'edge';

export async function GET() {
  return new ImageResponse(
    (
      <div
        style={{
          height: '100%',
          width: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#9d152b',
          padding: '80px',
          position: 'relative',
        }}
      >
        {/* Decorative corner elements for Halloween vibe */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100px',
            height: '100px',
            borderTop: '4px solid white',
            borderLeft: '4px solid white',
          }}
        />
        <div
          style={{
            position: 'absolute',
            top: 0,
            right: 0,
            width: '100px',
            height: '100px',
            borderTop: '4px solid white',
            borderRight: '4px solid white',
          }}
        />
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            width: '100px',
            height: '100px',
            borderBottom: '4px solid white',
            borderLeft: '4px solid white',
          }}
        />
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            right: 0,
            width: '100px',
            height: '100px',
            borderBottom: '4px solid white',
            borderRight: '4px solid white',
          }}
        />

        {/* Main content */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            textAlign: 'center',
          }}
        >
          {/* Title */}
          <div
            style={{
              fontSize: 96,
              fontWeight: 700,
              color: 'white',
              marginBottom: 24,
              letterSpacing: '-0.02em',
              textTransform: 'uppercase',
            }}
          >
            GHOSTBUSTERS
          </div>

          {/* Subtitle/Description */}
          <div
            style={{
              fontSize: 36,
              color: 'white',
              marginBottom: 60,
              opacity: 0.9,
              maxWidth: '900px',
            }}
          >
            A live classification of trick-or-treaters in San Francisco
          </div>

          {/* Stats section with pink accents */}
          <div
            style={{
              display: 'flex',
              gap: 60,
              justifyContent: 'center',
              alignItems: 'center',
            }}
          >
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                padding: '20px 40px',
                border: '2px solid white',
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
              }}
            >
              <div
                style={{
                  fontSize: 48,
                  fontWeight: 700,
                  color: '#ffb3c1',
                }}
              >
                REAL-TIME
              </div>
              <div
                style={{
                  fontSize: 24,
                  color: 'white',
                  opacity: 0.8,
                }}
              >
                Detection
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                padding: '20px 40px',
                border: '2px solid white',
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
              }}
            >
              <div
                style={{
                  fontSize: 48,
                  fontWeight: 700,
                  color: '#ff8fa3',
                }}
              >
                YOLOv8
              </div>
              <div
                style={{
                  fontSize: 24,
                  color: 'white',
                  opacity: 0.8,
                }}
              >
                Computer Vision
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                padding: '20px 40px',
                border: '2px solid white',
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
              }}
            >
              <div
                style={{
                  fontSize: 48,
                  fontWeight: 700,
                  color: '#ff4d6d',
                }}
              >
                EDGE AI
              </div>
              <div
                style={{
                  fontSize: 24,
                  color: 'white',
                  opacity: 0.8,
                }}
              >
                Raspberry Pi
              </div>
            </div>
          </div>
        </div>

        {/* Footer tech indicator */}
        <div
          style={{
            position: 'absolute',
            bottom: 40,
            fontSize: 20,
            color: 'white',
            opacity: 0.6,
            fontFamily: 'monospace',
          }}
        >
          Powered by Baseten AI • Halloween 2024
        </div>
      </div>
    ),
    {
      width: 1200,
      height: 630,
    },
  );
}
