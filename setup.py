from setuptools import setup, find_packages

setup(
    name="crypto-trading-bot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pytest>=7.4.3",
        "pytest-cov>=4.1.0",
        "pytest-mock>=3.12.0",
        "pytest-asyncio>=0.23.2",
        "python-dotenv>=1.0.0",
        "SQLAlchemy>=2.0.23",
    ],
    python_requires=">=3.11",
) 