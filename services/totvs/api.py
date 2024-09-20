import requests

# Configurações da API
base_url = "http://10.1.1.221:11980/api/totvsmoda"
auth_url = f"{base_url}/authorization/v2/token"

# Credenciais de autenticação
auth_data = {
    "username": "77776",
    "password": "ib77776",
    "client_id": "kduapiv2",
    "client_secret": "9157489678",
    "grant_type": "password"
}

def get_access_token():
    """Obtém o token de acesso para a API TOTVS."""
    response = requests.post(auth_url, data=auth_data)
    response.raise_for_status()  # Lança uma exceção se a requisição falhar
    token_data = response.json()
    return token_data["access_token"]
