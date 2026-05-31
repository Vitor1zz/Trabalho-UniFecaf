"""
Conecta o Trivago Food ao iFood via navegador.
1. Abre o iFood no Chrome
2. Voce faz login (se necessario)
3. Salva a sessao em ifood_session.json
4. Baixa restaurantes para dados_ifood.json

Uso: python conectar_ifood.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SESSION_FILE = ROOT / "ifood_session.json"


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Instale o Playwright:")
        print("  pip install playwright")
        print("  playwright install chromium")
        sys.exit(1)

    captured_headers = {}

    def on_request(request):
        if "marketplace.ifood.com.br" not in request.url:
            return
        for key in (
            "authorization",
            "x-ifood-session-id",
            "x-ifood-device-id",
            "x-ifood-user-id",
            "x-client-application-key",
        ):
            value = request.headers.get(key)
            if value and key not in captured_headers:
                captured_headers[key] = value

    print("Abrindo iFood no navegador...")
    print("Faca login se pedido, depois navegue um pouco e pressione ENTER aqui.")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(locale="pt-BR")
        page = context.new_page()
        page.on("request", on_request)
        page.goto("https://www.ifood.com.br/", wait_until="domcontentloaded", timeout=60000)
        input("\nPressione ENTER apos o iFood carregar (logado)... ")

        if not captured_headers.get("authorization"):
            print("Nenhum token capturado. Tente buscar um restaurante no site e pressione ENTER de novo.")
            input("ENTER... ")

        if not captured_headers.get("authorization"):
            print("Falhou ao capturar sessao. Copie headers manualmente para ifood_session.json")
            browser.close()
            sys.exit(1)

        with SESSION_FILE.open("w", encoding="utf-8") as file:
            json.dump(captured_headers, file, indent=2)
        print(f"Sessao salva em: {SESSION_FILE}")

        browser.close()

    print("Sincronizando restaurantes...")
    import ifood_service

    data, error = ifood_service.buscar_ifood_api("")
    if data:
        print(f"OK! {len(data['merchants'])} restaurantes salvos em dados_ifood.json")
    else:
        print(f"Aviso: {error}")
        print("A sessao foi salva; tente Atualizar precos iFood no site.")


if __name__ == "__main__":
    main()
