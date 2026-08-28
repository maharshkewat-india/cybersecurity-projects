# Login Redirect Fix Report

## Issue

After successful login, the application briefly displayed the dashboard and then redirected the user back to the login page.

## Root cause

The backend generated the JWT `exp` (expiry) claim as an ISO-8601 string. JWT requires this claim to be a NumericDate (Unix timestamp). `python-jose` therefore rejected the token on protected dashboard requests and returned HTTP 401.

The frontend response interceptor is designed to clear invalid tokens and redirect to `/login` after a 401, which produced the observed loop.

## Fix

`backend/core/security.py` now passes the expiry as a Python `datetime`. `python-jose` serializes it to the required NumericDate format, and it can then verify the token successfully.

## Verification

- A newly created token verifies successfully in the backend.
- Protected endpoints accept the token instead of returning HTTP 401.
- The dashboard remains available after login.

## Operational note

Restart the backend after deploying this change. Users with tokens issued before the restart must sign in again.
