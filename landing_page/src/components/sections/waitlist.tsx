"use client";

import { BackgroundBeams } from "@/components/ui/background-beams";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import Link from "next/link";

export default function WaitlistSection() {
  return (
    <section className="h-[80vh] w-full relative flex flex-col items-center justify-center overflow-hidden bg-white">
      <BackgroundBeams className="opacity-70" />
      <div className="relative z-10 flex flex-col items-center px-5">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="relative"
        >
          <h1 className="text-center text-6xl md:text-7xl lg:text-8xl font-bold">
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-purple-600 to-purple-400">
              Join the waitlist
            </span>
          </h1>
          <div className="absolute -top-8 right-0 text-purple-600/20 text-9xl font-bold select-none">
            ✦
          </div>
          <div className="absolute -bottom-8 left-0 text-purple-600/20 text-9xl font-bold rotate-12 select-none">
            ✦
          </div>
        </motion.div>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="text-center text-lg md:text-xl text-neutral-800 max-w-2xl mb-12 mt-8"
        >
          Be the first to experience our revolutionary AI-powered bank
          reconciliation platform. Sign up now to get early access.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="relative"
        >
          <div className="absolute -inset-1 bg-gradient-to-r from-purple-600 to-purple-400 rounded-lg blur opacity-30 group-hover:opacity-40 transition duration-1000"></div>
          <Link
            href="/signup"
            className={cn(
              buttonVariants({ variant: "default" }),
              "relative bg-white text-purple-600 hover:text-purple-700 hover:bg-white/80 px-8 py-6 text-lg font-semibold border-2 border-purple-400"
            )}
          >
            Get Early Access →
          </Link>
        </motion.div>
      </div>
    </section>
  );
}
