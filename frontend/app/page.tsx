import { Navbar } from "@/components/landing/navbar";
import {
  HeroSection,
  DemoSection,
  FeaturesSection,
  TeamSection,
  Footer,
} from "@/components/landing/sections";

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        <HeroSection />
        <section id="demo">
          <DemoSection />
        </section>
        <section id="features">
          <FeaturesSection />
        </section>
        <section id="team">
          <TeamSection />
        </section>
      </main>
      <Footer />
    </>
  );
}
