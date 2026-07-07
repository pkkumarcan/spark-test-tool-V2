import './globals.css'

export const metadata = {
  title: 'Spark Media Factory V2',
  description: 'AI-powered media generation and coding agent platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
