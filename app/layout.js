export const metadata = {
  title: 'Tech News Feed',
  description: '🚀 Interactive Tech News Feed - Like, Comment, Share',
  icons: {
    icon: '🚀',
  },
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
