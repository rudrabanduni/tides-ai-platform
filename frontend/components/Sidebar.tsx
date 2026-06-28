'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/auth-context';
import { 
  LayoutDashboard, 
  Rocket, 
  UploadCloud, 
  Users, 
  TrendingUp, 
  Settings, 
  LogOut, 
  ShieldCheck,
  Moon,
  Sun
} from 'lucide-react';

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [theme, setTheme] = React.useState('dark');

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    if (typeof window !== 'undefined') {
      const root = window.document.documentElement;
      root.classList.remove('light', 'dark');
      root.classList.add(nextTheme);
    }
  };

  const navItems = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Startups', href: '/startups', icon: Rocket },
    { name: 'Upload Deck', href: '/upload', icon: UploadCloud },
    { name: 'Committee', href: '/committee', icon: Users },
    { name: 'Portfolio', href: '/portfolio', icon: TrendingUp },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  if (!user) return null;

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-950 h-screen fixed left-0 top-0 flex flex-col justify-between text-slate-200 z-30">
      <div>
        <div className="p-6 border-b border-slate-900 flex items-center space-x-3">
          <div className="bg-primary/20 p-2 rounded-lg text-primary">
            <ShieldCheck className="w-6 h-6 text-blue-500" />
          </div>
          <div>
            <h1 className="font-extrabold text-lg bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
              TIDES Platform
            </h1>
            <span className="text-xs text-slate-500">Intelligence Engine</span>
          </div>
        </div>

        <nav className="mt-6 px-4 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname?.startsWith(item.href + '/');
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20'
                    : 'text-slate-400 hover:bg-slate-900 hover:text-slate-100 border border-transparent'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="p-4 border-t border-slate-900 space-y-4">
        <div className="flex items-center justify-between px-4 py-2 rounded-lg bg-slate-900">
          <span className="text-xs text-slate-400 font-medium">Appearance</span>
          <button 
            onClick={toggleTheme}
            className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
          >
            {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
        </div>

        <div className="flex items-center justify-between px-2">
          <div className="flex flex-col">
            <span className="text-sm font-semibold text-slate-200">{user.name}</span>
            <span className="text-xs text-slate-500">{user.role}</span>
          </div>
          <button
            onClick={logout}
            className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
            title="Log Out"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </div>
    </aside>
  );
}
