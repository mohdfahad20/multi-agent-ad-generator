from setuptools import setup, find_packages

setup(
    name="cwt_ads_agent",
    version="1.0.0",
    description="CrowdWisdomTrading Daily Ads AI Agent - CrewAI multi-agent pipeline",
    author="CWT Intern",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "crewai>=0.80.0",
        "crewai-tools>=0.17.0",
        "apify-client>=1.7.0",
        "google-api-python-client>=2.120.0",
        "google-auth-httplib2>=0.2.0",
        "google-auth-oauthlib>=1.2.0",
        "openai>=1.30.0",          # OpenRouter uses OpenAI-compatible SDK
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
        "pydantic>=2.6.0",
        "rich>=13.7.0",            # Beautiful terminal logging
        "tenacity>=8.2.0",         # Retry logic
        "httpx>=0.27.0",
        "huggingface_hub>=0.23.0", # InferenceClient for image generation
        "Pillow>=10.0.0",          # PIL — save images from InferenceClient
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "black>=24.0.0",
            "ruff>=0.3.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "cwt-ads=main:main",
        ]
    },
)