# Use Node.js 18 Alpine image for smaller size
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install system dependencies for node-gyp and curl for health checks
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    curl

# Copy package files first for better caching
COPY package*.json yarn.lock ./

# Install dependencies
RUN yarn install --frozen-lockfile

# Copy source code
COPY . .

# Create non-root user
RUN addgroup -g 1001 -S nodejs \
    && adduser -S reactjs -u 1001 -G nodejs \
    && chown -R reactjs:nodejs /app
USER reactjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Set environment to bind to all interfaces
ENV HOST=0.0.0.0
ENV PORT=3000

# Start the development server with host binding
CMD ["yarn", "start"]