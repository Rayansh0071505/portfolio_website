import { useEffect } from 'react';
import Hero from './components/Hero';
import About from './components/About';
import Experience from './components/Experience';
import Skills from './components/Skills';
import Education from './components/Education';
import Contact from './components/Contact';
import { CustomCursor } from './components/effects/CustomCursor';
import { ScrollProgress } from './components/effects/ScrollProgress';
import { NoiseTexture } from './components/effects/NoiseTexture';
import { useSmoothScroll } from './hooks/useSmoothScroll';

function App() {
  // Initialize smooth scrolling
  useSmoothScroll();

  // Add lenis class to html element
  useEffect(() => {
    document.documentElement.classList.add('lenis');
    return () => {
      document.documentElement.classList.remove('lenis');
    };
  }, []);

  return (
    <>
      {/* Global Effects */}
      <CustomCursor />
      <ScrollProgress />
      <NoiseTexture />

      {/* Main Content */}
      <div className="bg-slate-950 min-h-screen">
        <Hero />
        <About />
        <Experience />
        <Skills />
        <Education />
        <Contact />
      </div>
    </>
  );
}

export default App;
