# System Architecture

This document provides an overview of CipherQuant's architecture.

## Overview

CipherQuant is built around a hybrid ingestion strategy:

- **API-based collectors**: For sources like CoinGecko, Yahoo Finance, and Crunchbase.
- **Web scraper**: For data not available via APIs.
- **PostgreSQL**: Central data store.
- **Flask**: Serves REST endpoints.
- **React**: Front-end dashboard.

```mermaid
graph TD
    A[React Frontend] --> B[Flask API]
    B --> C[SQL Database]
    B --> D[Strategy Engine]
    D --> E[ML Models]
