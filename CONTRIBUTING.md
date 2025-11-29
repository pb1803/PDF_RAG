# 🤝 Contributing to Enhanced RAG Pipeline - Academic Agent

Thank you for your interest in contributing to the Enhanced RAG Pipeline! This document provides guidelines and information for contributors.

## 🎯 **How to Contribute**

### **Types of Contributions**

We welcome several types of contributions:

- 🐛 **Bug Reports**: Help us identify and fix issues
- ✨ **Feature Requests**: Suggest new functionality
- 📝 **Documentation**: Improve guides, examples, and API docs
- 🧪 **Tests**: Add or improve test coverage
- 🔧 **Code**: Fix bugs or implement new features
- 🎨 **UI/UX**: Improve the web interface and user experience

---

## 🚀 **Getting Started**

### **1. Fork and Clone**
```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/Academic_agent.git
cd Academic_agent
```

### **2. Set Up Development Environment**
```bash
# Run automated setup
python setup.py

# Or manual setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
```

### **3. Create a Branch**
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

---

## 🛠️ **Development Workflow**

### **Code Style and Standards**

We use several tools to maintain code quality:

```bash
# Format code
make format

# Run linting
make lint

# Type checking
make type-check

# Run all checks
make pre-commit
```

**Code Style Guidelines:**
- Follow PEP 8 Python style guide
- Use type hints for all functions
- Write docstrings for all public functions and classes
- Keep functions focused and small
- Use meaningful variable and function names

### **Testing**

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test categories
make test-quick      # Quick unit tests
make test-api        # API endpoint tests
make test-enhanced   # Enhanced RAG features
```

**Testing Guidelines:**
- Write tests for all new features
- Maintain at least 80% code coverage
- Include both unit and integration tests
- Test error conditions and edge cases
- Use descriptive test names

### **Documentation**

```bash
# Generate documentation
make docs

# Serve documentation locally
make docs-serve
```

**Documentation Guidelines:**
- Update README.md for user-facing changes
- Add docstrings to all public APIs
- Include code examples in documentation
- Update API documentation for endpoint changes

---

## 📋 **Pull Request Process**

### **Before Submitting**

1. **Run all checks:**
   ```bash
   make format lint type-check test
   ```

2. **Update documentation:**
   - Update README.md if needed
   - Add/update docstrings
   - Update API documentation

3. **Test your changes:**
   - Run existing tests
   - Add new tests for your changes
   - Test manually with the demo interface

### **Pull Request Guidelines**

1. **Title**: Use a clear, descriptive title
   - ✅ "Add table generation for comparison questions"
   - ❌ "Fix stuff"

2. **Description**: Include:
   - What changes were made
   - Why the changes were needed
   - How to test the changes
   - Any breaking changes

3. **Commits**: 
   - Use clear commit messages
   - Keep commits focused and atomic
   - Reference issues when applicable

### **Example PR Template**
```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Refactoring

## Testing
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

---

## 🐛 **Reporting Issues**

### **Bug Reports**

When reporting bugs, please include:

1. **Environment Information:**
   - Operating System
   - Python version
   - Package versions (`pip freeze`)

2. **Steps to Reproduce:**
   - Exact steps that cause the issue
   - Expected behavior
   - Actual behavior

3. **Additional Context:**
   - Error messages and stack traces
   - Log files (if applicable)
   - Screenshots (for UI issues)

### **Feature Requests**

For feature requests, please include:

1. **Problem Description:**
   - What problem does this solve?
   - Who would benefit from this feature?

2. **Proposed Solution:**
   - Detailed description of the feature
   - How it should work
   - Alternative solutions considered

3. **Additional Context:**
   - Examples from other projects
   - Mockups or diagrams (if applicable)

---

## 🏗️ **Architecture Guidelines**

### **Project Structure**

```
app/
├── api/           # FastAPI routes and endpoints
├── core/          # Core configuration and utilities
├── models/        # Database models
├── rag/           # RAG pipeline components
└── schemas/       # Pydantic schemas for API
```

### **Key Components**

1. **RAG Pipeline** (`app/rag/rag_pipeline.py`):
   - Main orchestration logic
   - Answer type determination
   - Response formatting

2. **API Routes** (`app/api/`):
   - RESTful endpoints
   - Request/response handling
   - Error handling

3. **Vector Store** (`app/rag/vectorstore.py`):
   - Qdrant integration
   - Document indexing
   - Similarity search

### **Design Principles**

- **Modularity**: Keep components loosely coupled
- **Testability**: Design for easy testing
- **Extensibility**: Make it easy to add new features
- **Performance**: Optimize for response time and throughput
- **Reliability**: Handle errors gracefully

---

## 🔧 **Development Tips**

### **Local Development**

```bash
# Start development server with auto-reload
make run

# Run in debug mode
DEBUG=True python main.py

# Test API endpoints
make test-api

# Open web demo
make demo-web
```

### **Debugging**

```bash
# Enable detailed logging
export LOG_LEVEL=DEBUG

# Use IPython for interactive debugging
pip install ipython
# Add: import IPython; IPython.embed() in your code

# Profile performance
make profile
```

### **Docker Development**

```bash
# Build and run with Docker
make docker-build
make docker-run

# View logs
make docker-logs

# Stop containers
make docker-stop
```

---

## 📚 **Resources**

### **Documentation**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Google AI Documentation](https://ai.google.dev/docs)
- [Pydantic Documentation](https://docs.pydantic.dev/)

### **Tools**
- [Black Code Formatter](https://black.readthedocs.io/)
- [Ruff Linter](https://docs.astral.sh/ruff/)
- [pytest Testing Framework](https://docs.pytest.org/)
- [mypy Type Checker](https://mypy.readthedocs.io/)

### **Learning Resources**
- [RAG Systems Guide](https://docs.llamaindex.ai/en/stable/getting_started/concepts.html)
- [Vector Databases](https://www.pinecone.io/learn/vector-database/)
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)

---

## 🎖️ **Recognition**

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- GitHub contributors page

---

## 📞 **Getting Help**

### **Communication Channels**
- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Code Reviews**: For feedback on pull requests

### **Response Times**
- Issues: We aim to respond within 48 hours
- Pull Requests: Initial review within 72 hours
- Questions: Response within 24 hours when possible

---

## 📄 **Code of Conduct**

### **Our Standards**

- **Be Respectful**: Treat everyone with respect and kindness
- **Be Inclusive**: Welcome contributors from all backgrounds
- **Be Constructive**: Provide helpful feedback and suggestions
- **Be Patient**: Remember that everyone is learning

### **Unacceptable Behavior**

- Harassment or discrimination of any kind
- Trolling, insulting, or derogatory comments
- Publishing private information without permission
- Any conduct that would be inappropriate in a professional setting

### **Enforcement**

Instances of unacceptable behavior may result in:
1. Warning
2. Temporary ban from the project
3. Permanent ban from the project

Report issues to the project maintainers.

---

## 🙏 **Thank You**

Thank you for contributing to the Enhanced RAG Pipeline! Your contributions help make this project better for everyone in the academic and AI community.

**Happy coding! 🚀**