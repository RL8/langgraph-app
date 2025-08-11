#!/usr/bin/env python3
"""Simple local CORS proxy for LangGraph server."""

from flask import Flask, request, Response
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)

# LangGraph server URL
LANGGRAPH_URL = "http://127.0.0.1:2025"

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def proxy(path):
    """Proxy all requests to the LangGraph server."""
    try:
        # Build the target URL
        target_url = f"{LANGGRAPH_URL}/{path}"
        
        # Forward the request
        if request.method == 'GET':
            response = requests.get(target_url, params=request.args)
        elif request.method == 'POST':
            response = requests.post(target_url, json=request.get_json(), params=request.args)
        elif request.method == 'PUT':
            response = requests.put(target_url, json=request.get_json(), params=request.args)
        elif request.method == 'DELETE':
            response = requests.delete(target_url, params=request.args)
        else:
            return Response("Method not allowed", status=405)
        
        # Return the response with CORS headers
        return Response(
            response.content,
            status=response.status_code,
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Content-Type': response.headers.get('Content-Type', 'application/json')
            }
        )
        
    except requests.exceptions.ConnectionError:
        return Response(
            json.dumps({"error": "Cannot connect to LangGraph server. Make sure it's running on port 2025."}),
            status=503,
            headers={'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
        )
    except Exception as e:
        return Response(
            json.dumps({"error": f"Proxy error: {str(e)}"}),
            status=500,
            headers={'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
        )

@app.route('/health')
def health():
    """Health check endpoint."""
    return Response(
        json.dumps({"status": "healthy", "service": "cors-proxy", "target": LANGGRAPH_URL}),
        status=200,
        headers={'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
    )

if __name__ == '__main__':
    print(f"🚀 Starting CORS proxy on http://127.0.0.1:8080")
    print(f"📡 Proxying to: {LANGGRAPH_URL}")
    print(f"🌐 Use this URL in agentchat.vercel.app: http://127.0.0.1:8080")
    app.run(host='0.0.0.0', port=8080, debug=True)
