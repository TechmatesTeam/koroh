"""
MeiliSearch integration utilities for Koroh platform.

This module provides search functionality for jobs, companies,
peer groups, and other searchable content using MeiliSearch.
"""

import logging
from typing import Dict, Any, List, Optional
import meilisearch
from django.conf import settings

logger = logging.getLogger(__name__)


class MeiliSearchClient:
    """
    Centralized client for MeiliSearch operations.
    
    Provides methods for indexing and searching various content types
    including jobs, companies, users, and peer groups.
    """
    
    def __init__(self):
        """Initialize the MeiliSearch client."""
        try:
            self.client = meilisearch.Client(
                settings.MEILISEARCH_URL,
                settings.MEILISEARCH_MASTER_KEY
            )
            logger.info("MeiliSearch client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MeiliSearch client: {e}")
            self.client = None
    
    def create_index(self, index_name: str, primary_key: str = 'id') -> bool:
        """
        Create a new search index.
        
        Args:
            index_name: Name of the index to create
            primary_key: Primary key field for documents
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            self.client.create_index(index_name, {'primaryKey': primary_key})
            logger.info(f"Created MeiliSearch index: {index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {e}")
            return False
    
    def configure_index(self, index_name: str, config: Dict[str, Any]) -> bool:
        """
        Configure index settings like searchable attributes, filters, etc.
        
        Args:
            index_name: Name of the index to configure
            config: Configuration dictionary
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            index = self.client.index(index_name)
            
            if 'searchable_attributes' in config:
                index.update_searchable_attributes(config['searchable_attributes'])
            
            if 'filterable_attributes' in config:
                index.update_filterable_attributes(config['filterable_attributes'])
            
            if 'sortable_attributes' in config:
                index.update_sortable_attributes(config['sortable_attributes'])
            
            if 'ranking_rules' in config:
                index.update_ranking_rules(config['ranking_rules'])
            
            logger.info(f"Configured MeiliSearch index: {index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to configure index {index_name}: {e}")
            return False
    
    def add_documents(self, index_name: str, documents: List[Dict[str, Any]]) -> bool:
        """
        Add or update documents in an index.
        
        Args:
            index_name: Name of the index
            documents: List of documents to add/update
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client or not documents:
            return False
        
        try:
            index = self.client.index(index_name)
            index.add_documents(documents)
            logger.info(f"Added {len(documents)} documents to index {index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add documents to index {index_name}: {e}")
            return False
    
    def search(
        self,
        index_name: str,
        query: str,
        filters: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        sort: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Search documents in an index.
        
        Args:
            index_name: Name of the index to search
            query: Search query string
            filters: Filter expression
            limit: Maximum number of results
            offset: Number of results to skip
            sort: List of sort criteria
            
        Returns:
            Search results or None if failed
        """
        if not self.client:
            return None
        
        try:
            index = self.client.index(index_name)
            search_params = {
                'limit': limit,
                'offset': offset,
            }
            
            if filters:
                search_params['filter'] = filters
            
            if sort:
                search_params['sort'] = sort
            
            results = index.search(query, search_params)
            logger.info(f"Search in {index_name} returned {len(results['hits'])} results")
            return results
        except Exception as e:
            logger.error(f"Search failed in index {index_name}: {e}")
            return None
    
    def delete_document(self, index_name: str, document_id: str) -> bool:
        """
        Delete a document from an index.
        
        Args:
            index_name: Name of the index
            document_id: ID of the document to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            index = self.client.index(index_name)
            index.delete_document(document_id)
            logger.info(f"Deleted document {document_id} from index {index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {document_id} from index {index_name}: {e}")
            return False


# Global instance for use throughout the application
search_client = MeiliSearchClient()


def setup_search_indexes():
    """
    Set up all required search indexes with their configurations.
    This should be called during application initialization.
    """
    indexes_config = {
        'jobs': {
            'searchable_attributes': [
                'title',
                'description',
                'company_name',
                'location',
                'requirements',
                'skills'
            ],
            'filterable_attributes': [
                'company_id',
                'location',
                'job_type',
                'experience_level',
                'salary_range',
                'is_active',
                'posted_date'
            ],
            'sortable_attributes': [
                'posted_date',
                'salary_min',
                'salary_max'
            ],
            'ranking_rules': [
                'words',
                'typo',
                'proximity',
                'attribute',
                'sort',
                'exactness'
            ]
        },
        'companies': {
            'searchable_attributes': [
                'name',
                'description',
                'industry',
                'location'
            ],
            'filterable_attributes': [
                'industry',
                'size',
                'location'
            ],
            'sortable_attributes': [
                'name',
                'size'
            ]
        },
        'peer_groups': {
            'searchable_attributes': [
                'name',
                'description',
                'industry',
                'tags'
            ],
            'filterable_attributes': [
                'industry',
                'experience_level',
                'is_private',
                'member_count'
            ],
            'sortable_attributes': [
                'created_at',
                'member_count'
            ]
        },
        'users': {
            'searchable_attributes': [
                'first_name',
                'last_name',
                'headline',
                'skills',
                'industry'
            ],
            'filterable_attributes': [
                'industry',
                'location',
                'experience_level'
            ],
            'sortable_attributes': [
                'first_name',
                'last_name'
            ]
        }
    }
    
    for index_name, config in indexes_config.items():
        # Create index if it doesn't exist
        search_client.create_index(index_name)
        
        # Configure the index
        search_client.configure_index(index_name, config)
    
    logger.info("Search indexes setup completed")


def index_job(job_data: Dict[str, Any]) -> bool:
    """
    Index a job posting for search.
    
    Args:
        job_data: Job data dictionary
        
    Returns:
        True if successful, False otherwise
    """
    return search_client.add_documents('jobs', [job_data])


def index_company(company_data: Dict[str, Any]) -> bool:
    """
    Index a company for search.
    
    Args:
        company_data: Company data dictionary
        
    Returns:
        True if successful, False otherwise
    """
    return search_client.add_documents('companies', [company_data])


def index_peer_group(group_data: Dict[str, Any]) -> bool:
    """
    Index a peer group for search.
    
    Args:
        group_data: Peer group data dictionary
        
    Returns:
        True if successful, False otherwise
    """
    return search_client.add_documents('peer_groups', [group_data])


def search_jobs(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 20,
    offset: int = 0
) -> Optional[Dict[str, Any]]:
    """
    Search for jobs.
    
    Args:
        query: Search query
        filters: Filter criteria
        limit: Maximum results
        offset: Results offset
        
    Returns:
        Search results or None if failed
    """
    filter_str = None
    if filters:
        filter_parts = []
        for key, value in filters.items():
            if isinstance(value, list):
                filter_parts.append(f"{key} IN {value}")
            else:
                filter_parts.append(f"{key} = '{value}'")
        filter_str = ' AND '.join(filter_parts)
    
    return search_client.search('jobs', query, filter_str, limit, offset)


def search_companies(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 20,
    offset: int = 0
) -> Optional[Dict[str, Any]]:
    """
    Search for companies.
    
    Args:
        query: Search query
        filters: Filter criteria
        limit: Maximum results
        offset: Results offset
        
    Returns:
        Search results or None if failed
    """
    filter_str = None
    if filters:
        filter_parts = []
        for key, value in filters.items():
            if isinstance(value, list):
                filter_parts.append(f"{key} IN {value}")
            else:
                filter_parts.append(f"{key} = '{value}'")
        filter_str = ' AND '.join(filter_parts)
    
    return search_client.search('companies', query, filter_str, limit, offset)