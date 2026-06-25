# Stage 1: Build React app inside Docker
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps
COPY . .
ARG VITE_API_URL=http://72.60.163.124:8003
ARG VITE_GATEWAY_URL=http://72.60.163.124:4001
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_GATEWAY_URL=$VITE_GATEWAY_URL
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
RUN printf 'server {\n\
  listen 3002;\n\
  root /usr/share/nginx/html;\n\
  index index.html;\n\
  location / {\n\
    try_files $uri $uri/ /index.html;\n\
  }\n\
}\n' > /etc/nginx/conf.d/default.conf
EXPOSE 3002
CMD ["nginx", "-g", "daemon off;"]
