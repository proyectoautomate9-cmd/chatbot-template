"""
Configuración centralizada del proyecto.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class EmailSettings:
    """Configuración de email."""
    host: str = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    port: int = int(os.getenv('EMAIL_PORT', '587'))
    user: Optional[str] = os.getenv('EMAIL_USER')
    password: Optional[str] = os.getenv('EMAIL_PASSWORD')
    admin_email: Optional[str] = os.getenv('ADMIN_EMAIL')
    timeout: int = 30
    
    @property
    def is_configured(self) -> bool:
        return all([self.user, self.password, self.admin_email])


@dataclass
class AdminPanelSettings:
    password: str = os.getenv('ADMIN_PANEL_PASSWORD', 'admin123')
    items_per_page: int = 20
    auto_refresh: bool = False


@dataclass
class BotSettings:
    name: str = 'Milhojaldres Bot'
    version: str = '2.0.0'
    support_phone: str = '+57 300 123 4567'
    estimated_delivery_time: str = '30-45 minutos'


class Settings:
    def __init__(self):
        self.email = EmailSettings()
        self.admin_panel = AdminPanelSettings()
        self.bot = BotSettings()
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.debug = self.environment == 'development'
    
    @property
    def is_production(self) -> bool:
        return self.environment == 'production'


settings = Settings()
