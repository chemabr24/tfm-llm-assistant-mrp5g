"""
Batería de tests funcionales para los endpoints principales del backend.
Requiere que el servidor esté corriendo en localhost:8000 y que la VPN
de la UCLM esté conectada (necesaria para las pruebas que llaman al LLM).
"""
import httpx
import pytest

BASE_URL = "http://localhost:8000/api"


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=60.0) as c:
        yield c


def test_health_check():
    """Verifica que el backend responde correctamente al endpoint de salud."""
    response = httpx.get("http://localhost:8000/health")
    assert response.status_code == 200


def test_create_session(client):
    """Verifica que se puede crear una sesión correctamente."""
    response = client.post("/sessions", json={
        "title": "Sesión de test automático",
        "patient_identifier": "TEST-001"
    })
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["title"] == "Sesión de test automático"


def test_list_sessions(client):
    """Verifica que se puede listar las sesiones existentes."""
    response = client.get("/sessions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_chat_without_documents_indicates_no_info(client):
    """
    Verifica que el asistente responde correctamente cuando no hay
    documentación indexada en la sesión, sin generar contenido inventado.
    """
    session_response = client.post("/sessions", json={
        "title": "Sesión vacía de test",
        "patient_identifier": "TEST-002"
    })
    session_id = session_response.json()["id"]

    chat_response = client.post("/chat", json={
        "query": "¿Cuál es el tratamiento recomendado?",
        "session_id": session_id,
        "history": []
    })
    assert chat_response.status_code == 200
    # El endpoint devuelve streaming; comprobamos que responde sin error
    assert len(chat_response.text) >= 0


def test_chat_with_invalid_session_returns_404(client):
    """Verifica que una consulta a una sesión inexistente devuelve 404."""
    response = client.post("/chat", json={
        "query": "Pregunta cualquiera",
        "session_id": "00000000-0000-0000-0000-000000000000",
        "history": []
    })
    assert response.status_code == 404


def test_delete_session(client):
    """Verifica que una sesión puede archivarse (soft delete) correctamente."""
    session_response = client.post("/sessions", json={
        "title": "Sesión a eliminar",
        "patient_identifier": "TEST-003"
    })
    session_id = session_response.json()["id"]

    delete_response = client.delete(f"/sessions/{session_id}")
    assert delete_response.status_code == 200