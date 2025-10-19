# File Organization System for User AI Analysis

## Overview

This document outlines the file organization system for storing user-generated content and AI analysis results in the Koroh platform. The system ensures data integrity, user privacy, efficient retrieval, and scalability.

## Directory Structure

```
storage/
├── users/
│   └── {user_id}/
│       ├── profile/
│       │   ├── documents/
│       │   │   ├── resume/
│       │   │   │   ├── original/
│       │   │   │   │   └── resume_{timestamp}.{ext}
│       │   │   │   ├── processed/
│       │   │   │   │   └── resume_{timestamp}_processed.json
│       │   │   │   └── analysis/
│       │   │   │       └── resume_{timestamp}_analysis.json
│       │   │   ├── cover_letters/
│       │   │   │   ├── original/
│       │   │   │   ├── processed/
│       │   │   │   └── analysis/
│       │   │   └── portfolios/
│       │   │       ├── original/
│       │   │       ├── processed/
│       │   │       └── analysis/
│       │   ├── images/
│       │   │   ├── profile_photos/
│       │   │   │   ├── original/
│       │   │   │   └── processed/
│       │   │   └── portfolio_images/
│       │   │       ├── original/
│       │   │       └── processed/
│       │   └── metadata/
│       │       ├── profile_data.json
│       │       ├── preferences.json
│       │       └── privacy_settings.json
│       ├── ai_analysis/
│       │   ├── skill_analysis/
│       │   │   ├── {analysis_id}/
│       │   │   │   ├── input_data.json
│       │   │   │   ├── ai_response.json
│       │   │   │   ├── processed_results.json
│       │   │   │   └── metadata.json
│       │   ├── personality_analysis/
│       │   ├── career_recommendations/
│       │   ├── networking_suggestions/
│       │   └── content_optimization/
│       ├── connections/
│       │   ├── requests/
│       │   ├── accepted/
│       │   └── analytics/
│       ├── conversations/
│       │   ├── {conversation_id}/
│       │   │   ├── messages.json
│       │   │   ├── ai_insights.json
│       │   │   └── metadata.json
│       └── temp/
│           ├── uploads/
│           └── processing/
├── shared/
│   ├── templates/
│   ├── models/
│   └── cache/
└── system/
    ├── logs/
    ├── backups/
    └── analytics/
```

## File Naming Conventions

### User Files

- **Format**: `{type}_{timestamp}_{version}.{extension}`
- **Example**: `resume_20241019143022_v1.pdf`
- **Timestamp**: YYYYMMDDHHMMSS format
- **Version**: Incremental version number

### AI Analysis Files

- **Format**: `{analysis_type}_{user_id}_{timestamp}_{analysis_id}.json`
- **Example**: `skill_analysis_12345_20241019143022_abc123.json`

### Metadata Files

- **Format**: `{data_type}_metadata.json`
- **Example**: `profile_metadata.json`

## File Types and Storage

### Document Storage

```json
{
  "original": {
    "path": "/users/{user_id}/profile/documents/resume/original/",
    "formats": ["pdf", "doc", "docx", "txt"],
    "max_size": "10MB",
    "retention": "permanent"
  },
  "processed": {
    "path": "/users/{user_id}/profile/documents/resume/processed/",
    "format": "json",
    "contains": ["extracted_text", "structured_data", "metadata"],
    "retention": "permanent"
  },
  "analysis": {
    "path": "/users/{user_id}/profile/documents/resume/analysis/",
    "format": "json",
    "contains": ["ai_insights", "skills", "recommendations", "scores"],
    "retention": "permanent"
  }
}
```

### Image Storage

```json
{
  "original": {
    "path": "/users/{user_id}/profile/images/profile_photos/original/",
    "formats": ["jpg", "jpeg", "png", "webp"],
    "max_size": "5MB",
    "retention": "permanent"
  },
  "processed": {
    "path": "/users/{user_id}/profile/images/profile_photos/processed/",
    "formats": ["webp", "jpg"],
    "sizes": ["thumbnail", "medium", "large"],
    "retention": "permanent"
  }
}
```

## Data Organization Principles

### 1. User Isolation

- Each user has a dedicated directory identified by their unique user ID
- No cross-user data access at the file system level
- Separate processing queues per user

### 2. Data Categorization

- **Profile Data**: Core user information and documents
- **AI Analysis**: All AI-generated insights and recommendations
- **Connections**: Networking-related data
- **Conversations**: Communication history and AI insights
- **Temporary**: Short-lived processing files

### 3. Version Control

- All files maintain version history
- Original files are never modified
- Processed versions are stored separately
- Analysis results are timestamped and versioned

### 4. Metadata Management

