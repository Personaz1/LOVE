"""
Configuration management for ΔΣ Guardian AI Client
Centralized settings and environment variables
"""

import os
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Centralized configuration for the AI client"""
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')
    VISION_API_KEY: str = os.getenv('GOOGLE_CLOUD_VISION_API_KEY', 'AIzaSyCxdKfHptmqDDdLHSx8C2xOhjg9RLjCm_w')
    
    # Model Configuration
    MODELS: List[Dict[str, Any]] = [
        {
            'name': 'gemini-2.5-pro',
            'quota': 100,
            'vision': True
        },
        {
            'name': 'gemini-1.5-pro',
            'quota': 150,
            'vision': True
        },
        {
            'name': 'gemini-2.5-flash',
            'quota': 250,
            'vision': True
        },
        {
            'name': 'gemini-1.5-flash',
            'quota': 500,
            'vision': True
        },
        {
            'name': 'gemini-2.0-flash',
            'quota': 200,
            'vision': True
        },
        {
            'name': 'gemini-2.0-flash-lite',
            'quota': 1000,
            'vision': False
        },
        {
            'name': 'gemini-2.5-flash-lite',
            'quota': 1000,
            'vision': False
        }
    ]
    
    # System Limits
    LIMITS = {
        'max_steps': 666,
        'react_max_steps': 20,
        'memory_limit': 1000,
        'file_size_limit': 10 * 1024 * 1024,  # 10MB
        'command_timeout': 30
    }
    
    # File Paths
    PATHS = {
        'sandbox': 'guardian_sandbox/',
        'memory': 'memory/',
        'prompts': 'prompts/',
        'static': 'static/',
        'templates': 'templates/',
        'logs': 'app.log'
    }
    
    # Security
    SECURITY = {
        'blocked_commands': [
            'rm -rf', 'sudo', 'chmod', 'dd', 'shutdown', 'halt',
            'reboot', 'init', 'killall', 'pkill', 'kill -9'
        ],
        'allowed_directories': [
            '.', 'guardian_sandbox', 'memory', 'prompts', 'static', 'templates'
        ]
    }
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        return True 