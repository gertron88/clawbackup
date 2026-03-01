#!/bin/bash
# ClawBackup Live Demo Script
# Run this to showcase the working API

echo "🛡️  CLAWBACKUP LIVE DEMO"
echo "========================"
echo ""
echo "API Endpoint: https://clawbackup-api.vercel.app/api"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}1. Health Check${NC}"
echo "----------------"
curl -s https://clawbackup-api.vercel.app/api/health | python3 -m json.tool 2>/dev/null || curl -s https://clawbackup-api.vercel.app/api/health
echo ""

echo -e "${BLUE}2. Register New Agent${NC}"
echo "----------------------"
RESPONSE=$(curl -s -X POST https://clawbackup-api.vercel.app/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"agent_name\":\"demo-agent-$(date +%s)\",\"email\":\"demo@test.com\",\"moltbook_username\":\"@demo\"}")

echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Extract API key
API_KEY=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('api_key',''))" 2>/dev/null)

if [ -n "$API_KEY" ]; then
    echo -e "${GREEN}✅ Agent registered!${NC}"
    echo ""
    
    echo -e "${BLUE}3. Create Backup${NC}"
    echo "-----------------"
    curl -s -X POST https://clawbackup-api.vercel.app/api/v1/backups \
      -H "Authorization: Bearer $API_KEY" \
      -H "Content-Type: application/json" \
      -d '{"name":"demo-backup","tags":["demo","test"],"size_bytes":1024,"content_hash":"demo123"}' | \
      python3 -m json.tool 2>/dev/null || echo "Backup creation attempted"
    echo ""
    
    echo -e "${BLUE}4. List Backups${NC}"
    echo "----------------"
    curl -s https://clawbackup-api.vercel.app/api/v1/backups \
      -H "Authorization: Bearer $API_KEY" | \
      python3 -m json.tool 2>/dev/null || echo "List attempted"
    echo ""
    
    echo -e "${GREEN}✅ Demo complete!${NC}"
else
    echo -e "${BLUE}Note: Agent name may already exist, try running again${NC}"
fi

echo ""
echo "========================"
echo "🔗 Links:"
echo "   API: https://clawbackup-api.vercel.app/api"
echo "   GitHub: https://github.com/gertron88/clawbackup"
echo ""
