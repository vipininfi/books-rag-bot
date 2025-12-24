#!/bin/bash

# Book RAG System Deployment Script
set -e

echo "🚀 Starting Book RAG System deployment..."

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install Python 3.11 and dependencies
echo "🐍 Installing Python and dependencies..."
apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
apt install -y postgresql postgresql-contrib
apt install -y nginx
apt install -y git curl wget

# Create application directory
APP_DIR="/opt/book-rag-system"
echo "📁 Creating application directory: $APP_DIR"
mkdir -p $APP_DIR
cd $APP_DIR

# Clone repository (you'll need to replace with your repo URL)
echo "📥 Cloning repository..."
# git clone https://github.com/yourusername/book-rag-system.git .

# Create virtual environment
echo "🔧 Setting up Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Set up environment variables
echo "⚙️ Setting up environment variables..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "❗ Please edit .env file with your configuration"
fi

# Set up PostgreSQL database
echo "🗄️ Setting up PostgreSQL database..."
sudo -u postgres createdb book_rag_system || echo "Database might already exist"
sudo -u postgres createuser book_rag_user || echo "User might already exist"
sudo -u postgres psql -c "ALTER USER book_rag_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE book_rag_system TO book_rag_user;"

# Run database migrations
echo "🔄 Running database migrations..."
alembic upgrade head

# Create uploads directory
echo "📁 Creating uploads directory..."
mkdir -p uploads
chmod 755 uploads

# Set permissions
echo "🔐 Setting permissions..."
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR

echo "✅ Deployment script completed!"
echo "📝 Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Set up systemd service"
echo "3. Configure Nginx"
echo "4. Start the application"