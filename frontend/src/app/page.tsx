'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  ArrowRight, CheckCircle, BarChart3,
  Bot, Zap, Shield, Star, ChevronDown,
  Clock, Globe, Sparkles,
} from 'lucide-react';
import { NeoBotIcon as NeoLogo } from '@/components/ui/NeoBotLogo';

// ─── Galaxy constants (déterministes) ────────────────────────────────────

// c = index dans STAR_COLORS
const STAR_COLORS = ['#FFFFFF','#FFFFFF','#00E5CC','#FDE68A','#FF9A6C','#FFFFFF','#00E5CC','#FDE68A'];

const STARS = [
  { x:4,  y:6,  s:1.2, d:4.2, op:.5, c:0 }, { x:11, y:19, s:1.6, d:6.1, op:.4, c:2 },
  { x:17, y:43, s:.9,  d:3.4, op:.6, c:0 }, { x:23, y:11, s:1.1, d:5.3, op:.5, c:3 },
  { x:29, y:67, s:1.0, d:7.1, op:.4, c:0 }, { x:37, y:28, s:1.9, d:4.0, op:.8, c:4 },
  { x:41, y:84, s:.8,  d:5.5, op:.5, c:0 }, { x:47, y:14, s:1.3, d:6.3, op:.6, c:2 },
  { x:54, y:54, s:1.0, d:4.1, op:.4, c:0 }, { x:59, y:3,  s:2.1, d:3.2, op:.9, c:3 },
  { x:64, y:71, s:1.1, d:5.2, op:.5, c:0 }, { x:69, y:27, s:.9,  d:7.2, op:.4, c:4 },
  { x:74, y:91, s:1.5, d:4.3, op:.7, c:2 }, { x:79, y:17, s:1.0, d:6.1, op:.5, c:0 },
  { x:84, y:59, s:1.8, d:3.3, op:.8, c:3 }, { x:89, y:39, s:1.2, d:5.4, op:.6, c:0 },
  { x:94, y:77, s:.9,  d:4.2, op:.4, c:4 }, { x:7,  y:89, s:1.0, d:6.2, op:.5, c:0 },
  { x:21, y:77, s:1.5, d:5.1, op:.7, c:2 }, { x:34, y:49, s:.9,  d:3.3, op:.5, c:0 },
  { x:49, y:37, s:1.3, d:4.4, op:.6, c:3 }, { x:62, y:87, s:1.0, d:7.3, op:.4, c:0 },
  { x:76, y:9,  s:1.8, d:5.2, op:.8, c:4 }, { x:87, y:81, s:1.3, d:4.1, op:.6, c:2 },
  { x:14, y:59, s:2.0, d:3.1, op:.7, c:0 }, { x:44, y:94, s:.9,  d:6.4, op:.5, c:0 },
  { x:56, y:41, s:1.2, d:5.3, op:.4, c:3 }, { x:71, y:65, s:1.6, d:4.2, op:.7, c:2 },
  { x:91, y:21, s:1.0, d:6.3, op:.5, c:0 }, { x:3,  y:34, s:1.9, d:3.2, op:.9, c:4 },
  { x:27, y:3,  s:1.2, d:5.1, op:.6, c:0 }, { x:43, y:71, s:.9,  d:7.1, op:.4, c:2 },
  { x:67, y:47, s:1.0, d:4.3, op:.5, c:3 }, { x:82, y:35, s:1.5, d:6.2, op:.7, c:0 },
  { x:96, y:54, s:1.1, d:3.4, op:.4, c:4 }, { x:9,  y:14, s:.9,  d:5.2, op:.6, c:0 },
  { x:32, y:87, s:2.1, d:4.1, op:.8, c:2 }, { x:51, y:19, s:1.3, d:7.2, op:.5, c:0 },
  { x:78, y:94, s:1.0, d:5.3, op:.4, c:3 }, { x:90, y:11, s:1.9, d:3.1, op:.9, c:0 },
  { x:16, y:33, s:1.1, d:4.4, op:.5, c:4 }, { x:38, y:62, s:1.7, d:6.1, op:.6, c:2 },
  { x:60, y:78, s:.8,  d:5.4, op:.4, c:0 }, { x:73, y:22, s:1.4, d:4.2, op:.7, c:3 },
  { x:85, y:48, s:1.0, d:3.3, op:.5, c:0 }, { x:2,  y:75, s:1.8, d:6.3, op:.6, c:2 },
  { x:25, y:52, s:1.0, d:5.2, op:.4, c:0 }, { x:46, y:8,  s:1.5, d:4.1, op:.7, c:4 },
  { x:68, y:36, s:.9,  d:7.1, op:.5, c:0 }, { x:93, y:63, s:1.2, d:3.4, op:.6, c:3 },
];

// c = index dans SHOOT_GRADS
const SHOOT_GRADS = [
  'linear-gradient(90deg,transparent 0%,rgba(255,255,255,.85) 45%,rgba(255,255,255,.3) 75%,transparent 100%)',
  'linear-gradient(90deg,transparent 0%,rgba(34,211,238,.9) 45%,rgba(34,211,238,.2) 75%,transparent 100%)',
  'linear-gradient(90deg,transparent 0%,rgba(253,230,138,.9) 45%,rgba(253,230,138,.2) 75%,transparent 100%)',
  'linear-gradient(90deg,transparent 0%,rgba(255,180,120,.9) 45%,rgba(255,180,120,.2) 75%,transparent 100%)',
];

