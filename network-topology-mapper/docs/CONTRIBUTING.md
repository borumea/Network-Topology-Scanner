# Contributing to Network Topology Mapper

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive experience for everyone.

### Standards

**Positive behavior**:
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community

**Unacceptable behavior**:
- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information
- Other conduct which could reasonably be considered inappropriate

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Neo4j 5.0+
- Redis 7.0+
- Git

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/network-topology-mapper.git
cd network-topology-mapper
```

3. Add upstream remote:

```bash
git remote add upstream https://github.com/ORIGINAL_OWNER/network-topology-mapper.git
```

### Install Dependencies

**Backend**:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

**Frontend**:
```bash
cd frontend
npm install
```

### Run Tests

Ensure everything works:

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

---

## Development Workflow

### Branch Strategy

- `main` - Stable production branch
- `develop` - Integration branch for features
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes

### Creating a Feature Branch

```bash
git checkout develop
git pull upstream develop
git checkout -b feature/your-feature-name
```

### Making Changes

1. **Write code** following our [coding standards](#coding-standards)
2. **Write tests** for new functionality
3. **Update documentation** if needed
4. **Run tests** to ensure nothing breaks
5. **Commit changes** with clear messages

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:

```
feat(scanner): add support for IPv6 scanning

- Implement IPv6 address parsing
- Update nmap wrapper for IPv6 targets
- Add tests for IPv6 functionality

Closes #123
```

```
fix(graph): prevent memory leak in Cytoscape updates

The graph was re-rendering entirely on each update, causing
memory buildup. Now uses incremental updates via cy.add().

Fixes #456
```

### Syncing with Upstream

Keep your branch up to date:

```bash
git fetch upstream
git rebase upstream/develop
```

---

## Coding Standards

### Python (Backend)

#### Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications.

**Use Black for formatting**:
```bash
black app/
```

**Use isort for imports**:
```bash
isort app/
```

**Use flake8 for linting**:
```bash
flake8 app/
```

**Use mypy for type checking**:
```bash
mypy app/
```

#### Code Organization

```python
# Standard library imports
import os
import sys
from datetime import datetime

# Third-party imports
from fastapi import APIRouter, Depends
from pydantic import BaseModel

# Local imports
from app.services.scanner import ActiveScanner
from app.db.neo4j_client import get_neo4j_driver
```

#### Type Hints

Always use type hints:

```python
def calculate_risk_score(
    device: Device,
    connections: list[Connection]
) -> float:
    """
    Calculate risk score for a device.

    Args:
        device: The device to analyze
        connections: List of device connections

    Returns:
        Risk score between 0.0 and 1.0
    """
    # Implementation
```

#### Docstrings

Use Google-style docstrings:

```python
def simulate_failure(
    graph: NetworkGraph,
    target_nodes: list[str],
    target_edges: list[str]
) -> SimulationResult:
    """Simulate removal of devices/connections and calculate impact.

    Args:
        graph: The network graph to simulate on
        target_nodes: List of device IDs to remove
        target_edges: List of connection IDs to remove

    Returns:
        SimulationResult containing impact analysis

    Raises:
        ValueError: If graph is empty or targets don't exist
    """
```

#### Error Handling

Be explicit with error handling:

```python
try:
    result = await scanner.scan(target)
except ScanTimeoutError as e:
    logger.error(f"Scan timeout for {target}: {e}")
    raise HTTPException(
        status_code=504,
        detail=f"Scan timeout: {str(e)}"
    )
except ScanPermissionError as e:
    logger.error(f"Permission denied: {e}")
    raise HTTPException(
        status_code=403,
        detail="Insufficient permissions for scanning"
    )
```

### TypeScript/React (Frontend)

#### Style Guide

We use ESLint and Prettier for code formatting.

**Run linter**:
```bash
npm run lint
```

**Format code**:
```bash
npm run format
```

#### Component Structure

```typescript
// Component imports
import React, { useState, useEffect } from 'react';

// Type imports
import type { Device, Connection } from '@/types';

// Hook imports
import { useTopology } from '@/hooks/useTopology';

// UI imports
import { Button } from '@/components/shared/Button';

// Utils
import { cn } from '@/lib/utils';

interface Props {
  deviceId: string;
  onClose: () => void;
}

export function DeviceInspector({ deviceId, onClose }: Props) {
  // Hooks first
  const { device, isLoading } = useTopology(deviceId);

  // State
  const [activeTab, setActiveTab] = useState('overview');

  // Effects
  useEffect(() => {
    // Side effects
  }, [deviceId]);

  // Event handlers
  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
  };

  // Early returns
  if (isLoading) return <LoadingSpinner />;
  if (!device) return <NotFound />;

  // Render
  return (
    <div className={cn('panel', 'device-inspector')}>
      {/* Component JSX */}
    </div>
  );
}
```

#### Naming Conventions

- **Components**: PascalCase (`DeviceInspector.tsx`)
- **Hooks**: camelCase with `use` prefix (`useTopology.ts`)
- **Utils**: camelCase (`formatBandwidth.ts`)
- **Types**: PascalCase (`Device`, `Connection`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_DEVICES`, `DEFAULT_LAYOUT`)

#### Type Safety

Always define interfaces for props and data:

```typescript
interface Device {
  id: string;
  ip: string;
  hostname: string;
  device_type: DeviceType;
  risk_score: number;
  status: DeviceStatus;
}

type DeviceType = 'router' | 'switch' | 'server' | 'workstation';
type DeviceStatus = 'online' | 'offline' | 'degraded';
```

#### Hooks Usage

- Use React hooks appropriately
- Extract complex logic into custom hooks
- Avoid prop drilling (use context or Zustand)

