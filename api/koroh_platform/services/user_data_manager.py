"""
User Data Management Service for Koroh Platform

This service provides comprehensive user data organization, storage, and retrieval
for AI analysis results, portfolios, and related files. It ensures proper data
isolation, security, and easy access while maintaining data integrity.
"""

import os
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid

logger = logging.getLogger(__name__)


class UserDataManager:
    """
    Comprehensive user data management system for AI analysis and portfolio generation.
    
    Organizes user data in a structured hierarchy:
    /user_data/
    ├── user_{user_id}/
    │   ├── profile/
    │   │   ├── avatar.jpg
    │   │   └── metadata.json
    │   ├── cvs/
    │   │   ├── cv_{timestamp}/
    │   │   │   ├── original/
    │   │   │   │   ├── cv.pdf
    │   │   │   │   └── metadata.json
    │   │   │   ├── extracted/
    │   │   │   │   ├── text.txt
    │   │   │   │   ├── images/
    │   │   │   │   └── analysis.json
    │   │   │   └── processed/
    │   │   │       ├── enhanced_cv.pdf
    │   │   │       └── recommendations.json
    │   ├── portfolios/
    │   │   ├── portfolio_{timestamp}/
    │   │   │   ├── website/
    │   │   │   │   ├── index.html
    │   │   │   │   ├── styles.css
    │   │   │   │   ├── script.js
    │   │   │   │   └── images/
    │   │   │   ├── analysis/
    │   │   │   │   ├── cv_analysis.json
    │   │   │   │   ├── online_presence.json
    │   │   │   │   └── recommendations.json
    │   │   │   └── metadata.json
    │   ├── analysis_history/
    │   │   ├── session_{timestamp}.json
    │   │   └── ...
    │   └── exports/
    │       ├── portfolio_export_{timestamp}.zip
    │       └── ...
    """
    
    def __init__(self, user: Optional[User] = None, user_id: Optional[int] = None):
        """
        Initialize user data manager.
        
        Args:
            user: Django User instance
            user_id: User ID if User instance not available
        """
        if user:
            self.user = user
            self.user_id = user.id
        elif user_id:
            self.user_id = user_id
            try:
                self.user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                self.user = None
        else:
            raise ValueError("Either user or user_id must be provided")
        
        # Base paths
        self.base_path = Path(settings.MEDIA_ROOT) / "user_data"
        self.user_path = self.base_path / f"user_{self.user_id}"
        
        # User-specific paths
        self.profile_path = self.user_path / "profile"
        self.cvs_path = self.user_path / "cvs"
        self.portfolios_path = self.user_path / "portfolios"
        self.analysis_history_path = self.user_path / "analysis_history"
        self.exports_path = self.user_path / "exports"
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all necessary directories exist."""
        directories = [
            self.user_path,
            self.profile_path,
            self.cvs_path,
            self.portfolios_path,
            self.analysis_history_path,
            self.exports_path
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def store_cv_upload(self, cv_file, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Store uploaded CV file with proper organization.
        
        Args:
            cv_file: Uploaded file object
            filename: Optional custom filename
            
        Returns:
            Dict with CV storage information
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cv_session_id = f"cv_{timestamp}_{uuid.uuid4().hex[:8]}"
        
        # Create CV session directory
        cv_session_path = self.cvs_path / cv_session_id
        original_path = cv_session_path / "original"
        extracted_path = cv_session_path / "extracted"
        processed_path = cv_session_path / "processed"
        
        for path in [original_path, extracted_path, processed_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Store original file
        if filename is None:
            filename = getattr(cv_file, 'name', f'cv_{timestamp}.pdf')
        
        original_file_path = original_path / filename
        
        # Save file
        with open(original_file_path, 'wb') as f:
            for chunk in cv_file.chunks():
                f.write(chunk)
        
        # Create metadata
        metadata = {
            'cv_session_id': cv_session_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'original_filename': filename,
            'upload_timestamp': timestamp,
            'file_size': original_file_path.stat().st_size,
            'file_path': str(original_file_path),
            'status': 'uploaded',
            'analysis_status': 'pending'
        }
        
        # Save metadata
        metadata_file = original_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"CV uploaded for user {self.user_id}: {cv_session_id}")
        
        return {
            'cv_session_id': cv_session_id,
            'file_path': str(original_file_path),
            'metadata': metadata,
            'paths': {
                'session': str(cv_session_path),
                'original': str(original_path),
                'extracted': str(extracted_path),
                'processed': str(processed_path)
            }
        }
    
    def store_cv_analysis(self, cv_session_id: str, analysis_data: Dict[str, Any], 
                         extracted_content: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Store CV analysis results.
        
        Args:
            cv_session_id: CV session identifier
            analysis_data: Complete analysis results from AI
            extracted_content: Extracted text, images, etc.
            
        Returns:
            Dict with storage information
        """
        cv_session_path = self.cvs_path / cv_session_id
        
        if not cv_session_path.exists():
            raise ValueError(f"CV session {cv_session_id} not found")
        
        extracted_path = cv_session_path / "extracted"
        
        # Store extracted content
        if extracted_content:
            # Store extracted text
            if extracted_content.get('text'):
                text_file = extracted_path / "extracted_text.txt"
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(extracted_content['text'])
            
            # Store extracted images
            if extracted_content.get('images'):
                images_path = extracted_path / "images"
                images_path.mkdir(exist_ok=True)
                
                for img_info in extracted_content['images']:
                    if 'path' in img_info and Path(img_info['path']).exists():
                        src_path = Path(img_info['path'])
                        dst_path = images_path / img_info['filename']
                        shutil.copy2(src_path, dst_path)
            
            # Store extraction metadata
            extraction_file = extracted_path / "extraction_metadata.json"
            with open(extraction_file, 'w') as f:
                json.dump(extracted_content, f, indent=2)
        
        # Store AI analysis results
        analysis_file = extracted_path / "ai_analysis.json"
        analysis_with_metadata = {
            'analysis_timestamp': datetime.now().isoformat(),
            'user_id': self.user_id,
            'cv_session_id': cv_session_id,
            'model_used': analysis_data.get('model_used', 'unknown'),
            'analysis_data': analysis_data
        }
        
        with open(analysis_file, 'w') as f:
            json.dump(analysis_with_metadata, f, indent=2)
        
        # Update CV metadata
        original_metadata_file = cv_session_path / "original" / "metadata.json"
        if original_metadata_file.exists():
            with open(original_metadata_file, 'r') as f:
                metadata = json.load(f)
            
            metadata['analysis_status'] = 'completed'
            metadata['analysis_timestamp'] = datetime.now().isoformat()
            metadata['analysis_score'] = analysis_data.get('cv_analysis', {}).get('overall_score', 0)
            
            with open(original_metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        
        logger.info(f"CV analysis stored for user {self.user_id}, session {cv_session_id}")
        
        return {
            'cv_session_id': cv_session_id,
            'analysis_file': str(analysis_file),
            'extracted_path': str(extracted_path)
        }
    
    def store_portfolio(self, cv_session_id: str, portfolio_content: Dict[str, Any], 
                       website_files: Dict[str, str], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store generated portfolio with all associated files.
        
        Args:
            cv_session_id: Associated CV session ID
            portfolio_content: Generated portfolio content
            website_files: Dict of filename -> content for website files
            analysis_data: Complete analysis data
            
        Returns:
            Dict with portfolio storage information
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        portfolio_id = f"portfolio_{timestamp}_{uuid.uuid4().hex[:8]}"
        
        # Create portfolio directory structure
        portfolio_path = self.portfolios_path / portfolio_id
        website_path = portfolio_path / "website"
        analysis_path = portfolio_path / "analysis"
        
        for path in [website_path, analysis_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Store website files
        for filename, content in website_files.items():
            file_path = website_path / filename
            
            if filename.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                # Handle binary files (images)
                if isinstance(content, (str, Path)):
                    # If content is a path, copy the file
                    if Path(content).exists():
                        shutil.copy2(content, file_path)
                else:
                    # If content is binary data
                    with open(file_path, 'wb') as f:
                        f.write(content)
            else:
                # Handle text files
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
        
        # Store analysis data
        analysis_files = {
            'cv_analysis.json': analysis_data.get('cv_analysis', {}),
            'online_assessment.json': analysis_data.get('online_assessment', {}),
            'portfolio_content.json': portfolio_content,
            'complete_analysis.json': analysis_data
        }
        
        for filename, data in analysis_files.items():
            file_path = analysis_path / filename
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        
        # Create portfolio metadata
        metadata = {
            'portfolio_id': portfolio_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'cv_session_id': cv_session_id,
            'creation_timestamp': timestamp,
            'website_files': list(website_files.keys()),
            'analysis_files': list(analysis_files.keys()),
            'portfolio_score': analysis_data.get('cv_analysis', {}).get('overall_score', 0),
            'online_presence_score': analysis_data.get('online_assessment', {}).get('overall_presence_score', 0),
            'status': 'completed'
        }
        
        metadata_file = portfolio_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Store in analysis history
        self._store_analysis_session(cv_session_id, portfolio_id, analysis_data)
        
        logger.info(f"Portfolio stored for user {self.user_id}: {portfolio_id}")
        
        return {
            'portfolio_id': portfolio_id,
            'portfolio_path': str(portfolio_path),
            'website_path': str(website_path),
            'analysis_path': str(analysis_path),
            'metadata': metadata,
            'website_url': f"/media/user_data/user_{self.user_id}/portfolios/{portfolio_id}/website/index.html"
        }
    
    def _store_analysis_session(self, cv_session_id: str, portfolio_id: str, analysis_data: Dict[str, Any]):
        """Store analysis session in history."""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session_file = self.analysis_history_path / f"{session_id}.json"
        
        session_data = {
            'session_id': session_id,
            'user_id': self.user_id,
            'cv_session_id': cv_session_id,
            'portfolio_id': portfolio_id,
            'timestamp': datetime.now().isoformat(),
            'cv_score': analysis_data.get('cv_analysis', {}).get('overall_score', 0),
            'online_score': analysis_data.get('online_assessment', {}).get('overall_presence_score', 0),
            'strengths_count': len(analysis_data.get('cv_analysis', {}).get('strengths', [])),
            'recommendations_count': len(analysis_data.get('cv_analysis', {}).get('recommendations', [])),
            'technical_skills_count': len(analysis_data.get('cv_analysis', {}).get('technical_skills', [])),
            'work_experience_count': len(analysis_data.get('cv_analysis', {}).get('work_experience', []))
        }
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
    
    def get_user_cvs(self) -> List[Dict[str, Any]]:
        """Get list of all CVs for the user."""
        cvs = []
        
        if not self.cvs_path.exists():
            return cvs
        
        for cv_dir in self.cvs_path.iterdir():
            if cv_dir.is_dir() and cv_dir.name.startswith('cv_'):
                metadata_file = cv_dir / "original" / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    cvs.append(metadata)
        
        # Sort by upload timestamp (newest first)
        cvs.sort(key=lambda x: x.get('upload_timestamp', ''), reverse=True)
        return cvs
    
    def get_user_portfolios(self) -> List[Dict[str, Any]]:
        """Get list of all portfolios for the user."""
        portfolios = []
        
        if not self.portfolios_path.exists():
            return portfolios
        
        for portfolio_dir in self.portfolios_path.iterdir():
            if portfolio_dir.is_dir() and portfolio_dir.name.startswith('portfolio_'):
                metadata_file = portfolio_dir / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    portfolios.append(metadata)
        
        # Sort by creation timestamp (newest first)
        portfolios.sort(key=lambda x: x.get('creation_timestamp', ''), reverse=True)
        return portfolios
    
    def get_analysis_history(self) -> List[Dict[str, Any]]:
        """Get analysis history for the user."""
        history = []
        
        if not self.analysis_history_path.exists():
            return history
        
        for session_file in self.analysis_history_path.glob("session_*.json"):
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            history.append(session_data)
        
        # Sort by timestamp (newest first)
        history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return history
    
    def get_cv_analysis(self, cv_session_id: str) -> Optional[Dict[str, Any]]:
        """Get CV analysis results."""
        analysis_file = self.cvs_path / cv_session_id / "extracted" / "ai_analysis.json"
        
        if not analysis_file.exists():
            return None
        
        with open(analysis_file, 'r') as f:
            return json.load(f)
    
    def get_portfolio_data(self, portfolio_id: str) -> Optional[Dict[str, Any]]:
        """Get complete portfolio data."""
        portfolio_path = self.portfolios_path / portfolio_id
        
        if not portfolio_path.exists():
            return None
        
        # Read metadata
        metadata_file = portfolio_path / "metadata.json"
        if not metadata_file.exists():
            return None
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Read analysis data
        analysis_file = portfolio_path / "analysis" / "complete_analysis.json"
        analysis_data = {}
        if analysis_file.exists():
            with open(analysis_file, 'r') as f:
                analysis_data = json.load(f)
        
        return {
            'metadata': metadata,
            'analysis_data': analysis_data,
            'portfolio_path': str(portfolio_path),
            'website_path': str(portfolio_path / "website"),
            'website_url': f"/media/user_data/user_{self.user_id}/portfolios/{portfolio_id}/website/index.html"
        }
    
    def create_portfolio_export(self, portfolio_id: str) -> Optional[str]:
        """Create a ZIP export of a portfolio."""
        portfolio_path = self.portfolios_path / portfolio_id
        
        if not portfolio_path.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_filename = f"portfolio_export_{portfolio_id}_{timestamp}.zip"
        export_path = self.exports_path / export_filename
        
        # Create ZIP file
        shutil.make_archive(str(export_path.with_suffix('')), 'zip', str(portfolio_path))
        
        logger.info(f"Portfolio export created for user {self.user_id}: {export_filename}")
        
        return str(export_path)
    
    def cleanup_old_data(self, days_old: int = 90):
        """Clean up old data older than specified days."""
        cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        
        cleaned_items = []
        
        # Clean old exports
        if self.exports_path.exists():
            for export_file in self.exports_path.glob("*.zip"):
                if export_file.stat().st_mtime < cutoff_date:
                    export_file.unlink()
                    cleaned_items.append(f"Export: {export_file.name}")
        
        # Clean old analysis sessions (keep metadata but remove large files)
        if self.analysis_history_path.exists():
            for session_file in self.analysis_history_path.glob("session_*.json"):
                if session_file.stat().st_mtime < cutoff_date:
                    session_file.unlink()
                    cleaned_items.append(f"Session: {session_file.name}")
        
        logger.info(f"Cleaned {len(cleaned_items)} old items for user {self.user_id}")
        return cleaned_items
    
    def get_user_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics for the user."""
        def get_dir_size(path: Path) -> int:
            """Get total size of directory."""
            if not path.exists():
                return 0
            
            total_size = 0
            for item in path.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
            return total_size
        
        stats = {
            'user_id': self.user_id,
            'total_size': get_dir_size(self.user_path),
            'cvs_size': get_dir_size(self.cvs_path),
            'portfolios_size': get_dir_size(self.portfolios_path),
            'exports_size': get_dir_size(self.exports_path),
            'cvs_count': len(self.get_user_cvs()),
            'portfolios_count': len(self.get_user_portfolios()),
            'analysis_sessions_count': len(self.get_analysis_history()),
            'last_activity': None
        }
        
        # Get last activity
        history = self.get_analysis_history()
        if history:
            stats['last_activity'] = history[0].get('timestamp')
        
        return stats


class UserDataManagerFactory:
    """Factory for creating UserDataManager instances."""
    
    @staticmethod
    def for_user(user: User) -> UserDataManager:
        """Create UserDataManager for a User instance."""
        return UserDataManager(user=user)
    
    @staticmethod
    def for_user_id(user_id: int) -> UserDataManager:
        """Create UserDataManager for a user ID."""
        return UserDataManager(user_id=user_id)
    
    @staticmethod
    def get_all_users_stats() -> List[Dict[str, Any]]:
        """Get storage statistics for all users."""
        base_path = Path(settings.MEDIA_ROOT) / "user_data"
        
        if not base_path.exists():
            return []
        
        stats = []
        for user_dir in base_path.iterdir():
            if user_dir.is_dir() and user_dir.name.startswith('user_'):
                try:
                    user_id = int(user_dir.name.split('_')[1])
                    manager = UserDataManager(user_id=user_id)
                    user_stats = manager.get_user_storage_stats()
                    stats.append(user_stats)
                except (ValueError, Exception) as e:
                    logger.warning(f"Could not get stats for {user_dir.name}: {e}")
        
        return stats