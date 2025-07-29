# Contributing to mcp-server-rabbitmq

Thank you for your interest in contributing to mcp-server-rabbitmq! This document provides guidelines and instructions for contributing to this project.

## Development Environment Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) for dependency management

### Setting Up Your Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/amazon-mq/mcp-server-rabbitmq.git
   cd mcp-server-rabbitmq
   ```

2. Create and activate a virtual environment using `uv`:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   uv pip install -e .
   uv pip install -r requirements-dev.txt  # If available, otherwise use dev dependencies from pyproject.toml
   ```

4. Install pre-commit hooks:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Development Workflow

### Code Style

This project follows a specific code style enforced by Ruff. Key style guidelines include:

- Line length: 99 characters
- Quote style: Double quotes
- Indentation: 4 spaces
- Import sorting: Using isort configuration via Ruff

The pre-commit hooks will automatically check and fix many style issues when you commit.

### Running Tests

Tests are written using pytest. To run the tests:

```bash
pytest
```

For more verbose output:

```bash
pytest -v
```

### Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality. The hooks include:

- Ruff for linting and formatting
- Trailing whitespace removal
- End-of-file fixing
- YAML and TOML checking
- Large file checking

## Pull Request Process

1. Fork the repository and create a new branch from `main`.
2. Make your changes, following the code style guidelines.
3. Add tests for any new functionality.
4. Ensure all tests pass.
5. Update documentation as needed.
6. Submit a pull request with a clear description of the changes.

### Commit Messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for commit messages, managed by Commitizen. Your commit messages should follow this format:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Common types include:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or modifying tests
- `chore`: Routine tasks, maintenance, etc.

## Versioning

This project uses semantic versioning. Version bumps are handled by Commitizen based on commit messages.

## Project Structure

- `mcp_server_rabbitmq/`: Main package directory
  - `server.py`: Main server implementation
  - `connection.py`: RabbitMQ connection handling
  - `admin.py`: RabbitMQ administration
  - `handlers.py`: Request handlers
  - `constant.py`: Constants and configuration
- `tests/`: Test directory

## License

By contributing to this project, you agree that your contributions will be licensed under the project's [Apache 2.0 License](LICENSE).

## Questions or Need Help?

If you have questions or need help with the contribution process, please open an issue in the repository.
