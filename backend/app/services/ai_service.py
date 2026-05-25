import json
import uuid
from typing import Optional
from app.core.config import settings
from app.schemas.schemas import SymptomAnalysisRequest, SymptomAnalysisResponse, ChatResponse
from app.db.cache import cache

SYMPTOM_SYSTEM = """You are a medical AI assistant. Analyze symptoms and respond ONLY in valid JSON:
{
  "suggested_conditions": [{"name": "...", "probability": "low/medium/high", "description": "..."}],
  "recommended_specialist": "Specialist type",
  "urgency_level": "low/medium/high/emergency",
  "advice": "What the patient should do",
  "disclaimer": "This is not a medical diagnosis. Consult a real doctor."
}"""

CHAT_SYSTEM = """You are a helpful hospital assistant chatbot. Help patients with appointments,
doctor info, and general health queries. Never diagnose. Keep responses brief and empathetic."""

SYMPTOM_MAP = {
    "chest pain": ("Cardiologist", "high", [("Angina", "high"), ("Myocardial Infarction", "medium")]),
    "heart": ("Cardiologist", "high", [("Cardiac Issue", "medium")]),
    "headache": ("Neurologist", "low", [("Tension Headache", "high"), ("Migraine", "medium")]),
    "head": ("Neurologist", "low", [("Neurological Condition", "low")]),
    "fever": ("General Physician", "medium", [("Viral Infection", "high"), ("Bacterial Infection", "medium")]),
    "cough": ("Pulmonologist", "low", [("Upper Respiratory Infection", "high"), ("Bronchitis", "medium")]),
    "skin": ("Dermatologist", "low", [("Dermatitis", "medium"), ("Eczema", "low")]),
    "rash": ("Dermatologist", "low", [("Contact Dermatitis", "high")]),
    "stomach": ("Gastroenterologist", "medium", [("Gastritis", "medium"), ("IBS", "low")]),
    "abdominal": ("Gastroenterologist", "medium", [("Gastritis", "medium")]),
    "joint": ("Orthopedic Surgeon", "low", [("Arthritis", "medium"), ("Joint Strain", "low")]),
    "child": ("Pediatrician", "medium", [("Common Childhood Illness", "medium")]),
    "anxiety": ("Psychiatrist", "low", [("Anxiety Disorder", "medium")]),
    "depression": ("Psychiatrist", "medium", [("Clinical Depression", "medium")]),
}


class AIService:

    @staticmethod
    async def analyze_symptoms(request: SymptomAnalysisRequest) -> SymptomAnalysisResponse:
        cache_key = f"ai:symptoms:{hash(tuple(sorted(request.symptoms)))}"
        cached = await cache.get(cache_key)
        if cached:
            return SymptomAnalysisResponse(**cached)

        if settings.ANTHROPIC_API_KEY:
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                prompt = (f"Symptoms: {', '.join(request.symptoms)}\n"
                          f"Age: {request.age or 'unknown'}\n"
                          f"Gender: {request.gender or 'unknown'}\n"
                          f"History: {request.medical_history or 'none'}")
                msg = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    system=SYMPTOM_SYSTEM,
                    messages=[{"role": "user", "content": prompt}],
                )
                data = json.loads(msg.content[0].text)
                response = SymptomAnalysisResponse(**data)
                await cache.set(cache_key, response.model_dump(), ttl=3600)
                return response
            except Exception:
                pass

        return AIService._rule_based_analysis(request.symptoms)

    @staticmethod
    def _rule_based_analysis(symptoms: list) -> SymptomAnalysisResponse:
        specialist = "General Physician"
        urgency = "low"
        conditions = [{"name": "General Condition", "probability": "medium",
                       "description": "Please consult a physician for proper evaluation"}]

        for symptom in symptoms:
            s_lower = symptom.lower()
            for keyword, (spec, urg, conds) in SYMPTOM_MAP.items():
                if keyword in s_lower:
                    specialist = spec
                    urgency = urg
                    conditions = [{"name": c, "probability": p,
                                   "description": f"Possible condition related to: {symptom}"}
                                  for c, p in conds]
                    break

        return SymptomAnalysisResponse(
            suggested_conditions=conditions,
            recommended_specialist=specialist,
            urgency_level=urgency,
            advice=f"Schedule an appointment with a {specialist} for proper evaluation of your symptoms.",
            disclaimer="This is an AI-generated suggestion, NOT a medical diagnosis. Always consult a licensed healthcare professional.",
        )

    @staticmethod
    async def chat(message: str, conversation_id: Optional[str] = None) -> ChatResponse:
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        history_key = f"chat:{conversation_id}"
        history = await cache.get(history_key) or []
        history.append({"role": "user", "content": message})

        if settings.ANTHROPIC_API_KEY:
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                resp = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=512,
                    system=CHAT_SYSTEM,
                    messages=history[-10:],
                )
                reply = resp.content[0].text
            except Exception:
                reply = AIService._fallback_reply(message)
        else:
            reply = AIService._fallback_reply(message)

        history.append({"role": "assistant", "content": reply})
        await cache.set(history_key, history, ttl=3600)
        return ChatResponse(reply=reply, conversation_id=conversation_id)

    @staticmethod
    def _fallback_reply(message: str) -> str:
        msg = message.lower()
        if "appointment" in msg:
            return "You can book, view, or cancel appointments from the Appointments section in your dashboard."
        if "doctor" in msg:
            return "Browse available doctors in the Doctors section. Filter by specialty to find the right one."
        if "emergency" in msg:
            return "For emergencies, please call 112 immediately or go to our Emergency Department."
        if "record" in msg or "report" in msg:
            return "Your medical records are available in the Medical Records section of your dashboard."
        return "I'm here to help! Ask me about appointments, doctors, medical records, or hospital services."
