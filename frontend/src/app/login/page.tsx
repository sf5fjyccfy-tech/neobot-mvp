import LoginForm from '@/components/auth/LoginForm';

export const metadata = {
  title: 'Se Connecter - NéoBot',
  description: 'Connectez-vous à votre compte NéoBot',
};

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center px-4">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
        <h1 className="text-3xl font-bold text-gray-900 mb-6 text-center">
          Connexion NéoBot
        </h1>
        
        <LoginForm />
        
        <div className="mt-8 pt-8 border-t border-gray-200">
          <p className="text-center text-sm text-gray-600">
            By logging in, you agree to our Terms of Service and Privacy Policy
          </p>
        </div>
      </div>
    </div>
  );
}
