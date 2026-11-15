#!/usr/bin/env python3
"""
Script para criação automática das Issues do Epic: Integração do Módulo de IA com WhatsApp no GitHub.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error

def main():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith("GITHUB_TOKEN="):
                        token = line.strip().split("=", 1)[1]
                        break

    if not token:
        print("Erro: GITHUB_TOKEN não encontrado!")
        sys.exit(1)

    repo = "crisb2reis/SmartPetShop"
    url = f"https://api.github.com/repos/{repo}/issues"

    issues = [
        {
            "title": "[Backend] Configurar Webhook e infraestrutura de recebimento de mensagens da Meta Cloud API",
            "body": """## 📌 Contexto
Implementar os endpoints necessários para receber, autenticar e processar os eventos (mensagens de texto, áudio e mídia) enviados pelo WhatsApp Business API (Meta Cloud API ou provedor oficial).

## 🎯 Critérios de Aceitação
- [ ] Endpoint `GET /api/v1/whatsapp/webhook/` configurado para validação do token (`hub.mode`, `hub.verify_token` e `hub.challenge`) da Meta.
- [ ] Endpoint `POST /api/v1/whatsapp/webhook/` para capturar os payloads de mensagens e status recebidos dos clientes.
- [ ] Validação da assinatura do webhook (`X-Hub-Signature-256`) utilizando o App Secret da Meta para segurança.
- [ ] Tratamento de idempotência baseado em `message_id` para evitar processamento duplicado de mensagens em caso de retentativas da Meta.
- [ ] Criação de modelo e migração para tabela de auditoria/histórico `whatsapp_messages` (campos: id, tenant_id, message_id, phone, direction, message_type, content, status, raw_payload, created_at).
""",
            "labels": ["backend", "whatsapp", "meta-api"]
        },
        {
            "title": "[Backend] Desenvolver o motor de processamento e prompt engineering do Agente de IA",
            "body": """## 📌 Contexto
Criar o serviço de IA responsável por interpretar a intenção do usuário (Natural Language Understanding), manter o contexto da sessão (estado da conversa) e gerar respostas humanizadas focadas no contexto de pet shop (agendamentos, dúvidas sobre vacinas, produtos e serviços).

## 🎯 Critérios de Aceitação
- [ ] Gerenciamento de histórico de conversas por número de telefone do tutor (janela de contexto com persistência em cache/Redis ou banco de dados).
- [ ] System Prompt especializado definindo o tom de voz amigável do assistente virtual (Rex 🐾), restrições sanitárias do CFMV (IA não prescreve nem dá diagnósticos médicos veterinários, fornecendo apenas orientações gerais e direcionamento para consulta).
- [ ] Tool Calling / Function Calling integrado para permitir que a IA consulte e execute ações no sistema:
  - Verificar horários livres na agenda de banho, tosa e veterinário.
  - Consultar a carteirinha de vacinação digital do pet (doses em dia, reforços e atrasadas).
  - Consultar tabela de preços de serviços e adicionais.
  - Criar pré-agendamento de atendimento.
""",
            "labels": ["backend", "ai", "llm", "whatsapp"]
        },
        {
            "title": "[Backend] Implementar o serviço de disparo de respostas e mensagens multimídia via WhatsApp API",
            "body": """## 📌 Contexto
Desenvolver a camada que envia de volta ao usuário a resposta gerada pela IA (ou mensagens transacionais do sistema, como lembretes de vacina).

## 🎯 Critérios de Aceitação
- [ ] Cliente HTTP assíncrono (`httpx`) de integração com a API de envio de mensagens do WhatsApp Graph API (`POST /{phone_number_id}/messages`).
- [ ] Suporte a envio de texto formatado (negrito, itálico, listas) e tratamento de caracteres especiais.
- [ ] Suporte a envio de mensagens interativas com botões de resposta rápida e listas de opções (ex: seleção de horário, confirmação sim/não).
- [ ] Suporte ao disparo de templates pré-aprovados pela Meta (HSM) para mensagens ativas fora da janela de atendimento de 24 horas (ex: lembretes de vacina D-30, D-7, D-0).
- [ ] Tratamento robusto de erros e fallbacks (se a IA falhar ou exceder o timeout, disparar mensagem automática orientando contato ou aguardo de atendente humano).
""",
            "labels": ["backend", "whatsapp", "meta-api"]
        },
        {
            "title": "[Backend] Implementar processamento assíncrono de mensagens com Fila (Celery / Workers)",
            "body": """## 📌 Contexto
Garantir que o recebimento de webhooks e a chamada aos modelos de IA não bloqueiem o servidor HTTP, evitando timeouts e perda de requisições da Meta.

## 🎯 Critérios de Aceitação
- [ ] O endpoint de webhook apenas enfileira o payload bruto e responde `HTTP 200 OK` em menos de 1 segundo para a Meta.
- [ ] Worker em background assíncrono (Celery / Redis / BackgroundTasks) consome a fila de mensagens, executa a lógica do Agente de IA e despacha a resposta via WhatsApp.
- [ ] Mecanismo de retry automático com backoff exponencial em caso de instabilidade temporária na API do LLM ou na Graph API da Meta.
- [ ] Monitoramento e logs de fila para acompanhamento de taxa de entrega e tempo médio de resposta (SLA).
""",
            "labels": ["backend", "celery", "async", "redis"]
        },
        {
            "title": "[Fullstack] Desenvolver funcionalidade de transbordo da IA para Atendimento Humano",
            "body": """## 📌 Contexto
Permitir que o atendente do pet shop assuma a conversa caso o cliente solicite ou a IA detecte necessidade de intervenção humana (Handoff).

## 🎯 Critérios de Aceitação
- [ ] Flag de status na sessão de atendimento (`STATUS: AI_ACTIVE` vs `STATUS: HUMAN_REQUIRED`).
- [ ] Gatilho automático de transbordo (ex: cliente digita "falar com atendente", "humano", ou a IA detecta baixa confiança/dúvida complexa) que pausa a IA e gera notificação no sistema.
- [ ] Painel web no frontend para os atendentes/recepcionistas visualizarem a fila de conversas em atendimento humano.
- [ ] Interface de chat onde o operador visualiza o histórico completo trocado entre o tutor e a IA e pode enviar mensagens diretamente pelo WhatsApp do pet shop.
- [ ] Botão para devolver o controle da conversa para a IA (`STATUS: AI_ACTIVE`) após a conclusão do atendimento humano.
""",
            "labels": ["fullstack", "frontend", "backend", "handoff", "whatsapp"]
        }
    ]

    print(f"🚀 Iniciando criação de {len(issues)} issues no repositório {repo}...\n")

    created_issues = []
    for idx, iss in enumerate(issues, start=1):
        payload = {
            "title": iss["title"],
            "body": iss["body"]
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "SmartPetShop-Automation",
                "Content-Type": "application/json"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req) as resp:
                res_data = json.loads(resp.read().decode())
                issue_num = res_data["number"]
                created_issues.append((issue_num, iss["title"]))
                print(f"✅ Issue #{issue_num} criada: {iss['title']}")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode()
            print(f"❌ Erro ao criar issue {idx}: {e.code} - {err_body}")

        time.sleep(1)

    print("\n🎉 Todas as issues do Epic foram criadas com sucesso:")
    for num, title in created_issues:
        print(f" - #{num}: {title}")

if __name__ == "__main__":
    main()

