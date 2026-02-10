#!/bin/bash
# 🎯 NEOBOT MVP - COMMANDES PRINCIPALES
# Menu interactif pour contrôler le projet NeoBOT

# Arrêter le script s'il y a une erreur
set -e

# Répertoire racine du projet
ROOT_DIR="/home/tim/neobot-mvp"
cd "$ROOT_DIR" || exit 1

# Couleurs pour afficher le texte de manière lisible
ROUGE='\033[0;31m'
VERT='\033[0;32m'
JAUNE='\033[1;33m'
BLEU='\033[0;34m'
NC='\033[0m' # Pas de couleur

# Fonction : afficher un titre/section
print_section() {
    echo -e "\n${BLEU}================================${NC}"
    echo -e "${BLEU}$1${NC}"
    echo -e "${BLEU}================================${NC}\n"
}

# Fonction : afficher un message de succès (en vert)
print_success() {
    echo -e "${VERT}✅ $1${NC}"
}

# Fonction : afficher un message d'erreur (en rouge)
print_error() {
    echo -e "${ROUGE}❌ $1${NC}"
}

# Fonction : afficher un message informatif (en jaune)
print_info() {
    echo -e "${JAUNE}ℹ️  $1${NC}"
}

# Fonction : afficher le menu principal avec toutes les options
show_menu() {
    print_section "NEOBOT MVP - MENU PRINCIPAL"
    echo "1.  Vérifier l'état du système"
    echo "2.  Diagnostic complet"
    echo "3.  Démarrer tous les services (intégré)"
    echo "4.  Démarrer backend uniquement"
    echo "5.  Démarrer service WhatsApp uniquement"
    echo "6.  Exécuter les tests d'intégration"
    echo "7.  Afficher les logs récents"
    echo "8.  Vérifier l'état Git"
    echo "9.  Voir la documentation du projet"
    echo "10. Résumé rapide des corrections"
    echo "11. Vérifier la santé de la base de données"
    echo "12. Réinitialiser et redémarrer"
    echo "0.  Quitter"
    echo ""
    read -p "Sélectionner option (0-12): " choice
    
    case $choice in
        1) check_status ;;
        2) run_diagnostic ;;
        3) start_integrated ;;
        4) start_backend ;;
        5) start_whatsapp ;;
        6) run_tests ;;
        7) view_logs ;;
        8) check_git ;;
        9) view_docs ;;
        10) quick_summary ;;
        11) db_health ;;
        12) reset_restart ;;
        0) exit 0 ;;
        *) print_error "Option invalide"; show_menu ;;
    esac
}

check_status() {
    print_section "System Status"
    
    print_info "Python Environment"
    python3 --version
    
    print_info "Node.js Environment"
    node --version && npm --version
    
    print_info "Docker Status"
    docker --version
    
    print_info "Service Ports"
    (netstat -tuln 2>/dev/null || ss -tuln) | grep -E ":8000|:3001|:5432" || print_info "No services currently running"
    
    print_info "Backend Dependencies"
    cd "$ROOT_DIR/backend"
    grep -E "fastapi|sqlalchemy|psycopg2|httpx" requirements.txt | head -4 || print_error "Could not check"
    
    print_info "WhatsApp Dependencies"  
    cd "$ROOT_DIR/whatsapp-service"
    npm list --depth=0 2>/dev/null | head -10 || print_error "npm packages not installed"
    
    show_menu
}

run_diagnostic() {
    print_section "Full System Diagnostic"
    
    if [ -f "$ROOT_DIR/scripts/verify_system.sh" ]; then
        bash "$ROOT_DIR/scripts/verify_system.sh"
    else
        print_error "Diagnostic script not found"
    fi
    
    show_menu
}

start_integrated() {
    print_section "Starting All Services (Integrated)"
    
    if [ -f "$ROOT_DIR/scripts/integration_test.sh" ]; then
        bash "$ROOT_DIR/scripts/integration_test.sh"
    else
        print_error "Integration test script not found"
    fi
    
    show_menu
}

start_backend() {
    print_section "Starting Backend Server"
    
    cd "$ROOT_DIR/backend"
    
    print_info "Backend starting on http://localhost:8000"
    print_info "Press Ctrl+C to stop"
    print_info ""
    
    python3 -m uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
}

start_whatsapp() {
    print_section "Starting WhatsApp Service"
    
    cd "$ROOT_DIR/whatsapp-service"
    
    if [ ! -d "node_modules" ]; then
        print_info "Installing npm dependencies..."
        npm install
    fi
    
    print_info "WhatsApp service starting on port 3001"
    print_info "Scan QR code with your phone when prompted"
    print_info "Press Ctrl+C to stop"
    print_info ""
    
    npm start
}

