# Arsify API - Tailscale Buffer Zone (using api.upshalter.com)
# Only accessible via Tailscale (100.64.0.0/10)

server {
    listen 100.109.101.58:80;
    server_name api.upshalter.com;
    
    # Security - only allow Tailscale range
    allow 100.64.0.0/10;
    deny all;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # Landing page for Tailscale users
    location = / {
        return 200 "🚀 Arsify MoE - Tailscale Buffer Zone\n\nAccess: Tailscale only (100.64.0.0/10)\nVersion: 3.0.0\n\nEndpoints:\n- /v1/* : OpenAI API\n- /control : Control Panel\n- /admin : Admin Dashboard\n- /health : Health Check\n\n---\nUpshalter × Arsify Collaboration";
        add_header Content-Type text/plain;
    }
    
    # Health endpoint (Tailscale only)
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # OpenAI-compatible API (full access for Tailscale users)
    location /v1/ {
        proxy_pass http://127.0.0.1:8000/v1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
    }
    
    # Control Panel (Tailscale only)
    location /control {
        proxy_pass http://127.0.0.1:8000/control;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Admin Dashboard (Tailscale only)
    location /admin {
        proxy_pass http://127.0.0.1:8000/admin;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Documentation
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
    }
}
