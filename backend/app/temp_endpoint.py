
@app.post("/api/tenants/{tenant_id}/whatsapp/message")
async def process_whatsapp_message(
    tenant_id: int,
    request: dict,
    db: Session = Depends(get_db)
):
    from services.ai_service import generate_ai_response
    
    phone = request.get("phone")
    message_text = request.get("message")
    
    # Récupérer le tenant
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Trouver ou créer la conversation
    conversation = db.query(Conversation).filter(
        Conversation.tenant_id == tenant_id,
        Conversation.customer_phone == phone
    ).first()
    
    if not conversation:
        conversation = Conversation(
            tenant_id=tenant_id,
            customer_phone=phone,
            customer_name=f"Client {phone[-4:]}",
            status="active"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    # Récupérer l'historique
    history = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.created_at.desc()).limit(5).all()
    
    history_list = [
        {"content": msg.content, "is_ai": msg.is_ai}
        for msg in reversed(history)
    ]
    
    # Enregistrer le message client
    incoming_msg = Message(
        conversation_id=conversation.id,
        content=message_text,
        direction="incoming",
        is_ai=False
    )
    db.add(incoming_msg)
    db.flush()
    
    # Générer réponse IA
    ai_response = await generate_ai_response(
        message=message_text,
        business_type=tenant.business_type or "service",
        business_name=tenant.name,
        conversation_history=history_list
    )
    
    # Enregistrer la réponse
    outgoing_msg = Message(
        conversation_id=conversation.id,
        content=ai_response,
        direction="outgoing",
        is_ai=True
    )
    db.add(outgoing_msg)
    
    # Mettre à jour compteurs
    tenant.messages_used += 2
    
    db.commit()
    
    return {"response": ai_response}
