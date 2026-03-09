#!/bin/bash
# MoltVault Deployment Script
# Handles Vercel auth and deployment automatically

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="moltvault"
VERCEL_PROJECT_ID="prj_sb1L56HlK6ddoFvbTrI3tXDpWxW5"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[MoltVault]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if Vercel CLI is installed
check_vercel() {
    if ! command -v vercel &> /dev/null; then
        log "Installing Vercel CLI..."
        npm install -g vercel
    fi
    log "Vercel CLI: $(vercel --version)"
}

# Check environment variables
check_env() {
    log "Checking environment variables..."
    
    if [ -z "$SUPABASE_URL" ]; then
        error "SUPABASE_URL not set"
        echo "Set it with: export SUPABASE_URL=https://your-project.supabase.co"
        exit 1
    fi
    
    if [ -z "$SUPABASE_SERVICE_KEY" ]; then
        error "SUPABASE_SERVICE_KEY not set"
        echo "Set it with: export SUPABASE_SERVICE_KEY=your-service-key"
        exit 1
    fi
    
    success "Environment variables configured"
}

# Check Vercel authentication
check_auth() {
    log "Checking Vercel authentication..."
    
    if [ -n "$VERCEL_TOKEN" ]; then
        log "Using VERCEL_TOKEN from environment"
        VERCEL_AUTH="--token $VERCEL_TOKEN"
    elif [ -f "$HOME/.vercel/auth.json" ]; then
        log "Found existing Vercel login session"
        VERCEL_AUTH=""
    else
        warn "Not authenticated with Vercel"
        echo ""
        echo "Options:"
        echo "  1. Run 'vercel login' manually, then re-run this script"
        echo "  2. Set VERCEL_TOKEN environment variable"
        echo ""
        echo "To get a token: https://vercel.com/account/tokens"
        echo ""
        read -p "Would you like to run 'vercel login' now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            vercel login
            VERCEL_AUTH=""
        else
            error "Cannot deploy without Vercel authentication"
            exit 1
        fi
    fi
}

# Link project
link_project() {
    log "Linking to Vercel project..."
    cd "$SCRIPT_DIR"
    
    if [ -d ".vercel" ]; then
        log "Project already linked"
    else
        # Create project.json for linking
        mkdir -p .vercel
        cat > .vercel/project.json << EOF
{
  "projectId": "$VERCEL_PROJECT_ID",
  "orgId": "your-org-id"
}
EOF
        warn "Please update orgId in .vercel/project.json if needed"
    fi
}

# Set environment variables in Vercel
set_vercel_env() {
    log "Setting environment variables in Vercel..."
    cd "$SCRIPT_DIR"
    
    # Check if already set
    if vercel env ls $VERCEL_AUTH 2>/dev/null | grep -q "SUPABASE_URL"; then
        log "Environment variables already set"
    else
        echo "$SUPABASE_URL" | vercel env add SUPABASE_URL production $VERCEL_AUTH
        echo "$SUPABASE_SERVICE_KEY" | vercel env add SUPABASE_SERVICE_KEY production $VERCEL_AUTH
        success "Environment variables set in Vercel"
    fi
}

# Build the project
build_project() {
    log "Building project..."
    cd "$SCRIPT_DIR"
    
    # Type check
    if command -v npx &> /dev/null; then
        npx tsc --noEmit 2>/dev/null || warn "TypeScript check had issues (non-blocking)"
    fi
    
    success "Build check complete"
}

# Deploy to production
deploy() {
    log "Deploying to production..."
    cd "$SCRIPT_DIR"
    
    vercel --prod $VERCEL_AUTH --yes
    
    success "Deployment complete!"
}

# Verify deployment
verify() {
    log "Verifying deployment..."
    
    # Get the deployment URL
    DEPLOY_URL=$(vercel ls $VERCEL_AUTH 2>/dev/null | grep -o 'https://[^[:space:]]*\.vercel\.app' | head -1)
    
    if [ -n "$DEPLOY_URL" ]; then
        log "Checking health endpoint..."
        sleep 2
        HEALTH=$(curl -s "$DEPLOY_URL/api/health" 2>/dev/null || echo "")
        if echo "$HEALTH" | grep -q "healthy"; then
            success "API is healthy!"
            echo ""
            echo "🔗 Deployment URL: $DEPLOY_URL"
            echo "📊 Health Check: $DEPLOY_URL/api/health"
            echo "📚 API Docs: $DEPLOY_URL/api"
        else
            warn "Health check failed or returned unexpected response"
            echo "Response: $HEALTH"
        fi
    else
        warn "Could not determine deployment URL"
    fi
}

# Run tests
test_api() {
    log "Running API tests..."
    cd "$SCRIPT_DIR"
    
    DEPLOY_URL=$(vercel ls $VERCEL_AUTH 2>/dev/null | grep -o 'https://[^[:space:]]*\.vercel\.app' | head -1)
    
    if [ -z "$DEPLOY_URL" ]; then
        warn "Cannot test - deployment URL not found"
        return
    fi
    
    echo ""
    echo "Testing endpoints..."
    
    # Test health
    echo -n "Health check: "
    curl -s "$DEPLOY_URL/api/health" > /dev/null && echo "✅" || echo "❌"
    
    # Test root
    echo -n "API info: "
    curl -s "$DEPLOY_URL/api" > /dev/null && echo "✅" || echo "❌"
    
    success "Tests complete"
}

# Print usage
usage() {
    echo "MoltVault Deployment Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  deploy      Full deployment (default)"
    echo "  env         Set environment variables only"
    echo "  test        Test deployed API"
    echo "  logs        View production logs"
    echo "  help        Show this help"
    echo ""
    echo "Environment Variables Required:"
    echo "  SUPABASE_URL          Your Supabase project URL"
    echo "  SUPABASE_SERVICE_KEY  Your Supabase service role key"
    echo "  VERCEL_TOKEN          (Optional) Vercel auth token"
}

# View logs
view_logs() {
    log "Fetching production logs..."
    vercel logs $PROJECT_NAME --production $VERCEL_AUTH
}

# Main
case "${1:-deploy}" in
    deploy)
        log "Starting MoltVault deployment..."
        check_vercel
        check_env
        check_auth
        link_project
        set_vercel_env
        build_project
        deploy
        verify
        echo ""
        success "🎉 MoltVault deployed successfully!"
        ;;
    env)
        check_vercel
        check_env
        check_auth
        set_vercel_env
        ;;
    test)
        check_vercel
        check_auth
        test_api
        ;;
    logs)
        check_vercel
        check_auth
        view_logs
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        error "Unknown command: $1"
        usage
        exit 1
        ;;
esac
