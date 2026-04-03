import LoginForm from '@/components/auth/LoginForm';
import { Shield, Zap, Users } from 'lucide-react';
import { NeoBotBrandmark } from '@/components/ui/NeoBotLogo';

export const metadata = {
  title: 'Connexion - NéoBot',
  description: 'Connectez-vous à votre espace NéoBot',
};

const STATS = [
  { value: '24/7', label: 'Disponible en continu' },
  { value: '< 2s', label: 'Temps de réponse' },
  { value: '5 min', label: 'Pour configurer' },
];

export default function LoginPage() {
  return (
    <div className="min-h-screen flex" style={{ background: '#06040E' }}>
      {/* GAUCHE : Branding */}
      <div className="hidden lg:flex lg:w-1/2 relative flex-col justify-between p-12 overflow-hidden">
        {/* Fond galaxie */}
        <div className="absolute inset-0" style={{ background: 'linear-gradient(135deg, #0D0008, #06040E, #00080A)' }} />
        {/* Nébuleuses */}
        <div className="absolute" style={{ top: '-10%', left: '-10%', width: '60%', height: '60%', background: 'radial-gradient(circle, rgba(255,77,0,0.15) 0%, transparent 70%)', borderRadius: '50%' }} />
        <div className="absolute" style={{ bottom: '-10%', right: '-10%', width: '50%', height: '50%', background: 'radial-gradient(circle, rgba(0,229,204,0.12) 0%, transparent 70%)', borderRadius: '50%' }} />
        {/* Grid cosmique */}
        <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(rgba(255,77,0,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,77,0,0.04) 1px, transparent 1px)', backgroundSize: '60px 60px' }} />

        {/* Content */}
        <div className="relative z-10">
          <div className="mb-14">
            <NeoBotBrandmark size={30} iconColor="#00E5CC" textColor="#FFFFFF" />
          </div>

          <h1 className="text-4xl font-bold text-white leading-tight mb-4">
            Bon retour<br />
            <span style={{ background: 'linear-gradient(90deg, #FF9A6C, #00E5CC)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>parmi nous</span> 👋
          </h1>
          <p style={{ color: 'rgba(255,180,120,0.6)' }} className="text-lg leading-relaxed mb-12">
            Votre assistant WhatsApp IA n'attend que vous.
            Gérez vos conversations, vos clients et vos ventes.
          </p>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mb-12">
            {STATS.map(({ value, label }) => (
              <div key={label} style={{ background: 'rgba(255,77,0,0.08)', border: '1px solid rgba(255,77,0,0.25)' }} className="backdrop-blur-sm rounded-2xl p-4 text-center">
                <div className="text-2xl font-bold mb-1" style={{ background: 'linear-gradient(90deg, #FF9A6C, #00E5CC)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>{value}</div>
                <div style={{ color: 'rgba(255,180,120,0.5)' }} className="text-xs">{label}</div>
              </div>
            ))}
          </div>

          {/* Features */}
          <div className="space-y-3">
            {[
              { icon: Shield, text: 'Données sécurisées et isolées' },
              { icon: Zap, text: 'IA de dernière génération, réponse < 2s' },
              { icon: Users, text: 'Support disponible 7j/7' },
            ].map(({ icon: Icon, text }) => (
              <div key={text} className="flex items-center gap-3">
                <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(255,77,0,0.12)', border: '1px solid rgba(255,77,0,0.25)' }}>
                  <Icon className="w-3.5 h-3.5" style={{ color: '#FF9A6C' }} />
                </div>
                <span style={{ color: 'rgba(255,180,120,0.7)' }} className="text-sm">{text}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="relative z-10 text-xs" style={{ color: 'rgba(0,229,204,0.5)' }}>
          © 2026 NéoBot. Tous droits réservés.
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
            <h2 className="text-3xl font-bold text-white mb-2">Connexion</h2>
            <p style={{ color: 'rgba(255,180,120,0.5)' }}>Accédez à votre tableau de bord</p>
          </div>

          <LoginForm />

          <p className="text-center text-xs mt-8" style={{ color: 'rgba(0,229,204,0.5)' }}>
            Protégé par chiffrement JWT 256-bit
          </p>
        </div>
      </div>
    </div>
  );
}

