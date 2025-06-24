# 🤝 Contributing to Calendar Insights

Thank you for your interest in contributing! This guide will help you get started quickly.

## 🚀 Quick Start

1. **Fork** the repository
2. **Clone** your fork: `git clone <your-fork-url>`
3. **Create** a branch: `git checkout -b feature/your-feature`
4. **Make** your changes
5. **Test** your changes
6. **Commit**: `git commit -m "Add your feature"`
7. **Push**: `git push origin feature/your-feature`
8. **Submit** a Pull Request

## 🛠️ Development Setup

```bash
# Clone and setup
git clone <repository-url>
cd calendar-insights

# Choose your environment
cd app-gcp    # For cloud development
cd app        # For self-hosted development

# Install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run locally
streamlit run dashboard.py
```

## 📝 Guidelines

### Code Quality
- Follow PEP 8 style guidelines
- Add docstrings to functions
- Include type hints where helpful
- Write tests for new features

### Pull Requests
- Keep changes focused and atomic
- Write clear commit messages
- Update documentation if needed
- Test your changes locally

### Issues
- Use clear, descriptive titles
- Provide steps to reproduce bugs
- Include environment details
- Suggest solutions when possible

## 🧪 Testing

```bash
# Code formatting
black .
isort .

# Linting
flake8 .

# Run tests (when available)
pytest
```

## 📂 Project Structure

```
calendar-insights/
├── app/              # Self-hosted application
├── app-gcp/          # Cloud application
├── .github/          # GitHub Actions
├── .gitlab-ci.yml    # GitLab CI
└── README.md         # Main documentation
```

## 🎯 Areas for Contribution

- **Features**: New analytics, visualizations, filters
- **Performance**: Database optimization, caching
- **UI/UX**: Dashboard improvements, responsive design
- **Documentation**: Setup guides, troubleshooting
- **Testing**: Unit tests, integration tests
- **Security**: Authentication, data protection

## 💡 Feature Requests

Have an idea? [Open an issue](../../issues) with:
- Clear description of the feature
- Use case and benefits
- Possible implementation approach

## 🐛 Bug Reports

Found a bug? [Report it](../../issues) with:
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Screenshots if applicable

## 📞 Getting Help

- **Issues**: For bugs and feature requests
- **Discussions**: For questions and ideas

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License. 