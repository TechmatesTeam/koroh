import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { ChatButton } from "@/components/ai-chat/chat-button";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { SmartPageTransition } from "@/components/ui/smart-page-transition";
import { AppInitializer } from "@/components/ui/app-initializer";

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
      <body className="font-sans antialiased bg-white text-gray-900">
        <ErrorBoundary>
          <AppInitializer>
            <Providers>
              <SmartPageTransition>
                {children}
              </SmartPageTransition>
              <ChatButton />
            </Providers>
          </AppInitializer>
        </ErrorBoundary>
      </body>
    </html>
  );
}
