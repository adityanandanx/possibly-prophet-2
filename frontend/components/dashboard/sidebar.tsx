"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import {
  FiHome,
  FiFileText,
  FiUpload,
  FiLink,
  FiList,
  FiSettings,
  FiLogOut,
  FiChevronLeft,
} from "react-icons/fi";

interface SidebarProps {
  children: React.ReactNode;
}

const menuItems = [
  { icon: FiHome, label: "Dashboard", href: "/dashboard" },
  { icon: FiFileText, label: "Text Input", href: "/dashboard/text" },
  { icon: FiUpload, label: "File Upload", href: "/dashboard/upload" },
  { icon: FiLink, label: "Web URL", href: "/dashboard/url" },
  { icon: FiList, label: "Your Lessons", href: "/dashboard/lessons" },
];

export function DashboardLayout({ children }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen bg-zinc-50 dark:bg-zinc-950">
      {/* Sidebar */}
      <motion.aside
        className={cn(
          "fixed left-0 top-0 bottom-0 z-40 flex flex-col bg-gradient-to-b from-slate-900 to-indigo-950 text-white transition-all duration-300",
          collapsed ? "w-20" : "w-72"
        )}
        initial={false}
        animate={{ width: collapsed ? 80 : 288 }}
      >
        {/* Logo */}
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          {!collapsed && (
            <Link href="/">
              <motion.span
                className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent"
                style={{ fontFamily: 'var(--font-playfair)' }}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                BLOOM
              </motion.span>
            </Link>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-2 rounded-xl hover:bg-white/10 transition-colors"
          >
            <motion.div animate={{ rotate: collapsed ? 180 : 0 }}>
              <FiChevronLeft className="w-5 h-5" />
            </motion.div>
          </button>
        </div>

        {/* Menu */}
        <nav className="flex-1 py-6 px-3 space-y-2">
          {menuItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link key={item.href} href={item.href}>
                <motion.div
                  className={cn(
                    "flex items-center gap-3 px-4 py-3 rounded-2xl transition-all duration-200",
                    isActive
                      ? "bg-gradient-to-r from-blue-600/30 to-indigo-600/30 text-white"
                      : "text-zinc-400 hover:bg-white/10 hover:text-white"
                  )}
                  whileHover={{ x: 4 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <item.icon className="w-5 h-5 flex-shrink-0" />
                  {!collapsed && (
                    <motion.span
                      className="text-sm font-medium"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                    >
                      {item.label}
                    </motion.span>
                  )}
                  {isActive && (
                    <motion.div
                      className="absolute left-0 w-1 h-8 bg-blue-500 rounded-r-full"
                      layoutId="activeIndicator"
                    />
                  )}
                </motion.div>
              </Link>
            );
          })}
        </nav>

        {/* Bottom section */}
        <div className="p-3 border-t border-white/10 space-y-2">
          <Link href="/dashboard/settings">
            <motion.div
              className="flex items-center gap-3 px-4 py-3 rounded-2xl text-zinc-400 hover:bg-white/10 hover:text-white transition-all"
              whileHover={{ x: 4 }}
            >
              <FiSettings className="w-5 h-5 flex-shrink-0" />
              {!collapsed && <span className="text-sm font-medium">Settings</span>}
            </motion.div>
          </Link>
          <Link href="/">
            <motion.div
              className="flex items-center gap-3 px-4 py-3 rounded-2xl text-zinc-400 hover:bg-white/10 hover:text-white transition-all"
              whileHover={{ x: 4 }}
            >
              <FiLogOut className="w-5 h-5 flex-shrink-0" />
              {!collapsed && <span className="text-sm font-medium">Log out</span>}
            </motion.div>
          </Link>
        </div>
      </motion.aside>

      {/* Main content */}
      <main
        className={cn(
          "flex-1 transition-all duration-300",
          collapsed ? "ml-20" : "ml-72"
        )}
      >
        {children}
      </main>
    </div>
  );
}
