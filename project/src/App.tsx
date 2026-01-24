import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Hero from './components/Hero';
import About from './components/About';
import Experience from './components/Experience';
import Skills from './components/Skills';
import Education from './components/Education';
import Contact from './components/Contact';
import ChatWithAI from './components/ChatWithAI';
import ChatBubble from './components/chat/ChatBubble';
import { CustomCursor } from './components/effects/CustomCursor';
import { ScrollProgress } from './components/effects/ScrollProgress';
import { NoiseTexture } from './components/effects/NoiseTexture';
import { useSmoothScroll } from './hooks/useSmoothScroll';

function HomePage() {
  return (
    <div className="bg-slate-950 min-h-screen">
      <Hero />
      <About />
      <Experience />
      <Skills />
      <Education />
      <Contact />
    </div>
  );
}

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
    <Router>
      {/* Global Effects */}
      <CustomCursor />
      <ScrollProgress />
      <NoiseTexture />

      {/* Routes */}
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/chat" element={<ChatWithAI />} />
      </Routes>

      {/* Floating Chat Bubble - Always visible */}
      <ChatBubble />
    </Router>
  );
}

export default App;
