import httpx
import sys

BASE = "http://localhost:8000/api/v1/whatsapp"

def run_tests():
    print("=== Verificação Completa dos Endpoints WhatsApp (Issues 17, 18, 19, 20) ===")

    # 1. Hub Challenge
    r1 = httpx.get(f"{BASE}/webhook?hub.mode=subscribe&hub.challenge=test_challenge_123&hub.verify_token=smartpetshop_meta_webhook_token_2026")
    assert r1.status_code == 200 and r1.text == "test_challenge_123", f"Erro no Challenge: {r1.status_code} - {r1.text}"
    print("✅ 1. Hub Challenge verificado (Issue 17)")

    # 2. Queue Status
    r2 = httpx.get(f"{BASE}/queue/status")
    assert r2.status_code == 200 and r2.json()["is_running"] is True
    print(f"✅ 2. Queue Status verificado: {r2.json()['broker']} (Issue 20)")

    # 3. Send Text
    r3 = httpx.post(f"{BASE}/send-text", json={"phone": "11987654321", "text": "Teste de mensagem direta *SmartPetShop*"})
    assert r3.status_code == 200 and r3.json()["success"] is True
    print("✅ 3. Send Text verificado (Issue 19)")

    # 4. Send Interactive
    r4 = httpx.post(f"{BASE}/send-interactive", json={
        "phone": "11987654321",
        "body_text": "Você gostaria de agendar uma consulta?",
        "buttons": [{"id": "btn_yes", "title": "Sim, por favor"}, {"id": "btn_no", "title": "Agora não"}]
    })
    assert r4.status_code == 200 and r4.json()["success"] is True
    print("✅ 4. Send Interactive verificado (Issue 19)")

    # 5. Send Template
    r5 = httpx.post(f"{BASE}/send-template", json={
        "phone": "11987654321",
        "template_name": "lembrete_vacina_v10",
        "language_code": "pt_BR",
        "parameters": ["Thor", "V10 Vanguard", "30/11/2026"]
    })
    assert r5.status_code == 200 and r5.json()["success"] is True
    print("✅ 5. Send Template verificado (Issue 19)")

    # 6. Send Vaccine Reminder
    r6 = httpx.post(f"{BASE}/send-vaccine-reminder", json={
        "phone": "11987654321",
        "pet_name": "Thor",
        "vaccine_name": "V10",
        "due_date": "30/11/2026",
        "alert_type": "vaccine_d7"
    })
    assert r6.status_code == 200 and r6.json()["success"] is True
    print("✅ 6. Send Vaccine Reminder verificado (Issue 19)")

    # 7. Messages audit
    r7 = httpx.get(f"{BASE}/messages?limit=5")
    assert r7.status_code == 200 and len(r7.json()) > 0
    print(f"✅ 7. Audit log verificado: {len(r7.json())} mensagens listadas (Issue 17)")

    print("\n🎉 TODOS OS MÓDULOS DE WHATSAPP ESTÃO 100% OPERACIONAIS!")

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"❌ Falha: {e}")
        sys.exit(1)
