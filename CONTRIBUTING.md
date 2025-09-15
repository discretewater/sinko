# Contributing to Sinko

We welcome contributions to the Sinko project! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```
   git clone https://github.com/your-username/sinko.git
   cd sinko
   ```
3. Install the project in editable mode with development dependencies:
   ```
   pip install -e ".[dev]"
   ```

## Making Changes

1. Create a new branch for your changes:
   ```
   git checkout -b your-feature-branch
   ```
2. Make your changes and commit them:
   ```
   git commit -am "Add a brief description of your changes"
   ```
3. Push your changes to your fork on GitHub:
   ```
   git push origin your-feature-branch
   ```

## Code Style

- Follow PEP 8 guidelines for Python code.
- Use meaningful variable and function names.
- Write docstrings for all functions, classes, and modules.

## Testing

- Add tests for new features or bug fixes.
- Ensure all tests pass before submitting a pull request:
  ```
  pytest
  ```

## Submitting Changes

1. Create a pull request from your fork to the main Sinko repository.
2. Describe your changes in detail in the pull request description.
3. Reference any related issues in your pull request description.

## Code of Conduct

Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms.

Thank you for contributing to Sinko!
