import { GraduationCap, Award } from 'lucide-react';

export default function Education() {
  return (
    <section className="relative py-24 px-6">
      <div className="absolute inset-0 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950"></div>

      <div className="relative z-10 max-w-5xl mx-auto">
        <h2 className="text-5xl font-bold mb-16 text-center bg-gradient-to-r from-blue-400 to-teal-400 bg-clip-text text-transparent">
          Education & Certifications
        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-sm rounded-2xl p-8 border border-blue-500/20 hover:border-blue-500/40 transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-blue-500/20">
            <div className="flex items-start gap-4 mb-6">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-teal-500/20 flex items-center justify-center flex-shrink-0">
                <GraduationCap className="w-8 h-8 text-blue-400" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-white mb-2">B.Tech in Computer Science</h3>
                <p className="text-lg text-blue-400 font-semibold mb-1">AI & Machine Learning</p>
                <p className="text-gray-400">SRM Institute of Science and Technology</p>
                <p className="text-gray-400">Chennai, India</p>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-sm rounded-2xl p-8 border border-blue-500/20 hover:border-blue-500/40 transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-blue-500/20">
            <div className="flex items-start gap-4 mb-6">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-teal-500/20 to-cyan-500/20 flex items-center justify-center flex-shrink-0">
                <Award className="w-8 h-8 text-teal-400" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-white mb-4">Certifications</h3>
              </div>
            </div>
            <div className="space-y-4 mt-6">
              <div className="p-4 bg-slate-800/30 rounded-xl border border-slate-700/50 hover:border-teal-500/50 transition-all duration-200">
                <p className="text-white font-semibold mb-1">TensorFlow Developer</p>
                <p className="text-gray-400 text-sm">Google</p>
              </div>
              <div className="p-4 bg-slate-800/30 rounded-xl border border-slate-700/50 hover:border-teal-500/50 transition-all duration-200">
                <p className="text-white font-semibold mb-1">Data Analysis Using Python</p>
                <p className="text-gray-400 text-sm">IBM</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
