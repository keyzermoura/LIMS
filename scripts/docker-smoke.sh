#!/usr/bin/env bash
# Smoke test da stack Docker: banco -> migrações -> API -> Nginx/SPA.
#
# Roda depois de `docker compose up -d` e do seed. Valida o que os testes
# unitários não cobrem: as imagens reais, o proxy do Nginx e o schema criado
# por `alembic upgrade head` com AUTO_CREATE_SCHEMA=false.

set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
WEB_URL="${WEB_URL:-http://localhost:8080}"
TIMEOUT="${TIMEOUT:-180}"

info() { printf '==> %s\n' "$*"; }
die() { printf 'ERRO: %s\n' "$*" >&2; exit 1; }

# Valida o JSON recebido no stdin com uma expressão Python.
check_json() {
  python3 -c "import json, sys; data = json.load(sys.stdin); assert $1, data; print('   ok')"
}

# A rota /auth/login segue o password grant do OAuth2: corpo
# application/x-www-form-urlencoded, não JSON (igual ao front-end).
login() {
  curl -fsS -X POST "$API_URL/api/v1/auth/login" \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    --data-urlencode "username=$1" \
    --data-urlencode "password=$2" \
    | python3 -c 'import json, sys; print(json.load(sys.stdin)["access_token"])'
}

info "Aguardando API em $API_URL/health"
deadline=$((SECONDS + TIMEOUT))
until curl -fsS "$API_URL/health" -o /tmp/lims-health.json 2>/dev/null; do
  (( SECONDS < deadline )) || die "API não respondeu em ${TIMEOUT}s"
  sleep 2
done
check_json "data['status'] == 'ok' and data['database'] == 'up'" < /tmp/lims-health.json

info "Aguardando SPA em $WEB_URL"
until curl -fsS "$WEB_URL/" -o /tmp/lims-index.html 2>/dev/null; do
  (( SECONDS < deadline )) || die "SPA não respondeu em ${TIMEOUT}s"
  sleep 2
done
grep -qi "<title>LIMS" /tmp/lims-index.html || die "index.html inesperado"

info "API publicada pelo Nginx (mesma origem, sem CORS)"
curl -fsS "$WEB_URL/api/v1/meta" | check_json "'project' in data"

info "Login e leitura autenticada (perfil fiscal)"
TOKEN=$(login fiscal 'Fiscal@Lims2026') || die "login do fiscal falhou"
[ -n "$TOKEN" ] || die "login não retornou access_token"
curl -fsS "$API_URL/api/v1/samples?size=5" \
  -H "Authorization: Bearer $TOKEN" | check_json "data['total'] >= 1"

info "Trilha de auditoria e verificação da cadeia (perfil auditor)"
AUDITOR=$(login auditor 'Auditor@Lims2026') || die "login do auditor falhou"
curl -fsS "$API_URL/api/v1/audit?size=5" \
  -H "Authorization: Bearer $AUDITOR" | check_json "data['total'] >= 1"
curl -fsS -X POST "$API_URL/api/v1/audit/verify" \
  -H "Authorization: Bearer $AUDITOR" \
  | check_json "data['ok'] is True and data['checked'] >= 1"

info "Smoke test concluído"
