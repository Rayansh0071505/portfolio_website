/**
 * Floating Chat Bubble - Always visible on bottom right
 */
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChatBubbleLeftRightIcon, XMarkIcon, SparklesIcon } from '@heroicons/react/24/solid';
import ChatInterface from './ChatInterface';

export default function ChatBubble() {
  const [isOpen, setIsOpen] = useState(false);
  const [hasNewMessage, setHasNewMessage] = useState(false);

  return (
    <>
      {/* Expanded Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="fixed bottom-24 right-6 z-50 w-[400px] h-[600px] bg-slate-900 rounded-2xl shadow-2xl border border-slate-700 overflow-hidden"
          >
            {/* Header */}
            <div className="absolute top-0 left-0 right-0 bg-gradient-to-r from-blue-600 to-teal-500 p-4 flex items-center justify-between z-10">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <img
                    src="/edit.jpg"
                    alt="Rayansh"
                    className="w-12 h-12 rounded-full border-2 border-white object-cover"
                  />
                  <div className="absolute bottom-0 right-0 w-3.5 h-3.5 bg-green-400 border-2 border-white rounded-full"></div>
                </div>
                <div>
                  <h3 className="text-white font-semibold">Rayansh AI</h3>
                  <p className="text-blue-100 text-xs flex items-center gap-1">
                    <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                    Online • AI Assistant
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="text-white hover:bg-white/20 rounded-lg p-2 transition-colors"
              >
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>

            {/* Chat Interface */}
            <div className="h-full pt-20">
              <ChatInterface mode="bubble" />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating Chat Button */}
      <motion.button
        onClick={() => {
          setIsOpen(!isOpen);
          setHasNewMessage(false);
        }}
        className="fixed bottom-6 right-6 z-40"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <div className="relative">
          {/* Pulse animation when closed */}
          {!isOpen && (
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-blue-500 to-teal-500 rounded-full"
              animate={{
                scale: [1, 1.2, 1],
                opacity: [0.5, 0.2, 0.5],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />
          )}

          {/* Main button */}
          <div className="relative w-16 h-16 bg-gradient-to-r from-blue-600 to-teal-500 rounded-full shadow-2xl flex items-center justify-center">
            <AnimatePresence mode="wait">
              {isOpen ? (
                <motion.div
                  key="close"
                  initial={{ rotate: -90, opacity: 0 }}
                  animate={{ rotate: 0, opacity: 1 }}
                  exit={{ rotate: 90, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <XMarkIcon className="w-7 h-7 text-white" />
                </motion.div>
              ) : (
                <motion.div
                  key="chat"
                  initial={{ rotate: -90, opacity: 0 }}
                  animate={{ rotate: 0, opacity: 1 }}
                  exit={{ rotate: 90, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <ChatBubbleLeftRightIcon className="w-7 h-7 text-white" />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* New message indicator */}
          {hasNewMessage && !isOpen && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="absolute -top-1 -right-1 w-6 h-6 bg-red-500 rounded-full border-2 border-white flex items-center justify-center"
            >
              <SparklesIcon className="w-3.5 h-3.5 text-white" />
            </motion.div>
          )}
        </div>
      </motion.button>
    </>
  );
}