const SHOOTING = [
  { x:5,  y:5,  dur:3.4, delay:0,    c:0 },
  { x:20, y:3,  dur:4.1, delay:3.2,  c:1 },
  { x:50, y:1,  dur:3.7, delay:6.8,  c:2 },
  { x:70, y:6,  dur:4.6, delay:11.5, c:3 },
  { x:38, y:14, dur:3.2, delay:15.0, c:1 },
  { x:15, y:30, dur:4.3, delay:19.0, c:0 },
  { x:65, y:12, dur:3.9, delay:23.5, c:2 },
  { x:85, y:4,  dur:3.5, delay:27.0, c:3 },
  { x:55, y:22, dur:4.8, delay:31.0, c:1 },
];

const NEBULAS = [
  { x:18, y:18, sz:700, r:'109,40,217',  op:.07 },
  { x:80, y:60, sz:620, r:'14,165,233',  op:.055 },
  { x:48, y:88, sz:500, r:'217,70,239',  op:.045 },
  { x:12, y:68, sz:420, r:'109,40,217',  op:.04  },
  { x:88, y:28, sz:360, r:'234,88,12',   op:.03  },
  { x:55, y:42, sz:280, r:'14,165,233',  op:.025 },
];

// ─── Fond galaxique ───────────────────────────────────────────────────────

function GalaxyBG() {
  return (
    <div style={{ position:'fixed', inset:0, pointerEvents:'none', zIndex:0, overflow:'hidden' }}>

      {/* ── Cœur galactique central ── */}
      <div style={{
        position:'absolute', left:'50%', top:'28%',
        width:320, height:320,
        transform:'translate(-50%,-50%)', borderRadius:'50%',
        background:'radial-gradient(circle, rgba(204,61,0,.18) 0%, rgba(204,61,0,.06) 40%, transparent 70%)',
        filter:'blur(28px)',
      }}/>
      <div style={{
        position:'absolute', left:'50%', top:'28%',
        width:120, height:120,
        transform:'translate(-50%,-50%)', borderRadius:'50%',
        background:'radial-gradient(circle, rgba(255,180,120,.25) 0%, transparent 70%)',
        filter:'blur(10px)',
      }}/>

      {/* ── Bras spiraux galactiques ── */}
      <div className="neo-galaxy-slow" style={{
        position:'absolute', left:'50%', top:'28%',
        width:'170vmin', height:'170vmin',
        transform:'translate(-50%,-50%)', borderRadius:'50%',
        background:`conic-gradient(
          from 0deg,
          transparent 0%,
          rgba(204,61,0,.065) 8%,
          transparent 16%,
          rgba(34,211,238,.04) 26%,
          transparent 34%,
          rgba(204,61,0,.055) 50%,
          transparent 58%,
          rgba(34,211,238,.04) 68%,
          transparent 76%,
          rgba(217,70,239,.03) 88%,
          transparent 100%
        )`,
      }}/>
      <div className="neo-galaxy-medium" style={{
        position:'absolute', left:'50%', top:'28%',
        width:'110vmin', height:'110vmin',
        transform:'translate(-50%,-50%)', borderRadius:'50%',
        background:`conic-gradient(
          from 110deg,
          transparent 0%,
          rgba(0,229,204,.05) 7%,
          transparent 15%,
          rgba(217,70,239,.04) 30%,
          transparent 38%,
          rgba(0,229,204,.05) 58%,
          transparent 66%,
          rgba(217,70,239,.03) 82%,
          transparent 90%
        )`,
      }}/>

      {/* ── Nébuleuses colorées ── */}
      {NEBULAS.map((n, i) => (
        <div key={i} style={{
          position:'absolute', left:`${n.x}%`, top:`${n.y}%`,
          width:n.sz, height:n.sz,
          transform:'translate(-50%,-50%)', borderRadius:'50%',
          background:`radial-gradient(circle, rgba(${n.r},${n.op}) 0%, transparent 68%)`,
          filter:'blur(6px)',
        }}/>
      ))}

      {/* ── Étoiles multicolores ── */}
      {STARS.map((s, i) => (
        <div key={i} className="neo-star" style={{
          position:'absolute', left:`${s.x}%`, top:`${s.y}%`,
          width:s.s, height:s.s, borderRadius:'50%',
          background:STAR_COLORS[s.c], opacity:s.op,
          animationDuration:`${s.d}s`,
          animationDelay:`${(i * 0.27) % 5}s`,
          boxShadow: s.c !== 0 ? `0 0 ${s.s*2}px ${STAR_COLORS[s.c]}` : undefined,
        }}/>
      ))}

      {/* ── Étoiles filantes colorées ── */}
      {SHOOTING.map((ss, i) => (
        <div key={i} className="neo-shoot" style={{
          position:'absolute', left:`${ss.x}%`, top:`${ss.y}%`,
          animationDuration:`${ss.dur}s`,
          animationDelay:`${ss.delay}s`,
          animationIterationCount:'infinite',
          animationTimingFunction:'linear',
        }}>
          <div style={{
            width:220, height:1.5,
            background:SHOOT_GRADS[ss.c],
            borderRadius:2, transform:'rotate(38deg)',
          }}/>
        </div>
      ))}

      {/* ── Poussières cosmiques ── */}
      {STARS.filter((_,i)=>i%3===0).map((s, i) => (
        <div key={i} className="neo-dust" style={{
          position:'absolute',
          left:`${(s.x * 1.1 + s.y * 0.3) % 100}%`,
          top:`${(s.y * 1.2 + s.x * 0.2) % 100}%`,
          width:.9, height:.9, borderRadius:'50%',
          background: i % 3 === 0
            ? 'rgba(34,211,238,.55)'
            : i % 3 === 1
            ? 'rgba(255,180,120,.5)'
            : 'rgba(253,230,138,.45)',
          animationDuration:`${s.d + 2.5}s`,
          animationDelay:`${i * 0.35}s`,
        }}/>
      ))}
    </div>
  );
}

