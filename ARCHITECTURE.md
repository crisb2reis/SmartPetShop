# SmartPetShop - Arquitetura do Sistema

> Documento de Arquitetura de Software do Sistema Inteligente para Pet Shop.
> Stack: Python (FastAPI) + PostgreSQL + Docker + React + Agentes de IA (Gemini).

---

## 1. Visão Geral da Arquitetura

O sistema adota uma arquitetura em camadas modular (Clean Architecture simplificada), priorizando alta coesão, baixo acoplamento, desempenho assíncrono e facilidade de manutenção.

```mermaid
graph TD
    UserClient[Cliente / Tutor - Web/Mobile] -->|HTTP / WebSocket| Gateway[Nginx / Reverse Proxy]
    StaffClient[Equipe Pet Shop - Dashboard React] -->|HTTP / WebSocket| Gateway
    
    Gateway --> Frontend[Frontend React + Vite + Tailwind]
    Gateway --> Backend[Backend FastAPI]
    
    subgraph Backend_Ecosystem[FastAPI Backend]
        API_Routers[API Endpoints / REST]
        Service_Layer[Camada de Servicos & Regras de Negocio]
        Agent_Chatbot[Agente Chatbot - Gemini + Function Calling]
        Agent_Alerts[Agente Preditivo de Alertas - Background Worker]
        Data_Access[SQLAlchemy 2.0 Async ORM]
    end
    
    API_Routers --> Service_Layer
    Agent_Chatbot --> Service_Layer
    Agent_Alerts --> Service_Layer
    Service_Layer --> Data_Access
    
    Data_Access --> PostgreSQL[(PostgreSQL Database)]
    Agent_Chatbot --> GeminiAPI[Google Gemini API]
    Agent_Alerts --> GeminiAPI
```

---

## 2. Modelagem do Banco de Dados (PostgreSQL)

O modelo relacional suporta operações transacionais rigorosas (agendamentos, cadastros e finanças) e armazena o histórico dos pets e conversas com a IA.

```mermaid
erDiagram
    TUTOR ||--o{ PET : "possui"
    PET ||--o{ APPOINTMENT : "possui"
    SERVICE ||--o{ APPOINTMENT : "inclui"
    PET ||--o{ HEALTH_RECORD : "possui"
    TUTOR ||--o{ ALERT : "recebe"
    PET ||--o{ ALERT : "relacionado"
    TUTOR ||--o{ CHAT_SESSION : "interage"
    CHAT_SESSION ||--o{ CHAT_MESSAGE : "contem"

    TUTOR {
        uuid id PK
        string name
        string phone
        string email
        string address
        timestamp created_at
    }

    PET {
        uuid id PK
        uuid tutor_id FK
        string name
        string species
        string breed
        date birth_date
        float weight
        text medical_notes
        timestamp created_at
    }

    SERVICE {
        uuid id PK
        string name
        string category
        decimal price
        int duration_minutes
        boolean active
    }

    APPOINTMENT {
        uuid id PK
        uuid pet_id FK
        uuid service_id FK
        timestamp scheduled_at
        string status
        text notes
        timestamp created_at
    }

    HEALTH_RECORD {
        uuid id PK
        uuid pet_id FK
        string record_type
        string title
        date application_date
        date next_due_date
        text notes
    }

    ALERT {
        uuid id PK
        uuid tutor_id FK
        uuid pet_id FK
        string alert_type
        string message
        string status
        timestamp scheduled_for
        timestamp sent_at
    }

    CHAT_SESSION {
        uuid id PK
        uuid tutor_id FK
        string channel
        timestamp created_at
    }

    CHAT_MESSAGE {
        uuid id PK
        uuid session_id FK
        string role
        text content
        jsonb metadata
        timestamp created_at
    }
```

---

## 3. Especificação dos Agentes de IA

### 3.1. Agente de Atendimento & Agendamento (Chatbot)
- **Modelo:** Gemini 2.5 / 3.x Flash (alta velocidade e suporte a Function Calling).
- **Missão:** Atender clientes via chat, responder dúvidas sobre serviços e preços, verificar horários livres e efetuar agendamentos.
- **Ferramentas (Function Calling):**
  - `check_available_slots(service_id: str, date: str) -> list[str]`
  - `list_services() -> list[dict]`
  - `get_pet_history(tutor_phone: str) -> list[dict]`
  - `create_appointment(pet_id: str, service_id: str, date_time: str) -> dict`

### 3.2. Agente Preditivo de Alertas e Retenção
- **Execução:** Worker agendado (executado diariamente em background).
- **Missão:** 
  1. Identificar vacinas e vermífugos próximos do vencimento (`next_due_date <= hoje + 7 dias`).
  2. Analisar ciclo de banho/tosa (ex: se o pet vem a cada 15 dias e já se passaram 20 dias).
  3. Gerar mensagens personalizadas de alerta com tom acolhedor e chamada para agendamento.

---

## 4. Estrutura de Diretórios Recomendada

```text
SmartPetShop/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── auth.py
│   │   │       │   ├── tutors.py
│   │   │       │   ├── pets.py
│   │   │       │   ├── services.py
│   │   │       │   ├── appointments.py
│   │   │       │   ├── chat.py
│   │   │       │   └── alerts.py
│   │   │       └── router.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   ├── models/           # SQLAlchemy ORM Models
│   │   ├── schemas/          # Pydantic Schemas (Request/Response)
│   │   ├── services/         # Regras de Negocio (CRUD, Agendas)
│   │   ├── agents/           # Agentes de IA (Gemini SDK & Tools)
│   │   │   ├── chatbot_agent.py
│   │   │   ├── alert_agent.py
│   │   │   └── tools.py
│   │   └── main.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # Componentes visuais reutilizaveis
│   │   ├── pages/            # Telas (Dashboard, Pets, Agenda, Chat)
│   │   ├── services/         # Comunicacao com API (Axios / TanStack)
│   │   ├── hooks/
│   │   └── App.tsx
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
├── .env.example
├── .gitignore
└── ARCHITECTURE.md
```

---

## 5. Orquestração com Docker

Ambiente unificado para desenvolvimento e produção:
- **`db`**: PostgreSQL 16 com volume persistente para dados.
- **`backend`**: Container Python 3.11 executando Uvicorn com hot-reload.
- **`frontend`**: Container Node.js executando servidor de desenvolvimento Vite (ou Nginx multi-stage build para produção).

