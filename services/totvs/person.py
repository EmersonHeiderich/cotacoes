import requests
import re
import json
from services.totvs.api import get_access_token

# Mapeamento de UFs para os códigos IBGE
uf_to_ibge = {
    "AC": "12", "AL": "27", "AP": "16", "AM": "13", "BA": "29",
    "CE": "23", "DF": "53", "ES": "32", "GO": "52", "MA": "21",
    "MT": "51", "MS": "50", "MG": "31", "PA": "15", "PB": "25",
    "PR": "41", "PE": "26", "PI": "22", "RJ": "33", "RN": "24",
    "RS": "43", "RO": "11", "RR": "14", "SC": "42", "SP": "35",
    "SE": "28", "TO": "17"
}

legal_entities_url = "http://10.1.1.221:11980/api/totvsmoda/person/v2/legal-entities/search"

def is_cnpj(value):
    """Verifica se a string fornecida é um CNPJ válido."""
    pattern = r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$'  # Formato com pontuação
    digits_pattern = r'^\d{14}$'  # Apenas dígitos
    return bool(re.match(pattern, value)) or bool(re.match(digits_pattern, value))

def get_legal_entity_data(identifier):
    """Consulta os dados de uma pessoa jurídica na API TOTVS."""
    page = 1
    page_size = 500  # Valor máximo permitido pela API

    if is_cnpj(identifier):
        filter_key = "cnpjList"
        identifier_value = [identifier]
    else:
        filter_key = "personCodeList"
        identifier_value = [int(identifier)]

    data = {
        "filter": {
            filter_key: identifier_value,
        },
        "expand": "addresses",
        "page": page,
        "pageSize": page_size
    }

    headers = {
        "Authorization": f"Bearer {get_access_token()}"
    }

    response = requests.post(legal_entities_url, headers=headers, json=data)
    response.raise_for_status()
    response_data = response.json()

    if response_data["count"] > 0:
        item = response_data["items"][0]  # Assumindo que sempre há apenas um item
        code = item.get("code")  # Extrair o código do cliente
        name = item.get("name")
        cnpj = item.get("cnpj")
        
        number_state_registration = item.get("numberStateRegistration")
        if not number_state_registration:
            number_state_registration = "ISENTO"
        else:
            number_state_registration = re.sub(r'\D', '', number_state_registration)

        # Selecionar o endereço correto
        addresses = item.get("addresses", [])
        address_info = None

        for address in addresses:
            if address.get("addressTypeCode") == 5:  # Procurar endereço do tipo "Delivery"
                address_info = address
                break

        if not address_info:
            address_info = addresses[0] if addresses else {}

        city_name = address_info.get("cityName")
        state_abbreviation = address_info.get("stateAbbreviation")
        cep = address_info.get("cep")
        address = address_info.get("address")
        neighborhood = address_info.get("neighborhood")
        address_number = address_info.get("addressNumber")
        public_place = address_info.get("publicPlace")

        if public_place:
            address = f"{public_place} {address}"

        ibge_city_code_partial = address_info.get("ibgeCityCode")
        ibge_city_code = uf_to_ibge.get(state_abbreviation, "") + str(ibge_city_code_partial).zfill(5)

        return {
            "code": code,
            "name": name,
            "cnpj": cnpj,
            "number_state_registration": number_state_registration,
            "city_name": city_name,
            "state_abbreviation": state_abbreviation,
            "cep": cep,
            "address": address,
            "neighborhood": neighborhood,
            "address_number": address_number,
            "ibge_city_code": ibge_city_code
        }
    else:
        return None

# Exemplo de uso
if __name__ == "__main__":
    code_person_input = input("Digite o código da pessoa: ")
    legal_entity_data = get_legal_entity_data(code_person_input)

    if legal_entity_data:
        print("Dados mapeados da pessoa jurídica:")
        print(json.dumps(legal_entity_data, indent=4, ensure_ascii=False))
    else:
        print("Nenhum dado encontrado para o código informado.")
