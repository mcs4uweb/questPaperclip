import "./globals.css";

export const metadata = {
  title: "Quest Paperclip",
  description: "Hermes agent control plane",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased">{children}</body>
    </html>
  );
}
