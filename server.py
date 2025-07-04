from aiohttp import web
import server
import os
import json

SESSION_KEYS = {}


def generate_key():
    return os.urandom(32)


@server.PromptServer.instance.routes.post("/ram_nodes/get_key")
async def get_key(request):
    """API endpoint to generate and return a session key."""
    try:
        try:
            json_data = await request.json()
            client_id = json_data.get("client_id")
        except json.JSONDecodeError:
            return web.json_response({"error": "Invalid JSON in request body"}, status=400)

        if not client_id:
            return web.json_response({"error": "Client ID is required"}, status=400)

        key = generate_key()
        SESSION_KEYS[client_id] = key

        return web.json_response({"key": key.hex()})
    except Exception as e:
        print(f"Error in /ram_nodes/get_key: {e}")
        return web.json_response({"error": str(e)}, status=500)


@server.PromptServer.instance.routes.post("/ram_nodes/validate_key")
async def validate_key(request):
    """API endpoint to validate a client's session key."""
    try:
        json_data = await request.json()
        client_id = json_data.get("client_id")
        key_hex = json_data.get("key_hex")

        if not client_id or not key_hex:
            return web.json_response({"error": "Client ID and key are required"}, status=400)

        server_key = SESSION_KEYS.get(client_id)

        if server_key and server_key.hex() == key_hex:
            return web.json_response({"valid": True})
        else:
            return web.json_response({"valid": False})

    except Exception as e:
        print(f"Error in /ram_nodes/validate_key: {e}")
        return web.json_response({"error": str(e)}, status=500)


def get_session_key(client_id):
    return SESSION_KEYS.get(client_id)