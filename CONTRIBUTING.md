# Contributing to Resume Screening System

Thank you for your interest in contributing to the Resume Screening System! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- `uv` package manager (recommended) or `pip`
- Git

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/resume-screening-system.git
   cd resume-screening-system
   ```

2. **Install Dependencies**
   ```bash
   # Using uv (recommended)
   uv sync --group dev
   
   # Or using pip
   pip install -e ".[dev]"
   ```

3. **Set Up Environment**
   ```bash
   cp env_example.txt .env
   # Edit .env with your API keys
   ```

## 🛠️ Development Workflow

### Code Style

We use several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

Run these tools before committing:

```bash
# Format code
uv run black .

# Sort imports
uv run isort .

# Lint code
uv run flake8 .

# Type check
uv run mypy .
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=resume_screener --cov=gladio_app

# Run specific test file
uv run pytest test_system.py
```

### Pre-commit Hooks

Consider setting up pre-commit hooks to automatically run quality checks:

```bash
# Install pre-commit
uv run pip install pre-commit

# Install hooks
uv run pre-commit install
```

## 📝 Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-new-file-format`
- `bugfix/fix-google-drive-parsing`
- `docs/update-readme`

### Commit Messages

Follow conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Maintenance tasks

Examples:
```
feat(extractor): add support for RTF files
fix(api): handle Google Drive API rate limits
docs(readme): update installation instructions
```

### Pull Request Process

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Write code following the style guidelines
   - Add tests for new functionality
   - Update documentation if needed

3. **Test Your Changes**
   ```bash
   uv run pytest
   uv run black .
   uv run flake8 .
   uv run mypy .
   ```

4. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat(scope): description"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Submit Pull Request**
   - Use the PR template
   - Describe your changes clearly
   - Link any related issues

## 🧪 Testing Guidelines

### Writing Tests

- Write tests for all new functionality
- Use descriptive test names
- Group related tests in classes
- Use fixtures for common setup

Example:
```python
import pytest
from resume_screener import ResumeScreenerNode

class TestResumeScreenerNode:
    def test_extract_candidate_info(self):
        """Test candidate information extraction from resume text."""
        node = ResumeScreenerNode()
        resume_text = "John Doe\njohn.doe@email.com\nSoftware Engineer"
        
        result = node.extract_candidate_info(resume_text)
        
        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"
        assert result["email"] == "john.doe@email.com"
```

### Test Categories

- **Unit Tests**: Test individual functions/methods
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows

## 📚 Documentation

### Code Documentation

- Use docstrings for all public functions and classes
- Follow Google docstring format
- Include type hints

Example:
```python
def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text content from a PDF file.
    
    Args:
        file_content: Raw PDF file content as bytes.
        
    Returns:
        Extracted text content as string.
        
    Raises:
        ValueError: If file content is not a valid PDF.
    """
```

### README Updates

- Update README.md for new features
- Include usage examples
- Update installation instructions if needed

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment Information**
   - Python version
   - Operating system
   - Package versions

2. **Steps to Reproduce**
   - Clear, step-by-step instructions
   - Sample data if applicable

3. **Expected vs Actual Behavior**
   - What you expected to happen
   - What actually happened

4. **Additional Context**
   - Error messages
   - Screenshots if relevant

## 💡 Feature Requests

When suggesting features:

1. **Describe the Problem**
   - What problem does this solve?
   - Who would benefit from this?

2. **Propose a Solution**
   - How should this work?
   - Any implementation ideas?

3. **Consider Impact**
   - How does this affect existing functionality?
   - What are the trade-offs?

## 🤝 Code Review

### Review Process

1. **Automated Checks**
   - All tests must pass
   - Code style checks must pass
   - Type checking must pass

2. **Manual Review**
   - At least one maintainer must approve
   - Address all review comments

3. **Merge Requirements**
   - All checks pass
   - No merge conflicts
   - Approved by maintainers

### Review Guidelines

- Be constructive and respectful
- Focus on the code, not the person
- Suggest improvements when possible
- Ask questions if something is unclear

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

## 🆘 Getting Help

If you need help:

1. Check the documentation
2. Search existing issues
3. Create a new issue with clear details
4. Join our community discussions

Thank you for contributing! 🎉 