/**
 * Full Page Chat Component - WhatsApp-style layout
 */
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeftIcon } from '@heroicons/react/24/solid';
import ChatInterface from './chat/ChatInterface';

export default function ChatWithAI() {
  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      {/* Header */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="bg-gradient-to-r from-blue-600 to-teal-500 px-6 py-4 flex items-center justify-between shadow-xl"
      >
        <div className="flex items-center gap-4">
          <Link to="/">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            >
              <ArrowLeftIcon className="w-6 h-6 text-white" />
            </motion.button>
          </Link>

          <div className="flex items-center gap-3">
            <div className="relative">
              <motion.img
                whileHover={{ scale: 1.05 }}
                src="/edit.jpg"
                alt="Rayansh Srivastava"
                className="w-14 h-14 rounded-full border-3 border-white object-cover shadow-lg"
              />
              <div className="absolute bottom-0 right-0 w-4 h-4 bg-green-400 border-2 border-white rounded-full"></div>
            </div>

            <div>
              <h1 className="text-white font-bold text-xl">
                Rayansh's AI Assistant
              </h1>
              <p className="text-blue-100 text-sm flex items-center gap-2">
                <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                Online
              </p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Chat Interface */}
      <div className="flex-1 max-w-6xl w-full mx-auto">
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="h-[calc(100vh-120px)] bg-slate-900/30 border-x border-slate-800"
        >
          <ChatInterface mode="full" />
        </motion.div>
      </div>

      {/* Footer */}
      <div className="bg-slate-900 border-t border-slate-800 px-6 py-3">
        <div className="max-w-6xl mx-auto flex items-center justify-center text-sm text-slate-500">
          <p className="text-slate-600">
            © 2026 Rayansh Srivastava • AI-Powered Portfolio
          </p>
        </div>
      </div>
    </div>
  );
}
