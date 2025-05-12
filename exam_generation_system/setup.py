from setuptools import setup, find_packages

setup(
    name='exam_generation_system',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask>=2.0',
        # Add other specific dependencies if any, e.g., specific PDF library version
    ],
    entry_points={
        'console_scripts': [
            'exam_generator = src.main:app.run'  # Example, adjust if needed
        ],
    },
    author='AI Assistant',
    author_email='ai@example.com',
    description='A system to generate exam papers from PDF books using AI.',
    long_description=open('README.md').read() if os.path.exists('README.md') else '',
    long_description_content_type='text/markdown',
    url='https://github.com/example/exam_generation_system', # Replace with actual URL if available
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License', # Choose an appropriate license
        'Operating System :: OS Independent',
        'Framework :: Flask',
        'Topic :: Education',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
    python_requires='>=3.9',
)

