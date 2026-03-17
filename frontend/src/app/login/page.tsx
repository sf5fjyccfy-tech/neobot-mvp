import LoginForm from '@/components/auth/LoginForm';
import { Bot, Shield, Zap, Users } from 'lucide-react';

export const metadata = {
  title: 'Connexion - NéoBot',
  description: 'Connectez-vous à votre espace NéoBot',
};

const STATS = [
  { value: '2,500+', label: 'Entreprises actives' },
  { value: '98%', label: 'Satisfaction client' },
  { value: '< 2s', label: 'Temps de réponse' },
];

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-gray-950 flex">
      {/* GAUCHE : Branding */}
      <div className="hidden lg:flex lg:w-1/2 relative flex-col justify-between p-12 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-emerald-900 via-green-900 to-teal-900" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(52,211,153,0.15),_transparent_60%)]" />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:60px_60px]" />

        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-16">
            <div className="w-10 h-10 bg-emerald-400 rounded-xl flex items-center justify-center">
              <Bot className="w-6 h-6 text-gray-900" />
            </div>
            <span className="text-white text-xl font-bold tracking-tight">NéoBot</span>
          </div>

          <h1 className="text-4xl font-bold text-white leading-tight mb-4">
            Bon retour<br />
            <span className="text-emerald-400">parmi nous</span> 👋
          </h1>
          <p className="text-white/60 text-lg leading-relaxed mb-12">
            Votre assistant WhatsApp IA n'attend que vous.
            Gérez vos conversations, vos clients et vos ventes.
          </p>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mb-12">
            {STATS.map(({ value, label }) => (
              <div key={label} className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 border border-white/10 text-center">
                <div className="text-2xl font-bold text-emerald-400 mb-1">{value}</div>
                <div className="text-white/50 text-xs">{label}</div>
              </div>
            ))}
          </div>

          {/* Features */}
          <div className="space-y-3">
            {[
              { icon: Shield, text: 'Données sécurisées et isolées' },
              { icon: Zap, text: 'IA ultra-rapide basée sur DeepSeek' },
              { icon: Users, text: 'Support disponible 7j/7' },
            ].map(({ icon: Icon, text }) => (
              <div key={text} className="flex items-center gap-3">
                <div className="w-7 h-7 bg-emerald-400/20 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Icon className="w-3.5 h-3.5 text-emerald-400" />
                </div>
                <span className="text-white/70 text-sm">{text}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="relative z-10 text-white/30 text-xs">
          © 2026 NéoBot — Tim Patrick DIMANI BALLA
        </div>
      </div>

      {/* DROITE : Formulaire */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 lg:p-12">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <div className="w-8 h-8 bg-emerald-400 rounded-lg flex items-center justify-center">
              <Bot className="w-5 h-5 text-gray-900" />
            </div>
            <span className="text-white text-lg font-bold">NéoBot</span>
          </div>

          <div className="mb-8">
            <h2 className="text-3xl font-bold text-white mb-2">Connexion</h2>
            <p className="text-white/50">Accédez à votre tableau de bord</p>
          </div>

          <LoginForm />

          <p className="text-center text-white/30 text-xs mt-8">
            Protégé par chiffrement JWT 256-bit
          </p>
        </div>
      </div>
    </div>
  );
}

