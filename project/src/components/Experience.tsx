import { Building2, MapPin } from 'lucide-react';

export default function Experience() {
  const experiences = [
    {
      title: "Founding AI Engineer",
      company: "Saturnin",
      location: "Remote",
      period: "Nov 2025 – Jan 2026",
      achievements: [
        "Built multi-agent RAG system for investor portfolio analysis using LangGraph, Pinecone, and Google Vertex AI (Gemini)",
        "Architected AWS ECS Fargate deployment with 99.9% uptime using multi-model fallback (Gemini → Groq LLaMA)",
        "Hosted open-source models (Qwen 3, Kimi K2 thinking) on private servers using vLLM and Ray for sensitive data processing",
        "Developed persistent portfolio intelligence platform enabling cross-company queries and automated due diligence",
        "Created 4 specialized AI agents: investor research, financial analysis, book training, and personalized analyst",
        "Designed RAG pipeline with semantic search across pitch decks, websites, and investment books (Pinecone vector DB)",
        "Implemented real-time market intelligence synthesis with web search, scraping, and precise financial calculations"
      ]
    },
    {
      title: "AI Solution Engineer",
      company: "Everest Commerce Group",
      location: "Netherlands",
      period: "Mar 2025 – Nov 2025",
      achievements: [
        "Built Peak OS, a unified AI platform integrating company data, analytics, and automation",
        "Designed AI agents for business monitoring, performance optimization, and automation",
        "Created AI systems for ads generation, content automation, and creative analysis",
        "Developed AI-driven customer communication systems (chatbot, email, WhatsApp)",
        "Built an AI-based M&A due diligence and company evaluation platform",
        "Designed dashboards for business intelligence and decision-making",
        "Automated supply chain intelligence: product discovery, supplier analysis, and negotiations"
      ]
    },
    {
      title: "AI / Machine Learning Engineer",
      company: "Ooodles",
      location: "United Kingdom",
      period: "Apr 2024 – Mar 2025",
      achievements: [
        "Built AI-powered product onboarding and catalog automation pipelines",
        "Developed internal LLM automation tools for operations",
        "Created AI-based company vetting and digital footprint analysis systems",
        "Built multi-channel AI chatbot systems (WhatsApp, Slack, Teams) for e-commerce",
        "Designed scalable AI architectures for low-latency production systems"
      ]
    },
    {
      title: "Machine Learning Engineer",
      company: "Moe-Assist",
      location: "USA",
      period: "Dec 2023 – May 2024",
      achievements: [
        "Built sentiment analysis pipelines and automated data systems",
        "Developed social media intelligence tools and RAG-based chatbots",
        "Led ML architecture design and cross-team coordination"
      ]
    },
    {
      title: "ML Engineer",
      company: "Playback",
      location: "New York (Remote)",
      period: "Jan 2023 – Dec 2023",
      achievements: [
        "Engineered an AI brand intelligence system with 95% human-level quality, zero hallucination",
        "Built proprietary Voice AI models with 80–90% voice similarity across custom brand voices",
        "Created a proprietary generative video engine producing AAA-grade videos (30–120s)",
        "Conducted deep research and model benchmarking across state-of-the-art multimodal architectures"
      ]
    },
    {
      title: "ML Intern",
      company: "Samsung Prism",
      location: "India",
      period: "Jan 2024 – Apr 2024",
      achievements: [
        "Worked on LLM inference optimization and performance improvement"
      ]
    }
  ];

  return (
    <section id="experience" className="relative py-24 px-6">
      <div className="absolute inset-0 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950"></div>

      <div className="relative z-10 max-w-6xl mx-auto">
        <h2 className="text-5xl font-bold mb-16 text-center bg-gradient-to-r from-blue-400 to-teal-400 bg-clip-text text-transparent">
          Experience
        </h2>

        <div className="relative">
          <div className="absolute left-0 md:left-8 h-full w-0.5 bg-gradient-to-b from-blue-500 to-teal-500"></div>

          {experiences.map((exp, index) => (
            <div
              key={index}
              className="relative mb-16 md:pl-20"
            >
              <div className="absolute left-0 md:left-[1.75rem] w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-teal-500 border-4 border-slate-950 shadow-lg shadow-blue-500/50"></div>

              <div
                className="ml-12 md:ml-0 bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-sm rounded-2xl p-8 border border-blue-500/20 hover:border-blue-500/40 transition-all duration-300 hover:shadow-2xl hover:shadow-blue-500/20 hover:scale-[1.02]"
              >
                <div className="flex items-start gap-3 mb-4">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-teal-500/20 flex items-center justify-center flex-shrink-0">
                    <Building2 className="w-6 h-6 text-blue-400" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-2xl font-bold text-white mb-2">{exp.title}</h3>
                    <p className="text-xl text-blue-400 font-semibold mb-2">{exp.company}</p>
                    <div className="flex flex-wrap gap-4 text-gray-400 text-sm">
                      <span className="flex items-center gap-1">
                        <MapPin className="w-4 h-4" />
                        {exp.location}
                      </span>
                      <span>{exp.period}</span>
                    </div>
                  </div>
                </div>

                <ul className="space-y-3 mt-6">
                  {exp.achievements.map((achievement, i) => (
                    <li key={i} className="text-gray-300 flex gap-3">
                      <span className="text-teal-400 mt-1 flex-shrink-0">▹</span>
                      <span>{achievement}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
