import express from 'express'
import axios from 'axios'

const app = express()
app.use(express.json())

// Version simplifiée sans Baileys pour tester d'abord
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', service: 'whatsapp-simple' })
})

app.post('/session/create', (req, res) => {
    const { tenantId } = req.body
    res.json({ 
        status: 'created', 
        tenantId,
        message: 'Session simulée - Baileys sera ajouté après'
    })
})

app.listen(3001, () => {
    console.log('Service WhatsApp simple sur port 3001')
})
