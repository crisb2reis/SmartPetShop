import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.agents import tools as agent_tools

logger = logging.getLogger("smartpetshop.agent")

SYSTEM_INSTRUCTION = """Você é o Rex 🐾, o assistente virtual inteligente e acolhedor do SmartPetShop!
Sua missão é atender clientes e tutores com simpatia e agilidade:
1. Informar sobre serviços oferecidos (Banho, Tosa, Consultas Veterinárias, Vacinas) e seus respectivos preços.
2. Consultar horários disponíveis na agenda para qualquer data informada pelo cliente.
3. Ajudar o tutor a agendar serviços para seus pets de forma conversacional e prática.

Diretrizes importantes:
- Responda sempre em português do Brasil, de maneira atenciosa, cordial e clara.
- Sempre utilize as ferramentas disponíveis para obter dados atualizados antes de responder sobre preços, horários ou agendamentos.
- Ao agendar, certifique-se de coletar ou confirmar o telefone do tutor, o nome do pet, o serviço desejado e o horário escolhido.
- Seja proativo sugerindo horários próximos caso o horário desejado esteja ocupado.
"""

# Definições de ferramentas para o Gemini
TOOL_DEFINITIONS = [
    {
        "name": "list_services",
        "description": "Retorna a lista de serviços ativos do Pet Shop (Banho, Tosa, Veterinário, Vacinas), preços e durações.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "category": {
                    "type": "STRING",
                    "description": "Categoria opcional para filtro: Banho, Tosa, Veterinário, Vacinação"
                }
            }
        }
    },
    {
        "name": "check_availability",
        "description": "Consulta os horários livres na agenda do Pet Shop para determinado serviço em uma data específica (YYYY-MM-DD).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "service_name": {
                    "type": "STRING",
                    "description": "Nome do serviço desejado (ex: Banho e Tosa, Consulta Veterinária)"
                },
                "target_date": {
                    "type": "STRING",
                    "description": "Data no formato YYYY-MM-DD (ex: 2026-11-20)"
                }
            },
            "required": ["service_name", "target_date"]
        }
    },
    {
        "name": "get_tutor_and_pets",
        "description": "Busca os pets cadastrados para um tutor utilizando seu telefone/WhatsApp.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "tutor_phone": {
                    "type": "STRING",
                    "description": "Número de telefone ou WhatsApp do tutor (ex: 11999998888)"
                }
            },
            "required": ["tutor_phone"]
        }
    },
    {
        "name": "schedule_appointment",
        "description": "Realiza o agendamento de um serviço para o pet de um tutor em determinada data e hora.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "tutor_phone": {
                    "type": "STRING",
                    "description": "Telefone do tutor cadastrado"
                },
                "pet_name": {
                    "type": "STRING",
                    "description": "Nome do pet que receberá o atendimento"
                },
                "service_name": {
                    "type": "STRING",
                    "description": "Nome do serviço a ser realizado"
                },
                "date_time_str": {
                    "type": "STRING",
                    "description": "Data e hora no formato ISO (ex: 2026-11-20T10:00:00)"
                },
                "notes": {
                    "type": "STRING",
                    "description": "Observações adicionais ou preferências"
                }
            },
            "required": ["tutor_phone", "pet_name", "service_name", "date_time_str"]
        }
    }
]


async def execute_tool(
    db: AsyncSession,
    tool_name: str,
    args: Dict[str, Any]
) -> Dict[str, Any]:
    """Despacha a chamada da ferramenta para a função Python correspondente."""
    try:
        if tool_name == "list_services":
            return {"services": await agent_tools.list_services_tool(db, category=args.get("category"))}
        elif tool_name == "check_availability":
            return await agent_tools.check_availability_tool(
                db,
                service_name=args["service_name"],
                target_date=args["target_date"]
            )
        elif tool_name == "get_tutor_and_pets":
            return await agent_tools.get_tutor_and_pets_tool(db, tutor_phone=args["tutor_phone"])
        elif tool_name == "schedule_appointment":
            return await agent_tools.schedule_appointment_tool(
                db,
                tutor_phone=args["tutor_phone"],
                pet_name=args["pet_name"],
                service_name=args["service_name"],
                date_time_str=args["date_time_str"],
                notes=args.get("notes")
            )
        else:
            return {"error": f"Ferramenta desconhecida: {tool_name}"}
    except Exception as e:
        logger.error(f"Erro ao executar tool {tool_name}: {e}", exc_info=True)
        return {"error": f"Falha na execução da ferramenta {tool_name}: {str(e)}"}


