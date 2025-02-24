"use client";

import Section from "@/components/section";
import { motion } from "framer-motion";
import { Clock, Database, Lock, RefreshCw } from "lucide-react";

export default function InsolvencyDataAccess() {
  return (
    <Section id="data-access" className="py-20 bg-muted/50">
      <div className="container mx-auto px-4">
        <motion.div 
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="text-3xl font-bold leading-tight md:text-4xl mb-4">
            Day-One Bank Data Access
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Eliminate delays in financial investigations with immediate access to banking data, 
            allowing you to start your insolvency work from day one.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          <DataAccessFeature 
            icon={<Clock className="h-10 w-10 text-primary" />}
            title="Immediate Access"
            description="Get access to banking data immediately upon appointment, without waiting for bank mandates or manual processes."
            delay={0.1}
          />
          <DataAccessFeature 
            icon={<Database className="h-10 w-10 text-primary" />}
            title="Complete History"
            description="Access up to 7 years of historical transaction data across multiple bank accounts and financial institutions."
            delay={0.2}
          />
          <DataAccessFeature 
            icon={<RefreshCw className="h-10 w-10 text-primary" />}
            title="Real-Time Updates"
            description="Receive ongoing updates to banking data throughout the insolvency process, ensuring you always have the latest information."
            delay={0.3}
          />
          <DataAccessFeature 
            icon={<Lock className="h-10 w-10 text-primary" />}
            title="Secure & Compliant"
            description="Bank-level security and compliance with all relevant regulations, including GDPR and financial services requirements."
            delay={0.4}
          />
        </div>

        <motion.div 
          className="mt-16 p-6 bg-background rounded-lg border shadow-sm"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.5 }}
        >
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div>
              <h3 className="text-xl font-semibold mb-2">Typical Timeline Comparison</h3>
              <p className="text-muted-foreground">
                See how BankStream.io dramatically reduces the time to access critical financial data.
              </p>
            </div>
            <div className="w-full md:w-2/3">
              <div className="space-y-4">
                <TimelineComparison 
                  title="Traditional Process" 
                  days="14-28 days"
                  steps={["Bank mandate setup", "Manual data requests", "Wait for processing", "Data formatting"]}
                  isTraditional={true}
                />
                <TimelineComparison 
                  title="With BankStream.io" 
                  days="Same day"
                  steps={["Secure authorization", "Automated data retrieval", "Instant formatting", "Immediate analysis"]}
                  isTraditional={false}
                />
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </Section>
  );
}

function DataAccessFeature({ 
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
      className="flex flex-col items-center text-center p-6 bg-background rounded-lg border shadow-sm"
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay }}
    >
      <div className="mb-4 p-3 rounded-full bg-primary/10">{icon}</div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-muted-foreground">{description}</p>
    </motion.div>
  );
}

function TimelineComparison({ 
  title, 
  days, 
  steps, 
  isTraditional 
}: { 
  title: string; 
  days: string; 
  steps: string[];
  isTraditional: boolean;
}) {
  return (
    <div className={`p-4 rounded-lg ${isTraditional ? 'bg-destructive/10' : 'bg-primary/10'}`}>
      <div className="flex justify-between items-center mb-3">
        <h4 className="font-medium">{title}</h4>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
          isTraditional ? 'bg-destructive/20 text-destructive' : 'bg-primary/20 text-primary'
        }`}>
          {days}
        </span>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {steps.map((step, index) => (
          <div key={index} className="text-xs text-muted-foreground">
            {index + 1}. {step}
          </div>
        ))}
      </div>
    </div>
  );
} 