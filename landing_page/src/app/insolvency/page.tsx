import Blog from "@/components/sections/blog";
import FAQ from "@/components/sections/faq";
import Features from "@/components/sections/features";
import Footer from "@/components/sections/footer";
import Header from "@/components/sections/header";
import InsolvencyHero from "@/components/sections/insolvency/hero";
import InsolvencyBenefits from "@/components/sections/insolvency/benefits";
import InsolvencySIP from "@/components/sections/insolvency/sip";
import InsolvencyDataAccess from "@/components/sections/insolvency/data-access";
import InsolvencyAnalysis from "@/components/sections/insolvency/analysis";
import Logos from "@/components/sections/logos";
import WaitlistSection from "@/components/sections/waitlist";

export const metadata = {
  title: "BankStream.io | Insolvency & Restructuring Solutions",
  description: "Streamline insolvency processes with day-one bank data access, SIP 2.0 compliance, and automated financial analysis for insolvency practitioners.",
};

export default function InsolvencyPage() {
  return (
    <main>
      <Header />
      <InsolvencyHero />
      <Logos />
      <InsolvencySIP />
      <InsolvencyDataAccess />
      <InsolvencyBenefits />
      <InsolvencyAnalysis />
      <Features />
      <FAQ />
      <WaitlistSection />
      <Footer />
    </main>
  );
} 