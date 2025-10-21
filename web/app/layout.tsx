import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { ChatButton } from "@/components/ai-chat/chat-button";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Koroh - AI-Powered Professional Networking",
  description: "Connect, discover opportunities, and build your professional network with AI-powered insights",
  keywords: ["networking", "jobs", "career", "AI", "professional"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="font-sans antialiased bg-gray-50 text-gray-900">
        <Providers>
          {children}
          <ChatButton />
        </Providers>
      </body>
    </html>
  );
}
