import SignupForm from '@/components/auth/SignupForm';

export const metadata = {
  title: 'S\'inscrire - NéoBot',
  description: 'Créez votre compte NéoBot et commencez maintenant',
};

export default function SignupPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center px-4 py-8">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
        <h1 className="text-3xl font-bold text-gray-900 mb-2 text-center">
          Créer un Compte
        </h1>
        <p className="text-center text-gray-600 mb-6">
          Rejoignez NéoBot et automatisez votre WhatsApp
        </p>
        
        <SignupForm />
        
        <div className="mt-8 pt-8 border-t border-gray-200">
          <p className="text-center text-xs text-gray-600">
            By signing up, you agree to our Terms of Service and Privacy Policy
          </p>
        </div>
      </div>
    </div>
  );
}
