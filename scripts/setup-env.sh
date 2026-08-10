#!/bin/bash
#===============================================================================
# setup-env.sh
# Script de deploy do ambiente AWS para a Lambda de shutdown (aws-lambda-shutdown)
#
# Uso:
#   ./scripts/setup-env.sh                          # Usa valores default (prod)
#   ./scripts/setup-env.sh -e dev                    # Ambiente específico
#   ./scripts/setup-env.sh -e prod -r us-east-1      # Ambiente + região
#
# Dependências:
#   - Terraform >= 1.5
#   - AWS CLI >= 2.0
#
# Observações:
#   - O pacote da Lambda é gerado pelo próprio Terraform (provider archive),
#     sem etapa externa de zip via shell.
#   - Os EventBridge Schedulers não são gerenciados pelo Terraform; após o
#     apply, gere-os com `python -m src generate-schedulers` (ver README).
#===============================================================================

set -euo pipefail

# ─── Configurações ───────────────────────────────────────────────────────────
ENV="prod"
REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "000000000000")
TERRAFORM_DIR="$(cd "$(dirname "$0")/../infra" && pwd)"
TFVARS_FILE="${TERRAFORM_DIR}/terraform.tfvars"
TFVARS_EXAMPLE="${TERRAFORM_DIR}/terraform.tfvars.example"

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

# ─── Pré-requisitos ──────────────────────────────────────────────────────────
check_prerequisites() {
    log_info "Verificando pré-requisitos..."

    if ! command -v terraform &>/dev/null; then
        log_error "Terraform não encontrado. Instale em: https://developer.hashicorp.com/terraform/downloads"
        exit 1
    fi
    log_ok "Terraform $(terraform --version | head -1)"

    if ! command -v aws &>/dev/null; then
        log_error "AWS CLI não encontrado. Instale em: https://aws.amazon.com/cli/"
        exit 1
    fi
    log_ok "AWS CLI $(aws --version 2>&1 | cut -d' ' -f1)"

    # Verificar credenciais AWS
    if ! aws sts get-caller-identity &>/dev/null; then
        log_error "Credenciais AWS não configuradas. Execute 'aws configure' primeiro."
        exit 1
    fi
    log_ok "Credenciais AWS válidas (Account: ${ACCOUNT_ID})"

    # Verificar existência do terraform.tfvars
    if [[ ! -f "${TFVARS_FILE}" ]]; then
        log_error "Arquivo ${TFVARS_FILE} não encontrado."
        log_error "Copie o exemplo e preencha os valores:"
        log_error "  cp ${TFVARS_EXAMPLE} ${TFVARS_FILE}"
        exit 1
    fi
    log_ok "terraform.tfvars encontrado"
}

# ─── Inicializar Terraform ───────────────────────────────────────────────────
init_terraform() {
    log_info "Inicializando Terraform em ${TERRAFORM_DIR}..."
    cd "${TERRAFORM_DIR}"
    terraform init
    log_ok "Terraform init concluído"
}

# ─── Selecionar/Criar Workspace ──────────────────────────────────────────────
select_workspace() {
    log_info "Selecionando workspace Terraform '${ENV}'..."
    cd "${TERRAFORM_DIR}"

    if terraform workspace list 2>/dev/null | grep -q " ${ENV}$"; then
        terraform workspace select "${ENV}"
    else
        log_info "Criando workspace '${ENV}'..."
        terraform workspace new "${ENV}"
    fi
    log_ok "Workspace '${ENV}' ativo"
}

# ─── Aplicar Terraform ───────────────────────────────────────────────────────
apply_terraform() {
    log_info "Aplicando Terraform..."
    cd "${TERRAFORM_DIR}"

    # O pacote da Lambda (data.archive_file) e o upload do config.json ao S3
    # são gerados automaticamente durante o apply.
    terraform apply \
        -var="environment=${ENV}" \
        -auto-approve

    log_ok "Terraform apply concluído"
}

# ─── Resumo do deploy ────────────────────────────────────────────────────────
print_summary() {
    cd "${TERRAFORM_DIR}"
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo -e "${GREEN}  Deploy concluído com sucesso!${NC}"
    echo "  Environment: ${ENV} | Account: ${ACCOUNT_ID} | Região: ${REGION}"
    echo ""
    echo "  Lambda ARN:           $(terraform output -raw lambda_arn)"
    echo "  Bucket config:        $(terraform output -raw config_bucket_name)"
    echo "  SNS Topic ARN:        $(terraform output -raw sns_topic_arn)"
    echo ""
    echo "  Próximo passo: gerar os EventBridge Schedulers"
    echo -e "  ${CYAN}export LAMBDA_ARN=\$(terraform output -raw lambda_arn)${NC}"
    echo -e "  ${CYAN}export SCHEDULER_ROLE_ARN=\$(terraform output -raw scheduler_role_arn)${NC}"
    echo -e "  ${CYAN}python -m src generate-schedulers  (na raiz do repositório)${NC}"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
}

# ─── Main ────────────────────────────────────────────────────────────────────
main() {
    parse_args "$@"

    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  Setup Environment - aws-lambda-shutdown"
    echo "  Ambiente: ${ENV} | Account: ${ACCOUNT_ID} | Região: ${REGION}"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    check_prerequisites
    init_terraform
    select_workspace
    apply_terraform
    print_summary
}

main "$@"