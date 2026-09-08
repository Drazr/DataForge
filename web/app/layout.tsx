import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: 'DataForge — Voice appointment confirmation', description: 'Listen, repeat, and confirm a synthetic appointment with Rime speech.', icons: {icon:'/favicon.svg'} };
export default function RootLayout({ children }: Readonly<{children: React.ReactNode}>) {return <html lang="en"><body>{children}</body></html>;}
