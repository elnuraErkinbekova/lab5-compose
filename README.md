# Lab 5: Multi-container application with Docker Compose

## Описание проекта
Приложение состоит из трех сервисов:
1. **Backend API** (Python Flask)
2. **Database** (PostgreSQL 15)
3. **Cache** (Redis 7)

## Требования
- Docker
- Docker Compose

## Инструкция по запуску
1. Скопируйте файл с примером конфигурации:
   ```bash
   cp .env.example .env