// ─── Static data ──────────────────────────────────────────────────────────

const STATS = [
  { v:'2 500+', l:'Entreprises actives' },
  { v:'98%',    l:'Satisfaction client'  },
  { v:'< 2s',   l:'Temps de réponse'    },
  { v:'+34%',   l:'CA moyen à 3 mois'   },
];

const FEATURES = [
  { I:Bot,       t:'IA Contextualisée',       d:'Réponses personnalisées, gestion des objections — votre bot pense comme un vrai commercial.' },
  { I:Clock,     t:'Disponible 24h/24',        d:'Répond à 2h du matin comme à 14h. Zéro client sans réponse, zéro vente manquée.' },
  { I:Zap,       t:'Réponse en < 2 secondes',  d:'Alimenté par DeepSeek AI. Votre client a sa réponse avant même de poser son téléphone.' },
  { I:Shield,    t:'Ultra Sécurisé',           d:'Données isolées par tenant, chiffrement JWT. Votre business reste entièrement confidentiel.' },
  { I:BarChart3, t:'Analytics Temps Réel',     d:"Conversations, conversions — tout visible en un coup d'œil depuis votre dashboard." },
  { I:Globe,     t:'Multi-Secteurs',            d:"Restaurants, boutiques, agences — NéoBot apprend votre vocabulaire et vos produits." },
];

const USE_CASES = [
  { ic:'🍽️', t:'Restaurants',        d:'Menu, réservations, commandes' },
  { ic:'🛍️', t:'E-commerce',         d:'Catalogue, suivi, support'     },
  { ic:'✈️', t:'Tourisme',            d:'Voyages, circuits, hôtels'     },
  { ic:'💇', t:'Beauté & Bien-être',  d:'RDV, tarifs, promos'           },
  { ic:'💪', t:'Fitness',             d:'Séances, abonnements, coaching' },
  { ic:'💼', t:'Services B2B',        d:'Devis, RDV, support client'    },
];

const TESTIMONIALS = [
  { n:'Rodrigue K.', r:'Restaurant Chez Mama, Yaoundé', q:'En 1 semaine, notre bot répond à 200+ messages/jour. Nos commandes ont augmenté de 40%.',  s:5 },
  { n:'Aïcha N.',    r:'Boutique Fashion, Douala',      q:'Les clients commandent directement via WhatsApp. NéoBot envoie les confirmations tout seul.', s:5 },
  { n:'Patrick D.',  r:'Agence de voyage, Abidjan',     q:'Service client 24h/24 sans recruter. ROI immédiat dès le premier mois.',                     s:5 },
];

const FAQS = [
  { q:'Comment fonctionne NéoBot avec WhatsApp ?',    a:"Scannez un QR Code (30 secondes). Vos clients continuent à vous écrire sur votre numéro — le bot répond en votre nom." },
  { q:'Puis-je personnaliser les réponses du bot ?',  a:"Absolument. Vous configurez sa personnalité, vos prix, horaires et FAQ. Il utilise exactement vos informations, jamais rien d'inventé." },
  { q:'Mes données sont-elles sécurisées ?',          a:"Chaque client dispose d'un espace isolé. Vos données ne sont jamais partagées. Chiffrement JWT, pratiques RGPD." },
  { q:'La limite de messages est-elle stricte ?',     a:'Non. En cas de dépassement, vous êtes notifié — le service continue sans coupure brutale.' },
];

const CHAT = [
  { f:'user', t:"Bonsoir, comment ça marche ? 🤔" },
  { f:'bot',  t:"Bonsoir ! 👋 Connectez votre WhatsApp en 30s, configurez votre bot, et il répond 24h/24 en votre nom. Vous voulez démarrer ?" },
  { f:'user', t:"Oui ! C'est quoi le délai ?" },
  { f:'bot',  t:"⚡ 30 secondes — QR code scanné, bot actif immédiatement. Je vous envoie le lien ?" },
];

// ─── Sub-components ───────────────────────────────────────────────────────

function FaqItem({ q, a }: { q:string; a:string }) {
  const [open, setOpen] = useState(false);
  return (
    <div onClick={()=>setOpen(!open)} style={{
      border:`1px solid ${open?'rgba(255,77,0,.3)':'rgba(255,255,255,.07)'}`,
      background:open?'rgba(255,77,0,.04)':'rgba(255,255,255,.01)',
      borderRadius:14, overflow:'hidden', cursor:'pointer',
      transition:'border-color .2s', marginBottom:10,
    }}>
      <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'17px 22px',gap:16}}>
        <span style={{color:'#FFF0E8',fontWeight:600,fontSize:14,fontFamily:'"Syne",sans-serif'}}>{q}</span>
        <ChevronDown style={{color:'#FF9A6C',width:15,height:15,flexShrink:0,transform:open?'rotate(180deg)':'none',transition:'transform .2s'}}/>
      </div>
      {open && <div style={{padding:'0 22px 17px',fontSize:13,color:'rgba(237,233,254,.48)',lineHeight:1.7}}>{a}</div>}
    </div>
  );
}

