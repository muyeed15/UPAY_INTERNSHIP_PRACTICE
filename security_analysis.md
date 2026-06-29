# JWT Security Threat Analysis

## 1. Token Leakage

JWTs are bearer credentials. Anyone with the token can impersonate the user.
Common leaks: server logs, localStorage (XSS), non-HTTPS, HTTP referrer headers,
MITM attacks.

### Vulnerability: Stolen Refresh Token (fixed)

A stolen refresh token becomes useless after one legit rotation because the
old token is blacklisted. Test: `SecurityTokenLeakageTests.test_stolen_refresh_cannot_rotate`

![Stolen refresh rejected](screenshots/12-stolen-refresh-rejected.png)

**Fix**: `ROTATE_REFRESH_TOKENS=True`, `BLACKLIST_AFTER_ROTATION=True` in settings.

## 2. Token Expiry

| Token   | Lifetime | Reason                                 |
| ------- | -------- | -------------------------------------- |
| Access  | 15 min   | Short blast radius                     |
| Refresh | 7 days   | Week of access, rotation limits damage |

## 3. Signing Key Rotation

If `SIGNING_KEY` leaks, all JWTs are compromised. Rotating the key invalidates
all tokens. Mitigation: store key in environment variable, keep access tokens
short-lived. Multi-key support via `kid` claim is a future enhancement.

## 4. Custom Claims

`role` and `account_id` are base64-encoded, not encrypted. Any token holder can
read them. No passwords, PII, or secrets are placed in claims.

![JWT claims](screenshots/03-claims.png)

## 5. Email Enumeration

The login endpoint returns the same error for wrong email and wrong password,
preventing email enumeration. Rate-limiting should be added in production.
