# Digital Forensics Evidence Management System — Synopsis

## Overview

The Digital Forensics Evidence Management System is an educational web application for recording and managing digital-forensics cases, evidence items, and chain-of-custody events. It provides a centralized workflow for teams that need a clear, auditable record of investigation activity.

## Problem addressed

Digital evidence requires consistent documentation: who handled it, where it was stored, what was done to it, and whether its integrity changed. Informal spreadsheets or disconnected records make this difficult to track and audit.

## Solution

The system combines a FastAPI backend, Next.js frontend, and SQLite database to provide:

- JWT-based authentication and role-based access control.
- Case creation, assignment, status tracking, and archival.
- Evidence registration using source file paths with MD5 and SHA-256 hashing.
- Hash verification to detect integrity changes.
- Chronological chain-of-custody entries.
- Investigation notes, audit logging, user management, and JSON reports.

## Technology stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS.
- Backend: FastAPI, Python, Pydantic, python-jose.
- Storage: SQLite.

## Security approach

Passwords use PBKDF2-HMAC-SHA256 with per-user salts. The API uses signed JWT access tokens, checks permissions at the service layer, uses parameterized SQL queries, and preserves an append-only audit history through normal UI actions.

## Scope and limitation

This is a portfolio and educational evidence-management tool. It does not replace validated forensic imaging, write blockers, or legal evidence-handling procedures required for production forensic or court use.