function ChatDemo() {
  const [n, setN] = useState(0);
  const [typing, setTyping] = useState(false);
  useEffect(()=>{
    if(n>=CHAT.length) return;
    const wait = n===0 ? 600 : 1100;
    const t = setTimeout(()=>{
      if(CHAT[n].f==='bot') { setTyping(true); setTimeout(()=>{ setTyping(false); setN(v=>v+1); },700); }
      else setN(v=>v+1);
    }, wait);
    return ()=>clearTimeout(t);
  },[n]);

  return (
    <div style={{borderRadius:22,overflow:'hidden',border:'1px solid rgba(255,77,0,.2)',background:'#06010F',boxShadow:'0 0 80px rgba(204,61,0,.1), 0 0 40px rgba(0,229,204,.06)'}}>
      {/* Header */}
      <div style={{padding:'13px 18px',display:'flex',alignItems:'center',gap:12,background:'rgba(204,61,0,.1)',borderBottom:'1px solid rgba(255,77,0,.14)'}}>
        <div style={{width:38,height:38,borderRadius:'50%',background:'rgba(204,61,0,.18)',border:'1px solid rgba(255,77,0,.3)',display:'flex',alignItems:'center',justifyContent:'center'}}>
          <NeoLogo size={22} color="#FF9A6C"/>
        </div>
        <div>
          <div style={{color:'#FFF0E8',fontWeight:700,fontSize:13,fontFamily:'"Syne",sans-serif'}}>NéoBot</div>
          <div style={{display:'flex',alignItems:'center',gap:6}}>
            <span style={{width:6,height:6,borderRadius:'50%',background:'#00E5CC',display:'inline-block',boxShadow:'0 0 6px #00E5CC'}}/>
            <span style={{color:'#00E5CC',fontSize:11}}>En ligne · DeepSeek AI</span>
          </div>
        </div>
      </div>
      {/* Messages */}
      <div style={{padding:'18px 16px',minHeight:250,display:'flex',flexDirection:'column',gap:10}}>
        {CHAT.slice(0,n).map((m,i)=>(
          <div key={i} style={{display:'flex',justifyContent:m.f==='bot'?'flex-end':'flex-start'}}>
            <div style={{
              padding:'10px 14px',maxWidth:280,fontSize:13,lineHeight:1.55,
              background:m.f==='bot'?'rgba(204,61,0,.15)':'rgba(255,255,255,.05)',
              color:m.f==='bot'?'#FF9A6C':'rgba(237,233,254,.82)',
              border:`1px solid ${m.f==='bot'?'rgba(255,77,0,.25)':'rgba(255,255,255,.08)'}`,
              borderRadius:m.f==='bot'?'16px 16px 4px 16px':'16px 16px 16px 4px',
            }}>{m.t}</div>
          </div>
        ))}
        {typing && (
          <div style={{display:'flex',justifyContent:'flex-end'}}>
            <div style={{padding:'10px 16px',background:'rgba(204,61,0,.1)',border:'1px solid rgba(255,77,0,.18)',borderRadius:16,display:'flex',gap:5}}>
              {[0,1,2].map(j=>(
                <span key={j} className="neo-bounce" style={{width:6,height:6,borderRadius:'50%',background:'#FF9A6C',display:'inline-block',animationDelay:`${j*.15}s`}}/>
              ))}
            </div>
          </div>
        )}
        <div style={{textAlign:'center',fontSize:11,color:'rgba(255,255,255,.14)',marginTop:4}}>Réponse générée en 1.1s</div>
      </div>
    </div>
  );
}

// ─── Style helpers ────────────────────────────────────────────────────────

const PILL = {
  display:'inline-block' as const,
  fontSize:11, fontWeight:700, letterSpacing:2, textTransform:'uppercase' as const,
  fontFamily:'"Syne",sans-serif', color:'#FF9A6C',
  padding:'6px 16px', borderRadius:30,
  background:'rgba(255,77,0,.08)', border:'1px solid rgba(255,77,0,.22)',
  marginBottom:18,
};
const CARD_BASE = {
  borderRadius:20, padding:'26px 22px',
  background:'rgba(255,255,255,.012)',
  border:'1px solid rgba(255,255,255,.07)',
  transition:'border-color .3s, transform .3s, box-shadow .3s',
};
const hoverCard = (el:HTMLElement, on:boolean) => {
  el.style.borderColor = on?'rgba(255,77,0,.3)':'rgba(255,255,255,.07)';
  el.style.transform   = on?'translateY(-4px)':'none';
  el.style.boxShadow   = on?'0 12px 48px rgba(204,61,0,.12)':'none';
};
const CTA_GRAD = 'linear-gradient(135deg, #FF4D00 0%, #00E5CC 100%)';
const CTA_GRAD_HOVER = 'linear-gradient(135deg, #CC3D00 0%, #00B5A0 100%)';

// ─── Main page ────────────────────────────────────────────────────────────

export default function LandingPage() {
  return (
    <>
      {/* ── CSS Animations ──────────────────────────────────────────── */}
      <style>{`
        @keyframes twinkle      { 0%,100%{opacity:.12;transform:scale(1)} 50%{opacity:1;transform:scale(1.6)} }
        @keyframes float-dust   { 0%{transform:translateY(0) translateX(0);opacity:0} 18%{opacity:.6} 80%{opacity:.12} 100%{transform:translateY(-80px) translateX(8px);opacity:0} }
        @keyframes shoot        { 0%{transform:translate(0,0);opacity:0} 5%{opacity:1} 80%{opacity:.8} 100%{transform:translate(700px,700px);opacity:0} }
        @keyframes bounce3      { 0%,80%,100%{transform:translateY(0)} 40%{transform:translateY(-7px)} }
        @keyframes glow-violet  { 0%,100%{box-shadow:0 0 22px rgba(204,61,0,.18)} 50%{box-shadow:0 0 55px rgba(204,61,0,.45),0 0 100px rgba(0,229,204,.12)} }
        @keyframes float-logo   { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-10px)} }
        @keyframes fade-in-up   { from{opacity:0;transform:translateY(26px)} to{opacity:1;transform:translateY(0)} }
        @keyframes galaxy-spin-slow   { from{transform:translate(-50%,-50%) rotate(0deg)} to{transform:translate(-50%,-50%) rotate(360deg)} }
        @keyframes galaxy-spin-medium { from{transform:translate(-50%,-50%) rotate(0deg)} to{transform:translate(-50%,-50%) rotate(360deg)} }
        .neo-star       { animation:twinkle linear infinite }
        .neo-shoot      { animation:shoot linear }
        .neo-dust       { animation:float-dust ease-in-out infinite }
        .neo-bounce     { animation:bounce3 1.2s ease infinite }
        .neo-glow       { animation:glow-violet 3s ease-in-out infinite }
        .neo-float      { animation:float-logo 5s ease-in-out infinite }
        .neo-fade       { animation:fade-in-up .7s ease both }
        .neo-link       { text-decoration:none }
        .neo-nav-link   { transition:color .2s }
        .neo-nav-link:hover { color:#FFF0E8!important }
        .neo-galaxy-slow   { animation:galaxy-spin-slow   90s linear infinite }
        .neo-galaxy-medium { animation:galaxy-spin-medium 55s linear infinite reverse }
      `}</style>

      <div style={{minHeight:'100vh',color:'#FFF0E8',overflow:'hidden',background:'#06040E',fontFamily:'"DM Sans",sans-serif',position:'relative'}}>

        <GalaxyBG/>

        {/* ══════════════════════════════════════════════════════ NAV ══ */}
        <nav style={{
          position:'fixed',top:0,left:0,right:0,zIndex:50,
          borderBottom:'1px solid rgba(255,77,0,.1)',
          backdropFilter:'blur(24px)',
          background:'rgba(5,0,16,.82)',
          padding:'13px 40px',
          display:'flex',alignItems:'center',justifyContent:'space-between',
        }}>
          <Link href="/" className="neo-link" style={{display:'flex',alignItems:'center',gap:10}}>
            <NeoLogo size={32} color="#FF9A6C"/>
            <span style={{fontFamily:'"Syne",sans-serif',fontWeight:900,fontSize:19,color:'#FFF0E8',letterSpacing:3,textTransform:'uppercase'}}>
              NEOBOT
            </span>
          </Link>

          <div style={{display:'flex',alignItems:'center',gap:36}}>
            {([['#features','Fonctionnalités'],['#use-cases','Secteurs'],['#faq','FAQ']] as [string,string][]).map(([h,l])=>(
              <a key={h} href={h} className="neo-link neo-nav-link" style={{fontSize:13,color:'rgba(237,233,254,.38)'}}>
                {l}
              </a>
            ))}
          </div>

          <div style={{display:'flex',alignItems:'center',gap:14}}>
            <Link href="/login" className="neo-link" style={{fontSize:13,color:'rgba(237,233,254,.42)'}}>
              Connexion
            </Link>
            <Link href="/signup" className="neo-link neo-glow" style={{
              display:'flex',alignItems:'center',gap:7,
              fontSize:13,fontWeight:800,fontFamily:'"Syne",sans-serif',
              padding:'9px 22px',borderRadius:10,
              background:CTA_GRAD,color:'#fff', letterSpacing:.4,
            }}>
              Essai gratuit <ArrowRight style={{width:13,height:13}}/>
            </Link>
          </div>
        </nav>

        {/* ════════════════════════════════════════════════════ HERO ═══ */}
        <section style={{
          position:'relative',zIndex:1,
          minHeight:'100vh',display:'flex',alignItems:'center',justifyContent:'center',
          paddingTop:80,
        }}>
          {/* Halo héro */}
          <div style={{position:'absolute',inset:0,pointerEvents:'none',
            background:'radial-gradient(ellipse 80% 60% at 50% 36%, rgba(204,61,0,.08) 0%, rgba(0,229,204,.03) 45%, transparent 75%)',
          }}/>

          <div style={{textAlign:'center',maxWidth:840,padding:'0 24px',position:'relative',zIndex:1}}>
            {/* Logo */}
            <div className="neo-float neo-fade" style={{display:'flex',justifyContent:'center',marginBottom:32,animationDelay:'.1s'}}>
              <div className="neo-glow" style={{
                padding:'22px 24px',borderRadius:'50%',
                background:'rgba(204,61,0,.07)',
                border:'1px solid rgba(255,77,0,.2)',
                display:'inline-flex',alignItems:'center',justifyContent:'center',
              }}>
                <NeoLogo size={110} color="#FF9A6C"/>
              </div>
            </div>

            {/* Badge */}
            <div className="neo-fade" style={{animationDelay:'.2s'}}>
              <div style={{display:'inline-flex',alignItems:'center',gap:8,padding:'6px 18px',borderRadius:30,background:'rgba(255,77,0,.08)',border:'1px solid rgba(255,77,0,.22)',marginBottom:24}}>
                <Sparkles style={{width:12,height:12,color:'#FF9A6C'}}/>
                <span style={{fontSize:11,color:'#FF9A6C',fontWeight:700,letterSpacing:2,textTransform:'uppercase',fontFamily:'"Syne",sans-serif'}}>
                  Propulsé par DeepSeek AI · Conçu pour l&apos;Afrique
                </span>
              </div>
            </div>

            {/* Headline */}
            <div className="neo-fade" style={{animationDelay:'.3s'}}>
              <h1 style={{
                fontFamily:'"Syne",sans-serif',
                fontSize:'clamp(38px,7.5vw,82px)',
                fontWeight:900,lineHeight:1.04,letterSpacing:-1,
                color:'#F5F0FF',marginBottom:20,
              }}>
                L&apos;IA qui vend<br/>
                <span style={{
                  background:'linear-gradient(to right, #FF9A6C, #00E5CC)',
                  WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent',
                  filter:'drop-shadow(0 0 30px rgba(167,139,250,.3))',
                }}>
                  pendant que vous dormez
                </span>
              </h1>
            </div>

            {/* Sub */}
            <div className="neo-fade" style={{animationDelay:'.4s'}}>
              <p style={{fontSize:18,color:'rgba(237,233,254,.46)',maxWidth:570,margin:'0 auto 36px',lineHeight:1.75}}>
                Votre assistant WhatsApp IA répond, relance et convertit vos clients
                — 24h/24, avec votre voix, vos prix, votre secteur.
              </p>
            </div>

            {/* CTAs */}
            <div className="neo-fade" style={{animationDelay:'.5s',display:'flex',gap:14,justifyContent:'center',flexWrap:'wrap',marginBottom:18}}>
              <Link
                href="/signup"
                className="neo-link neo-glow"
                style={{
                  display:'inline-flex',alignItems:'center',gap:9,
                  padding:'15px 34px',borderRadius:14,
                  background:CTA_GRAD,color:'#fff',
                  fontWeight:900,fontSize:15,fontFamily:'"Syne",sans-serif',
                  letterSpacing:.4,
                }}
                onMouseEnter={e=>(e.currentTarget as HTMLElement).style.background=CTA_GRAD_HOVER}
                onMouseLeave={e=>(e.currentTarget as HTMLElement).style.background=CTA_GRAD}
              >
                Démarrer gratuitement <ArrowRight style={{width:16,height:16}}/>
              </Link>
              <a href="#demo" className="neo-link" style={{
                display:'inline-flex',alignItems:'center',
                padding:'15px 28px',borderRadius:14,
                border:'1px solid rgba(255,77,0,.2)',
                color:'rgba(237,233,254,.58)',fontSize:15,
                backdropFilter:'blur(8px)',
              }}>
                Voir la démo
              </a>
            </div>
            <p className="neo-fade" style={{fontSize:12,color:'rgba(255,255,255,.2)',animationDelay:'.6s'}}>
              ✓ 14 jours gratuits &nbsp;·&nbsp; ✓ Sans carte bancaire &nbsp;·&nbsp; ✓ Installation 30 secondes
            </p>

            {/* Stats */}
            <div className="neo-fade" style={{
              display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:12,
              maxWidth:700,margin:'52px auto 0',animationDelay:'.7s',
            }}>
              {STATS.map(({v,l})=>(
                <div key={l} style={{
                  borderRadius:14,padding:'17px 10px',
                  background:'rgba(204,61,0,.06)',
                  border:'1px solid rgba(255,77,0,.14)',
                  backdropFilter:'blur(10px)',
                }}>
                  <div style={{fontSize:23,fontWeight:800,
                    background:'linear-gradient(to right,#FF9A6C,#00E5CC)',
                    WebkitBackgroundClip:'text',WebkitTextFillColor:'transparent',
                    fontFamily:'"Syne",sans-serif',marginBottom:5}}>{v}</div>
                  <div style={{fontSize:11,color:'rgba(237,233,254,.36)'}}>{l}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Scroll indicator */}
          <div style={{position:'absolute',bottom:28,left:'50%',transform:'translateX(-50%)',opacity:.22}}>
            <ChevronDown className="neo-bounce" style={{width:20,height:20,color:'#FF9A6C'}}/>
          </div>
        </section>

        {/* ══════════════════════════════════════════════ FEATURES ══════ */}
        <section id="features" style={{position:'relative',zIndex:1,padding:'110px 24px'}}>
          <div style={{maxWidth:1100,margin:'0 auto'}}>
            <div style={{textAlign:'center',marginBottom:66}}>
              <div style={PILL}>Fonctionnalités</div>
              <h2 style={{fontFamily:'"Syne",sans-serif',fontSize:44,fontWeight:900,color:'#F5F0FF',marginBottom:12}}>
                Pourquoi NéoBot ?
              </h2>
              <p style={{fontSize:16,color:'rgba(237,233,254,.36)',maxWidth:500,margin:'0 auto'}}>
                Tout ce dont vous avez besoin pour vendre plus, dormir mieux et ravir vos clients.
              </p>
            </div>
            <div style={{display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:18}}>
              {FEATURES.map(({I,t,d})=>(
                <div key={t} style={{...CARD_BASE}}
                  onMouseEnter={e=>hoverCard(e.currentTarget as HTMLElement,true)}
                  onMouseLeave={e=>hoverCard(e.currentTarget as HTMLElement,false)}>
                  <div style={{width:42,height:42,borderRadius:12,background:'rgba(204,61,0,.12)',border:'1px solid rgba(255,77,0,.22)',display:'flex',alignItems:'center',justifyContent:'center',marginBottom:18}}>
                    <I style={{width:18,height:18,color:'#FF9A6C'}}/>
                  </div>
                  <h3 style={{fontFamily:'"Syne",sans-serif',fontWeight:700,fontSize:17,color:'#F5F0FF',marginBottom:8}}>{t}</h3>
                  <p style={{fontSize:13,color:'rgba(237,233,254,.42)',lineHeight:1.65,margin:0}}>{d}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ════════════════════════════════════════════════ DEMO ════════ */}
        <section id="demo" style={{position:'relative',zIndex:1,padding:'110px 24px'}}>
          <div style={{
            position:'absolute',inset:0,pointerEvents:'none',
            background:'radial-gradient(ellipse 55% 55% at 50% 50%, rgba(204,61,0,.05) 0%, transparent 70%)',
          }}/>
          <div style={{maxWidth:1100,margin:'0 auto',display:'grid',gridTemplateColumns:'1fr 1fr',gap:64,alignItems:'center',position:'relative',zIndex:1}}>
            <div>
              <div style={PILL}>Démo en direct</div>
              <h2 style={{fontFamily:'"Syne",sans-serif',fontSize:42,fontWeight:900,color:'#F5F0FF',marginBottom:20,lineHeight:1.1}}>
                Votre bot,<br/>
                <span style={{background:'linear-gradient(to right,#FF9A6C,#00E5CC)',WebkitBackgroundClip:'text',WebkitTextFillColor:'transparent'}}>
                  votre style de vente
                </span>
              </h2>
              <p style={{fontSize:16,color:'rgba(237,233,254,.46)',marginBottom:28,lineHeight:1.72}}>
                NéoBot s&apos;adapte à votre secteur. Donnez-lui vos informations et il parle
                exactement comme vous le feriez — en mieux.
              </p>
              <div style={{display:'flex',flexDirection:'column',gap:14}}>
                {[
                  'Répond avec vos prix et menus exacts',
                  'Gère les objections et relance automatiquement',
                  "Escalade vers vous si le client est urgent",
                  'Français, anglais, dialectes locaux',
                ].map(t=>(
                  <div key={t} style={{display:'flex',alignItems:'center',gap:12}}>
                    <CheckCircle style={{width:17,height:17,color:'#00E5CC',flexShrink:0}}/>
                    <span style={{fontSize:14,color:'rgba(237,233,254,.66)'}}>{t}</span>
                  </div>
                ))}
              </div>
            </div>
            <ChatDemo/>
          </div>
        </section>

        {/* ══════════════════════════════════════════ USE CASES ═════════ */}
        <section id="use-cases" style={{position:'relative',zIndex:1,padding:'110px 24px'}}>
          <div style={{maxWidth:1100,margin:'0 auto'}}>
            <div style={{textAlign:'center',marginBottom:58}}>
              <h2 style={{fontFamily:'"Syne",sans-serif',fontSize:44,fontWeight:900,color:'#F5F0FF',marginBottom:12}}>
                Pour tous les secteurs
              </h2>
              <p style={{fontSize:16,color:'rgba(237,233,254,.36)'}}>
                NéoBot s&apos;installe en moins de 5 minutes dans votre activité.
              </p>
            </div>
            <div style={{display:'grid',gridTemplateColumns:'repeat(6,1fr)',gap:14}}>
              {USE_CASES.map(({ic,t,d})=>(
                <div key={t} style={{
                  borderRadius:18,padding:'22px 14px',textAlign:'center',
                  background:'rgba(204,61,0,.04)',
                  border:'1px solid rgba(255,77,0,.1)',
                  transition:'border-color .2s, transform .2s, box-shadow .2s',
                }}
                  onMouseEnter={e=>{(e.currentTarget as HTMLElement).style.borderColor='rgba(34,211,238,.3)';(e.currentTarget as HTMLElement).style.transform='translateY(-4px)';(e.currentTarget as HTMLElement).style.boxShadow='0 8px 32px rgba(0,229,204,.1)'}}
                  onMouseLeave={e=>{(e.currentTarget as HTMLElement).style.borderColor='rgba(255,77,0,.1)';(e.currentTarget as HTMLElement).style.transform='none';(e.currentTarget as HTMLElement).style.boxShadow='none'}}>
                  <div style={{fontSize:30,marginBottom:12}}>{ic}</div>
                  <div style={{fontSize:13,fontWeight:700,color:'#FFF0E8',fontFamily:'"Syne",sans-serif',marginBottom:6}}>{t}</div>
                  <div style={{fontSize:11,color:'rgba(237,233,254,.32)',lineHeight:1.55}}>{d}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ═══════════════════════════════════════ TESTIMONIALS ═════════ */}
        <section style={{position:'relative',zIndex:1,padding:'110px 24px'}}>
          <div style={{maxWidth:1100,margin:'0 auto'}}>
            <div style={{textAlign:'center',marginBottom:58}}>
              <h2 style={{fontFamily:'"Syne",sans-serif',fontSize:44,fontWeight:900,color:'#F5F0FF'}}>
                Ce qu&apos;ils en disent
              </h2>
            </div>
            <div style={{display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:18}}>
              {TESTIMONIALS.map(({n,r,q,s})=>(
                <div key={n} style={{...CARD_BASE}}
                  onMouseEnter={e=>hoverCard(e.currentTarget as HTMLElement,true)}
                  onMouseLeave={e=>hoverCard(e.currentTarget as HTMLElement,false)}>
                  <div style={{display:'flex',gap:3,marginBottom:16}}>
                    {Array.from({length:s}).map((_,i)=>(
                      <Star key={i} style={{width:13,height:13,fill:'#FDE68A',color:'#FDE68A'}}/>
                    ))}
                  </div>
                  <p style={{fontSize:14,color:'rgba(237,233,254,.56)',lineHeight:1.72,marginBottom:20}}>&ldquo;{q}&rdquo;</p>
                  <div style={{display:'flex',alignItems:'center',gap:12}}>
                    <div style={{width:36,height:36,borderRadius:'50%',background:'rgba(204,61,0,.18)',border:'1px solid rgba(255,77,0,.3)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:14,fontWeight:800,color:'#FF9A6C',fontFamily:'"Syne",sans-serif'}}>
                      {n[0]}
                    </div>
                    <div>
                      <div style={{fontSize:14,fontWeight:700,color:'#FFF0E8',fontFamily:'"Syne",sans-serif'}}>{n}</div>
                      <div style={{fontSize:12,color:'rgba(237,233,254,.3)'}}>{r}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ═════════════════════════════════════════════════ FAQ ════════ */}
        <section id="faq" style={{position:'relative',zIndex:1,padding:'110px 24px'}}>
          <div style={{maxWidth:680,margin:'0 auto'}}>
            <div style={{textAlign:'center',marginBottom:52}}>
              <h2 style={{fontFamily:'"Syne",sans-serif',fontSize:44,fontWeight:900,color:'#F5F0FF'}}>
                Questions fréquentes
              </h2>
            </div>
            {FAQS.map(({q,a})=><FaqItem key={q} q={q} a={a}/>)}
          </div>
        </section>

        {/* ══════════════════════════════════════════ CTA FINAL ═════════ */}
        <section style={{position:'relative',zIndex:1,padding:'130px 24px'}}>
          <div style={{position:'absolute',inset:0,pointerEvents:'none',
            background:'radial-gradient(ellipse 55% 55% at 50% 50%, rgba(204,61,0,.09) 0%, rgba(0,229,204,.03) 40%, transparent 70%)',
          }}/>
          <div style={{maxWidth:640,margin:'0 auto',textAlign:'center',position:'relative',zIndex:1}}>
            <div style={{display:'flex',justifyContent:'center',marginBottom:28}}>
              <div className="neo-glow neo-float" style={{
                padding:'22px 24px',borderRadius:'50%',
                background:'rgba(204,61,0,.08)',
                border:'1px solid rgba(255,77,0,.2)',
                display:'inline-flex',alignItems:'center',justifyContent:'center',
              }}>
                <NeoLogo size={60} color="#FF9A6C"/>
              </div>
            </div>
            <h2 style={{fontFamily:'"Syne",sans-serif',fontSize:46,fontWeight:900,color:'#F5F0FF',marginBottom:18,lineHeight:1.08}}>
              Prêt à transformer<br/>votre WhatsApp ?
            </h2>
            <p style={{fontSize:17,color:'rgba(237,233,254,.46)',marginBottom:36,lineHeight:1.75}}>
              Rejoignez des milliers d&apos;entreprises africaines<br/>qui font déjà confiance à NéoBot.
            </p>
            <Link href="/signup" className="neo-link neo-glow" style={{
              display:'inline-flex',alignItems:'center',gap:10,
              padding:'17px 42px',borderRadius:14,
              background:CTA_GRAD,color:'#fff',
              fontWeight:900,fontSize:16,fontFamily:'"Syne",sans-serif',
              letterSpacing:.4,
            }}>
              Démarrer gratuitement <ArrowRight style={{width:18,height:18}}/>
            </Link>
            <p style={{fontSize:12,color:'rgba(255,255,255,.16)',marginTop:18}}>
              ✓ Sans carte &nbsp;·&nbsp; ✓ 14 jours gratuits &nbsp;·&nbsp; ✓ Annulation immédiate
            </p>
          </div>
        </section>

        {/* ═══════════════════════════════════════════════ FOOTER ═══════ */}
        <footer style={{borderTop:'1px solid rgba(255,77,0,.1)',padding:'60px 24px',position:'relative',zIndex:1}}>
          <div style={{maxWidth:1100,margin:'0 auto'}}>
            <div style={{display:'grid',gridTemplateColumns:'2fr 1fr 1fr 1fr',gap:44,marginBottom:48}}>
              <div>
                <div style={{display:'flex',alignItems:'center',gap:10,marginBottom:16}}>
                  <NeoLogo size={28} color="#FF9A6C"/>
                  <span style={{fontFamily:'"Syne",sans-serif',fontWeight:900,fontSize:17,color:'#FFF0E8',letterSpacing:3,textTransform:'uppercase'}}>
                    NEOBOT
                  </span>
                </div>
                <p style={{fontSize:13,color:'rgba(237,233,254,.27)',lineHeight:1.7,margin:0}}>
                  L&apos;assistant IA WhatsApp conçu pour les entreprises africaines.
                </p>
                <p style={{fontSize:12,color:'rgba(167,139,250,.45)',marginTop:10,fontStyle:'italic'}}>
                  L&apos;AI à votre service
                </p>
              </div>
              {([
                ['Produit',    [['Fonctionnalités','#'],['Roadmap','#'],['API','#']]],
                ['Support',    [['Documentation','#'],['Contact','mailto:contact@neobot-ai.com'],['WhatsApp','#']]],
                ['Entreprise', [['À propos','#'],['CGU','/legal?tab=cgu'],['Confidentialité','/legal?tab=confidentialite'],['Mentions légales','/legal?tab=mentions']]],
              ] as [string,[string,string][]][]).map(([title,links])=>(
                <div key={title}>
                  <h4 style={{fontFamily:'"Syne",sans-serif',fontWeight:700,fontSize:13,color:'#FFF0E8',marginBottom:16}}>{title}</h4>
                  <ul style={{listStyle:'none',margin:0,padding:0,display:'flex',flexDirection:'column',gap:10}}>
                    {links.map(([label,href])=>(
                      <li key={label}>
                        <a href={href} className="neo-link" style={{fontSize:13,color:'rgba(237,233,254,.28)',transition:'color .2s'}}
                          onMouseEnter={e=>(e.currentTarget as HTMLElement).style.color='rgba(167,139,250,.85)'}
                          onMouseLeave={e=>(e.currentTarget as HTMLElement).style.color='rgba(237,233,254,.28)'}>
                          {label}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
            <div style={{borderTop:'1px solid rgba(255,255,255,.05)',paddingTop:24,display:'flex',justifyContent:'space-between',alignItems:'center'}}>
              <p style={{fontSize:13,color:'rgba(255,255,255,.18)',margin:0}}>© 2026 NéoBot. Tous droits réservés.</p>
              <p style={{fontSize:13,color:'rgba(255,255,255,.12)',margin:0}}>Propulsé par DeepSeek AI · Conçu pour les PME africaines</p>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
}

