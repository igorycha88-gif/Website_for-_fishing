#!/bin/bash

# ELK Stack Setup Script for macOS

set -e

echo "🚀 Setting up ELK Stack for FishMap Monitoring..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop first."
    echo "   Visit: https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo "✅ Docker found"

# Create necessary directories
mkdir -p elasticsearch/data
mkdir -p logstash/config
mkdir -p logstash/pipeline

# Set permissions for Elasticsearch data directory
chmod -R 777 elasticsearch/data

echo "📁 Directories created"

# Check if docker-compose.elk.yml exists
if [ ! -f "docker-compose.elk.yml" ]; then
    echo "❌ docker-compose.elk.yml not found"
    exit 1
fi

# Start ELK Stack
echo "🐳 Starting ELK Stack..."
docker-compose -f docker-compose.elk.yml up -d

echo "⏳ Waiting for services to start..."
sleep 30

# Check if services are running
if curl -s http://localhost:9200 > /dev/null; then
    echo "✅ Elasticsearch is running at http://localhost:9200"
else
    echo "❌ Elasticsearch failed to start"
    exit 1
fi

if curl -s http://localhost:5601 > /dev/null; then
    echo "✅ Kibana is running at http://localhost:5601"
    echo "   Open this URL in your browser to access Kibana"
else
    echo "❌ Kibana failed to start"
    exit 1
fi

if curl -s http://localhost:9600 > /dev/null; then
    echo "✅ Logstash is running at http://localhost:9600"
else
    echo "❌ Logstash failed to start"
    exit 1
fi

echo ""
echo "🎉 ELK Stack setup complete!"
echo ""
echo "📊 Access points:"
echo "   - Kibana: http://localhost:5601"
echo "   - Elasticsearch: http://localhost:9200"
echo "   - Logstash: http://localhost:9600"
echo ""
echo "📝 Next steps:"
echo "   1. Open Kibana at http://localhost:5601"
echo "   2. Go to Management > Stack Management > Index Patterns"
echo "   3. Create index pattern: fishmap-logs-*"
echo "   4. Select @timestamp as time field"
echo ""
