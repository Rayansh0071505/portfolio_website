import { Brain, Code, Database, Zap } from 'lucide-react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ChatBubbleLeftRightIcon } from '@heroicons/react/24/solid';

export default function About() {
  const highlights = [
    { icon: Brain, text: "Expert in LLMs & Generative AI" },
    { icon: Code, text: "Production AI Systems" },
    { icon: Database, text: "Data Pipelines & Architecture" },
    { icon: Zap, text: "Automation & Orchestration" }
  ];

  return (
    <section className="relative py-24 px-6">
      <div className="absolute inset-0 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950"></div>

      <div className="relative z-10 max-w-6xl mx-auto">
        <h2 className="text-5xl font-bold mb-16 text-center bg-gradient-to-r from-blue-400 to-teal-400 bg-clip-text text-transparent">
          About Me
        </h2>

        <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm rounded-3xl p-8 md:p-12 border border-blue-500/20 shadow-2xl hover:shadow-blue-500/20 transition-all duration-500">
          <p className="text-xl text-gray-300 leading-relaxed mb-8">
            Solution Engineer / AI Engineer with strong experience building <span className="text-blue-400 font-semibold">production AI systems</span> for real businesses. Skilled at translating business problems into scalable AI solutions. Expert in <span className="text-teal-400 font-semibold">LLMs, automation, data pipelines, and AI architecture</span>, with proven experience working with product, operations, and leadership teams to deliver impact-driven systems.
          </p>

          <p className="text-lg text-gray-300 leading-relaxed">
            I have hands-on experience with <span className="text-purple-400 font-semibold">reinforcement learning techniques for LLM alignment</span>, including fine-tuning methods (LoRA), preference optimization (DPO), and reward-based RL (GRPO). This includes designing reward functions, hyperparameter tuning for RL training, and working with the complete pipeline from data preparation through model merging. I've also experimented with OpenAI Gym environments for classic RL problems and integrated human-in-the-loop feedback in production systems like orchestration in Peak OS and financial personal AI platforms.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-12">
            {highlights.map((item, index) => (
              <div
                key={index}
                className="flex flex-col items-center text-center p-6 bg-slate-800/30 rounded-2xl border border-slate-700/50 hover:border-blue-500/50 transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-blue-500/20"
              >
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500/20 to-teal-500/20 flex items-center justify-center mb-4">
                  <item.icon className="w-8 h-8 text-blue-400" />
                </div>
                <p className="text-gray-300 font-medium">{item.text}</p>
              </div>
            ))}
          </div>

          {/* AI Chat CTA */}
          <div className="mt-12 text-center">
            <p className="text-slate-400 mb-4">Want to know more about my experience?</p>
            <Link to="/chat">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-blue-600 to-blue-500 text-white font-semibold rounded-xl shadow-xl shadow-blue-500/30 hover:shadow-blue-500/50 transition-all"
              >
                <ChatBubbleLeftRightIcon className="w-5 h-5" />
                <span>Ask My AI Anything</span>
              </motion.button>
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
