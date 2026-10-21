import React from "react";
import "./globals.css";

export const metadata = {
  title: "AetherMail — Email Automation & Reminder System",
  description: "Enterprise async email dispatch, Jinja2 dynamic templating, and reminder scheduler dashboard.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body style={{ margin: 0, padding: 0, backgroundColor: "#090d16" }}>
        {children}
      </body>
    </html>
  );
}