class ChatbotAgent:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.client = None
        if self.api_key and self.api_key != "your_gemini_api_key_here":
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Não foi possível inicializar o cliente Google GenAI: {e}")

    async def run(
        self,
        db: AsyncSession,
        user_message: str,
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Processa a mensagem do usuário usando o modelo Gemini com Function Calling.
        Caso o Gemini não esteja configurado, utiliza o motor inteligente de fallback local.
        """
        tools_called: List[Dict[str, Any]] = []

        if not self.client:
            return await self._fallback_response(db, user_message, conversation_history)

        try:
            from google.genai import types

            # Formata histórico
            contents: List[types.Content] = []
            for msg in conversation_history:
                role = "user" if msg["role"] == "user" else "model"
                contents.append(types.Content(role=role, parts=[types.Part.from_text(msg["content"])]))

            # Adiciona mensagem atual
            contents.append(types.Content(role="user", parts=[types.Part.from_text(user_message)]))

            # Configuração com Tools e System Instruction
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.3,
                tools=[{"function_declarations": TOOL_DEFINITIONS}],
            )

            # Primeira chamada ao Gemini
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=config,
            )

            # Loop de execução de ferramentas (até 3 iterações)
            max_turns = 3
            current_turn = 0

            while response.function_calls and current_turn < max_turns:
                current_turn += 1
                function_call = response.function_calls[0]
                fn_name = function_call.name
                fn_args = dict(function_call.args) if function_call.args else {}

                # Executa no banco local
                tool_result = await execute_tool(db, fn_name, fn_args)
                tools_called.append({
                    "tool": fn_name,
                    "args": fn_args,
                    "result": tool_result
                })

                # Adiciona a resposta da tool ao histórico da conversa
                contents.append(response.candidates[0].content)
                contents.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_function_response(
                                name=fn_name,
                                response={"result": tool_result}
                            )
                        ]
                    )
                )

                # Gera nova resposta considerando o resultado da ferramenta
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents,
                    config=config,
                )

            reply_text = response.text or "Olá! Como posso ajudar você e seu pet hoje?"
            return {
                "reply": reply_text,
                "tools_called": tools_called
            }

        except Exception as e:
            logger.error(f"Erro na chamada do Gemini API: {e}", exc_info=True)
            return await self._fallback_response(db, user_message, conversation_history, error_detail=str(e))

    async def _fallback_response(
        self,
        db: AsyncSession,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        error_detail: Optional[str] = None
    ) -> Dict[str, Any]:
        """Motor inteligente local para respostas imediatas e suporte offline."""
        msg = user_message.lower()
        tools_called: List[Dict[str, Any]] = []

        if any(w in msg for w in ["serviço", "servico", "preço", "preco", "valor", "banho", "tosa", "consulta"]):
            services = await agent_tools.list_services_tool(db)
            tools_called.append({"tool": "list_services", "result": services})
            if services:
                lines = [f"🐾 **{s['name']}** ({s['category']}): R$ {s['price']:.2f} (~{s['duration_minutes']} min)" for s in services]
                reply = "Aqui estão os nossos serviços disponíveis:\n\n" + "\n".join(lines) + "\n\nQual deles você gostaria de agendar para o seu pet?"
            else:
                reply = "Olá! Nosso catálogo de serviços está sendo preparado. Em instantes teremos Banho, Tosa e Consultas disponíveis!"
        elif any(w in msg for w in ["olá", "ola", "oi", "bom dia", "boa tarde", "boa noite"]):
            reply = "Olá! Eu sou o Rex 🐾, assistente virtual do SmartPetShop. Posso te ajudar a consultar nossos serviços e valores, verificar horários livres ou agendar um atendimento para o seu pet. Como posso ajudar?"
        else:
            reply = "Entendido! Posso consultar nossos serviços e valores, verificar horários vagos na agenda e agendar o atendimento para seu pet. Deseja ver a lista de serviços disponíveis?"

        return {
            "reply": reply,
            "tools_called": tools_called
        }


chatbot_agent = ChatbotAgent()

