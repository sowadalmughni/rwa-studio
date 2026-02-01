# RWA-Studio Frontend Dockerfile
# Multi-stage build for production React/Vite application

# Stage 1: Build
FROM node:20-alpine as builder

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source code
COPY . .

# Build application
RUN pnpm build

# Stage 2: Production with Nginx
FROM nginx:alpine as production

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Create non-root user
RUN addgroup -S rwa && adduser -S rwa -G rwa \
    && chown -R rwa:rwa /usr/share/nginx/html \
    && chown -R rwa:rwa /var/cache/nginx \
    && touch /var/run/nginx.pid \
    && chown -R rwa:rwa /var/run/nginx.pid

# Security: Remove default nginx index page
RUN rm -rf /usr/share/nginx/html/index.html 2>/dev/null || true

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Run nginx
CMD ["nginx", "-g", "daemon off;"]
