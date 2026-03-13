#!/usr/bin/env python3

import os
import requests
from dotenv import load_dotenv
from openai import OpenAI
from web3 import Web3

load_dotenv()

# Cargar keys reales (IA y ETH)
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
ADDRESS_COINBASE = os.getenv("ADDRESS_COINBASE")
ADDRESS_BINANCE = os.getenv("ADDRESS_BINANCE")

if not all(
    [
        ALCHEMY_API_KEY,
        OPENAI_API_KEY,
        PRIVATE_KEY,
        ADDRESS_COINBASE,
        ADDRESS_BINANCE,
    ]
):
    raise ValueError("Faltan keys en .env – configura todo para ejecución real")

# Conexión real a mainnet ETH via Alchemy
RPC_URL = f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    raise ConnectionError("No conecta a mainnet – chequea Alchemy key o red")

account = w3.eth.account.from_key(PRIVATE_KEY)
WALLET = account.address.lower()

print(f"Entorno real iniciado. Wallet: {WALLET}")

# Obtener datos reales actuales (gas y precio ETH via CoinGecko – real, no simulado)
try:
    res = requests.get(
        "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd",
        timeout=10,
    )
    res.raise_for_status()
    eth_price_usd = res.json()["ethereum"]["usd"]
except (requests.RequestException, KeyError, TypeError, ValueError):
    eth_price_usd = 1980  # Fallback si falla (actual ~1980 USD marzo 2026)

latest_block = w3.eth.get_block("latest")
base_fee = latest_block.get("baseFeePerGas", 0)  # in wei
base_fee_gwei = w3.from_wei(base_fee, "gwei")
print(f"Datos reales: ETH ~${eth_price_usd} USD | Base fee ~{base_fee_gwei:.4f} Gwei")

# Usar OpenAI API real para "decidir" si ejecutar transferencia (análisis inteligente)
client = OpenAI(api_key=OPENAI_API_KEY)
prompt = f"""
Analiza si es buen momento para transferir ETH en mainnet:
- Precio ETH: ${eth_price_usd} USD
- Base fee gas: {base_fee_gwei:.4f} Gwei
- Responde SOLO 'SI' si gas < 1 Gwei y precio estable (>1900 USD), o 'NO' si no.
"""
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
)
decision = response.choices[0].message.content.strip()
print(f"Decisión de IA (OpenAI real): {decision}")

if decision != "SI":
    print("IA recomienda NO ejecutar ahora (gas alto o precio inestable). Abortando.")
    raise SystemExit(0)

# Si IA aprueba, proceder con transferencia real 50/50
balance_wei = w3.eth.get_balance(WALLET)
balance_eth = w3.from_wei(balance_wei, "ether")
print(f"Saldo real: {balance_eth:.8f} ETH")

if balance_eth < 0.005:
    print("Saldo bajo. Abortando.")
    raise SystemExit(0)

# Gas dinámico real (corregido: todo en wei)
max_priority_fee = w3.eth.max_priority_fee or w3.to_wei(0.1, "gwei")  # in wei
max_fee_per_gas = base_fee * 2 + max_priority_fee  # in wei, margen conservador
gas_limit = 21000
gas_cost_one_tx = gas_limit * max_fee_per_gas
gas_total_estimate = gas_cost_one_tx * 3  # margen para 2 tx + extra

if balance_wei < gas_total_estimate:
    print("Insuficiente para gas real. Abortando.")
    raise SystemExit(0)

net_wei = balance_wei - gas_total_estimate
half_wei = net_wei // 2

nonce = w3.eth.get_transaction_count(WALLET, "pending")


def send_real_tx(to_addr: str, value_wei: int, nonce_val: int):
    tx = {
        "type": 0x2,
        "chainId": 1,
        "nonce": nonce_val,
        "to": to_addr,
        "value": value_wei,
        "gas": gas_limit,
        "maxFeePerGas": max_fee_per_gas,
        "maxPriorityFeePerGas": max_priority_fee,
    }
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"TX real enviada: {tx_hash.hex()} | Ver: https://etherscan.io/tx/{tx_hash.hex()}")
    return tx_hash


try:
    print("Ejecutando real: 50% a Coinbase...")
    hash1 = send_real_tx(ADDRESS_COINBASE, half_wei, nonce)
    receipt1 = w3.eth.wait_for_transaction_receipt(hash1, timeout=180)
    if receipt1.status != 1:
        raise RuntimeError("TX1 falló")

    print("Ejecutando real: 50% a Binance...")
    hash2 = send_real_tx(ADDRESS_BINANCE, half_wei, nonce + 1)
    receipt2 = w3.eth.wait_for_transaction_receipt(hash2, timeout=180)
    if receipt2.status != 1:
        raise RuntimeError("TX2 falló")

    print("Ejecución real completada. Fondos enviados.")

except Exception as e:
    print(f"Error en ejecución real: {str(e)} – Revisa Etherscan inmediatamente.")

print("BORRA PRIVATE_KEY de .env YA por seguridad.")
