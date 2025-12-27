#!/bin/bash
# Ultra Research System - Startup Script
# Kimi Researcher-class Scientific Literature Discovery Engine

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_banner() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║          🔬 Ultra Research System v1.0.0                      ║"
    echo "║     Kimi Researcher-class Literature Discovery Engine         ║"
    echo "╠═══════════════════════════════════════════════════════════════╣"
    echo "║  • 70+ Data Sources    • Multi-turn Reasoning                 ║"
    echo "║  • 50+ Publishers      • Citation Networks                    ║"
    echo "║  • Complete Coverage   • FREE & Open Source                   ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_java() {
    if command -v java &> /dev/null; then
        JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
        if [ "$JAVA_VERSION" -ge 17 ]; then
            echo -e "${GREEN}✓${NC} Java $JAVA_VERSION detected"
            return 0
        fi
    fi
    echo -e "${RED}✗${NC} Java 17+ required. Please install Java 17 or later."
    return 1
}

check_maven() {
    if command -v mvn &> /dev/null; then
        MVN_VERSION=$(mvn -version 2>&1 | head -n 1)
        echo -e "${GREEN}✓${NC} Maven detected: $MVN_VERSION"
        return 0
    fi
    echo -e "${YELLOW}!${NC} Maven not found. Will use mvnw wrapper if available."
    return 0
}

check_python() {
    if command -v python3 &> /dev/null; then
        PY_VERSION=$(python3 --version 2>&1)
        echo -e "${GREEN}✓${NC} $PY_VERSION detected"
        return 0
    fi
    echo -e "${YELLOW}!${NC} Python 3 not found. Google Scholar integration will be limited."
    return 0
}

setup_python() {
    echo -e "${BLUE}Setting up Python environment...${NC}"
    
    cd python-utils
    
    # Create virtual environment if not exists
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    # Activate and install dependencies
    source venv/bin/activate
    pip install -q -r requirements.txt
    
    echo -e "${GREEN}✓${NC} Python dependencies installed"
    cd ..
}

build_java() {
    echo -e "${BLUE}Building Java backend...${NC}"
    
    cd java-backend
    
    if [ -f "mvnw" ]; then
        ./mvnw clean package -DskipTests -q
    else
        mvn clean package -DskipTests -q
    fi
    
    echo -e "${GREEN}✓${NC} Java backend built successfully"
    cd ..
}

check_config() {
    echo -e "${BLUE}Checking configuration...${NC}"
    
    CONFIG_OK=true
    
    # Check required API keys
    if [ -z "$NCBI_API_KEY" ]; then
        echo -e "${YELLOW}!${NC} NCBI_API_KEY not set (PubMed will have reduced rate limit)"
    else
        echo -e "${GREEN}✓${NC} NCBI_API_KEY configured"
    fi
    
    if [ -z "$NCBI_EMAIL" ]; then
        echo -e "${YELLOW}!${NC} NCBI_EMAIL not set (required for PubMed)"
    else
        echo -e "${GREEN}✓${NC} NCBI_EMAIL configured"
    fi
    
    if [ -z "$UNPAYWALL_EMAIL" ]; then
        echo -e "${YELLOW}!${NC} UNPAYWALL_EMAIL not set (open access detection limited)"
    else
        echo -e "${GREEN}✓${NC} UNPAYWALL_EMAIL configured"
    fi
    
    # Optional but recommended
    if [ -n "$SEMANTIC_SCHOLAR_KEY" ]; then
        echo -e "${GREEN}✓${NC} SEMANTIC_SCHOLAR_KEY configured"
    fi
    
    if [ -n "$SPRINGER_API_KEY" ]; then
        echo -e "${GREEN}✓${NC} SPRINGER_API_KEY configured"
    fi
    
    echo ""
}

run_search() {
    QUERY="$1"
    
    if [ -z "$QUERY" ]; then
        echo -e "${RED}Error: No search query provided${NC}"
        echo "Usage: $0 search \"your query\""
        exit 1
    fi
    
    JAR_FILE="java-backend/target/ultra-research-system-1.0.0.jar"
    
    if [ ! -f "$JAR_FILE" ]; then
        echo -e "${YELLOW}JAR not found, building...${NC}"
        build_java
    fi
    
    java -jar "$JAR_FILE" search "$QUERY"
}

run_server() {
    PORT="${1:-8080}"
    
    JAR_FILE="java-backend/target/ultra-research-system-1.0.0.jar"
    
    if [ ! -f "$JAR_FILE" ]; then
        echo -e "${YELLOW}JAR not found, building...${NC}"
        build_java
    fi
    
    java -jar "$JAR_FILE" serve --port "$PORT"
}

show_help() {
    print_banner
    echo "USAGE:"
    echo "  ./start.sh <command> [options]"
    echo ""
    echo "COMMANDS:"
    echo "  setup       Install dependencies and build"
    echo "  search      Run a search query"
    echo "  serve       Start API server"
    echo "  config      Show configuration status"
    echo "  sources     List available data sources"
    echo "  help        Show this help"
    echo ""
    echo "EXAMPLES:"
    echo "  ./start.sh setup"
    echo "  ./start.sh search \"CRISPR gene therapy\""
    echo "  ./start.sh serve 8080"
    echo ""
    echo "ENVIRONMENT VARIABLES:"
    echo "  NCBI_API_KEY        PubMed API key (get at ncbi.nlm.nih.gov)"
    echo "  NCBI_EMAIL          Email for PubMed"
    echo "  UNPAYWALL_EMAIL     Email for Unpaywall"
    echo "  SEMANTIC_SCHOLAR_KEY  Semantic Scholar API key"
    echo "  SPRINGER_API_KEY    Springer Nature API key"
    echo "  IEEE_API_KEY        IEEE Xplore API key"
    echo ""
}

# Main script logic
case "$1" in
    setup)
        print_banner
        echo -e "${BLUE}Setting up Ultra Research System...${NC}"
        echo ""
        check_java
        check_maven
        check_python
        echo ""
        setup_python
        build_java
        echo ""
        echo -e "${GREEN}Setup complete!${NC}"
        echo "Run './start.sh search \"your query\"' to start searching."
        ;;
    
    search)
        shift
        run_search "$*"
        ;;
    
    serve)
        run_server "${2:-8080}"
        ;;
    
    config)
        print_banner
        check_config
        ;;
    
    sources)
        JAR_FILE="java-backend/target/ultra-research-system-1.0.0.jar"
        if [ -f "$JAR_FILE" ]; then
            java -jar "$JAR_FILE" sources
        else
            echo "Run './start.sh setup' first to build the system."
        fi
        ;;
    
    help|--help|-h|"")
        show_help
        ;;
    
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac
