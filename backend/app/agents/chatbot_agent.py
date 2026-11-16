import json
import logging
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.agents import tools as agent_tools
from app.models.chat import ChatSession, ChatMessage
from app.models.tutor import Tutor
from app.models.organization import Organization
from app.services import tutor_service

logger = logging.getLogger("smartpetshop.agent")

SYSTEM_INSTRUCTION = """Você é o Rex 🐾, o assistente virtual oficial, inteligente e afetuoso do SmartPetShop!
Sua missão é atender clientes e tutores no WhatsApp com excelência, empatia e agilidade.

🎯 Principais atribuições:
1. Apresentar os serviços do Pet Shop (Banho, Tosa, Procedimentos Adicionais, Consultas Veterinárias, Vacinação) com valores e durações atualizados.
2. Consultar horários livres na agenda e realizar agendamentos conversacionais para os pets dos clientes.
3. Consultar a Carteirinha de Vacinação Digital do pet (conforme normas do CFMV) para verificar se as vacinas estão em dia, alertar sobre vacinas vencidas/atrasadas e reforços previstos.
4. Esclarecer dúvidas sobre o calendário oficial de imunização de cães e gatos (V8/V10, Raiva, Giárdia, Tosse dos Canis, Leishmaniose, V3/V4/V5, FeLV).

⚠️ DIRETRIZES DE SEGURANÇA E REGULAMENTAÇÃO DO CFMV (MANDATÓRIO):
- Você NÃO é um médico veterinário. Em NENHUMA hipótese faça diagnósticos clínicos, prescreva medicamentos, dosagens ou receitas.
- Se o tutor relatar que o animal está doente ou apresentar sintomas (como vômito, apatia, dor, diarreia, coceira intensa, falta de apetite, febre ou ferimentos), seja extremamente acolhedor e empático. Explique com clareza que esses sintomas exigem avaliação clínica profissional presencial e ofereça-se prontamente para agendar uma Consulta Veterinária na nossa clínica.
- Mantenha sempre o foco em bem-estar animal, medicina preventiva e direcionamento responsável.

💬 ESTILO DE COMUNICAÇÃO NO WHATSAPP:
- Responda em português do Brasil, de forma acolhedora, objetiva e simpática.
- Utilize formatação nativa do WhatsApp: *negrito* para termos e nomes importantes, listas claras com marcadores (-) e emojis com moderação (🐾, 🐶, 🐱, 💉, 📅, ✨).
- Mantenha as mensagens concisas e fáceis de ler no smartphone, evitando blocos gigantes de texto.
- Se o cliente pedir expressamente para 'falar com atendente', 'humano', 'recepção' ou 'pessoa', acolha o pedido imediatamente e confirme que a equipe da recepção foi notificada para assumir a conversa.
"""

# Definições de ferramentas para o Gemini
TOOL_DEFINITIONS = [
    {
        "name": "list_services",
        "description": "Retorna a lista de serviços ativos do Pet Shop (Banho, Tosa, Veterinário, Vacinas, Adicionais), preços e durações.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "category": {
                    "type": "STRING",
                    "description": "Categoria opcional para filtro: Banho, Tosa, Veterinário, Vacinação, Adicional"
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
        "description": "Busca os dados cadastrais do tutor e seus pets vinculados utilizando seu telefone/WhatsApp.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "tutor_phone": {
                    "type": "STRING",
                    "description": "Número de telefone ou WhatsApp do tutor (ex: 11987654321)"
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
    },
    {
        "name": "get_pet_vaccination_card",
        "description": "Consulta a caderneta oficial de vacinação digital de um pet (CFMV), detalhando vacinas aplicadas, doses de reforço programadas e vacinas em atraso.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "tutor_phone": {
                    "type": "STRING",
                    "description": "Telefone ou WhatsApp do tutor do pet"
                },
                "pet_name": {
                    "type": "STRING",
                    "description": "Nome do pet a consultar (ex: Bob, Thor, Luna)"
                }
            },
            "required": ["tutor_phone", "pet_name"]
        }
    },
    {
        "name": "get_vaccine_catalog",
        "description": "Consulta o calendário sanitário oficial de vacinas para cães ou gatos (V8/V10, Raiva, Giárdia, V3/V4/V5, etc.), idade recomendada e periodicidade de reforço.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "species": {
                    "type": "STRING",
                    "description": "Espécie para consulta: CANINO, FELINO ou AMBOS"
                }
            }
        }
    }
]


