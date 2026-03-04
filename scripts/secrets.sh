#!/bin/bash
set -e

echo "=== FishMap Docker Secrets Setup ==="
echo ""

SECRETS_DIR="./secrets"
mkdir -p "$SECRETS_DIR"

create_secret() {
    local name=$1
    local file="$SECRETS_DIR/$name.txt"
    
    if [ -f "$file" ]; then
        echo "File $file exists. Using existing value."
    else
        echo "Enter value for $name:"
        read -s value
        echo "$value" > "$file"
        chmod 600 "$file"
        echo "Created $file"
    fi
}

create_docker_secret() {
    local name=$1
    local file="$SECRETS_DIR/$name.txt"
    
    if docker secret inspect "$name" > /dev/null 2>&1; then
        echo "Docker secret '$name' already exists. Skipping..."
    else
        if [ -f "$file" ]; then
            docker secret create "$name" "$file"
            echo "Created Docker secret: $name"
        else
            echo "ERROR: File $file not found. Run with --generate first."
            exit 1
        fi
    fi
}

remove_docker_secret() {
    local name=$1
    
    if docker secret inspect "$name" > /dev/null 2>&1; then
        docker secret rm "$name"
        echo "Removed Docker secret: $name"
    else
        echo "Docker secret '$name' not found. Skipping..."
    fi
}

case "${1:-help}" in
    --generate|-g)
        echo "Generating secret files..."
        create_secret "secret_key"
        create_secret "postgres_password"
        create_secret "smtp_password"
        create_secret "stripe_secret_key"
        create_secret "stripe_webhook_secret"
        create_secret "cloudinary_api_secret"
        echo ""
        echo "Secrets generated in $SECRETS_DIR/"
        echo "Review files and run: $0 --create"
        ;;
    
    --create|-c)
        echo "Creating Docker Swarm secrets..."
        if ! docker info 2>/dev/null | grep -q "Swarm: active"; then
            echo "ERROR: Docker Swarm is not active. Run 'docker swarm init' first."
            exit 1
        fi
        create_docker_secret "secret_key"
        create_docker_secret "postgres_password"
        create_docker_secret "smtp_password"
        create_docker_secret "stripe_secret_key"
        create_docker_secret "stripe_webhook_secret"
        create_docker_secret "cloudinary_api_secret"
        echo ""
        echo "All secrets created. Deploy with: docker stack deploy -c docker-compose.yml fishmap"
        ;;
    
    --remove|-r)
        echo "Removing Docker Swarm secrets..."
        remove_docker_secret "secret_key"
        remove_docker_secret "postgres_password"
        remove_docker_secret "smtp_password"
        remove_docker_secret "stripe_secret_key"
        remove_docker_secret "stripe_webhook_secret"
        remove_docker_secret "cloudinary_api_secret"
        echo ""
        echo "All secrets removed."
        ;;
    
    --list|-l)
        echo "Docker Swarm secrets:"
        docker secret ls
        echo ""
        echo "Local secret files:"
        ls -la "$SECRETS_DIR/" 2>/dev/null || echo "No local secrets directory."
        ;;
    
    *)
        echo "Usage: $0 [OPTION]"
        echo ""
        echo "Options:"
        echo "  --generate, -g    Generate secret files in ./secrets/"
        echo "  --create, -c      Create Docker Swarm secrets from files"
        echo "  --remove, -r      Remove Docker Swarm secrets"
        echo "  --list, -l        List all secrets"
        echo ""
        echo "Example:"
        echo "  $0 --generate     # Create secret files"
        echo "  $0 --create       # Create Docker secrets"
        echo "  docker stack deploy -c docker-compose.yml fishmap"
        ;;
esac