run_tests() {
    print_section "Running Integration Tests"
    
    if [ -f "$ROOT_DIR/scripts/integration_test.sh" ]; then
        bash "$ROOT_DIR/scripts/integration_test.sh"
    else
        print_error "Test script not found"
    fi
    
    show_menu
}

view_logs() {
    print_section "Recent Logs & Status"
    
    echo ""
    print_info "Last 20 lines of available logs:"
    
    if [ -f "$ROOT_DIR/logs/app.log" ]; then
        echo -e "${BLUE}Backend Logs:${NC}"
        tail -10 "$ROOT_DIR/logs/app.log"
    fi
    
    if [ -f "$ROOT_DIR/logs/whatsapp.log" ]; then
        echo -e "${BLUE}WhatsApp Service Logs:${NC}"
        tail -10 "$ROOT_DIR/logs/whatsapp.log"
    fi
    
    show_menu
}

check_git() {
    print_section "Git Status"
    
    echo -e "${BLUE}Current Branch:${NC}"
    git branch -v
    
    echo -e "\n${BLUE}Recent Commits:${NC}"
    git log --oneline -5
    
    echo -e "\n${BLUE}Working Directory:${NC}"
    git status
    
    show_menu
}

view_docs() {
    print_section "Project Documentation"
    
    docs_dir="$ROOT_DIR/docs"
    if [ -d "$docs_dir" ]; then
        echo "Available documentation files:"
        ls -1 "$docs_dir" | sed 's/^/  - /'
        echo ""
        read -p "Enter filename to view (or press Enter to skip): " doc_file
        if [ -n "$doc_file" ]; then
            if [ -f "$docs_dir/$doc_file" ]; then
                less "$docs_dir/$doc_file"
            else
                print_error "File not found: $doc_file"
            fi
        fi
    else
        print_error "Documentation directory not found"
    fi
    
    show_menu
}

quick_summary() {
    print_section "Quick Fix Summary"
    
    if [ -f "$ROOT_DIR/QUICK_FIX_SUMMARY.md" ]; then
        cat "$ROOT_DIR/QUICK_FIX_SUMMARY.md"
    else
        print_error "Quick fix summary not found"
    fi
    
    show_menu
}

db_health() {
    print_section "Database Health Check"
    
    cd "$ROOT_DIR/backend"
    
    print_info "Checking PostgreSQL configuration..."
    
    if grep -q "DATABASE_URL" .env 2>/dev/null; then
        print_success "DATABASE_URL configured"
    else
        print_error "DATABASE_URL not configured in .env"
    fi
    
    print_info "Checking psycopg2-binary installation..."
    if grep -q "psycopg2-binary" requirements.txt; then
        print_success "PostgreSQL driver configured"
    else
        print_error "PostgreSQL driver missing"
    fi
    
    print_info "Checking connection pooling..."
    if grep -q "pool_size\|POOL_SIZE" app/database.py; then
        print_success "Connection pooling configured"
    else
        print_error "Connection pooling not configured"
    fi
    
    show_menu
}

reset_restart() {
    print_section "Reset & Restart Services"
    
    read -p "This will stop all services. Continue? (y/n): " confirm
    if [ "$confirm" != "y" ]; then
        show_menu
        return
    fi
    
    print_info "Stopping services..."
    pkill -f "uvicorn" || true
    pkill -f "npm start" || true
    pkill -f "node index.js" || true
    
    print_info "Clearing caches..."
    cd "$ROOT_DIR/backend"
    rm -rf __pycache__ .pytest_cache
    
    cd "$ROOT_DIR/whatsapp-service"
    rm -rf .cache
    
    print_success "Ready to restart. Use options 4 & 5 to start services"
    show_menu
}

# Main entry point
if [ "$#" -eq 0 ]; then
    show_menu
else
    case $1 in
        status) check_status ;;
        diagnostic) run_diagnostic ;;
        start-all) start_integrated ;;
        start-backend) start_backend ;;
        start-whatsapp) start_whatsapp ;;
        test) run_tests ;;
        logs) view_logs ;;
        git) check_git ;;
        docs) view_docs ;;
        summary) quick_summary ;;
        db) db_health ;;
        reset) reset_restart ;;
        *)
            echo "Usage: $0 [command]"
            echo "Commands:"
            echo "  status          - Check system status"
            echo "  diagnostic      - Run full diagnostic"
            echo "  start-all       - Start all services"
            echo "  start-backend   - Start backend only"
            echo "  start-whatsapp  - Start WhatsApp service only"
            echo "  test            - Run integration tests"
            echo "  logs            - View recent logs"
            echo "  git             - Show git status"
            echo "  docs            - View documentation"
            echo "  summary         - Show quick summary"
            echo "  db              - Database health check"
            echo "  reset           - Reset and restart services"
            echo ""
            echo "Run with no arguments for interactive menu"
            exit 1
            ;;
    esac
fi
