from fastapi import APIRouter
import random

router = APIRouter()

@router.get("/")
async def get_insights():
    # Mock insights for now
    insights = [
        {
            "id": 1,
            "type": "tip",
            "title": "Oportunidade de Fim de Semana",
            "content": "Seu concorrente principal aumentou as tarifas em 15% para o próximo sábado. Considere manter sua tarifa ou aumentar levemente para maximizar o RevPAR.",
            "priority": "high"
        },
        {
            "id": 2,
            "type": "alert",
            "title": "Queda de braço tarifária",
            "content": "Detectamos uma redução agressiva de preços no Hotel X para o período de feriado. Monitore a ocupação.",
            "priority": "medium"
        },
        {
            "id": 3,
            "type": "info",
            "title": "Tendência de Mercado",
            "content": "A procura por hotéis na sua região cresceu 10% nos últimos 7 dias para buscas de 2 adultos.",
            "priority": "low"
        }
    ]
    return insights
