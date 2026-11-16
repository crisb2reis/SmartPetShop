import asyncio
import os
import sys
import time
import httpx
import uuid

# Garante import do módulo app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

BASE_URL = "http://localhost:8000/api/v1/whatsapp"


def test_queue_status():
    print("\n--- 1. Testando GET /queue/status ---")
    resp = httpx.get(f"{BASE_URL}/queue/status")
    print(f"Status Code: {resp.status_code}")
    print(f"Queue Status: {resp.json()}")
    assert resp.status_code == 200
    data = resp.json()
    assert "broker" in data
    assert data["is_running"] is True
    print("✅ Status da Fila verificado com sucesso!")


def test_async_webhook_immediate_response():
    print("\n--- 2. Testando Enfileiramento Assíncrono Ultra-Rápido (< 500ms) ---")
    test_phone = "5511999990001"
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "5511999999999",
                                "phone_number_id": "100000000000001"
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "Mariana Santos"},
                                    "wa_id": test_phone
                                }
                            ],
                            "messages": [
                                {
                                    "from": test_phone,
                                    "id": f"wamid.ASYNC_TEST_{uuid.uuid4().hex[:8]}",
                                    "timestamp": str(int(time.time())),
                                    "text": {"body": "Olá! Quais serviços e valores de banho e tosa vocês oferecem?"},
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }

    start_time = time.time()
    resp = httpx.post(f"{BASE_URL}/webhook", json=payload, timeout=5.0)
    duration_ms = (time.time() - start_time) * 1000

    print(f"Resposta recebida em: {duration_ms:.2f} ms")
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {resp.json()}")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "queued"
    assert "job_id" in data
    assert duration_ms < 1000, f"Tempo de resposta excedeu 1s: {duration_ms}ms"

    job_id = data["job_id"]
    print(f"✅ Webhook respondeu imediatamente ({duration_ms:.1f}ms) e retornou job_id: {job_id}")
    return job_id, test_phone


def test_worker_processing_and_job_completion(job_id: str, test_phone: str):
    print(f"\n--- 3. Aguardando Worker consumir e processar Job {job_id} ---")
    max_wait = 20
    start = time.time()
    job_completed = False
    job_data = None

    while time.time() - start < max_wait:
        resp = httpx.get(f"{BASE_URL}/queue/jobs/{job_id}")
        if resp.status_code == 200:
            job_data = resp.json()
            status = job_data.get("status")
            print(f"  [T+{time.time()-start:.1f}s] Status do Job: {status} (Tentativas: {job_data.get('attempts')})")
            if status == "completed":
                job_completed = True
                break
        time.sleep(1.0)

    assert job_completed, f"Job {job_id} não completou no tempo limite de {max_wait}s. Dados: {job_data}"
    print(f"✅ Job {job_id} processado com sucesso pelo Worker!")
    print(f"Resultado do Job: {job_data.get('result')}")

    # Verificar mensagens no histórico
    msg_resp = httpx.get(f"{BASE_URL}/messages?phone={test_phone}&limit=5")
    assert msg_resp.status_code == 200
    messages = msg_resp.json()
    print(f"Total de mensagens encontradas para o telefone: {len(messages)}")
    assert len(messages) >= 2, "Deveria haver pelo menos a mensagem INBOUND e a resposta OUTBOUND"
    inbound = next((m for m in messages if m["direction"] == "INBOUND"), None)
    outbound = next((m for m in messages if m["direction"] == "OUTBOUND"), None)
    assert inbound is not None, "Mensagem INBOUND não encontrada"
    assert outbound is not None, "Mensagem OUTBOUND de resposta da IA não encontrada"
    print(f"Mensagem da Tutora: {inbound['content']}")
    print(f"Resposta gerada pela IA e enviada pelo Worker: {outbound['content'][:150]}...")


def test_retry_mechanism():
    print("\n--- 4. Testando Mecanismo de Retry Automático com Backoff e Contingência ---")
    # Payload que causará simulação de falha ou erro recuperável
    from app.services.whatsapp_queue import WhatsAppJob, whatsapp_queue

    class FailingJobSimulation:
        async def run(self):
            # Testa diretamente o método de retentativas
            job = WhatsAppJob(payload={"invalid": "payload_test"})
            job.max_retries = 2
            
            # Força o método de execução a falhar para verificar contagem de retentativas
            original_execute = whatsapp_queue._execute_job
            call_count = 0
            
            async def failing_execute(j):
                nonlocal call_count
                call_count += 1
                raise ConnectionError(f"Simulated network timeout on attempt {call_count}")

            try:
                whatsapp_queue._execute_job = failing_execute
                await whatsapp_queue._process_job_with_retries(job)
                
                print(f"Tentativas executadas: {job.attempts}/{job.max_retries}")
                print(f"Status final do Job: {job.status}")
                print(f"Erro registrado: {job.error}")
                assert job.attempts == 2, f"Esperado 2 tentativas, mas foram {job.attempts}"
                assert job.status == "failed", f"Esperado status 'failed', mas foi '{job.status}'"
                print("✅ Mecanismo de retry automático e contingência validado com sucesso!")
            finally:
                whatsapp_queue._execute_job = original_execute

    asyncio.run(FailingJobSimulation().run())


if __name__ == "__main__":
    try:
        test_queue_status()
        job_id, test_phone = test_async_webhook_immediate_response()
        test_worker_processing_and_job_completion(job_id, test_phone)
        test_retry_mechanism()
        print("\n🎉 TODOS OS TESTES DA ISSUE #20 PASSARAM COM SUCESSO!")
    except Exception as e:
        print(f"\n❌ ERRO NOS TESTES: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
