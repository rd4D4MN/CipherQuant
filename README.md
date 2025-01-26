# Trading Strategy Backtester

## Features
- REST API with Flask
- React dashboard
- LSTM-based return prediction
- Web scraping pipeline

## Architecture
```mermaid
graph TD
    A[React Frontend] --> B[Flask API]
    B --> C[SQL Database]
    B --> D[Strategy Engine]
    D --> E[ML Models]