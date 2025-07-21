#!/bin/bash
# Setup script for the Hackathon Dashboard Frontend

echo "Setting up Hackathon Dashboard Frontend..."

# Navigate to dashboard directory
cd "$(dirname "$0")"

# Create frontend with Vite
echo "Creating React app with Vite..."
npm create vite@latest frontend -- --template react-ts

# Navigate to frontend directory
cd frontend

# Install dependencies
echo "Installing dependencies..."
npm install

# Install additional packages
echo "Installing UI and utility packages..."
npm install axios react-router-dom
npm install -D tailwindcss postcss autoprefixer @types/react @types/react-dom
npm install lucide-react clsx tailwind-merge

# Initialize Tailwind CSS
echo "Setting up Tailwind CSS..."
npx tailwindcss init -p

# Create basic project structure
echo "Creating project structure..."
mkdir -p src/components
mkdir -p src/pages
mkdir -p src/lib
mkdir -p src/hooks
mkdir -p src/types
mkdir -p public/data

echo "Frontend setup complete!"
echo ""
echo "Next steps:"
echo "1. Update tailwind.config.js with content paths"
echo "2. Add Tailwind directives to src/index.css"
echo "3. Start development server with: npm run dev"
echo ""
echo "To install and run:"
echo "  cd frontend"
echo "  npm install"
echo "  npm run dev"