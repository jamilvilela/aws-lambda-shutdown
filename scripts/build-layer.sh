#!/bin/bash
#===============================================================================
# build-layer.sh
# Prepara o conteúdo da Layer da Lambda com as dependências de runtime que NÃO
# fazem parte do runtime Python da AWS (ex.: jsonschema). O boto3/botocore são
# fornecidos pelo runtime e ficam de fora.
#
# Uso:
#   ./scripts/build-layer.sh                                  # padrão: cp313 + x86_64
#   ./scripts/build-layer.sh --python-version 3.12            # outra versão
#   ./scripts/build-layer.sh --arch arm64                     # wheels aarch64
#
# O resultado é o diretório build/layer, que o Terraform zips em dist/layer.zip
# (data.archive_file.lambda_layer) e anexa à função via aws_lambda_layer_version.
#
# Nota: a instalação cruzada baixa wheels manylinux (Linux) via pip, funcionando
# inclusive em Windows/macOS. Alternativa com Docker:
#   docker run --rm -v "$(pwd)":/app -w /app python:3.13-slim \
#     sh -c "pip install -r requirements-lambda.txt \
#            --target /app/build/layer/python/lib/python3.13/site-packages"
#===============================================================================

set -euo pipefail

# ─── Configurações ───────────────────────────────────────────────────────────
PYTHON_VERSION="${PYTHON_VERSION_LAMBDA:-3.13}"
ARCH="${LAMBDA_ARCH:-x86_64}"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TARGET_DIR="${REPO_DIR}/build/layer/python/lib/python${PYTHON_VERSION}/site-packages"

# ─── Cores para output ───────────────────────────────────────────────────────
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ─── Parse de argumentos ─────────────────────────────────────────────────────
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --python-version)
                PYTHON_VERSION="$2"
                shift 2
                ;;
            --arch)
                ARCH="$2"
                shift 2
                ;;
            -h|--help)
                echo "Uso: $0 [--python-version 3.13] [--arch x86_64|arm64]"
                exit 0
                ;;
            *)
                log_error "Argumento desconhecido: $1"
                exit 1
                ;;
        esac
    done
}

# ─── Mapeia arquitetura → plataforma manylinux ──────────────────────────────
manylinux_platform() {
    if [[ "${ARCH}" == "arm64" ]]; then
        echo "manylinux2014_aarch64"
    else
        echo "manylinux2014_x86_64"
    fi
}

# ─── Limpa e recria o diretório da layer ─────────────────────────────────────
reset_target() {
    log_info "Limpando build/layer ..."
    rm -rf "${REPO_DIR}/build/layer"
    mkdir -p "${TARGET_DIR}"
    log_ok "Diretório criado: ${TARGET_DIR}"
}

# ─── Instala as dependências (wheels Linux) ──────────────────────────────────
install_deps() {
    local platform
    platform="$(manylinux_platform)"
    log_info "Instalando dependências (cp${PYTHON_VERSION} / ${platform}) ..."
    cd "${REPO_DIR}"
    python -m pip install \
        -r requirements-lambda.txt \
        --platform "${platform}" \
        --implementation cp \
        --python-version "${PYTHON_VERSION}" \
        --only-binary=:all: \
        --upgrade \
        --target "${TARGET_DIR}"
    log_ok "Dependências instaladas em build/layer (tamanho: $(du -sh build/layer | cut -f1))"
}

# ─── Main ────────────────────────────────────────────────────────────────────
parse_args "$@"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Build Layer - aws-lambda-shutdown"
echo "  Python: ${PYTHON_VERSION} | Arquitetura: ${ARCH}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
reset_target
install_deps
log_ok "Layer pronta. Execute 'terraform apply' em infra/ para publicar."