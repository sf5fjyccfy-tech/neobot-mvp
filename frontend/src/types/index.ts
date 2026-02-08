export interface Tenant {
  id: number;
  name: string;
  email: string;
  phone: string;
  business_type: 'restaurant' | 'boutique' | 'service' | 'ecommerce';
  plan: 'basique' | 'standard' | 'pro';
  whatsapp_connected: boolean;
  messages_used: number;
  messages_limit: number;
  is_trial: boolean;
  trial_ends_at?: string;
  created_at: string;
}

export interface Conversation {
  id: number;
  tenant_id: number;
  customer_phone: string;
  customer_name?: string;
  channel: 'whatsapp';
  status: 'active' | 'closed' | 'pending';
  last_message_at: string;
  message_count: number;
}

export interface Message {
  id: number;
  conversation_id: number;
  content: string;
  direction: 'incoming' | 'outgoing';
  is_ai: boolean;
  created_at: string;
}

export interface Analytics {
  period: {
    start: string;
    end: string;
    days: number;
  };
  daily_data: DailyAnalytics[];
  summary: {
    total_messages: number;
    total_conversations: number;
    avg_response_rate: number;
    avg_daily_messages: number;
    busiest_day: string;
  };
}

export interface DailyAnalytics {
  date: string;
  messages: {
    total: number;
    incoming: number;
    outgoing: number;
  };
  conversations: {
    new: number;
  };
  response_rate: number;
}

export interface PlanConfig {
  name: string;
  price_fcfa: number;
  whatsapp_messages: number;
  other_platforms_messages: number;
  channels: number;
  features: string[];
  trial_days: number;
}
