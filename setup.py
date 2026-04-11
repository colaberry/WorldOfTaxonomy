from setuptools import setup, find_packages
from pathlib import Path

long_description = (Path(__file__).parent / "README.md").read_text(encoding="utf-8")

setup(
    name="world-of-taxanomy",
    version="0.1.0",
    packages=find_packages(exclude=["tests*", "frontend*", "data*"]),
    python_requires=">=3.9",
    install_requires=[
        "asyncpg>=0.29.0",
        "fastapi>=0.110.0",
        "uvicorn[standard]>=0.29.0",
        "python-dotenv>=1.0.0",
        "bcrypt>=4.0.0",
        "PyJWT>=2.8.0",
        "slowapi>=0.1.9",
        "openpyxl>=3.1.0",
        "xlrd>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.0",
            "twine>=5.0.0",
            "build>=1.0.0",
        ]
    },
    description="Unified global industry classification knowledge graph - NAICS, ISIC, NACE, SIC, and 6 more systems connected by crosswalk edges.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="ramdhanyk",
    author_email="",
    url="https://github.com/ramdhanyk/WorldOfTaxanomy",
    project_urls={
        "Documentation": "https://worldoftaxanomy.com",
        "Source": "https://github.com/ramdhanyk/WorldOfTaxanomy",
        "Tracker": "https://github.com/ramdhanyk/WorldOfTaxanomy/issues",
    },
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Database",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Operating System :: OS Independent",
    ],
    keywords=[
        "taxonomy", "classification", "industry", "NAICS", "ISIC", "NACE", "SIC",
        "knowledge-graph", "crosswalk", "MCP", "fastapi", "open-data",
    ],
    entry_points={
        "console_scripts": [
            "world-of-taxanomy=world_of_taxanomy.__main__:main",
        ],
    },
    include_package_data=True,
    package_data={
        "world_of_taxanomy": ["schema.sql", "schema_auth.sql"],
    },
)
