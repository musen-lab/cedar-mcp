# CI/CD Deployment Guide

This repository is configured with a comprehensive CI/CD pipeline using GitHub Actions.

## 🚀 Quick Setup

### 1. Configure Repository Secrets
Go to **Settings → Secrets and variables → Actions** and add:

**Optional for Integration Tests:**
- `CEDAR_API_KEY` - CEDAR repository API key
- `BIOPORTAL_API_KEY` - BioPortal API key

### 2. Enable Branch Protection
Go to **Settings → Branches** and add rules for `main`:
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- ✅ Include administrators

### 3. Enable Security Features
Go to **Settings → Code security and analysis**:
- ✅ Dependency graph
- ✅ Dependabot alerts
- ✅ Dependabot security updates
- ✅ Code scanning (CodeQL)
- ✅ Secret scanning

## 📋 Workflows Overview

| Workflow | Triggers | Purpose |
|----------|----------|---------|
| **CI** | Push/PR to `main`/`develop` | Code quality, testing, security |
| **Release** | Git tags (`v*`) | Build package and create GitHub release |
| **CodeQL** | Push/PR + weekly | Advanced security scanning |
| **Dependabot** | Weekly | Automated dependency updates |

## 🔄 CI Pipeline

### On Pull Request / Push
1. **Code Quality**: ruff linting, mypy type checking
2. **Testing**: Unit tests on Python 3.10, 3.11, 3.12
3. **Integration Tests**: Run if API keys available
4. **Security**: Dependency and code security scanning
5. **Build**: Package verification

### On Release Tag
1. **Build**: Create distribution packages
2. **Verify**: Check package integrity
3. **Release**: Create GitHub release with distribution artifacts

## 📦 Creating a Release

1. Update version in `pyproject.toml`
2. Commit and push changes
3. Create and push a tag:
   ```bash
   git tag v0.1.1
   git push origin v0.1.1
   ```
4. GitHub Actions will automatically:
   - Build the package
   - Create a GitHub release with installation instructions

## 🧪 Local Testing

Simulate CI checks locally:
```bash
# Code quality
ruff check .
ruff format --check .
mypy src/

# Testing
python run_tests.py --unit
python run_tests.py --integration  # if API keys configured

# CLI verification
python -m cedar_mcp.server --help
```

## 🔧 Troubleshooting

### Integration Tests Skip
If integration tests are skipped, ensure API keys are configured in repository secrets.

### Release Creation Fails
1. Ensure version number in `pyproject.toml` is incremented
2. Check that the git tag follows the `v*` pattern (e.g., v0.1.0)
3. Verify package builds successfully locally

### Code Quality Failures
Run locally to reproduce:
```bash
ruff check .              # Fix linting issues
ruff format .             # Auto-format code
mypy src/                 # Fix type hints
```

## 📊 Monitoring

- **GitHub Actions**: Monitor workflow runs in Actions tab
- **Security**: Review security advisories and Dependabot PRs
- **Coverage**: Check coverage reports from CI runs
- **GitHub Releases**: Monitor release downloads and user feedback

## 🎯 Success Indicators

- ✅ All CI workflows passing
- ✅ Automated releases working
- ✅ Security scanning active
- ✅ Dependencies automatically updated
- ✅ Package successfully installable from source via uvx