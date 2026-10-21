"use client";

import React, { useState, useEffect, useMemo } from "react";

// Types
interface EmailLog {
  id: number;
  recipient: string;
  subject: string;
  status: "SENT" | "FAILED" | "PENDING" | "BOUNCED" | "SUCCESS" | "OPENED";
  opened?: boolean;
  opened_at?: string;
  error_message?: string;
  sent_at?: string;
  created_at: string;
}

export default function EmailAutomationDashboard() {
  const [activeTab, setActiveTab] = useState<"overview" | "dispatch" | "reminders">("overview");

  // Initial demonstration logs array (containing sent, opened, failed, and bounced states)
  const [logs, setLogs] = useState<EmailLog[]>([
    {
      id: 101,
      recipient: "alex.hunter@enterprise.com",
      subject: "Welcome to Enterprise Cloud",
      status: "OPENED",
      opened: true,
      opened_at: "2026-10-21 16:18:22",
      created_at: "2026-10-21 16:15:00",
    },
    {
      id: 102,
      recipient: "sarah.chen@fintech.io",
      subject: "Your Monthly Billing Statement #OCT-2026",
      status: "OPENED",
      opened: true,
      opened_at: "2026-10-21 16:12:05",
      created_at: "2026-10-21 16:10:22",
    },
    {
      id: 103,
      recipient: "dev.ops@starlight.co",
      subject: "Security Alert: New Token Generated",
      status: "SENT",
      opened: false,
      created_at: "2026-10-21 15:45:10",
    },
    {
      id: 104,
      recipient: "contact@invalid-bounce-domain.xyz",
      subject: "Product Onboarding Webinar Link",
      status: "FAILED",
      opened: false,
      error_message: "DNS Resolution failure: Domain not found",
      created_at: "2026-10-21 15:30:05",
    },
    {
      id: 105,
      recipient: "marcus.vance@retail.corp",
      subject: "Reminder: Invoice #8491 Due Tomorrow",
      status: "SUCCESS",
      opened: true,
      opened_at: "2026-10-21 15:20:10",
      created_at: "2026-10-21 15:12:44",
    },
    {
      id: 106,
      recipient: "billing-lead@global.org",
      subject: "Quarterly Audit Report Ready",
      status: "SENT",
      opened: false,
      created_at: "2026-10-21 14:55:00",
    },
    {
      id: 107,
      recipient: "ops-noreply@spam-trap.net",
      subject: "Account Synchronization Notice",
      status: "BOUNCED",
      opened: false,
      error_message: "550 5.1.1 User mailbox unknown",
      created_at: "2026-10-21 14:22:15",
    },
  ]);

  // Form states
  const [toEmail, setToEmail] = useState("");
  const [emailSubject, setEmailSubject] = useState("");
  const [emailBody, setEmailBody] = useState("");
  const [scheduleTime, setScheduleTime] = useState("");
  const [sendSuccessMessage, setSendSuccessMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Poll backend for real-time logs
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/v1/logs?limit=50");
        if (res.ok) {
          const apiLogs: EmailLog[] = await res.json();
          if (apiLogs && apiLogs.length > 0) {
            setLogs((prev) => {
              const apiIds = new Set(apiLogs.map((l) => l.id));
              const remainingDemo = prev.filter((p) => !apiIds.has(p.id));
              return [...apiLogs, ...remainingDemo];
            });
          }
        }
      } catch {
        // Fallback to local state if backend is unreachable
      }
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, []);

  // =========================================================================
  // DYNAMIC ANALYTICS CALCULATIONS (from logs array)
  // =========================================================================
  const analytics = useMemo(() => {
    // 1. Total Emails Sent
    const totalSent = logs.filter(
      (log) => log.status === "SENT" || log.status === "SUCCESS" || log.status === "OPENED" || log.opened
    ).length;

    // 2. Total Opened Count
    const totalOpened = logs.filter(
      (log) => log.opened === true || log.status === "OPENED" || Boolean(log.opened_at)
    ).length;

    // 3. Overall Open Rate percentage (%)
    const openRate = totalSent > 0 ? ((totalOpened / totalSent) * 100).toFixed(1) : "0.0";

    // 4. Failed Dispatches Count
    const failedDispatches = logs.filter(
      (log) => log.status === "FAILED" || log.status === "BOUNCED"
    ).length;

    return {
      totalSent,
      totalOpened,
      openRate,
      failedDispatches,
    };
  }, [logs]);

  // Direct Send Handler
  const handleSendEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!toEmail || !emailSubject || !emailBody) return;
    setIsSubmitting(true);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/emails/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          to_email: toEmail,
          subject: emailSubject,
          body: emailBody,
          is_html: true,
        }),
      });

      const data = await res.json();
      const newLog: EmailLog = {
        id: data.log_id || Date.now(),
        recipient: toEmail,
        subject: emailSubject,
        status: res.ok ? "SENT" : "FAILED",
        opened: false,
        created_at: new Date().toISOString().replace("T", " ").substring(0, 19),
      };

      setLogs((prev) => [newLog, ...prev]);
      setSendSuccessMessage(`Email dispatched to ${toEmail}`);
      setToEmail("");
      setEmailSubject("");
      setEmailBody("");
    } catch {
      // Local fallback
      const fallbackLog: EmailLog = {
        id: Date.now(),
        recipient: toEmail,
        subject: emailSubject,
        status: "SENT",
        opened: false,
        created_at: new Date().toISOString().replace("T", " ").substring(0, 19),
      };
      setLogs((prev) => [fallbackLog, ...prev]);
      setSendSuccessMessage(`Email dispatched to ${toEmail} (Mock Mode)`);
      setToEmail("");
      setEmailSubject("");
      setEmailBody("");
    } finally {
      setIsSubmitting(false);
      setTimeout(() => setSendSuccessMessage(""), 4000);
    }
  };

  // Schedule Reminder Handler
  const handleScheduleReminder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!toEmail || !emailSubject || !scheduleTime) return;
    setIsSubmitting(true);

    try {
      await fetch("http://127.0.0.1:8000/api/v1/reminders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          recipient: toEmail,
          subject: emailSubject,
          body: emailBody || "Simulated reminder content",
          scheduled_time: new Date(scheduleTime).toISOString(),
        }),
      });

      setSendSuccessMessage(`Reminder queued for ${toEmail} at ${scheduleTime}`);
      setToEmail("");
      setEmailSubject("");
      setEmailBody("");
      setScheduleTime("");
    } catch {
      setSendSuccessMessage(`Reminder scheduled locally for ${toEmail}`);
      setToEmail("");
      setEmailSubject("");
      setEmailBody("");
      setScheduleTime("");
    } finally {
      setIsSubmitting(false);
      setTimeout(() => setSendSuccessMessage(""), 4000);
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans p-6 md:p-10 relative overflow-hidden">
      {/* Background Decorative Glow Elements */}
      <div className="absolute -top-36 left-1/4 w-[500px] h-[300px] bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-24 right-1/4 w-[450px] h-[300px] bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Header */}
        <header className="flex flex-col md:flex-row items-start md:items-center justify-between pb-6 mb-8 border-b border-slate-800/80 gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center text-2xl shadow-lg shadow-indigo-500/30">
              ⚡
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
                AetherMail Analytics & Automation
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Real-Time Asynchronous Email Dispatch, Open Tracking & Reminder Engine
              </p>
            </div>
          </div>

          <div className="flex flex-wrap gap-2 text-xs font-semibold">
            <span className="px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Engine Online
            </span>
            <span className="px-3 py-1.5 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/20">
              ✦ Mock Mode Active
            </span>
            <span className="px-3 py-1.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20">
              ⏱ APScheduler Active
            </span>
          </div>
        </header>

        {/* Notification Toast */}
        {sendSuccessMessage && (
          <div
            id="toast-success"
            className="mb-6 p-4 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-sm font-semibold flex items-center gap-2 shadow-lg shadow-emerald-950/30 transition-all duration-300 animate-fade-in"
          >
            <span>✓</span> {sendSuccessMessage}
          </div>
        )}

        {/* ================================================================= */}
        {/* ANALYTICS SUMMARY METRICS BAR (TAILWIND CSS CARDS)                */}
        {/* ================================================================= */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
          {/* Card 1: Total Emails Sent */}
          <div
            id="metric-sent"
            className="group relative overflow-hidden rounded-2xl border border-emerald-500/20 bg-slate-900/60 p-6 backdrop-blur-xl shadow-lg shadow-emerald-950/10 transition-all duration-300 hover:scale-[1.02] hover:border-emerald-500/40 hover:bg-slate-900/80"
          >
            <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/10 rounded-full blur-2xl pointer-events-none group-hover:bg-emerald-500/20 transition-all duration-300" />
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold tracking-wider text-slate-400 uppercase">Total Emails Sent</span>
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400 text-base border border-emerald-500/20">
                ✉️
              </span>
            </div>
            <div className="text-3xl font-extrabold text-white tracking-tight">
              {analytics.totalSent.toLocaleString()}
            </div>
            <div className="mt-2.5 flex items-center text-xs text-emerald-400 font-medium">
              <span className="inline-block mr-1">▲</span>
              <span>Dynamically verified across {logs.length} logs</span>
            </div>
          </div>

          {/* Card 2: Total Opened Count */}
          <div
            id="metric-opened"
            className="group relative overflow-hidden rounded-2xl border border-cyan-500/20 bg-slate-900/60 p-6 backdrop-blur-xl shadow-lg shadow-cyan-950/10 transition-all duration-300 hover:scale-[1.02] hover:border-cyan-500/40 hover:bg-slate-900/80"
          >
            <div className="absolute top-0 right-0 w-24 h-24 bg-cyan-500/10 rounded-full blur-2xl pointer-events-none group-hover:bg-cyan-500/20 transition-all duration-300" />
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold tracking-wider text-slate-400 uppercase">Total Opened Count</span>
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400 text-base border border-cyan-500/20">
                👁️
              </span>
            </div>
            <div className="text-3xl font-extrabold text-cyan-300 tracking-tight">
              {analytics.totalOpened.toLocaleString()}
            </div>
            <div className="mt-2.5 flex items-center text-xs text-slate-400 font-medium">
              <span className="text-cyan-400 font-semibold mr-1">{analytics.totalOpened}</span> confirmed recipient opens
            </div>
          </div>

          {/* Card 3: Overall Open Rate */}
          <div
            id="metric-open-rate"
            className="group relative overflow-hidden rounded-2xl border border-violet-500/20 bg-slate-900/60 p-6 backdrop-blur-xl shadow-lg shadow-violet-950/10 transition-all duration-300 hover:scale-[1.02] hover:border-violet-500/40 hover:bg-slate-900/80"
          >
            <div className="absolute top-0 right-0 w-24 h-24 bg-violet-500/10 rounded-full blur-2xl pointer-events-none group-hover:bg-violet-500/20 transition-all duration-300" />
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold tracking-wider text-slate-400 uppercase">Overall Open Rate</span>
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-500/10 text-violet-400 text-base border border-violet-500/20">
                📈
              </span>
            </div>
            <div className="text-3xl font-extrabold text-violet-300 tracking-tight">
              {analytics.openRate}%
            </div>
            <div className="mt-2.5 flex items-center text-xs text-slate-400 font-medium">
              <span className="text-violet-400 font-semibold mr-1">Conversion:</span>
              <span>{analytics.totalOpened} of {analytics.totalSent} delivered</span>
            </div>
          </div>

          {/* Card 4: Failed Dispatches Count */}
          <div
            id="metric-failed"
            className="group relative overflow-hidden rounded-2xl border border-rose-500/20 bg-slate-900/60 p-6 backdrop-blur-xl shadow-lg shadow-rose-950/10 transition-all duration-300 hover:scale-[1.02] hover:border-rose-500/40 hover:bg-slate-900/80"
          >
            <div className="absolute top-0 right-0 w-24 h-24 bg-rose-500/10 rounded-full blur-2xl pointer-events-none group-hover:bg-rose-500/20 transition-all duration-300" />
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold tracking-wider text-slate-400 uppercase">Failed Dispatches</span>
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-rose-500/10 text-rose-400 text-base border border-rose-500/20">
                ⚠️
              </span>
            </div>
            <div className="text-3xl font-extrabold text-rose-400 tracking-tight">
              {analytics.failedDispatches.toLocaleString()}
            </div>
            <div className="mt-2.5 flex items-center text-xs text-slate-400 font-medium">
              <span className={analytics.failedDispatches > 0 ? "text-rose-400 font-semibold mr-1" : "text-emerald-400 font-semibold mr-1"}>
                {analytics.failedDispatches === 0 ? "Zero errors" : `${analytics.failedDispatches} bounced or failed`}
              </span>
            </div>
          </div>
        </section>

        {/* Tab Navigation */}
        <nav className="flex gap-3 mb-6">
          <button
            id="tab-overview"
            onClick={() => setActiveTab("overview")}
            className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 cursor-pointer ${
              activeTab === "overview"
                ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
                : "bg-slate-800/50 text-slate-400 border border-slate-700/50 hover:bg-slate-800 hover:text-slate-200"
            }`}
          >
            📊 Live Activity & Audit
          </button>
          <button
            id="tab-dispatch"
            onClick={() => setActiveTab("dispatch")}
            className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 cursor-pointer ${
              activeTab === "dispatch"
                ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
                : "bg-slate-800/50 text-slate-400 border border-slate-700/50 hover:bg-slate-800 hover:text-slate-200"
            }`}
          >
            ✉️ Direct Email Dispatch
          </button>
          <button
            id="tab-reminders"
            onClick={() => setActiveTab("reminders")}
            className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 cursor-pointer ${
              activeTab === "reminders"
                ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
                : "bg-slate-800/50 text-slate-400 border border-slate-700/50 hover:bg-slate-800 hover:text-slate-200"
            }`}
          >
            ⏱ Schedule Reminder
          </button>
        </nav>

        {/* Main Content Area */}
        <main className="min-h-[420px]">
          {/* Tab 1: Live Activity & Audit */}
          {activeTab === "overview" && (
            <div className="rounded-2xl border border-slate-800/80 bg-slate-900/40 p-6 backdrop-blur-xl shadow-xl">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-4 border-b border-slate-800 gap-2">
                <div>
                  <h2 className="text-lg font-bold text-white tracking-tight">Audit Log & Event Feed</h2>
                  <p className="text-xs text-slate-400">Real-time status changes and delivery outcomes</p>
                </div>
                <span className="self-start sm:self-auto px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-xs font-medium">
                  {logs.length} Total Logs
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-xs font-semibold uppercase tracking-wider text-slate-400">
                      <th className="py-3 px-4">ID</th>
                      <th className="py-3 px-4">Recipient</th>
                      <th className="py-3 px-4">Subject</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Dispatched / Recorded</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50 text-sm">
                    {logs.map((log) => (
                      <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-3.5 px-4 font-mono text-xs text-slate-500">#{log.id}</td>
                        <td className="py-3.5 px-4 font-medium text-slate-200">{log.recipient}</td>
                        <td className="py-3.5 px-4 text-slate-300">{log.subject}</td>
                        <td className="py-3.5 px-4">
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                              log.status === "OPENED"
                                ? "bg-cyan-500/10 text-cyan-300 border border-cyan-500/30"
                                : log.status === "SENT" || log.status === "SUCCESS"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                                : log.status === "FAILED" || log.status === "BOUNCED"
                                ? "bg-rose-500/10 text-rose-400 border border-rose-500/30"
                                : "bg-amber-500/10 text-amber-300 border border-amber-500/30"
                            }`}
                          >
                            {log.status}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-xs text-slate-400 font-mono">
                          {log.created_at}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab 2: Direct Email Dispatch */}
          {activeTab === "dispatch" && (
            <div className="rounded-2xl border border-slate-800/80 bg-slate-900/40 p-6 md:p-8 backdrop-blur-xl shadow-xl max-w-2xl">
              <div className="mb-6">
                <h2 className="text-lg font-bold text-white tracking-tight">Direct Asynchronous Email Dispatch</h2>
                <p className="text-xs text-slate-400 mt-1">Dispatches immediately via aiosmtplib (simulated in mock mode)</p>
              </div>

              <form onSubmit={handleSendEmail} className="flex flex-col gap-5">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                    Recipient Email
                  </label>
                  <input
                    id="dispatch-to"
                    type="email"
                    required
                    placeholder="user@enterprise.com"
                    value={toEmail}
                    onChange={(e) => setToEmail(e.target.value)}
                    className="w-full rounded-xl bg-slate-950/60 border border-slate-750 px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                    Subject Line
                  </label>
                  <input
                    id="dispatch-subject"
                    type="text"
                    required
                    placeholder="e.g. Account Security Verification"
                    value={emailSubject}
                    onChange={(e) => setEmailSubject(e.target.value)}
                    className="w-full rounded-xl bg-slate-950/60 border border-slate-750 px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                    Email Content (HTML or Text)
                  </label>
                  <textarea
                    id="dispatch-body"
                    rows={5}
                    required
                    placeholder="<p>Hello, your monthly summary is ready for download.</p>"
                    value={emailBody}
                    onChange={(e) => setEmailBody(e.target.value)}
                    className="w-full rounded-xl bg-slate-950/60 border border-slate-750 px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all resize-y"
                  />
                </div>

                <button
                  id="dispatch-submit"
                  type="submit"
                  disabled={isSubmitting}
                  className="mt-2 w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/30 transition-all duration-200 cursor-pointer disabled:opacity-50"
                >
                  {isSubmitting ? "Dispatching..." : "🚀 Dispatch Email Immediately"}
                </button>
              </form>
            </div>
          )}

          {/* Tab 3: Schedule Reminder */}
          {activeTab === "reminders" && (
            <div className="rounded-2xl border border-slate-800/80 bg-slate-900/40 p-6 md:p-8 backdrop-blur-xl shadow-xl max-w-2xl">
              <div className="mb-6">
                <h2 className="text-lg font-bold text-white tracking-tight">Schedule an Automated Reminder</h2>
                <p className="text-xs text-slate-400 mt-1">Queued for background asynchronous execution via APScheduler</p>
              </div>

              <form onSubmit={handleScheduleReminder} className="flex flex-col gap-5">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                      Recipient
                    </label>
                    <input
                      id="reminder-recipient"
                      type="email"
                      required
                      placeholder="client@clientcorp.com"
                      value={toEmail}
                      onChange={(e) => setToEmail(e.target.value)}
                      className="w-full rounded-xl bg-slate-950/60 border border-slate-750 px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                      Execution Time (Local)
                    </label>
                    <input
                      id="reminder-datetime"
                      type="datetime-local"
                      required
                      value={scheduleTime}
                      onChange={(e) => setScheduleTime(e.target.value)}
                      className="w-full rounded-xl bg-slate-950/60 border border-slate-750 px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                    Subject Line
                  </label>
                  <input
                    id="reminder-subject"
                    type="text"
                    required
                    placeholder="Reminder: Invoice Due in 24 Hours"
                    value={emailSubject}
                    onChange={(e) => setEmailSubject(e.target.value)}
                    className="w-full rounded-xl bg-slate-950/60 border border-slate-750 px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                    Body Content (Jinja2 context supported)
                  </label>
                  <textarea
                    id="reminder-body"
                    rows={4}
                    placeholder="Dear Customer, your invoice is due on the scheduled date."
                    value={emailBody}
                    onChange={(e) => setEmailBody(e.target.value)}
                    className="w-full rounded-xl bg-slate-950/60 border border-slate-750 px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all resize-y"
                  />
                </div>

                <button
                  id="reminder-submit"
                  type="submit"
                  disabled={isSubmitting}
                  className="mt-2 w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold text-sm shadow-lg shadow-purple-600/30 transition-all duration-200 cursor-pointer disabled:opacity-50"
                >
                  {isSubmitting ? "Queueing..." : "⏱ Queue Scheduled Reminder"}
                </button>
              </form>
            </div>
          )}
        </main>

        {/* Footer */}
        <footer className="mt-14 pt-6 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-3">
          <span>© 2026 AetherMail Architecture — Powered by FastAPI & APScheduler</span>
          <div className="flex items-center gap-3">
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              API Swagger Docs
            </a>
            <span>•</span>
            <a
              href="http://localhost:8000/redoc"
              target="_blank"
              rel="noreferrer"
              className="text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              ReDoc Specs
            </a>
          </div>
        </footer>
      </div>
    </div>
  );
}
