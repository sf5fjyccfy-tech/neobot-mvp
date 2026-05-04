-- Migration 013: Unique constraint on (tenant_id, customer_phone) in conversations
-- Date: 2026-05-03
-- Purpose: Prevent duplicate conversations for the same customer per tenant.
--          Merges existing duplicates before adding the constraint.

-- Step 1: For each duplicate group, keep the conversation with the highest id
-- (most recent) and reassign all messages from older ones to it.
DO $$
DECLARE
    dup RECORD;
    keep_id INTEGER;
    old_id INTEGER;
BEGIN
    -- Find all (tenant_id, customer_phone) pairs that have more than one conversation
    FOR dup IN
        SELECT tenant_id, customer_phone
        FROM conversations
        GROUP BY tenant_id, customer_phone
        HAVING COUNT(*) > 1
    LOOP
        -- Identify the conversation to keep (highest id = most recent)
        SELECT MAX(id) INTO keep_id
        FROM conversations
        WHERE tenant_id = dup.tenant_id AND customer_phone = dup.customer_phone;

        -- Reassign messages and related rows from all other conversations to keep_id
        FOR old_id IN
            SELECT id FROM conversations
            WHERE tenant_id = dup.tenant_id
              AND customer_phone = dup.customer_phone
              AND id <> keep_id
        LOOP
            UPDATE messages SET conversation_id = keep_id WHERE conversation_id = old_id;
            UPDATE escalations SET conversation_id = keep_id WHERE conversation_id = old_id;
            DELETE FROM conversation_human_state WHERE conversation_id = old_id;
            DELETE FROM conversation_context WHERE conversation_id = old_id;
            DELETE FROM conversations WHERE id = old_id;
        END LOOP;
    END LOOP;
END $$;

-- Step 2: Now safe to add the unique constraint
ALTER TABLE conversations
    ADD CONSTRAINT uq_conversation_tenant_phone UNIQUE (tenant_id, customer_phone);
