import SignupForm from '@/components/auth/SignupForm';
import { CheckCircle, Bot, MessageSquare, TrendingUp } from 'lucide-react';
import { NeoBotBrandmark } from '@/components/ui/NeoBotLogo';

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
    <div className="min-h-screen flex" style={{ background: '#06040E' }}>
      {/* GAUCHE : Branding & Bénéfices */}
      <div className="hidden lg:flex lg:w-1/2 relative flex-col justify-between p-12 overflow-hidden">
        {/* Fond galaxie */}
        <div className="absolute inset-0" style={{ background: 'linear-gradient(135deg, #0D0008, #06040E, #00080A)' }} />
        {/* Nébuleuses */}
        <div className="absolute" style={{ top: '-10%', right: '-10%', width: '60%', height: '60%', background: 'radial-gradient(circle, rgba(255,77,0,0.15) 0%, transparent 70%)', borderRadius: '50%' }} />
        <div className="absolute" style={{ bottom: '-10%', left: '-10%', width: '50%', height: '50%', background: 'radial-gradient(circle, rgba(0,229,204,0.12) 0%, transparent 70%)', borderRadius: '50%' }} />
        {/* Grid cosmique */}
        <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(rgba(255,77,0,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,77,0,0.04) 1px, transparent 1px)', backgroundSize: '60px 60px' }} />

        {/* Content */}
        <div className="relative z-10">
          <div className="mb-14">
            <NeoBotBrandmark size={30} iconColor="#00E5CC" textColor="#FFFFFF" />
          </div>

          <h1 className="text-4xl font-bold text-white leading-tight mb-4">
            Automatisez votre<br />
            <span style={{ background: 'linear-gradient(90deg, #FF9A6C, #00E5CC)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>WhatsApp</span> dès aujourd'hui
          </h1>
          <p style={{ color: 'rgba(255,180,120,0.6)' }} className="text-lg leading-relaxed mb-12">
            Votre agent WhatsApp IA opérationnel en moins de 30 minutes.
            Disponible 24h/24, sans équipe support supplémentaire.
          </p>

          <div className="space-y-4">
            {BENEFITS.map(({ icon: Icon, text }, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(255,77,0,0.12)', border: '1px solid rgba(255,77,0,0.25)' }}>
                  <Icon className="w-4 h-4" style={{ color: '#FF9A6C' }} />
                </div>
                <span style={{ color: 'rgba(255,180,120,0.8)' }} className="text-sm">{text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Essai gratuit — info clé */}
        <div className="relative z-10 backdrop-blur-sm rounded-2xl p-6" style={{ background: 'rgba(0,229,204,0.05)', border: '1px solid rgba(0,229,204,0.15)' }}>
          <p style={{ color: 'rgba(255,180,120,0.7)' }} className="text-sm leading-relaxed">
            Essai gratuit 14 jours · Aucune carte bancaire requise · Résiliable à tout moment.
            Votre numéro WhatsApp Business reste le vôtre.
          </p>
        </div>
      </div>

      {/* DROITE : Formulaire */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 lg:p-12" style={{ background: 'rgba(5,0,16,0.95)' }}>
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <NeoBotBrandmark size={22} iconColor="#00E5CC" textColor="#FFFFFF" />
          </div>

          <div className="mb-8">
            <h2 className="text-3xl font-bold text-white mb-2">Créer un compte</h2>
            <p style={{ color: 'rgba(255,180,120,0.5)' }}>7 jours gratuits • Aucune carte requise</p>
          </div>

          <SignupForm />

          <p className="text-center text-xs mt-8" style={{ color: 'rgba(0,229,204,0.5)' }}>
            En vous inscrivant, vous acceptez nos{' '}
            <a href="#" style={{ color: 'rgba(0,229,204,0.7)' }} className="underline underline-offset-2">Conditions d'utilisation</a>
            {' '}et notre{' '}
            <a href="#" style={{ color: 'rgba(0,229,204,0.7)' }} className="underline underline-offset-2">Politique de confidentialité</a>.
          </p>
        </div>
      </div>
    </div>
  );
}
