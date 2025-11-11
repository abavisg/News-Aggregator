# Security Policy

## Overview

This document outlines security best practices and policies for the Weekly Tech & AI Aggregator project. We take security seriously and follow industry-standard practices to protect sensitive data and credentials.

## Reporting a Vulnerability

If you discover a security vulnerability, please report it privately:

1. **Do NOT** open a public GitHub issue
2. Email the maintainer at: [your-email@example.com]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We aim to respond within 48 hours and will work with you to resolve the issue promptly.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| main    | ✅ Yes             |
| < 1.0   | ❌ No              |

## Security Best Practices

### 1. Credential Management

#### ✅ DO:
- Store credentials in environment variables (`.env` file)
- Use `.env.example` for template with placeholder values
- Never commit `.env` files to version control
- Rotate credentials regularly (every 90 days recommended)
- Use separate credentials for development, staging, and production
- Store production secrets in a secure vault (AWS Secrets Manager, HashiCorp Vault, etc.)

#### ❌ DON'T:
- Hardcode credentials in source code
- Commit real API keys or tokens
- Share credentials via email or messaging apps
- Use production credentials in development/testing
- Log credentials or tokens to console/files

### 2. OAuth Security

#### LinkedIn OAuth Best Practices:
- **State Parameter**: Always use CSRF protection with state parameter
- **Redirect URI**: Whitelist exact redirect URIs in LinkedIn Developer Console
- **Token Storage**: Store tokens securely, never in plain text logs
- **Token Refresh**: Implement automatic token refresh before expiry
- **Scope Limitation**: Request only necessary OAuth scopes

#### Token Lifecycle:
```
1. Authorization Code → Exchange for Access Token (expires in 60 days)
2. Store Access Token + Refresh Token securely
3. Refresh Access Token before expiry
4. Rotate Refresh Token periodically
```

### 3. API Security

#### Rate Limiting:
- LinkedIn API: 100 posts/day, 1 post/minute
- Implement exponential backoff on rate limit errors
- Log rate limit hits for monitoring

#### Error Handling:
- Never expose internal errors to public APIs
- Log sensitive errors securely (exclude tokens)
- Return generic error messages to users

### 4. Data Protection

#### Local Storage (`./data/`):
- **Posts**: Stored as JSON with metadata (safe to backup)
- **Credentials**: OAuth tokens stored in `./data/credentials/` (NEVER commit)
- **Permissions**: Ensure `./data/` directory has restricted permissions (600 or 700)

#### Sensitive Data:
- Never log access tokens or refresh tokens
- Sanitize logs before sharing or debugging
- Use structured logging to control sensitive fields

### 5. Testing Security

#### Test Credentials:
- Use clearly fake values (e.g., `MOCK_CLIENT_ID_FOR_TESTING`)
- Never use real credentials in tests
- Mock all external API calls

#### Test Data:
- Use synthetic data for testing
- Avoid using real user data in tests
- Clean up test data after test runs

### 6. Pre-commit Hooks

#### Secret Detection:
Install pre-commit hooks to prevent accidental commits:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

#### Hooks Included:
- **detect-secrets**: Scans for hardcoded secrets
- **detect-private-key**: Detects private keys in commits
- **trufflehog**: Scans for leaked credentials
- **bandit**: Python security vulnerability scanner

### 7. Dependency Security

#### Regular Updates:
```bash
# Check for vulnerabilities
pip install safety
safety check

# Update dependencies
pip-review --auto
```

#### Known Vulnerabilities:
- Monitor GitHub Dependabot alerts
- Review security advisories monthly
- Update vulnerable packages promptly

### 8. Environment Configuration

#### `.env` File Structure:
```env
# AI Provider (choose one)
ANTHROPIC_API_KEY=your_real_api_key_here
OLLAMA_BASE_URL=http://localhost:11434

# LinkedIn OAuth
LINKEDIN_CLIENT_ID=your_real_client_id
LINKEDIN_CLIENT_SECRET=your_real_client_secret
LINKEDIN_REDIRECT_URI=http://localhost:8000/v1/oauth/callback

# Security Settings
DRY_RUN=false  # Set to true for testing
MAX_RETRIES=3
POSTS_STORAGE_DIR=./data/posts

# Database (if using PostgreSQL)
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

#### `.env.example` (Safe to Commit):
```env
# AI Provider (choose one)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
OLLAMA_BASE_URL=http://localhost:11434

# LinkedIn OAuth
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
LINKEDIN_REDIRECT_URI=http://localhost:8000/v1/oauth/callback

# Security Settings
DRY_RUN=true
MAX_RETRIES=3
POSTS_STORAGE_DIR=./data/posts
```

### 9. Production Deployment

#### Checklist:
- [ ] All secrets stored in secure vault
- [ ] `.env` file not committed to repository
- [ ] Pre-commit hooks installed
- [ ] HTTPS enforced for all endpoints
- [ ] Rate limiting configured
- [ ] Logging sanitized (no secrets)
- [ ] Error messages generic (no internal details)
- [ ] OAuth redirect URIs whitelisted
- [ ] CSRF protection enabled
- [ ] Input validation implemented
- [ ] Security headers configured

#### Security Headers (FastAPI):
```python
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Whitelist specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
)
```

### 10. Incident Response

#### If Credentials are Leaked:

1. **Immediate Actions** (within 1 hour):
   - Revoke compromised credentials immediately
   - Generate new credentials
   - Update all systems with new credentials
   - Check logs for unauthorized access

2. **Investigation** (within 24 hours):
   - Determine scope of exposure
   - Identify affected systems
   - Review access logs for suspicious activity
   - Document timeline of events

3. **Remediation** (within 48 hours):
   - Rotate all related credentials
   - Update security policies if needed
   - Implement additional monitoring
   - Notify affected parties if required

4. **Post-Mortem** (within 1 week):
   - Document root cause
   - Identify preventive measures
   - Update security practices
   - Train team on lessons learned

## Security Checklist for Developers

### Before Every Commit:
- [ ] No hardcoded credentials in code
- [ ] All secrets in `.env` file (not committed)
- [ ] Pre-commit hooks pass
- [ ] Tests use mock credentials only
- [ ] Logs don't contain sensitive data
- [ ] Error messages are generic

### Before Every Pull Request:
- [ ] Security review completed
- [ ] Dependencies updated
- [ ] No new vulnerabilities introduced
- [ ] Secrets baseline updated if needed
- [ ] Documentation updated

### Before Every Release:
- [ ] Full security audit completed
- [ ] All dependencies up to date
- [ ] Secret rotation performed
- [ ] Production credentials verified
- [ ] Monitoring alerts configured

## Resources

### Tools:
- [detect-secrets](https://github.com/Yelp/detect-secrets) - Secret detection
- [trufflehog](https://github.com/trufflesecurity/trufflehog) - Credential scanning
- [bandit](https://github.com/PyCQA/bandit) - Python security linting
- [safety](https://github.com/pyupio/safety) - Dependency vulnerability checking

### References:
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [LinkedIn API Security](https://docs.microsoft.com/en-us/linkedin/shared/authentication/authentication)
- [OAuth 2.0 Security Best Practices](https://tools.ietf.org/html/rfc6749)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

## Contact

For security concerns or questions:
- **Email**: [security@example.com]
- **GitHub**: Open a private security advisory

---

**Last Updated**: 2025-11-10
**Version**: 1.0
**Reviewed By**: Security Team
