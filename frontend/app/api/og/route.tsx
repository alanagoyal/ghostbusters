import { ImageResponse } from 'next/og';

export const runtime = 'edge';

export async function GET(request: Request) {
  // Get the base URL from the request
  const { origin } = new URL(request.url);

  // Fetch the ghost image from the public directory
  const ghostImageData = await fetch(`${origin}/ghost.png`).then((res) =>
    res.arrayBuffer()
  );

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
          gap: 40,
        }}
      >
        {/* Ghost Image */}
        <img
          // @ts-ignore
          src={ghostImageData}
          alt="Ghost"
          width="300"
          height="300"
          style={{
            objectFit: 'contain',
          }}
        />

        {/* Ghostbusters Text */}
        <div
          style={{
            fontSize: 120,
            fontWeight: 700,
            color: 'white',
            letterSpacing: '-0.02em',
          }}
        >
          Ghostbusters
        </div>
      </div>
    ),
    {
      width: 1200,
      height: 630,
    },
  );
}
