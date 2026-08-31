# Reflex

Reflex is a delivery management system designed for small Kenyan retailers.

## Problem

Small retailers currently coordinate deliveries through WhatsApp and phone calls, making it difficult to track assignments, delivery status, and proof of delivery.

## Technology Stack

### Frontend
HTML, CSS and JavaScript

### Backend
Python and Flask

### Database
MySQL

## Architecture

Frontend → Flask REST API → MySQL

## Core Delivery Flow

Pending → Assigned → Picked Up → Delivered

## API Endpoints

- GET /api/health
- GET /api/riders
- POST /api/riders
- GET /api/retailers
- POST /api/retailers
- GET /api/deliveries
- POST /api/deliveries
- PUT /api/deliveries/<id>/assign
- PUT /api/deliveries/<id>/status

## Running the Project

Create and activate a Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
A delivery system allowing delivery request, rider assignment, delivery status update, real-time request syncing and order confirmation scanning
