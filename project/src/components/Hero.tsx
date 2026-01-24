import { motion } from 'framer-motion';
import { ChevronDown } from 'lucide-react';
import { Link } from 'react-router-dom';
import { SparklesIcon } from '@heroicons/react/24/solid';
import { GradientMesh } from './hero/GradientMesh';
import { ParticleBackground } from './hero/ParticleBackground';
import { AnimatedProfileImage } from './hero/AnimatedProfileImage';
import { TypewriterText } from './hero/TypewriterText';
import { MagneticButton } from './ui/MagneticButton';
import { heroText } from '../utils/animations';

/**
 * Hero Section
 * Ultra-modern hero with animated profile image, particles, gradient mesh,
 * typewriter effect, and magnetic buttons
 */
export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Gradient Mesh Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-blue-950/50 to-teal-950/50">
        <GradientMesh />
      </div>

      {/* Particle Background */}
      <ParticleBackground />

      {/* Grid Pattern Overlay */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZGVmcz48cGF0dGVybiBpZD0iZ3JpZCIgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIj48cGF0aCBkPSJNIDQwIDAgTCAwIDAgMCA0MCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJyZ2JhKDI1NSwgMjU1LCAyNTUsIDAuMDUpIiBzdHJva2Utd2lkdGg9IjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')] opacity-10" />

      {/* Main Content */}
      <div className="relative z-10 text-center px-6 max-w-6xl mx-auto py-20">
        <div className="space-y-8">
          {/* Animated Profile Image */}
          <div className="mb-12">
            <AnimatedProfileImage />
          </div>

          {/* Name with Typewriter Effect */}
          <motion.div
            variants={heroText}
            initial="hidden"
            animate="visible"
            className="mb-6"
          >
            <h1 className="text-5xl md:text-7xl lg:text-8xl font-display font-bold mb-2">
              <span className="bg-gradient-to-r from-blue-400 via-teal-400 to-cyan-400 bg-clip-text text-transparent animate-gradient">
                Rayansh Srivastava
              </span>
            </h1>
          </motion.div>

          {/* Title with Typewriter */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.8 }}
            className="mb-6"
          >
            <div className="text-2xl md:text-4xl lg:text-5xl mb-4">
              <TypewriterText
                words={[
                  'AI Solution Engineer',
                  'ML Architect',
                  'Data Scientist',
                  'Problem Solver',
                ]}
              />
            </div>
          </motion.div>

          {/* Subtitle */}
          <motion.p
            className="text-lg md:text-xl text-slate-300 mb-12 max-w-3xl mx-auto leading-relaxed"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.8 }}
          >
            Building production AI systems that transform business problems into
            scalable, intelligent solutions
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            className="flex flex-wrap gap-6 justify-center"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9, duration: 0.8 }}
          >
            {/* Chat with AI Button - PRIMARY CTA */}
            <Link to="/chat">
              <MagneticButton variant="primary" strength={0.4}>
                <div className="flex items-center gap-2">
                  <SparklesIcon className="w-5 h-5" />
                  <span>Chat with Rayansh AI</span>
                </div>
              </MagneticButton>
            </Link>

            <MagneticButton
              href="mailto:rayanshsrivastava.ai@gmail.com"
              variant="primary"
              strength={0.4}
            >
              Get In Touch
            </MagneticButton>
            <MagneticButton
              href="#experience"
              variant="primary"
              strength={0.3}
            >
              View My Work
            </MagneticButton>
          </motion.div>
        </div>

        {/* Scroll Indicator */}
        <motion.div
          className="absolute bottom-10 left-1/2 transform -translate-x-1/2"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.2, duration: 0.8 }}
        >
          <motion.div
            animate={{ y: [0, 10, 0] }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          >
            <ChevronDown className="w-8 h-8 text-slate-400" />
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
