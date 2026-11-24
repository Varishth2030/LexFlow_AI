def test_root_endpoint(client):
    """
    Test the GET / root endpoint.
    """
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["status"] == "online"
    assert "version" in data
    assert data["docs_url"] == "/docs"


def test_health_endpoint(client):
    """
    Test the GET /health health check endpoint.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "version" in data
    assert "environment" in data


def test_api_v1_health_endpoint(client):
    """
    Test the GET /api/v1/health modular endpoint.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_cors_headers(client):
    """
    Test that CORS headers are returned for configured frontend origins.
    """
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
    }
    response = client.options("/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
