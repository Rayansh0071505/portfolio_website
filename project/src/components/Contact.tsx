import { Mail, Phone, Linkedin, Github } from 'lucide-react';

export default function Contact() {
  const contactInfo = [
    {
      icon: Mail,
      label: "Email",
      value: "rayanshsrivastava.ai@gmail.com",
      link: "mailto:rayanshsrivastava.ai@gmail.com"
    },
    {
      icon: Phone,
      label: "Phone",
      value: "+91 7521018614",
      link: "tel:+917521018614"
    },
    {
      icon: Linkedin,
      label: "LinkedIn",
      value: "Connect on LinkedIn",
      link: "https://www.linkedin.com/in/rayansh-srivastava-419951219/"
    },
    {
      icon: Github,
      label: "GitHub",
      value: "View Projects",
      link: "https://github.com/Rayansh0071505"
    }
  ];

  return (
    <section className="relative py-24 px-6">
      <div className="absolute inset-0 bg-gradient-to-b from-slate-950 via-blue-950 to-slate-950"></div>

      <div className="relative z-10 max-w-4xl mx-auto">
        <h2 className="text-5xl font-bold mb-8 text-center bg-gradient-to-r from-blue-400 to-teal-400 bg-clip-text text-transparent">
          Let's Connect
        </h2>
        <p className="text-xl text-gray-400 text-center mb-16">
          Ready to build something amazing together? Let's talk.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {contactInfo.map((item, index) => (
            <a
              key={index}
              href={item.link}
              target={item.link.startsWith('http') ? '_blank' : '_self'}
              rel="noopener noreferrer"
              className="group bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-sm rounded-2xl p-6 border border-blue-500/20 hover:border-blue-500/50 transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-blue-500/30"
            >
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-blue-500/20 to-teal-500/20 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                  <item.icon className="w-7 h-7 text-blue-400" />
                </div>
                <div>
                  <p className="text-gray-400 text-sm mb-1">{item.label}</p>
                  <p className="text-white font-semibold group-hover:text-blue-400 transition-colors duration-300">
                    {item.value}
                  </p>
                </div>
              </div>
            </a>
          ))}
        </div>

      </div>
    </section>
  );
}
