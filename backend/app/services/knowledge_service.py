"""
Service de connaissance temporairement désactivé
"""

class KnowledgeService:
    def __init__(self, db):
        self.db = db
    
    def get_response(self, message, tenant_id=None):
        return None
