"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";

export function Navbar() {
  return (
    <motion.nav
      className="fixed top-0 left-0 right-0 z-50 glass"
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="container mx-auto px-6">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center gap-2">
            <span
              className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent"
              style={{ fontFamily: 'var(--font-playfair)' }}
            >
              BLOOM
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-sm text-zinc-300 hover:text-white transition-colors">
              Features
            </a>
            <a href="#demo" className="text-sm text-zinc-300 hover:text-white transition-colors">
              Demo
            </a>
            <a href="#team" className="text-sm text-zinc-300 hover:text-white transition-colors">
              Team
            </a>
          </div>

          <div className="flex items-center gap-3">
            <Link href="/dashboard">
              <Button variant="ghost" size="sm" className="text-zinc-300 hover:text-white">
                Log in
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button size="sm">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </motion.nav>
  );
}
