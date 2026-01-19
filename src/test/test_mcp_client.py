#!/usr/bin/env python3
"""
MCP клиент для тестирования MCP сервера через JSON-RPC протокол (stdio).

Этот скрипт тестирует MCP сервер через настоящий MCP протокол,
а не через прямой вызов функций Python.
"""

import json
import subprocess
import sys
from pathlib import Path


class MCPClient:
    """Простой MCP клиент для тестирования через stdio"""

    def __init__(self, server_script: str):
        """Инициализация клиента"""
        self.server_script = server_script
        self.process = None
        self.request_id = 0

    def start(self):
        """Запуск MCP сервера через subprocess"""
        script_path = Path(__file__).parent / self.server_script
        self.process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=0,
        )

    def send_request(self, method: str, params: dict = None) -> dict:
        """Отправка JSON-RPC запроса к MCP серверу"""
        if params is None:
            params = {}

        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params if params else {},
        }

        request_str = json.dumps(request) + "\n"
        print(f"[SEND] {request_str.strip()}")
        self.process.stdin.write(request_str)
        self.process.stdin.flush()

        # Читаем ответ (MCP отправляет ответы через stdout)
        response_line = self.process.stdout.readline()
        if response_line:
            try:
                response = json.loads(response_line.strip())
                print(f"[RECV] {json.dumps(response, ensure_ascii=False)[:200]}...")
                return response
            except json.JSONDecodeError as e:
                print(f"[ERROR] Не удалось распарсить JSON: {e}")
                print(f"[ERROR] Ответ сервера: {response_line}")
                return {"error": str(e)}
        return {"error": "No response"}

    def initialize(self) -> dict:
        """Инициализация MCP сессии"""
        return self.send_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

    def list_tools(self) -> dict:
        """Получение списка доступных инструментов"""
        return self.send_request("tools/list")

    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Вызов инструмента MCP сервера"""
        return self.send_request(
            "tools/call", {"name": tool_name, "arguments": arguments}
        )

    def stop(self):
        """Остановка MCP сервера"""
        if self.process:
            self.process.terminate()
            self.process.wait()


def test_mcp_api():
    """Тестирование MCP сервера через JSON-RPC API"""
    print("=" * 70)
    print("Тестирование MCP сервера через JSON-RPC протокол (stdio)")
    print("=" * 70)

    client = MCPClient("mcp_index.py")

    try:
        # Запуск сервера
        print("\n[1] Запуск MCP сервера...")
        client.start()
        print("[OK] Сервер запущен")

        # Инициализация
        print("\n[2] Инициализация MCP сессии...")
        init_response = client.initialize()
        if "result" in init_response:
            print("[OK] Сессия инициализирована")
        else:
            print(f"[ERROR] Ошибка инициализации: {init_response}")

        # Получение списка инструментов
        print("\n[3] Получение списка инструментов...")
        tools_response = client.list_tools()
        if "result" in tools_response and "tools" in tools_response["result"]:
            tools = tools_response["result"]["tools"]
            print(f"[OK] Найдено {len(tools)} инструментов:")
            for tool in tools[:5]:  # Показываем первые 5
                print(f"   - {tool.get('name', 'unknown')}")
        else:
            print(f"[ERROR] Ошибка получения инструментов: {tools_response}")

        # Тест 1: search_docs
        print("\n[4] Тест: search_docs('test', limit=3)...")
        result = client.call_tool("search_docs", {"query": "test", "limit": 3})
        if "result" in result:
            content = result["result"].get("content", [])
            if content and isinstance(content, list) and len(content) > 0:
                text = (
                    content[0].get("text", "")
                    if isinstance(content[0], dict)
                    else str(content[0])
                )
                print(f"[OK] Результат получен ({len(text)} символов)")
                print(f"   Первые 100 символов: {text[:100]}...")
            else:
                print(f"[OK] Результат: {result['result']}")
        else:
            print(f"[ERROR] Ошибка вызова инструмента: {result}")

        # Тест 2: list_docs
        print("\n[5] Тест: list_docs(recursive=False)...")
        result = client.call_tool("list_docs", {"recursive": False})
        if "result" in result:
            content = result["result"].get("content", [])
            if content:
                text = (
                    content[0].get("text", "")
                    if isinstance(content[0], dict)
                    else str(content[0])
                )
                print("[OK] Результат получен")
                print(f"   Первые 150 символов: {text[:150]}...")
            else:
                print(f"[OK] Результат: {result['result']}")
        else:
            print(f"[ERROR] Ошибка вызова инструмента: {result}")

        # Тест 3: list_snapshots
        print("\n[6] Тест: list_snapshots()...")
        result = client.call_tool("list_snapshots", {})
        if "result" in result:
            content = result["result"].get("content", [])
            if content:
                text = (
                    content[0].get("text", "")
                    if isinstance(content[0], dict)
                    else str(content[0])
                )
                print("[OK] Результат получен")
                print(f"   Первые 150 символов: {text[:150]}...")
            else:
                print(f"[OK] Результат: {result['result']}")
        else:
            print(f"[ERROR] Ошибка вызова инструмента: {result}")

        print("\n" + "=" * 70)
        print("Тестирование завершено!")
        print("=" * 70)

    except Exception as e:
        print(f"\n[ERROR] Ошибка тестирования: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Остановка сервера
        print("\n[7] Остановка MCP сервера...")
        client.stop()
        print("[OK] Сервер остановлен")


if __name__ == "__main__":
    test_mcp_api()
