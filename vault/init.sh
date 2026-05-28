#!/bin/sh
set -e

VAULT_ADDR="${VAULT_ADDR:-http://vault:8200}"
VAULT_TOKEN="${VAULT_TOKEN:-dev-root-token}"

export VAULT_ADDR
export VAULT_TOKEN

wait_for_vault() {
    echo "Waiting for Vault to be ready..."
    max_attempts=30
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if vault status > /dev/null 2>&1; then
            echo "Vault is ready!"
            return 0
        fi
        attempt=$((attempt + 1))
        echo "Attempt $attempt/$max_attempts: Vault not ready yet..."
        sleep 2
    done
    echo "ERROR: Vault did not become ready in time"
    return 1
}

enable_kv_secrets() {
    echo "Enabling KV secrets engine..."
    vault secrets enable -path=secret kv-v2 2>/dev/null || echo "KV already enabled"
}

create_secrets() {
    echo "Creating secrets..."

    vault kv put secret/fishmap/auth/jwt \
        secret_key="${SECRET_KEY:-dev-secret-key-change-in-production-min-32-chars}"

    vault kv put secret/fishmap/database/postgres \
        password="${POSTGRES_PASSWORD:-postgres_password}"

    vault kv put secret/fishmap/email/smtp \
        password="${SMTP_PASSWORD:-}"

    vault kv put secret/fishmap/payment/stripe \
        secret_key="${STRIPE_SECRET_KEY:-}" \
        webhook_secret="${STRIPE_WEBHOOK_SECRET:-}"

    vault kv put secret/fishmap/storage/cloudinary \
        api_secret="${CLOUDINARY_API_SECRET:-}"

    vault kv put secret/fishmap/external/weather \
        api_key="${OPENWEATHERMAP_API_KEY:-}"

    vault kv put secret/fishmap/external/mapbox \
        api_key="${MAPBOX_API_KEY:-}"

    echo "Secrets created successfully!"
}

create_policies() {
    echo "Creating policies..."
    
    for policy_file in /vault/policies/*.hcl; do
        policy_name=$(basename "$policy_file" .hcl)
        echo "Creating policy: $policy_name"
        vault policy write "$policy_name" "$policy_file"
    done
    
    echo "Policies created successfully!"
}

enable_approle() {
    echo "Enabling AppRole auth method..."
    vault auth enable approle 2>/dev/null || echo "AppRole already enabled"
}

create_approles() {
    echo "Creating AppRoles for services..."

    SERVICES="auth-service email-service places-service reports-service booking-service shop-service forecast-service"

    for service in $SERVICES; do
        echo "Creating AppRole for $service..."
        
        vault write auth/approle/role/$service \
            token_policies=$service \
            token_ttl=1h \
            token_max_ttl=4h \
            secret_id_ttl=0

        role_id=$(vault read -field=role_id auth/approle/role/$service/role-id)
        secret_id=$(vault write -field=secret_id -f auth/approle/role/$service/secret-id)

        echo "Role ID for $service: $role_id"
        echo "Secret ID for $service: $secret_id"
        echo ""
    done

    echo "AppRoles created successfully!"
}

main() {
    echo "=== Vault Initialization Script ==="
    echo "VAULT_ADDR: $VAULT_ADDR"
    echo ""

    wait_for_vault
    enable_kv_secrets
    create_secrets
    create_policies
    enable_approle
    create_approles

    echo ""
    echo "=== Vault initialization complete! ==="
    echo ""
    echo "IMPORTANT: Save the Role IDs and Secret IDs above!"
    echo "Set them as environment variables in your services:"
    echo "  VAULT_ROLE_ID=<role-id>"
    echo "  VAULT_SECRET_ID=<secret-id>"
}

main "$@"
