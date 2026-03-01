"""
Database connection module for Air Tracker application.

This module handles the connection to the PostgreSQL database
and provides utilities for database operations.
"""

import os
import psycopg2
from typing import Optional
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv()


def get_connection() -> Optional[psycopg2.extensions.connection]:
    """
    Establish a connection to the PostgreSQL database.
    
    Returns:
        psycopg2.connection: Database connection object
    
    Raises:
        psycopg2.OperationalError: If connection fails
    
    Example:
        >>> conn = get_connection()
        >>> cursor = conn.cursor()
    """
    
    try:
        logger.info("Establishing database connection...")
        
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT")
        )
        
        logger.info("Database connection established successfully")
        return conn
        
    except psycopg2.OperationalError as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise

