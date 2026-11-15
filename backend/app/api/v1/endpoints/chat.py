import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import (
    ChatMessageIn,
    ChatMessageOut,
    ChatSessionOut,
    ChatResponse
)
from app.agents.chatbot_agent import chatbot_agent

router = APIRouter()


@router.post(
    "/message",
    response_model=ChatResponse,
    summary="Conversar com o Agente Virtual (Rex)",
    description="Envia uma mensagem para o Chatbot com IA (Gemini), que processa o contexto, invoca ferramentas e responde com informações de serviços e agendamentos."
)
async def send_chat_message(
    chat_in: ChatMessageIn,
    db: AsyncSession = Depends(get_db)
):
    # 1. Recuperar ou criar a sessão de chat
    session = None
    if chat_in.session_id:
        query = select(ChatSession).where(ChatSession.id == chat_in.session_id)
        result = await db.execute(query)
        session = result.scalar_one_or_none()

    if not session:
        session = ChatSession(
            tutor_id=chat_in.tutor_id,
            channel=chat_in.channel,
            status="active"
        )
        db.add(session)
        await db.flush()

    # 2. Carregar histórico recente de mensagens (últimas 10 mensagens)
    history_query = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
        .limit(10)
    )
    history_result = await db.execute(history_query)
    past_messages = history_result.scalars().all()

    conversation_history = [
        {"role": m.role, "content": m.content}
        for m in past_messages
    ]

    # 3. Persistir mensagem do usuário
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=chat_in.content
    )
    db.add(user_msg)
    await db.flush()

    # 4. Processar com o Agente de IA
    agent_output = await chatbot_agent.run(
        db=db,
        user_message=chat_in.content,
        conversation_history=conversation_history
    )

    # 5. Persistir resposta do assistente
    metadata = {}
    if agent_output.get("tools_called"):
        metadata["tools_called"] = agent_output["tools_called"]

    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=agent_output["reply"],
        metadata_info=metadata if metadata else None
    )
    db.add(assistant_msg)
    await db.commit()

    return ChatResponse(
        session_id=session.id,
        reply=agent_output["reply"],
        tools_called=agent_output.get("tools_called", []),
        created_at=datetime.utcnow()
    )


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionOut,
    summary="Obter histórico da sessão",
    description="Retorna todas as mensagens trocadas em uma sessão de atendimento."
)
async def get_chat_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(ChatSession)
        .where(ChatSession.id == session_id)
        .options(selectinload(ChatSession.messages))
    )
    result = await db.execute(query)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sessão de chat não encontrada."
        )

    # Ordenar mensagens cronologicamente
    session.messages.sort(key=lambda m: m.created_at)
    return session


@router.get(
    "/sessions",
    response_model=List[ChatSessionOut],
    summary="Listar sessões de chat",
    description="Lista as sessões de chat ativas com paginação."
)
async def list_chat_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .order_by(ChatSession.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    sessions = result.scalars().all()
    return list(sessions)

