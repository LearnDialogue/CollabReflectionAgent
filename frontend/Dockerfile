FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Build for production
RUN npm run build

# Expose port
EXPOSE 3000

# Production server
CMD ["npm", "start"]
