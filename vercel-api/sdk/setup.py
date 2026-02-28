from setuptools import setup, find_packages

setup(
    name="clawbackup-agent",
    version="2.0.1",
    description="ClawBackup Agent SDK - Easy backup/restore for AI agents (Hosted Version)",
    author="Altron",
    author_email="",
    url="https://github.com/gertron88/clawbackup",
    py_modules=["clawbackup"],
    install_requires=[
        "requests>=2.28.0",
        "cryptography>=41.0.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: System :: Archiving :: Backup",
    ],
    keywords="backup agent ai automation cloud supabase vercel",
)
