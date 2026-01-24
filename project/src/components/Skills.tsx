import { motion } from 'framer-motion';
import { TiltCard } from './ui/TiltCard';
import { StaggerContainer, StaggerItem } from './animations/StaggerContainer';
import { FadeInView } from './animations/FadeInView';

export default function Skills() {
  const skillCategories = [
    {
      category: "Machine Learning",
      skills: ["Deep Learning", "NLP", "Computer Vision", "Time Series Analysis", "LLMs", "Generative AI", "Statistical Machine Learning", "GANs"]
    },
    {
      category: "Languages",
      skills: ["C++", "Python"]
    },
    {
      category: "Databases",
      skills: ["MongoDB", "Big Query", "SQL"]
    },
    {
      category: "Solution Engineering",
      skills: ["Business Problem Mapping", "AI Solution Design", "System Architecture", "Stakeholder Alignment", "Technical Consulting", "Product Strategy", "Workflow Design", "AI Transformation"]
    },
    {
      category: "ML-OPS",
      skills: ["AWS (Cloud & Serverless)", "CI/CD", "Docker", "Render Cloud", "Grafana", "GitHub Actions", "GCP", "Azure", "MLFlow", "EC2", "ECS", "Lambda", "Airflow", "DVC", "Ray", "vllm"]
    },
    {
      category: "Automation",
      skills: ["Workflow Automation", "Multi-Agent Systems", "Process Automation", "AI Orchestration"]
    },
    {
      category: "Generative AI Tools",
      skills: ["OpenAI GPT Models", "AWS Bedrock", "Azure OpenAI", "Vertex AI (Gemini)", "Hugging Face Transformers", "Open-Source LLMs (LLaMA, Mistral, Falcon)", "LangChain", "LangGraph", "LlamaIndex", "RAG Pipelines", "Pinecone", "FAISS"]
    },
    {
      category: "Frameworks, Hosting & Libraries",
      skills: ["TensorFlow", "OpenCV", "Scikit-learn", "FastAPI", "Streamlit", "Pytorch"]
    },
    {
      category: "Product Management",
      skills: ["Shortcut", "Linear", "Trello"]
    },
    {
      category: "Product & Delivery",
      skills: ["Agile", "System Design", "Documentation", "Client Demos", "Cross-Team Collaboration", "Architecture Diagrams"]
    }
  ];

  return (
    <section id="skills" className="relative py-24 px-6 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
        {/* Animated background orbs */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto">
        <FadeInView direction="up" className="text-center mb-20">
          <motion.h2
            className="text-5xl md:text-6xl font-display font-bold mb-4"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <span className="bg-gradient-to-r from-blue-400 via-teal-400 to-cyan-400 bg-clip-text text-transparent">
              Skills & Expertise
            </span>
          </motion.h2>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            Comprehensive technical expertise across the entire AI/ML stack
          </p>
        </FadeInView>

        {/* Bento Grid Layout */}
        <StaggerContainer staggerDelay={0.08} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {skillCategories.map((category, index) => (
            <StaggerItem key={index}>
              <TiltCard
                tiltMaxAngle={8}
                scale={1.03}
                className="h-full"
              >
                <motion.div
                  className="glass-card h-full rounded-2xl p-6 group cursor-pointer"
                  whileHover={{ scale: 1.02 }}
                  transition={{ duration: 0.3 }}
                >
                  {/* Category Header */}
                  <div className="mb-4">
                    <div className="inline-block px-4 py-2 rounded-xl bg-gradient-to-r from-blue-500 to-blue-600 shadow-lg">
                      <h3 className="text-base md:text-lg font-bold text-white">
                        {category.category}
                      </h3>
                    </div>
                  </div>

                  {/* Skills Grid */}
                  <div className="flex flex-wrap gap-2">
                    {category.skills.map((skill, i) => (
                      <motion.span
                        key={i}
                        className="px-3 py-1.5 bg-slate-800/70 backdrop-blur-sm rounded-lg text-sm text-slate-300 border border-slate-700/50 hover:border-blue-500/50 transition-all duration-300 hover:text-blue-400 hover:bg-slate-700/70 hover:scale-105"
                        whileHover={{ y: -2 }}
                        transition={{ duration: 0.2 }}
                      >
                        {skill}
                      </motion.span>
                    ))}
                  </div>

                  {/* Hover Glow Effect */}
                  <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-blue-500/0 via-teal-500/0 to-purple-500/0 group-hover:from-blue-500/5 group-hover:via-teal-500/5 group-hover:to-purple-500/5 transition-all duration-500 pointer-events-none" />
                </motion.div>
              </TiltCard>
            </StaggerItem>
          ))}
        </StaggerContainer>

        {/* Professional Impact Stats */}
        <FadeInView direction="up" delay={0.4} className="mt-20">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { value: "17+", label: "Companies Collaborated" },
              { value: "30+", label: "Production Projects" },
              { value: "4+", label: "Years Experience" },
              { value: "100%", label: "Client Satisfaction" },
            ].map((stat, index) => (
              <motion.div
                key={index}
                className="glass-card rounded-2xl p-6 text-center group cursor-pointer"
                whileHover={{ scale: 1.05, y: -5 }}
                transition={{ duration: 0.3 }}
              >
                <div className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-blue-500 to-blue-600 bg-clip-text text-transparent mb-2">
                  {stat.value}
                </div>
                <div className="text-slate-400 text-sm md:text-base">
                  {stat.label}
                </div>
                <div className="h-1 w-0 group-hover:w-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all duration-500 mt-3 mx-auto" />
              </motion.div>
            ))}
          </div>
        </FadeInView>
      </div>
    </section>
  );
}
