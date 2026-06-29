# Development
FROM node:18-alpine as dev

WORKDIR /app

COPY package*.json .
RUN npm ci

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev"]

# Production Build
FROM node:18-alpine as build

WORKDIR /app

ARG VITE_API_URL

COPY package*.json .
RUN npm ci

COPY . .

ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

# Production Serve
FROM node:18-alpine

WORKDIR /app

RUN npm install -g serve

COPY --from=build /app/dist ./dist

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]