```json
{
  "file_id": "unique_file_identifier",
  "user_id": "user_identifier",
  "file_type": "resume|cover_letter|portfolio|image",
  "original_name": "user_provided_filename",
  "mime_type": "application/pdf",
  "size_bytes": 1048576,
  "upload_timestamp": "2024-10-19T14:30:22Z",
  "processing_status": "completed|pending|failed",
  "ai_analysis_status": "completed|pending|failed|not_started",
  "privacy_level": "private|connections|public",
  "retention_policy": "permanent|temporary|user_controlled",
  "checksum": "sha256_hash",
  "encryption_status": "encrypted|not_encrypted",
  "access_log": [
    {
      "timestamp": "2024-10-19T14:30:22Z",
      "action": "upload|view|download|analyze",
      "user_id": "accessor_user_id",
      "ip_address": "192.168.1.1"
    }
  ]
}
```

## Security and Privacy

### 1. Encryption

- All sensitive files encrypted at rest using AES-256
- Encryption keys managed separately from file storage
- User-specific encryption keys for additional security

### 2. Access Control

```json
{
  "file_permissions": {
    "owner": ["read", "write", "delete", "share"],
    "connections": ["read"],
    "public": [],
    "system": ["read", "analyze", "backup"]
  },
  "privacy_levels": {
    "private": "owner_only",
    "connections": "owner_and_approved_connections",
    "public": "all_users",
    "system_only": "ai_analysis_only"
  }
}
```

### 3. Data Retention

- User-controlled retention policies
- Automatic cleanup of temporary files
- Compliance with data protection regulations (GDPR, CCPA)

## AI Analysis Data Structure

### Analysis Input

```json
{
  "analysis_id": "unique_analysis_identifier",
  "user_id": "user_identifier",
  "analysis_type": "skill_analysis|personality|career_recommendation",
  "input_files": [
    {
      "file_id": "file_identifier",
      "file_path": "relative_path_to_file",
      "file_type": "resume|cover_letter|portfolio"
    }
  ],
  "analysis_parameters": {
    "model": "aws_bedrock_claude",
    "version": "v1.0",
    "custom_prompts": [],
    "focus_areas": ["skills", "experience", "education"]
  },
  "timestamp": "2024-10-19T14:30:22Z"
}
```

### Analysis Output

```json
{
  "analysis_id": "unique_analysis_identifier",
  "user_id": "user_identifier",
  "analysis_type": "skill_analysis",
  "status": "completed|failed|in_progress",
  "results": {
    "skills": {
      "technical": [
        {
          "skill": "Python",
          "proficiency": "advanced",
          "confidence": 0.95,
          "evidence": ["5 years experience", "multiple projects"]
        }
      ],
      "soft": [
        {
          "skill": "Leadership",
          "proficiency": "intermediate",
          "confidence": 0.8,
          "evidence": ["team lead role", "project management"]
        }
      ]
    },
    "recommendations": [
      {
        "type": "skill_development",
        "priority": "high",
        "suggestion": "Consider learning React for full-stack development",
        "reasoning": "Complements existing Python skills"
      }
    ],
    "insights": {
      "career_stage": "mid_level",
      "growth_potential": "high",
      "networking_opportunities": ["tech_meetups", "python_conferences"]
    }
  },
  "processing_time_ms": 2500,
  "ai_model_info": {
    "model": "claude-3-sonnet",
    "version": "20240229",
    "tokens_used": 1500
  },
  "timestamp": "2024-10-19T14:30:22Z"
}
```

## File Management API

### File Operations

```python
class UserFileManager:
    def upload_file(self, user_id: str, file_type: str, file_data: bytes) -> str
    def get_file(self, user_id: str, file_id: str) -> FileData
    def delete_file(self, user_id: str, file_id: str) -> bool
    def list_files(self, user_id: str, file_type: str = None) -> List[FileMetadata]
    def update_file_metadata(self, user_id: str, file_id: str, metadata: dict) -> bool

class AIAnalysisManager:
    def create_analysis(self, user_id: str, analysis_type: str, input_files: List[str]) -> str
    def get_analysis_results(self, user_id: str, analysis_id: str) -> AnalysisResults
    def list_analyses(self, user_id: str, analysis_type: str = None) -> List[AnalysisMetadata]
    def delete_analysis(self, user_id: str, analysis_id: str) -> bool
```

## Backup and Recovery

### Backup Strategy

- Daily incremental backups of user data
- Weekly full backups
- Geographic distribution of backups
- Point-in-time recovery capability

### Recovery Procedures

- User data recovery within 24 hours
- AI analysis recreation from original files
- Metadata reconstruction from logs

## Monitoring and Analytics

### File System Monitoring

- Storage usage per user
- File access patterns
- Processing queue status
- Error rates and types

### Performance Metrics

- File upload/download speeds
- AI analysis processing times
- Storage efficiency
- User engagement with AI features

## Implementation Considerations

### Scalability

- Horizontal scaling with user sharding
- CDN integration for file delivery
- Caching strategies for frequently accessed files
- Queue management for AI processing

### Compliance

- GDPR right to be forgotten
- Data portability requirements
- Audit trail maintenance
- Privacy by design principles

This file organization system ensures that user data is properly organized, secure, and efficiently accessible while maintaining clear ownership and privacy boundaries.
