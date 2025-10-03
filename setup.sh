#!/bin/bash

# Preklo Setup Script
echo "Setting up Preklo..."

# Check if Python 3.12+ is installed
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.12"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 12) else 1)" 2>/dev/null; then
    echo "ERROR: Python 3.12+ is required. Current version: $python_version"
    echo "Please install Python 3.12+ and try again."
    exit 1
fi

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "ERROR: PostgreSQL is not installed. Please install PostgreSQL first."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment file
if [ ! -f .env ]; then
    echo "Creating environment configuration..."
    cp env.example .env
    echo "Please edit .env file with your configuration before continuing."
fi

# Check if database exists
echo "Checking database..."
DB_NAME="preklo"
DB_USER="preklo"

if ! psql -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo "Creating database..."
    createdb $DB_NAME
    echo "Database created successfully"
else
    echo "Database already exists"
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

echo "Preklo setup completed!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration:"
echo "   nano .env"
echo ""
echo "2. Deploy Move contracts (optional for API testing):"
echo "   cd move && aptos move publish"
echo ""
echo "3. Start the API server:"
echo "   source venv/bin/activate"
echo "   python -m backend.app.main"
echo ""
echo "4. Test the API:"
echo "   python test_api.py"
echo ""
echo "5. View API documentation:"
echo "   http://localhost:8000/docs"
echo ""
echo "Happy coding with Preklo!"
