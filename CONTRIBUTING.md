# Contributing to Benjamin Graham Stock Screener

We welcome contributions to improve this conservative value investing tool!

## How to Contribute

### 1. Fork and Clone
```bash
git fork https://github.com/yourusername/benjamin-graham-screener
git clone https://github.com/yourusername/benjamin-graham-screener.git
cd benjamin-graham-screener
```

### 2. Set Up Development Environment
```bash
pip install -r requirements.txt
python test_basic.py  # Verify installation
```

### 3. Make Changes
- Create a feature branch: `git checkout -b feature/your-feature`
- Follow Benjamin Graham's conservative principles
- Add tests for new functionality
- Update documentation as needed

### 4. Test Your Changes
```bash
# Run unit tests
pytest tests/

# Test CLI functionality
python graham_scan.py --dry_run --random_sample 5

# Test basic components
python test_basic.py
```

### 5. Submit Pull Request
- Ensure all tests pass
- Update README if needed
- Describe your changes clearly
- Reference any related issues

## Development Guidelines

### Code Style
- Follow existing code style and patterns
- Use type hints where appropriate
- Add docstrings for new functions
- Keep functions focused and small

### Benjamin Graham Principles
When adding features, ensure they align with Graham's philosophy:
- **Safety First**: Conservative assumptions over optimistic ones
- **Margin of Safety**: Always require substantial safety buffers
- **Tangible Value**: Focus on real, measurable assets
- **Consistent Earnings**: Prefer proven business models
- **Low Leverage**: Favor financially strong companies

### Areas for Contribution

#### High Priority
- Additional data providers (Tiingo, Polygon, etc.)
- Improved sector-specific analysis
- Better handling of international stocks
- Performance optimizations for large datasets

#### Medium Priority
- Additional valuation methods
- Enhanced reporting features
- Mobile-friendly report formats
- Integration with portfolio management tools

#### Data Provider Integration
When adding new data providers:
1. Implement the `DataProvider` interface
2. Add to `DataProviderFactory`
3. Include rate limiting and error handling
4. Add comprehensive tests
5. Update documentation

### Testing
- Unit tests for all calculation methods
- Integration tests for data providers
- End-to-end tests for CLI functionality
- Mock data for testing without API calls

### Documentation
- Update README for new features
- Add examples for new functionality
- Include any new command-line options
- Document any breaking changes

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions about Graham's methodology
- Check existing issues before creating new ones

Thank you for helping make this tool better for value investors worldwide!