#!/bin/bash
#===============================================================================
# rollback-setup.sh
# Script de rollback do ambiente AWS para a Lambda de shutdown (aws-lambda-shutdown)
#
# Uso:
#   ./scripts/rollback-setup.sh                          # Usa valores default (prod)
#   ./scripts/rollback-setup.sh -e dev                    # Ambiente específico
#   ./scripts/rollback-setup.sh -e prod -r us-east-1      # Ambiente + região
#
# Dependências:
#   - Terraform >= 1.5
#   - AWS CLI >= 2.0
#
# Observações:
#   - Destrói APENAS os recursos gerenciados pelo Terraform (Lambda, IAM, SNS,
#     S3, permissões). Artefatos e configs não são removidos do S3 por este script.
#   - Os EventBridge Schedulers (shutdown-*) NÃO são gerenciados pelo Terraform.
#     Remova-os manualmente (Console ou `aws scheduler delete-schedule`).
#===============================================================================

set -euo pipefail

# ─── Configurações ───────────────────────────────────────────────────────────
ENV="prod"
REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "000000000000")
TERRAFORM_DIR="$(cd "$(dirname "$0")/../infra" && pwd)"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ─── Parse de argumentos ─────────────────────────────────────────────────────
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENV="$2"
                shift 2
                ;;
            -r|--region)
                REGION="$2"
                shift 2
                ;;
            -h|--help)
                echo "Uso: $0 [-e env] [-r region]"
                echo "  -e, --environment   Ambiente (dev, staging, prod)  [default: prod]"
                echo "  -r, --region        Região AWS                     [default: us-east-1]"
                exit 0
                ;;
            *)
                log_error "Argumento desconhecido: $1"
                exit 1
                ;;
        esac
    done
}

# ─── Confirmação ─────────────────────────────────────────────────────────────
confirm_rollback() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo -e "${RED}  ATENÇÃO: Rollback do ambiente '${ENV}'${NC}"
    echo "  Account: ${ACCOUNT_ID}"
    echo "  Região:  ${REGION}"
    echo "  ⚠️  EventBridge Schedulers ('shutdown-*') não são removidos"
    echo "     por este script (não são gerenciados pelo Terraform)."
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    read -p "Deseja continuar? (s/N): " confirm
    if [[ ! "$confirm" =~ ^[sS]$ ]]; then
        log_info "Rollback cancelado."
        exit 0
    fi
}

# ─── Destroy Terraform ──────────────────────────────────────────────────────
destroy_terraform() {
    log_info "Destruindo recursos Terraform do ambiente '${ENV}'..."
    cd "${TERRAFORM_DIR}"

    if [ -d ".terraform" ]; then
        if terraform workspace list 2>/dev/null | grep -q " ${ENV}$"; then
            terraform workspace select "${ENV}"
        fi
        terraform destroy \
            -var="environment=${ENV}" \
            -auto-approve
        log_ok "Recursos Terraform destruídos"
    else
        log_warn "Terraform não inicializado. Execute 'terraform init' primeiro."
    fi
}

# ─── Limpeza adicional (documentada) ────────────────────────────────────────
# O bucket S3 não é limpo por este script para evitar deleção acidental.
# Para remover o conteúdo do bucket, use: aws s3 rm s3://<bucket>/ --recursive
# Os EventBridge Schedulers 'shutdown-*' devem ser removidos manualmente:
#   aws scheduler delete-schedule --name <schedule-name>

# ─── Main ────────────────────────────────────────────────────────────────────
main() {
    parse_args "$@"
    confirm_rollback

    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  Rollback - aws-lambda-shutdown"
    echo "  Ambiente: ${ENV} | Account: ${ACCOUNT_ID} | Região: ${REGION}"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    destroy_terraform

    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo -e "${GREEN}  Rollback concluído com sucesso!${NC}"
    echo "  Recursos do ambiente '${ENV}' removidos."
    echo "  Lembre-se de remover manualmente os EventBridge Schedulers"
    echo "  'shutdown-*' e o conteúdo do bucket S3, se desejado."
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
}

main "$@"