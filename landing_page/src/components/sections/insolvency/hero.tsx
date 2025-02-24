"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { WavyBackground } from "@/components/ui/wavy-background";

const ease = [0.16, 1, 0.3, 1];

function HeroPill() {
  return (
    <motion.div
      className="flex w-auto items-center space-x-2 rounded-full bg-primary/20 px-2 py-1 ring-1 ring-accent whitespace-pre"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, ease }}
    >
      <div className="w-fit rounded-full bg-accent px-2 py-0.5 text-center text-xs font-medium text-primary sm:text-sm">
        🔍 Insolvency Solutions
      </div>
      <p className="text-xs font-medium text-primary sm:text-sm">
        SIP 2.0 Compliant
      </p>
    </motion.div>
  );
}

function HeroTitles() {
  return (
    <div className="flex w-full max-w-2xl flex-col space-y-4 overflow-hidden pt-8">
      <motion.h1
        className="text-center text-4xl font-medium leading-tight text-foreground sm:text-5xl md:text-6xl"
        initial={{ filter: "blur(10px)", opacity: 0, y: 50 }}
        animate={{ filter: "blur(0px)", opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.1, ease }}
      >
        Streamline Insolvency Processes with Day-One Bank Data
      </motion.h1>
      <motion.p
        className="text-center text-lg text-muted-foreground md:text-xl"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.2, ease }}
      >
        Accelerate investigations, ensure SIP 2.0 compliance, and gain immediate access to financial data for insolvency practitioners and restructuring professionals.
      </motion.p>
    </div>
  );
}

function HeroCTA() {
  return (
    <motion.div
      className="flex flex-col items-center justify-center space-y-4 pt-8 sm:flex-row sm:space-x-4 sm:space-y-0"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, delay: 0.3, ease }}
    >
      <Link
        href="#waitlist"
        className={cn(
          buttonVariants({
            size: "lg",
          }),
          "rounded-full bg-primary px-8 text-primary-foreground"
        )}
      >
        Get Started
      </Link>
      <Link
        href="#features"
        className={cn(
          buttonVariants({
            variant: "outline",
            size: "lg",
          }),
          "rounded-full px-8"
        )}
      >
        Learn More
      </Link>
    </motion.div>
  );
}

export default function InsolvencyHero() {
  return (
    <WavyBackground className="relative flex min-h-[calc(100vh-4rem)] w-full flex-col items-center justify-center overflow-hidden px-4 py-24">
      <div className="z-10 flex w-full max-w-7xl flex-col items-center justify-center space-y-8">
        <HeroPill />
        <HeroTitles />
        <HeroCTA />
      </div>
    </WavyBackground>
  );
} 