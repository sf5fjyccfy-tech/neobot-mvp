import SignupForm from '@/components/auth/SignupForm';
import { CheckCircle, Bot, MessageSquare, TrendingUp } from 'lucide-react';

export const metadata = {
  title: 'Créer un compte - NéoBot',
  description: 'Lancez votre assistant WhatsApp IA en 5 minutes. Essai gratuit 7 jours.',
};

const BENEFITS = [
  { icon: CheckCircle, text: 'Essai gratuit 7 jours, sans carte bancaire' },
  { icon: MessageSquare, text: 'Vos clients reçoivent des réponses en moins de 2s' },
  { icon: TrendingUp, text: 'Augmentez vos ventes de 30% en moyenne' },
  { icon: Bot, text: 'Configuration en moins de 5 minutes' },
];

export default function SignupPage() {
  return (
    <div className="min-h-screen bg-gray-950 flex">
      {/* GAUCHE : Branding & Bénéfices */}
      <div className="hidden lg:flex lg:w-1/2 relative flex-col justify-between p-12 overflow-hidden">
        {/* Gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-emerald-900 via-green-900 to-teal-900" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(52,211,153,0.15),_transparent_60%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_rgba(16,185,129,0.1),_transparent_60%)]" />
        
        {/* Grid pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:60px_60px]" />

        {/* Content */}
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-16">
            <div className="w-10 h-10 bg-emerald-400 rounded-xl flex items-center justify-center">
              <Bot className="w-6 h-6 text-gray-900" />
            </div>
            <span className="text-white text-xl font-bold tracking-tight">NéoBot</span>
          </div>

          <h1 className="text-4xl font-bold text-white leading-tight mb-4">
            Automatisez votre<br />
            <span className="text-emerald-400">WhatsApp</span> dès aujourd'hui
          </h1>
          <p className="text-white/60 text-lg leading-relaxed mb-12">
            Des milliers d'entreprises africaines font confiance à NéoBot 
            pour répondre à leurs clients 24h/24.
          </p>

          <div className="space-y-4">
            {BENEFITS.map(({ icon: Icon, text }, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-8 h-8 bg-emerald-400/20 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Icon className="w-4 h-4 text-emerald-400" />
                </div>
                <span className="text-white/80 text-sm">{text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Testimonial */}
        <div className="relative z-10 bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
          <p className="text-white/80 text-sm leading-relaxed mb-4">
            "NéoBot a transformé notre service client. On répond maintenant à 
            300+ messages par jour sans effort. Le ROI est incroyable."
          </p>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-emerald-400 rounded-full flex items-center justify-center text-gray-900 font-bold text-sm">K</div>
            <div>
              <p className="text-white font-medium text-sm">Kevin M.</p>
              <p className="text-white/50 text-xs">Restaurant Le Festin, Douala</p>
            </div>
            <div className="ml-auto text-emerald-400 text-xs font-semibold">★★★★★</div>
          </div>
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
            <h2 className="text-3xl font-bold text-white mb-2">Créer un compte</h2>
            <p className="text-white/50">7 jours gratuits • Aucune carte requise</p>
          </div>

          <SignupForm />

          <p className="text-center text-white/30 text-xs mt-8">
            En vous inscrivant, vous acceptez nos{' '}
            <a href="#" className="text-white/50 hover:text-white/70 underline underline-offset-2">Conditions d'utilisation</a>
            {' '}et notre{' '}
            <a href="#" className="text-white/50 hover:text-white/70 underline underline-offset-2">Politique de confidentialité</a>.
          </p>
        </div>
      </div>
    </div>
  );
}

