import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  MessageSquare,
  FileStack,
  Search,
  History,
  Gauge,
  Settings as SettingsIcon,
  LogOut,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/chat", label: "Reading Room", icon: MessageSquare },
  { to: "/documents", label: "Stacks", icon: FileStack },
  { to: "/search", label: "Catalog Search", icon: Search },
  { to: "/history", label: "Archives", icon: History },
  { to: "/evaluation", label: "Ledger", icon: Gauge },
  { to: "/settings", label: "Settings", icon: SettingsIcon },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="flex h-screen bg-paper text-ink">
      <aside className="w-64 shrink-0 bg-ink text-paper flex flex-col border-r border-rule">
        <div className="px-6 py-6 border-b border-ink-soft/30">
          <h1
            className="text-2xl leading-tight"
            style={{ fontFamily: "var(--font-display)" }}
          >
            Athenaeum
          </h1>
          <p className="text-xs text-paper/60 mt-1 font-mono">
            AI Knowledge Workspace
          </p>
        </div>

        <nav className="flex-1 py-4">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-6 py-3 text-sm transition-colors border-l-2 ${
                  isActive
                    ? "border-brass bg-white/5 text-brass-light"
                    : "border-transparent text-paper/75 hover:text-paper hover:bg-white/5"
                }`
              }
            >
              <Icon size={17} strokeWidth={1.75} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-6 py-4 border-t border-ink-soft/30">
          <p className="text-xs text-paper/50 font-mono truncate">
            {user?.email}
          </p>
          <button
            onClick={handleLogout}
            className="mt-2 flex items-center gap-2 text-sm text-paper/75 hover:text-brass-light transition-colors"
          >
            <LogOut size={15} strokeWidth={1.75} />
            Sign out
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