async def execute_tool(
    db: AsyncSession,
    tool_name: str,
    args: Dict[str, Any]
) -> Dict[str, Any]:
    """Despacha a chamada da ferramenta para a função correspondente."""
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
        elif tool_name == "get_pet_vaccination_card":
            return await agent_tools.get_pet_vaccination_card_tool(
                db,
                tutor_phone=args["tutor_phone"],
                pet_name=args["pet_name"]
            )
        elif tool_name == "get_vaccine_catalog":
            return await agent_tools.get_vaccine_catalog_tool(
                db,
                species=args.get("species")
            )
        else:
            return {"error": f"Ferramenta desconhecida: {tool_name}"}
    except Exception as e:
        logger.error(f"Erro ao executar tool {tool_name}: {e}", exc_info=True)
        return {"error": f"Falha na execução da ferramenta {tool_name}: {str(e)}"}


# ============================================================================
# Funções de Gerenciamento de Sessão e Contexto de Conversas
# ============================================================================

async def get_or_create_whatsapp_session(
    db: AsyncSession,
    phone: str,
    tutor: Optional[Tutor] = None
) -> ChatSession:
    """Busca ou cria uma sessão de chat ativa para o canal WhatsApp específica do tutor ou telefone."""
    clean_phone = "".join(filter(str.isdigit, phone))

    if tutor:
        query = (
            select(ChatSession)
            .where(
                ChatSession.channel == "whatsapp",
                ChatSession.tutor_id == tutor.id,
                ChatSession.status.in_(["active", "human_required"])
            )
            .order_by(ChatSession.created_at.desc())
        )
        res = await db.execute(query)
        session = res.scalars().first()
        if session:
            return session
    else:
        # Quando não há tutor ainda cadastrado, busca sessão existente associada a este telefone
        query = (
            select(ChatSession)
            .join(ChatMessage, ChatMessage.session_id == ChatSession.id)
            .where(
                ChatSession.channel == "whatsapp",
                ChatSession.status.in_(["active", "human_required"]),
                ChatMessage.metadata_info["from_phone"].as_string().ilike(f"%{clean_phone}%")
            )
            .order_by(ChatSession.created_at.desc())
        )
        res = await db.execute(query)
        session = res.scalars().first()
        if session:
            return session

    # Busca tenant padrão para criar nova sessão isolada
    org_res = await db.execute(select(Organization.id).limit(1))
    tenant_id = org_res.scalar_one_or_none()

    session = ChatSession(
        tenant_id=tutor.tenant_id if tutor else tenant_id,
        tutor_id=tutor.id if tutor else None,
        channel="whatsapp",
        status="active"
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return session


async def get_session_history(
    db: AsyncSession,
    session_id: uuid.UUID,
    limit: int = 10
) -> List[Dict[str, str]]:
    """Carrega as últimas N mensagens da sessão para compor a janela de contexto."""
    query = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(query)
    messages = list(reversed(res.scalars().all()))
    return [{"role": m.role, "content": m.content} for m in messages]


async def save_chat_message(
    db: AsyncSession,
    session_id: uuid.UUID,
    role: str,
    content: str,
    metadata_info: Optional[Dict[str, Any]] = None
) -> ChatMessage:
    """Persiste a mensagem no histórico da sessão."""
    msg = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        metadata_info=metadata_info
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


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
        conversation_history: List[Dict[str, str]],
        tutor_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processa a mensagem do usuário usando o modelo Gemini com Function Calling.
        Caso o Gemini não esteja configurado, utiliza o motor inteligente de fallback local.
        """
        tools_called: List[Dict[str, Any]] = []

        if not self.client:
            return await self._fallback_response(db, user_message, conversation_history, tutor_phone=tutor_phone)

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

                # Injeta automaticamente tutor_phone se omitido pelo modelo
                if "tutor_phone" in fn_args and not fn_args["tutor_phone"] and tutor_phone:
                    fn_args["tutor_phone"] = tutor_phone

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
            return await self._fallback_response(
                db,
                user_message,
                conversation_history,
                tutor_phone=tutor_phone,
                error_detail=str(e)
            )

    async def _fallback_response(
        self,
        db: AsyncSession,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        tutor_phone: Optional[str] = None,
        error_detail: Optional[str] = None
    ) -> Dict[str, Any]:
        """Motor inteligente local em conformidade com as regras sanitárias CFMV e de atendimento."""
        msg = user_message.lower()
        tools_called: List[Dict[str, Any]] = []

        # 1. Detecção de Transbordo (Handoff para atendente humano)
        if any(w in msg for w in ["atendente", "falar com humano", "pessoa real", "humano", "recepção"]):
            return {
                "reply": "Entendido! 🙋‍♂️ Estou transferindo sua solicitação para a nossa equipe de recepção. Um atendente humano responderá aqui no seu WhatsApp em instantes!",
                "tools_called": [],
                "handoff_requested": True
            }

        # 2. Diretriz CFMV: Detecção de sintomas médicos veterinários
        symptoms = ["vômito", "vomito", "vomitando", "diarreia", "diarréia", "dor", "mancando", "febre", "ferimento", "coceira", "não come", "sem comer", "apatia", "triste"]
        if any(s in msg for s in symptoms):
            services = await agent_tools.list_services_tool(db, category="Veterinário")
            price_info = f" (R$ {services[0]['price']:.2f})" if services else ""
            reply = (
                "Poxa, sinto muito que ele não esteja se sentindo bem! 🐾🩺\n\n"
                "⚠️ *Importante:* Como assistente virtual, sigo as normas do CFMV e não posso realizar diagnósticos ou indicar medicamentos sem uma avaliação presencial.\n\n"
                f"Para garantir a segurança e a saúde dele, recomendo agendarmos uma *Consulta Veterinária*{price_info} com nosso médico veterinário responsável. "
                "Gostaria que eu verificasse os horários livres para você trazê-lo hoje ou amanhã?"
            )
            return {
                "reply": reply,
                "tools_called": []
            }

        # 3. Consulta de Vacinas / Carteirinha Digital
        if any(w in msg for w in ["vacina", "vacinas", "v8", "v10", "raiva", "reforço", "carteirinha", "caderneta", "vencida", "atrasada"]):
            # Se tiver telefone do tutor, tenta buscar os pets e a carteirinha
            if tutor_phone:
                tutor_data = await agent_tools.get_tutor_and_pets_tool(db, tutor_phone)
                tools_called.append({"tool": "get_tutor_and_pets", "result": tutor_data})

                if tutor_data.get("status") == "found" and tutor_data.get("pets"):
                    first_pet = tutor_data["pets"][0]
                    card = await agent_tools.get_pet_vaccination_card_tool(db, tutor_phone, first_pet["name"])
                    tools_called.append({"tool": "get_pet_vaccination_card", "result": card})

                    if "records" in card and card["records"]:
                        lines = [f"💉 *{r['vaccine_name']}*: Aplicada em {r['application_date']} | Reforço: *{r['next_due_date']}* (Status: {r['status']})" for r in card["records"][:4]]
                        status_alert = "⚠️ *Atenção:* Há vacinas com reforço vencido ou próximo!" if card.get("has_overdue_vaccines") else "✅ Todas as vacinas registradas estão em dia!"
                        reply = (
                            f"Olá {tutor_data['name']}! 🐾 Aqui está o extrato da carteirinha digital de vacinação do *{first_pet['name']}*:\n\n"
                            + "\n".join(lines) + f"\n\n{status_alert}\n\nDeseja agendar uma aplicação ou dose de reforço?"
                        )
                        return {"reply": reply, "tools_called": tools_called}

            # Caso não tenha pet encontrado ou telefone, lista o catálogo oficial de vacinas
            cat_data = await agent_tools.get_vaccine_catalog_tool(db)
            tools_called.append({"tool": "get_vaccine_catalog", "result": cat_data})
            sample_vacs = [f"💉 *{v['name']}* ({v['species']}): {v['type']} - Reforço {v['booster_interval']}" for v in cat_data.get("vaccines", [])[:4]]
            reply = (
                "Trabalhamos com o calendário oficial de vacinas sanitárias (CFMV) para cães e gatos:\n\n"
                + "\n".join(sample_vacs) + "\n\nSeu pet já é cadastrado conosco? Se me informar o nome dele e seu telefone, posso consultar o extrato completo da carteirinha digital dele!"
            )
            return {"reply": reply, "tools_called": tools_called}

        # 4. Serviços e Preços
        if any(w in msg for w in ["serviço", "servico", "preço", "preco", "valor", "banho", "tosa", "adicional"]):
            services = await agent_tools.list_services_tool(db)
            tools_called.append({"tool": "list_services", "result": services})
            if services:
                lines = [f"🐾 *{s['name']}* ({s['category']}): R$ {s['price']:.2f} (~{s['duration_minutes']} min)" for s in services[:6]]
                reply = "Aqui estão os nossos principais serviços disponíveis:\n\n" + "\n".join(lines) + "\n\nQual deles você gostaria de agendar para o seu pet?"
            else:
                reply = "Olá! Nosso catálogo de serviços está sendo preparado. Em instantes teremos Banho, Tosa, Adicionais e Consultas disponíveis!"
            return {"reply": reply, "tools_called": tools_called}

        # 5. Saudações
        if any(w in msg for w in ["olá", "ola", "oi", "bom dia", "boa tarde", "boa noite"]):
            reply = (
                "Olá! Eu sou o Rex 🐾, assistente virtual do *SmartPetShop*!\n\n"
                "Como posso ajudar você e seu pet hoje? Você pode:\n"
                "- Consultar a *carteirinha de vacinas* do seu pet 💉\n"
                "- Verificar nossos *serviços e preços* de banho, tosa e clínica 🛁\n"
                "- Checar *horários livres* e agendar um atendimento 📅\n"
                "- Solicitar atendimento humano 🙋‍♂️"
            )
            return {"reply": reply, "tools_called": []}

        # 6. Fallback padrão
        reply = (
            "Entendido! Posso consultar a carteirinha de vacinas do seu pet, informar nossos serviços e valores ou verificar horários vagos na agenda.\n\n"
            "Como posso te ajudar hoje?"
        )
        return {"reply": reply, "tools_called": tools_called}

    async def process_whatsapp_message(
        self,
        db: AsyncSession,
        from_phone: str,
        user_text: str
    ) -> Dict[str, Any]:
        """
        Ponto de entrada orquestrado para mensagens vindas do WhatsApp (Meta Cloud API).
        1. Identifica ou busca tutor por telefone.
        2. Obtém ou cria a sessão ativa de chat (channel='whatsapp').
        3. Carrega o histórico recente de contexto.
        4. Detecta intenção de transbordo (Handoff para atendente humano).
        5. Salva a mensagem recebida.
        6. Executa a inferência de IA.
        7. Salva a resposta gerada e metadados.
        8. Retorna a resposta e dados da sessão.
        """
        # 1. Localiza tutor
        tutor = await tutor_service.get_tutor_by_phone(db, from_phone)
        if not tutor:
            clean_phone = "".join(filter(str.isdigit, from_phone))
            tutor = await tutor_service.get_tutor_by_phone(db, clean_phone)

        # 2. Localiza ou cria sessão de WhatsApp
        session = await get_or_create_whatsapp_session(db, from_phone, tutor=tutor)

        # 3. Carrega histórico de contexto
        history = await get_session_history(db, session.id, limit=8)

        # 4. Salva a mensagem de entrada do usuário
        await save_chat_message(
            db=db,
            session_id=session.id,
            role="user",
            content=user_text,
            metadata_info={"channel": "whatsapp", "from_phone": from_phone}
        )

        # 5. Verifica se a sessão já está em atendimento humano
        if session.status == "human_required":
            logger.info(f"[WhatsApp Agent] Sessão {session.id} está sob atendimento humano. IA pausada.")
            return {
                "session_id": str(session.id),
                "reply": None,
                "handoff_active": True,
                "status": "human_required"
            }

        # 6. Executa inferência do agente de IA
        agent_result = await self.run(
            db=db,
            user_message=user_text,
            conversation_history=history,
            tutor_phone=from_phone
        )

        reply_text = agent_result.get("reply", "")
        handoff_requested = agent_result.get("handoff_requested", False)

        # Se solicitou transbordo para humano, atualiza status da sessão
        if handoff_requested:
            session.status = "human_required"
            await db.commit()

        # 7. Salva a resposta da IA no histórico
        if reply_text:
            await save_chat_message(
                db=db,
                session_id=session.id,
                role="assistant",
                content=reply_text,
                metadata_info={
                    "tools_called": agent_result.get("tools_called", []),
                    "handoff_requested": handoff_requested
                }
            )

        return {
            "session_id": str(session.id),
            "reply": reply_text,
            "tools_called": agent_result.get("tools_called", []),
            "handoff_requested": handoff_requested,
            "status": session.status
        }


chatbot_agent = ChatbotAgent()
