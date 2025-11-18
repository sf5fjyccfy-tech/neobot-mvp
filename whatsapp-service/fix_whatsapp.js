// Test manuel de l'envoi de message
const testMessage = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/tenants/1/whatsapp/message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        phone: '+237612345678',
        message: 'Test technique'
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ Test réussi:', data);
    } else {
      console.log('❌ Erreur backend:', response.status, await response.text());
    }
  } catch (error) {
    console.log('❌ Erreur connexion:', error.message);
  }
};

testMessage();