### CSS/Tailwind

- Use Tailwind utility classes
- Create reusable components for repeated patterns
- Use `cn()` utility for conditional classes
- Follow mobile-first responsive design

---

## Testing Guidelines

### Backend Tests

#### Unit Tests

Test individual functions and classes:

```python
# tests/services/test_scanner.py
import pytest
from app.services.scanner.active_scanner import ActiveScanner

def test_parse_nmap_output():
    """Test nmap output parsing."""
    scanner = ActiveScanner()
    raw_output = """
    Host: 192.168.1.1
    Ports: 22/open, 80/open, 443/open
    """
    result = scanner.parse_output(raw_output)

    assert result.ip == "192.168.1.1"
    assert len(result.open_ports) == 3
    assert 22 in result.open_ports
```

#### Integration Tests

Test interactions between components:

```python
# tests/integration/test_scan_pipeline.py
import pytest
from app.services.scanner.scan_coordinator import ScanCoordinator
from app.services.graph.graph_builder import GraphBuilder

@pytest.mark.asyncio
async def test_full_scan_pipeline():
    """Test complete scan-to-graph pipeline."""
    coordinator = ScanCoordinator()
    builder = GraphBuilder()

    # Run scan
    results = await coordinator.run_scan("192.168.1.0/24")

    # Build graph
    graph = await builder.build_from_results(results)

    # Verify
    assert len(graph.nodes) > 0
    assert graph.has_node("192.168.1.1")
```

#### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/services/test_scanner.py

# Run with coverage
pytest --cov=app tests/

# Run in watch mode
ptw --runner "pytest -x"
```

### Frontend Tests

#### Component Tests

Use React Testing Library:

```typescript
// components/graph/NetworkCanvas.test.tsx
import { render, screen } from '@testing-library/react';
import { NetworkCanvas } from './NetworkCanvas';

describe('NetworkCanvas', () => {
  it('renders graph container', () => {
    render(<NetworkCanvas />);
    expect(screen.getByTestId('graph-container')).toBeInTheDocument();
  });

  it('displays devices', async () => {
    const devices = [{ id: '1', hostname: 'device-1' }];
    render(<NetworkCanvas devices={devices} />);
    expect(await screen.findByText('device-1')).toBeInTheDocument();
  });
});
```

#### Hook Tests

```typescript
// hooks/useTopology.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { useTopology } from './useTopology';

describe('useTopology', () => {
  it('fetches topology data', async () => {
    const { result } = renderHook(() => useTopology());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.devices).toHaveLength(247);
  });
});
```

#### Running Tests

```bash
# Run all tests
npm test

# Run in watch mode
npm test -- --watch

# Run with coverage
npm test -- --coverage
```

### Test Coverage

Aim for:
- **Unit tests**: 80%+ coverage
- **Integration tests**: Critical paths covered
- **E2E tests**: Happy paths covered

---

## Documentation

### Code Documentation

- Add docstrings/comments for complex logic
- Document public APIs thoroughly
- Keep README and docs up to date

### API Documentation

- Use FastAPI's built-in OpenAPI generation
- Add descriptions to endpoints and models:

```python
@router.get(
    "/devices/{device_id}",
    response_model=DeviceDetail,
    summary="Get device details",
    description="Retrieve detailed information about a specific device"
)
async def get_device(device_id: str):
    """Get device by ID with all related data."""
```

### Updating Documentation

When making changes:
- Update relevant `.md` files in `docs/`
- Update inline code comments
- Add examples for new features
- Update API documentation

---

## Pull Request Process

### Before Submitting

Checklist:
- [ ] Code follows style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] Commit messages follow conventions
- [ ] Branch rebased on latest develop
- [ ] No merge conflicts

### Creating Pull Request

1. Push your branch to your fork:

```bash
git push origin feature/your-feature-name
```

2. Go to GitHub and create a pull request
3. Fill out the PR template completely
4. Link related issues (e.g., "Closes #123")
5. Request review from maintainers

### PR Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tests pass locally
- [ ] No merge conflicts

## Screenshots (if applicable)
[Add screenshots for UI changes]

## Related Issues
Closes #123
```

### Review Process

1. **Automated checks** run (tests, linting)
2. **Code review** by maintainers
3. **Feedback** addressed by contributor
4. **Approval** from at least one maintainer
5. **Merge** into develop branch

### After Merge

- Your changes are in `develop`
- They'll be included in the next release
- Thank you for contributing! 🎉

---

## Issue Reporting

### Bug Reports

Use the bug report template:

```markdown
**Describe the bug**
Clear description of what's wrong.

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What should happen.

**Screenshots**
If applicable.

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Browser: [e.g., Chrome 120]
- Version: [e.g., 1.0.0]

**Additional context**
Any other relevant information.
```

### Feature Requests

Use the feature request template:

```markdown
**Is your feature related to a problem?**
Describe the problem.

**Describe the solution**
What you want to happen.

**Alternatives considered**
Other solutions you've thought about.

**Additional context**
Mockups, examples, etc.
```

### Security Issues

**Do not open public issues for security vulnerabilities.**

Email security@example.com with:
- Description of vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

---

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Discord**: Real-time chat (link TBD)
- **Stack Overflow**: Tag with `network-topology-mapper`

### Getting Help

- Check existing documentation first
- Search closed issues
- Ask in GitHub Discussions
- Join our community channels

---

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- Annual contributor reports

Significant contributors may be invited to become maintainers.

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

## Questions?

If you have questions about contributing, feel free to:
- Open a GitHub Discussion
- Ask in community channels
- Contact maintainers directly

Thank you for making Network Topology Mapper better! 🚀
