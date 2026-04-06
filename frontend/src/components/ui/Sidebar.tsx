"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { clearToken } from "@/lib/api";

interface Props {
  activePage: string;
}

const navItems = [
  { id: "dashboard", label: "Dashboard", icon: "📊", href: "/dashboard" },
  { id: "transactions", label: "Data Center", icon: "📥", href: "/dashboard/transactions" },
  { id: "recommendations", label: "Recommendations", icon: "💡", href: "/dashboard/recommendations" },
];

export default function Sidebar({ activePage }: Props) {
  const router = useRouter();

  const handleLogout = () => {
    clearToken();
    router.push("/");
  };

  return (
    <>
      {/* Desktop sidebar */}
      <aside
        className="hidden lg:flex fixed left-0 top-0 h-screen w-64 flex-col z-40"
        style={{
          background: "var(--color-surface)",
          borderRight: "1px solid var(--color-border)",
        }}
      >
        {/* Logo */}
        <div className="p-6 flex items-center gap-3" style={{ borderBottom: "1px solid var(--color-border)" }}>
          <div className="w-10 h-10 rounded-xl gradient-emerald flex items-center justify-center">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <div>
            <span className="font-bold text-lg" style={{ color: "var(--color-text-primary)" }}>
              FinSight
            </span>
            <span className="text-xs block" style={{ color: "var(--color-accent-emerald)" }}>
              AI Engine
            </span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => (
            <Link
              key={item.id}
              href={item.href}
              className="flex items-center gap-3 px-4 py-3 rounded-lg transition-all text-sm font-medium"
              style={{
                background:
                  activePage === item.id ? "rgba(16,185,129,0.1)" : "transparent",
                color:
                  activePage === item.id
                    ? "var(--color-accent-emerald)"
                    : "var(--color-text-secondary)",
                border:
                  activePage === item.id
                    ? "1px solid rgba(16,185,129,0.2)"
                    : "1px solid transparent",
              }}
            >
              <span className="text-lg">{item.icon}</span>
              {item.label}
            </Link>
          ))}
        </nav>

        {/* Logout */}
        <div className="p-4" style={{ borderTop: "1px solid var(--color-border)" }}>
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-4 py-3 rounded-lg w-full text-sm font-medium transition-all"
            style={{ color: "var(--color-text-muted)" }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "var(--color-accent-rose)")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "var(--color-text-muted)")}
          >
            <span className="text-lg">🚪</span>
            Sign Out
          </button>
        </div>
      </aside>

      {/* Mobile top bar */}
      <div
        className="lg:hidden fixed top-0 left-0 right-0 z-40 flex items-center justify-between px-4 py-3"
        style={{
          background: "var(--color-surface)",
          borderBottom: "1px solid var(--color-border)",
        }}
      >
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg gradient-emerald flex items-center justify-center">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <span className="font-bold" style={{ color: "var(--color-text-primary)" }}>
            FinSight AI
          </span>
        </div>
        <div className="flex gap-2">
          {navItems.map((item) => (
            <Link
              key={item.id}
              href={item.href}
              className="px-3 py-1.5 rounded-lg text-xs font-medium"
              style={{
                background: activePage === item.id ? "rgba(16,185,129,0.15)" : "transparent",
                color: activePage === item.id ? "var(--color-accent-emerald)" : "var(--color-text-secondary)",
              }}
            >
              {item.icon} {item.label}
            </Link>
          ))}
        </div>
      </div>
    </>
  );
}
