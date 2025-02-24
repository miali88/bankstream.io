"use client";

import Section from "@/components/section";
import { motion } from "framer-motion";
import { ArrowRight, BarChart3, Clock, CreditCard, Search, Shield } from "lucide-react";
import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function InsolvencyBenefits() {
  return (
    <Section id="benefits" className="py-20">
      <div className="container mx-auto px-4">
        <motion.div 
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="text-3xl font-bold leading-tight md:text-4xl mb-4">
            Benefits for Insolvency Practitioners
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            BankStream.io provides insolvency practitioners with powerful tools to streamline investigations,
            ensure compliance, and maximize recoveries.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <BenefitCard 
            icon={<Search className="h-8 w-8" />}
            title="Determine How Directors Spent Funds"
            description="Quickly identify and track director withdrawals, loans, and other transactions to assess conduct and identify potential misconduct."
            delay={0.1}
          />
          <BenefitCard 
            icon={<BarChart3 className="h-8 w-8" />}
            title="Pre-Prepared Analysis"
            description="Receive automated analysis of financial data, including cash flow, transaction patterns, and potential issues requiring investigation."
            delay={0.2}
          />
          <BenefitCard 
            icon={<CreditCard className="h-8 w-8" />}
            title="Identify Preferences & Transactions at Undervalue"
            description="Automatically flag potential preference payments and transactions at undervalue to support antecedent transaction claims."
            delay={0.3}
          />
          <BenefitCard 
            icon={<Clock className="h-8 w-8" />}
            title="Reduce Investigation Time"
            description="Cut investigation time by up to 80% with immediate access to banking data and automated analysis tools."
            delay={0.4}
          />
          <BenefitCard 
            icon={<Shield className="h-8 w-8" />}
            title="Ensure Regulatory Compliance"
            description="Meet all regulatory requirements, including SIP 2.0, with comprehensive documentation and audit trails."
            delay={0.5}
          />
          <motion.div 
            className="flex flex-col p-6 bg-primary/10 rounded-lg border border-primary/20 shadow-sm"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.6 }}
          >
            <div className="flex-1">
              <h3 className="text-xl font-semibold mb-4">Ready to Transform Your Insolvency Practice?</h3>
              <p className="text-muted-foreground mb-6">
                Join leading insolvency practitioners who are already using BankStream.io to streamline their investigations and improve outcomes.
              </p>
            </div>
            <Link
              href="#waitlist"
              className={cn(
                buttonVariants({
                  size: "lg",
                }),
                "rounded-full bg-primary px-8 text-primary-foreground w-full justify-between group"
              )}
            >
              <span>Get Started Today</span>
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Link>
          </motion.div>
        </div>
      </div>
    </Section>
  );
}

function BenefitCard({ 
  icon, 
  title, 
  description, 
  delay 
}: { 
  icon: React.ReactNode; 
  title: string; 
  description: string;
  delay: number;
}) {
  return (
    <motion.div 
      className="flex flex-col p-6 bg-background rounded-lg border shadow-sm h-full"
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay }}
    >
      <div className="mb-4 p-3 rounded-full bg-primary/10 w-fit">
        <div className="text-primary">{icon}</div>
      </div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-muted-foreground">{description}</p>
    </motion.div>
  );
} 