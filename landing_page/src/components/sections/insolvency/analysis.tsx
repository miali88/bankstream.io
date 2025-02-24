"use client";

import Section from "@/components/section";
import { motion } from "framer-motion";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BarChart, LineChart, PieChart } from "lucide-react";

export default function InsolvencyAnalysis() {
  return (
    <Section id="analysis" className="py-20 bg-muted/50">
      <div className="container mx-auto px-4">
        <motion.div 
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="text-3xl font-bold leading-tight md:text-4xl mb-4">
            Pre-Prepared Financial Analysis
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Get instant insights with automated financial analysis, helping you identify patterns, 
            anomalies, and potential issues requiring investigation.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <Tabs defaultValue="cash-flow" className="w-full">
            <TabsList className="grid w-full grid-cols-3 mb-8">
              <TabsTrigger value="cash-flow" className="flex items-center gap-2">
                <LineChart className="h-4 w-4" />
                <span>Cash Flow Analysis</span>
              </TabsTrigger>
              <TabsTrigger value="transaction" className="flex items-center gap-2">
                <BarChart className="h-4 w-4" />
                <span>Transaction Analysis</span>
              </TabsTrigger>
              <TabsTrigger value="creditor" className="flex items-center gap-2">
                <PieChart className="h-4 w-4" />
                <span>Creditor Analysis</span>
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="cash-flow" className="mt-0">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="p-6 bg-background rounded-lg border shadow-sm">
                  <h3 className="text-xl font-semibold mb-4">Cash Flow Insights</h3>
                  <p className="text-muted-foreground mb-6">
                    Automatically analyze cash flow patterns to identify when the company became cash flow insolvent, 
                    supporting your investigations and reports.
                  </p>
                  <div className="space-y-4">
                    <AnalysisFeature 
                      title="Cash Flow Insolvency Timeline" 
                      description="Identify the exact point when the company became cash flow insolvent."
                    />
                    <AnalysisFeature 
                      title="Working Capital Analysis" 
                      description="Track changes in working capital over time to identify financial distress signals."
                    />
                    <AnalysisFeature 
                      title="Seasonal Patterns" 
                      description="Identify seasonal patterns in cash flow to understand business cycles and potential pressure points."
                    />
                  </div>
                </div>
                <div className="relative h-[400px] w-full overflow-hidden rounded-lg border bg-background shadow-xl">
                  <div className="absolute inset-0 bg-gradient-to-br from-primary/30 to-background/10 p-8">
                    <div className="space-y-4">
                      <h3 className="text-xl font-semibold">Cash Flow Dashboard</h3>
                      <div className="h-[300px] bg-background/80 rounded-md p-4 flex items-center justify-center">
                        <div className="text-center text-muted-foreground">
                          [Interactive Cash Flow Visualization]
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>
            
            <TabsContent value="transaction" className="mt-0">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="p-6 bg-background rounded-lg border shadow-sm">
                  <h3 className="text-xl font-semibold mb-4">Transaction Pattern Analysis</h3>
                  <p className="text-muted-foreground mb-6">
                    Automatically identify unusual transaction patterns, potential preferences, and transactions at undervalue.
                  </p>
                  <div className="space-y-4">
                    <AnalysisFeature 
                      title="Preference Payment Detection" 
                      description="Automatically flag potential preference payments to specific creditors."
                    />
                    <AnalysisFeature 
                      title="Director Transaction Analysis" 
                      description="Track and analyze all transactions involving company directors."
                    />
                    <AnalysisFeature 
                      title="Unusual Transaction Patterns" 
                      description="Identify transactions that deviate from normal business patterns."
                    />
                  </div>
                </div>
                <div className="relative h-[400px] w-full overflow-hidden rounded-lg border bg-background shadow-xl">
                  <div className="absolute inset-0 bg-gradient-to-br from-primary/30 to-background/10 p-8">
                    <div className="space-y-4">
                      <h3 className="text-xl font-semibold">Transaction Analysis Dashboard</h3>
                      <div className="h-[300px] bg-background/80 rounded-md p-4 flex items-center justify-center">
                        <div className="text-center text-muted-foreground">
                          [Interactive Transaction Analysis Visualization]
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>
            
            <TabsContent value="creditor" className="mt-0">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="p-6 bg-background rounded-lg border shadow-sm">
                  <h3 className="text-xl font-semibold mb-4">Creditor Analysis</h3>
                  <p className="text-muted-foreground mb-6">
                    Automatically categorize and analyze creditor payments to identify potential preferential treatment.
                  </p>
                  <div className="space-y-4">
                    <AnalysisFeature 
                      title="Creditor Payment Patterns" 
                      description="Analyze payment patterns to different creditors to identify preferential treatment."
                    />
                    <AnalysisFeature 
                      title="Connected Party Analysis" 
                      description="Identify and analyze payments to connected parties and related entities."
                    />
                    <AnalysisFeature 
                      title="Creditor Pressure Indicators" 
                      description="Identify signs of creditor pressure, such as irregular payment patterns or partial payments."
                    />
                  </div>
                </div>
                <div className="relative h-[400px] w-full overflow-hidden rounded-lg border bg-background shadow-xl">
                  <div className="absolute inset-0 bg-gradient-to-br from-primary/30 to-background/10 p-8">
                    <div className="space-y-4">
                      <h3 className="text-xl font-semibold">Creditor Analysis Dashboard</h3>
                      <div className="h-[300px] bg-background/80 rounded-md p-4 flex items-center justify-center">
                        <div className="text-center text-muted-foreground">
                          [Interactive Creditor Analysis Visualization]
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </motion.div>
      </div>
    </Section>
  );
}

function AnalysisFeature({ title, description }: { title: string; description: string }) {
  return (
    <div className="border-l-2 border-primary pl-4">
      <h4 className="font-medium">{title}</h4>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  );
} 