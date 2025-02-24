"use client";

import Section from "@/components/section";
import { motion } from "framer-motion";
import { CheckCircle2 } from "lucide-react";
import Image from "next/image";

export default function InsolvencySIP() {
  return (
    <Section id="sip" className="py-20">
      <div className="container mx-auto px-4">
        <div className="flex flex-col items-center justify-between gap-12 lg:flex-row">
          <motion.div 
            className="w-full lg:w-1/2"
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="mb-6 text-3xl font-bold leading-tight md:text-4xl">
              SIP 2.0 Compliant Investigations
            </h2>
            <p className="mb-8 text-lg text-muted-foreground">
              BankStream.io helps insolvency practitioners meet Statement of Insolvency Practice (SIP) 2.0 requirements by providing immediate access to comprehensive banking data and automated analysis tools.
            </p>
            
            <div className="space-y-4">
              <SIPFeature 
                title="Comprehensive Transaction Review" 
                description="Automatically analyze all transactions to identify potential preferences, transactions at undervalue, and other matters requiring investigation."
              />
              <SIPFeature 
                title="Director Conduct Analysis" 
                description="Easily track director withdrawals, loans, and other transactions to assess conduct and identify potential misconduct."
              />
              <SIPFeature 
                title="Audit Trail & Documentation" 
                description="Generate detailed reports and maintain comprehensive audit trails to support your SIP 2.0 compliance requirements."
              />
              <SIPFeature 
                title="Early Warning Indicators" 
                description="Identify patterns of financial distress and potential insolvency indicators to support your investigations."
              />
            </div>
          </motion.div>
          
          <motion.div 
            className="relative w-full lg:w-1/2"
            initial={{ opacity: 0, x: 50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <div className="relative h-[400px] w-full overflow-hidden rounded-lg border bg-background shadow-xl">
              <div className="absolute inset-0 bg-gradient-to-br from-primary/30 to-background/10 p-8">
                <div className="space-y-4">
                  <h3 className="text-xl font-semibold">SIP 2.0 Investigation Dashboard</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="rounded-md bg-background/80 p-4 shadow-sm">
                      <p className="text-sm font-medium">Transactions Analyzed</p>
                      <p className="text-2xl font-bold">2,547</p>
                    </div>
                    <div className="rounded-md bg-background/80 p-4 shadow-sm">
                      <p className="text-sm font-medium">Flagged Transactions</p>
                      <p className="text-2xl font-bold">37</p>
                    </div>
                    <div className="rounded-md bg-background/80 p-4 shadow-sm">
                      <p className="text-sm font-medium">Director Withdrawals</p>
                      <p className="text-2xl font-bold">£42,850</p>
                    </div>
                    <div className="rounded-md bg-background/80 p-4 shadow-sm">
                      <p className="text-sm font-medium">Compliance Score</p>
                      <p className="text-2xl font-bold">98%</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </Section>
  );
}

function SIPFeature({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex items-start gap-3">
      <CheckCircle2 className="mt-1 h-5 w-5 flex-shrink-0 text-primary" />
      <div>
        <h3 className="font-medium">{title}</h3>
        <p className="text-muted-foreground">{description}</p>
      </div>
    </div>
  );
} 