import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { Sidebar } from "@/components/layout/sidebar";

export const metadata: Metadata = {
  title: "News Intelligence Platform",
  description: "Enterprise autonomous news intelligence with real-time event detection, multi-agent analysis, and executive reporting.",
  keywords: ["news intelligence", "event detection", "AI", "NLP", "BERTopic"],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background antialiased">
        <Providers>
          <div className="flex">
            <Sidebar />
            <main className="flex-1 ml-[260px] min-h-screen">
              <div className="p-8">
                {children}
              </div>
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
