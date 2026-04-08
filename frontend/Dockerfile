FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Backend URL for Next.js rewrites (resolved at build time)
ARG BACKEND_URL=http://backend:8000
ENV BACKEND_URL=${BACKEND_URL}

# Build for production
RUN npm run build

# Expose port
EXPOSE 3000

# Production server
CMD ["npm", "start"]
