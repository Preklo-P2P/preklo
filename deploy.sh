#!/bin/bash

# Preklo Deployment Script for CTRL+MOVE Hackathon
echo "Starting Preklo deployment process..."

# Check if git is configured
if ! git config user.name > /dev/null 2>&1; then
    echo "Error: Git not configured. Please run:"
    echo "git config --global user.name 'Your Name'"
    echo "git config --global user.email 'your.email@example.com'"
    exit 1
fi

# Check if repository is clean
if ! git diff-index --quiet HEAD --; then
    echo "Warning: You have uncommitted changes."
    read -p "Do you want to commit them? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add .
        git commit -m "Prepare for deployment"
    fi
fi

# Push to GitHub
echo "Pushing to GitHub..."
git push origin main

echo ""
echo "Deployment preparation complete!"
echo ""
echo "Next steps:"
echo "1. Go to https://vercel.com and deploy frontend"
echo "2. Go to https://railway.app and deploy backend"
echo "3. Follow the DEPLOYMENT_GUIDE.md for detailed instructions"
echo ""
echo "Your repository is ready for deployment!"
