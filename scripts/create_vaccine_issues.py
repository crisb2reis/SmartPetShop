#!/usr/bin/env python3
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
            "title": "[Backend] Criar tabelas e modelos para Catálogo de Vacinas, Lotes e Histórico de Imunização",
            "body": """## 📌 Contexto
Criar a estrutura relacional no banco de dados para suportar o catálogo oficial de vacinas e o registro de aplicação por pet, atendendo às normas do CFMV (Conselho Federal de Medicina Veterinária) e controle de zoonoses.

## 🎯 Critérios de Aceitação
- [ ] Criar a tabela `vaccine_catalogs` com os campos:
  - `id` (UUID PK)
  - `species` (CANINO, FELINO, AMBOS)
  - `name` (ex: V8/V10, Raiva, Giárdia, V3/V4/V5)
  - `type` (OBRIGATORIA, OPCIONAL)
  - `recommended_age_weeks` (idade recomendada para primeira dose)
  - `doses_required` (quantidade de doses no protocolo primário)
  - `booster_interval_days` (intervalo de reforço em dias)
- [ ] Criar a tabela `vaccine_batches` para controle de estoque/lote:
  - `id` (UUID PK)
  - `vaccine_catalog_id` (FK para vaccine_catalogs)
  - `batch_number` (número do lote)
  - `manufacturer` (fabricante)
  - `expiration_date` (validade)
- [ ] Criar a tabela `pet_vaccination_records` (caderneta digital do pet):
  - `id` (UUID PK)
  - `pet_id` (FK para pets)
  - `vaccine_catalog_id` (FK para vaccine_catalogs)
  - `vaccine_batch_id` (FK para vaccine_batches, opcional)
  - `application_date` (data da aplicação)
  - `next_due_date` (próxima dose / vencimento)
  - `vet_name` (nome do médico veterinário responsável)
  - `vet_crmv` (CRMV/UF do veterinário)
  - `clinic_id` (ou tenant_id para isolamento multi-empresa)
  - `status` (APLICADA, PENDENTE, ATRASADA)
  - `notes` (observações)
- [ ] Criar migração Alembic para versionamento do schema no PostgreSQL."""
        },
        {
            "title": "[Backend] Inserir seed data com o calendário oficial de vacinação para cães e gatos",
            "body": """## 📌 Contexto
Garantir que o sistema já nasça com as vacinas padrão de mercado e exigidas por leis sanitárias pré-preenchidas para seleção rápida pelo operador/veterinário.

## 🎯 Critérios de Aceitação
- [ ] **Caninos:**
  - **Múltipla (V8 ou V10 / DHPPi + L):** Protocolo de filhotes (3 doses a partir de 6-8 semanas, intervalo de 21-30 dias) + Reforço Anual.
  - **Raiva (Antirrábica):** Dose única a partir de 12 semanas + Reforço Anual (Obrigatória por lei federal de controle de zoonoses).
  - **Traqueobronquite Infecciosa (Tosse dos Canis - Bordetella bronchiseptica / Parainfluenza):** Opcional/Recomendada.
  - **Giárdia:** 2 doses iniciais + Reforço Anual.
  - **Leishmaniose Visceral Canina:** Protocolo específico de 3 doses (regiões endêmicas).
- [ ] **Felinos:**
  - **Tríplice (V3), Quádrupla (V4) ou Quíntupla (V5):** Rinotraqueíte, Calicivirose, Panleucopenia (e Clamidiose/Leucemia se V4/V5). Protocolo de filhotes (2 a 3 doses a partir de 8 semanas) + Reforço Anual.
  - **Raiva (Antirrábica):** Dose única a partir de 12 semanas + Reforço Anual.
  - **FeLV (Leucose Felina):** Recomendada mediante teste negativo prévio.
- [ ] Script idempotente de seed data para carga inicial no banco de dados."""
        },
        {
            "title": "[Backend] Desenvolver endpoints REST para consulta e registro de vacinas do pet",
            "body": """## 📌 Contexto
Implementar os endpoints RESTful necessários no FastAPI para que o front-end liste o catálogo oficial de vacinas, registre novas aplicações por pet e exiba o histórico da carteirinha digital.

## 🎯 Critérios de Aceitação
- [ ] `GET /api/v1/vaccine-catalogs/?species=CANINO`: Retorna a lista de vacinas pré-cadastradas filtrada por espécie (`CANINO`, `FELINO`, `AMBOS`).
- [ ] `GET /api/v1/pets/{pet_id}/vaccinations/`: Retorna o histórico completo da carteirinha digital do pet, agrupando por tomadas (aplicadas e próximas doses).
- [ ] `POST /api/v1/pets/{pet_id}/vaccinations/`: Registra uma nova aplicação de vacina validando o lote, data de aplicação e calculando automaticamente a `next_due_date` com base no `booster_interval_days`.
- [ ] `PUT /api/v1/pets/{pet_id}/vaccinations/{id}/`: Permite editar o registro em caso de correção de lote, data ou CRMV (com log de auditoria).
- [ ] Validações de segurança, multi-tenancy e validação de schema Pydantic."""
        },
        {
            "title": "[Frontend] Desenvolver tela da Carteirinha de Vacinação Digital no perfil do Pet",
            "body": """## 📌 Contexto
Criar uma interface visual amigável e intuitiva, inspirada no formato de uma carteirinha física tradicional de vacinação animal, integrada a alertas inteligentes de vencimento.

## 🎯 Critérios de Aceitação
- [ ] Exibir abas ou seções claras separando:
  - **Vacinas Aplicadas (Histórico)**
  - **Próximas Doses / Calendário Recomendado**
- [ ] Indicadores visuais de status com cores:
  - 🟢 **Verde:** Em dia / Aplicada
  - 🟡 **Amarelo:** Próximo do vencimento (janela de 30 dias)
  - 🔴 **Vermelho:** Vencida / Atrasada
- [ ] Cards informativos detalhando para cada vacina:
  - Nome do imunizante
  - Data da aplicação
  - Número do Lote e Fabricante
  - Assinatura e CRMV do Médico Veterinário responsável
  - Data prevista para o próximo reforço"""
        },
        {
            "title": "[Frontend] Criar modal de lançamento de vacina com seleção pré-preenchida do catálogo",
            "body": """## 📌 Contexto
Facilitar e agilizar o trabalho do atendente e do médico veterinário no balcão e no consultório ao registrar uma nova aplicação de vacina.

## 🎯 Critérios de Aceitação
- [ ] Ao abrir o modal "Adicionar Vacina", o usuário seleciona a vacina a partir de um Select carregado do catálogo oficial da espécie do pet (ex: V10, Raiva, V4).
- [ ] Campo de seleção de Lote (vinculado aos lotes ativos e válidos cadastrados no estoque do pet shop).
- [ ] Preenchimento automático ou manual da data de aplicação e cálculo automático sugerido da data de retorno (`next_due_date`).
- [ ] Campos obrigatórios para **CRMV** e **Nome do Médico Veterinário** para garantir conformidade legal com as normas do CFMV.
- [ ] Feedback visual de sucesso e atualização imediata da carteirinha do pet."""
        },
        {
            "title": "[Backend/Notification] Implementar disparos de alerta para reforço de vacinas",
            "body": """## 📌 Contexto
Automatizar o envio de lembretes e notificações aos tutores quando a vacina do pet estiver prestes a vencer ou estiver em atraso, impulsionando a recorrência e fidelização no pet shop.

## 🎯 Critérios de Aceitação
- [ ] Job agendado (Background Worker / Cron / FastAPI Scheduler) rodando periodicamente para verificar registros onde `next_due_date` atinja:
  - **D-30:** Aviso prévio de reforço (30 dias antes)
  - **D-7:** Lembrete de agendamento (7 dias antes)
  - **D-0:** Vacina com vencimento hoje
  - **Atrasada:** Notificação de atraso para regularização imediata
- [ ] Disparo de notificação registrado no módulo de alertas (pronto para integração WhatsApp / SMS / E-mail) e integrado ao CRM do pet shop.
- [ ] Atualização de status do alerta para auditoria e controle da recepção."""
        }
    ]

    print(f"Iniciando criação de {len(issues)} issues no repositório {repo}...")
    created_issues = []

    for idx, item in enumerate(issues, 1):
        payload = json.dumps({
            "title": item["title"],
            "body": item["body"]
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
                "User-Agent": "SmartPetShop-Automation"
            }
        )

        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                print(f"✅ [{idx}/6] Issue #{data['number']} criada: {data['title']}")
                print(f"   URL: {data['html_url']}")
                created_issues.append(data)
        except urllib.error.HTTPError as e:
            print(f"❌ Erro ao criar issue {idx}: {e.code} - {e.read().decode()}")
            sys.exit(1)

        time.sleep(1)

    print(f"\n🎉 Sucesso! {len(created_issues)} issues criadas no GitHub.")

if __name__ == "__main__":
    main()
