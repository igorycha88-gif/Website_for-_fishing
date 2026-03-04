#!/bin/bash

if [ ! -f .env ]; then
    echo "Error: .env file not found. Copy from .env.example"
    exit 1
fi

source .env

if [ -z "$SMTP_PASSWORD" ]; then
    echo "Warning: SMTP_PASSWORD not set"
fi

echo "Configuration check passed"
