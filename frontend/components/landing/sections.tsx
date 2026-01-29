"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { FiArrowRight, FiPlay, FiZap, FiBookOpen, FiVideo, FiUsers } from "react-icons/fi";

export function HeroSection() {
  return (
    <section className="gradient-hero min-h-screen flex items-center justify-center relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <motion.div
          className="absolute top-20 left-10 w-72 h-72 bg-blue-500/20 rounded-full blur-3xl"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
        <motion.div
          className="absolute bottom-20 right-10 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl"
          animate={{
            scale: [1.2, 1, 1.2],
            opacity: [0.5, 0.3, 0.5],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      </div>

      <div className="container mx-auto px-6 py-20 relative z-10">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <span className="inline-block px-4 py-2 rounded-full text-sm font-medium bg-blue-500/20 text-blue-300 mb-6">
              ✨ AI-Powered Education
            </span>
          </motion.div>

          <motion.h1
            className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight"
            style={{ fontFamily: 'var(--font-playfair)' }}
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            Transform Learning with{" "}
            <span className="bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
              BLOOM
            </span>
          </motion.h1>

          <motion.p
            className="text-xl text-zinc-300 mb-10 max-w-2xl mx-auto leading-relaxed"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            Create stunning, interactive educational content in minutes. 
            Our AI transforms your materials into engaging video lessons 
            that help students grasp complex topics effortlessly.
          </motion.p>

          <motion.div
            className="flex flex-col sm:flex-row gap-4 justify-center"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <Link href="/dashboard">
              <Button size="lg" className="group">
                Get Started Free
                <FiArrowRight className="ml-2 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
            <Button variant="outline" size="lg" className="border-white/20 text-white hover:bg-white/10">
              <FiPlay className="mr-2" />
              Watch Demo
            </Button>
          </motion.div>

          {/* Stats */}
          <motion.div
            className="mt-16 grid grid-cols-3 gap-8 max-w-lg mx-auto"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.5 }}
          >
            {[
              { value: "10K+", label: "Lessons Created" },
              { value: "500+", label: "Teachers" },
              { value: "98%", label: "Satisfaction" },
            ].map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl font-bold text-white">{stat.value}</div>
                <div className="text-sm text-zinc-400">{stat.label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        className="absolute bottom-8 left-1/2 transform -translate-x-1/2"
        animate={{ y: [0, 10, 0] }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        <div className="w-6 h-10 rounded-full border-2 border-white/30 flex items-start justify-center p-2">
          <div className="w-1.5 h-3 bg-white/50 rounded-full" />
        </div>
      </motion.div>
    </section>
  );
}

export function DemoSection() {
  return (
    <section className="relative py-32">
      <div className="gradient-slant absolute inset-0 -my-20" />
      <div className="container mx-auto px-6 relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-4xl font-bold text-white mb-6" style={{ fontFamily: 'var(--font-playfair)' }}>
              See BLOOM in Action
            </h2>
            <p className="text-lg text-blue-100 mb-8 leading-relaxed">
              Watch how our AI transforms raw educational content into beautifully 
              animated video lessons. Simply paste your text, upload a document, 
              or provide a URL – and let BLOOM do the magic.
            </p>
            <ul className="space-y-4">
              {[
                "Automatic content structuring",
                "AI-generated animations",
                "Customizable difficulty levels",
                "Assessment generation",
              ].map((feature, index) => (
                <motion.li
                  key={index}
                  className="flex items-center text-white"
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: index * 0.1 }}
                >
                  <span className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center mr-3">
                    <FiZap className="w-3 h-3" />
                  </span>
                  {feature}
                </motion.li>
              ))}
            </ul>
          </motion.div>

          <motion.div
            className="relative"
            initial={{ opacity: 0, x: 50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <div className="glass rounded-3xl p-2 animate-pulse-glow">
              <div className="bg-zinc-900 rounded-2xl aspect-video flex items-center justify-center">
                <motion.button
                  className="w-20 h-20 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600 flex items-center justify-center shadow-2xl"
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <FiPlay className="w-8 h-8 text-white ml-1" />
                </motion.button>
              </div>
            </div>
            {/* Decorative elements */}
            <div className="absolute -top-4 -right-4 w-20 h-20 bg-blue-500/30 rounded-full blur-xl" />
            <div className="absolute -bottom-4 -left-4 w-32 h-32 bg-indigo-500/30 rounded-full blur-xl" />
          </motion.div>
        </div>
      </div>
    </section>
  );
}

export function FeaturesSection() {
  const features = [
    {
      icon: FiBookOpen,
      title: "Smart Content Parsing",
      description: "Upload PDFs, paste text, or provide URLs. Our AI extracts and structures educational content automatically.",
      gradient: "from-blue-500 to-cyan-500",
    },
    {
      icon: FiVideo,
      title: "Animated Video Generation",
      description: "Transform static content into engaging animated videos using Manim, the same technology used by 3Blue1Brown.",
      gradient: "from-indigo-500 to-purple-500",
    },
    {
      icon: FiZap,
      title: "AI-Powered Learning",
      description: "Automatic learning objectives, assessments, and difficulty adaptation powered by advanced AI models.",
      gradient: "from-pink-500 to-rose-500",
    },
    {
      icon: FiUsers,
      title: "Multi-Level Audiences",
      description: "Customize content for primary school, high school, or university students with a single click.",
      gradient: "from-orange-500 to-amber-500",
    },
  ];

  return (
    <section className="py-24 bg-zinc-50 dark:bg-zinc-950">
      <div className="container mx-auto px-6">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <h2 className="text-4xl font-bold text-zinc-900 dark:text-white mb-4" style={{ fontFamily: 'var(--font-playfair)' }}>
            Powerful Features
          </h2>
          <p className="text-lg text-zinc-600 dark:text-zinc-400 max-w-2xl mx-auto">
            Everything you need to create exceptional educational content
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              className="group"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <div className="h-full p-6 rounded-3xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 transition-all duration-300 hover:shadow-xl hover:-translate-y-1">
                <div className={`w-14 h-14 rounded-2xl bg-gradient-to-r ${feature.gradient} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-2">
                  {feature.title}
                </h3>
                <p className="text-zinc-600 dark:text-zinc-400 text-sm leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function TeamSection() {
  const team = [
    { name: "Aditya Nandan", role: "Lead Developer", avatar: "AN" },
    { name: "Manish Gupta", role: "AI Engineer", avatar: "MG" },
    { name: "Sparsh Singh", role: "Full Stack Developer", avatar: "SS" },
    { name: "Mohd. Shahnawaz Khan", role: "Backend Developer", avatar: "MK" },
  ];

  return (
    <section className="py-24 bg-white dark:bg-zinc-900">
      <div className="container mx-auto px-6">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <h2 className="text-4xl font-bold text-zinc-900 dark:text-white mb-4" style={{ fontFamily: 'var(--font-playfair)' }}>
            Meet the Team
          </h2>
          <p className="text-lg text-zinc-600 dark:text-zinc-400">
            The brilliant minds behind BLOOM
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 max-w-4xl mx-auto">
          {team.map((member, index) => (
            <motion.div
              key={index}
              className="text-center"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <motion.div
                className="w-24 h-24 mx-auto mb-4 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600 flex items-center justify-center text-2xl font-bold text-white shadow-lg"
                whileHover={{ scale: 1.1, rotate: 5 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                {member.avatar}
              </motion.div>
              <h3 className="text-lg font-semibold text-zinc-900 dark:text-white">
                {member.name}
              </h3>
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                {member.role}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="bg-zinc-900 text-white py-16">
      <div className="container mx-auto px-6">
        <div className="grid md:grid-cols-4 gap-12">
          <div className="md:col-span-2">
            <h3 className="text-2xl font-bold mb-4" style={{ fontFamily: 'var(--font-playfair)' }}>
              BLOOM
            </h3>
            <p className="text-zinc-400 mb-6 max-w-md">
              Transforming education through AI-powered content creation. 
              Making learning engaging, accessible, and effective for everyone.
            </p>
            <div className="flex gap-4">
              {["Twitter", "GitHub", "LinkedIn"].map((social) => (
                <a
                  key={social}
                  href="#"
                  className="px-4 py-2 rounded-full bg-zinc-800 text-sm hover:bg-zinc-700 transition-colors"
                >
                  {social}
                </a>
              ))}
            </div>
          </div>

          <div>
            <h4 className="font-semibold mb-4">Product</h4>
            <ul className="space-y-2">
              {["Features", "Pricing", "API", "Documentation"].map((item) => (
                <li key={item}>
                  <a href="#" className="text-zinc-400 hover:text-white transition-colors">
                    {item}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-4">Company</h4>
            <ul className="space-y-2">
              {["About", "Blog", "Careers", "Contact"].map((item) => (
                <li key={item}>
                  <a href="#" className="text-zinc-400 hover:text-white transition-colors">
                    {item}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="border-t border-zinc-800 mt-12 pt-8 text-center text-zinc-400 text-sm">
          © 2026 BLOOM. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
