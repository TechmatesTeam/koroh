"""
Tests for AI Chat functionality in Koroh Platform

This module contains comprehensive tests for AI chat models, services, and views,
including conversational flows, context management, and platform integration.
"""

import json
import uuid
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import ChatSession, ChatMessage, ChatContext
from .services import ChatService, PlatformIntegrationService
from .serializers import ChatSessionSerializer, ChatMessageSerializer

User = get_user_model()


class ChatModelTests(TestCase):
    """Test AI chat models."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_chat_session_creation(self):
        """Test creating a chat session."""
        session = ChatSession.objects.create(user=self.user)
        
        self.assertEqual(session.user, self.user)
        self.assertTrue(session.is_active)
        self.assertIsNotNone(session.id)
        self.assertIsInstance(session.id, uuid.UUID)
    
    def test_chat_session_string_representation(self):
        """Test chat session string representation."""
        session = ChatSession.objects.create(user=self.user)
        expected = f"Chat Session {session.id} - {self.user.email}"
        self.assertEqual(str(session), expected)
    
    def test_chat_message_creation(self):
        """Test creating chat messages."""
        session = ChatSession.objects.create(user=self.user)
        
        user_message = ChatMessage.objects.create(
            session=session,
            role='user',
            content='Hello AI'
        )
        
        ai_message = ChatMessage.objects.create(
            session=session,
            role='assistant',
            content='Hello! How can I help you?'
        )
        
        self.assertEqual(user_message.session, session)
        self.assertEqual(user_message.role, 'user')
        self.assertEqual(user_message.content, 'Hello AI')
        self.assertEqual(user_message.status, 'completed')
        
        self.assertEqual(ai_message.role, 'assistant')
        self.assertEqual(ai_message.content, 'Hello! How can I help you?')
    
    def test_chat_message_ordering(self):
        """Test chat messages are ordered by creation time."""
        session = ChatSession.objects.create(user=self.user)
        
        msg1 = ChatMessage.objects.create(
            session=session,
            role='user',
            content='First message'
        )
        
        msg2 = ChatMessage.objects.create(
            session=session,
            role='assistant',
            content='Second message'
        )
        
        messages = list(session.messages.all())
        self.assertEqual(messages[0], msg1)
        self.assertEqual(messages[1], msg2)
    
    def test_chat_context_creation(self):
        """Test creating chat context."""
        session = ChatSession.objects.create(user=self.user)
        
        context = ChatContext.objects.create(
            session=session,
            user_profile_data={'name': 'Test User'},
            conversation_summary='Discussion about career',
            active_features=['cv_upload', 'portfolio_generation']
        )
        
        self.assertEqual(context.session, session)
        self.assertEqual(context.user_profile_data['name'], 'Test User')
        self.assertEqual(context.conversation_summary, 'Discussion about career')
        self.assertIn('cv_upload', context.active_features)
    
    def test_session_auto_title_generation(self):
        """Test automatic title generation from first message."""
        session = ChatSession.objects.create(user=self.user)
        
        ChatMessage.objects.create(
            session=session,
            role='user',
            content='I need help with my career development and job search'
        )
        
        session.save()  # Trigger title generation
        session.refresh_from_db()
        
        self.assertEqual(session.title, 'I need help with my career development and job se...')


class ChatServiceTests(TestCase):
    """Test AI chat service functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.chat_service = ChatService()
    
    @patch('ai_chat.services.AIServiceFactory.create_conversational_service')
    def test_get_or_create_session_new(self, mock_ai_factory):
        """Test creating a new chat session."""
        mock_ai_service = Mock()
        mock_ai_factory.return_value = mock_ai_service
        
        session = self.chat_service.get_or_create_session(self.user)
        
        self.assertEqual(session.user, self.user)
        self.assertTrue(session.is_active)
        self.assertTrue(hasattr(session, 'context'))
    
    def test_get_or_create_session_existing(self):
        """Test retrieving an existing chat session."""
        existing_session = ChatSession.objects.create(user=self.user)
        
        session = self.chat_service.get_or_create_session(
            self.user, 
            str(existing_session.id)
        )
        
        self.assertEqual(session.id, existing_session.id)
    
    def test_get_or_create_session_invalid_id(self):
        """Test handling invalid session ID."""
        session = self.chat_service.get_or_create_session(
            self.user, 
            'invalid-session-id'
        )
        
        # Should create new session when invalid ID provided
        self.assertIsNotNone(session)
        self.assertEqual(session.user, self.user)
    
    @patch('ai_chat.services.AIServiceFactory.create_conversational_service')
    def test_send_message_success(self, mock_ai_factory):
        """Test successful message sending."""
        mock_ai_service = Mock()
        mock_ai_service.process.return_value = "I'm here to help with your career!"
        mock_ai_factory.return_value = mock_ai_service
        
        user_message, ai_message = self.chat_service.send_message(
            user=self.user,
            message="Hello, I need career advice"
        )
        
        self.assertEqual(user_message.role, 'user')
        self.assertEqual(user_message.content, "Hello, I need career advice")
        self.assertEqual(user_message.status, 'completed')
        
        self.assertEqual(ai_message.role, 'assistant')
        self.assertEqual(ai_message.content, "I'm here to help with your career!")
        self.assertEqual(ai_message.status, 'completed')
        
        # Verify they belong to the same session
        self.assertEqual(user_message.session, ai_message.session)
    
    @patch('ai_chat.services.AIServiceFactory.create_conversational_service')
    def test_send_message_with_context(self, mock_ai_factory):
        """Test sending message with additional context."""
        mock_ai_service = Mock()
        mock_ai_service.process.return_value = "Based on your profile, here are some suggestions..."
        mock_ai_factory.return_value = mock_ai_service
        
        additional_context = {
            'feature': 'cv_analysis',
            'user_skills': ['Python', 'Django', 'React']
        }
        
        user_message, ai_message = self.chat_service.send_message(
            user=self.user,
            message="Analyze my skills",
            additional_context=additional_context
        )
        
        self.assertEqual(ai_message.content, "Based on your profile, here are some suggestions...")
        
        # Verify context was updated
        context = ai_message.session.context
        self.assertEqual(context.context_data['feature'], 'cv_analysis')
    
    @patch('ai_chat.services.AIServiceFactory.create_conversational_service')
    def test_send_message_ai_error(self, mock_ai_factory):
        """Test handling AI service errors."""
        mock_ai_service = Mock()
        mock_ai_service.process.side_effect = Exception("AI service error")
        mock_ai_factory.return_value = mock_ai_service
        
        user_message, ai_message = self.chat_service.send_message(
            user=self.user,
            message="Hello"
        )
        
        self.assertEqual(user_message.status, 'completed')
        self.assertEqual(ai_message.status, 'failed')
        self.assertIn("technical difficulties", ai_message.content)
    
    def test_get_session_history(self):
        """Test retrieving session history."""
        session = ChatSession.objects.create(user=self.user)
        
        ChatMessage.objects.create(
            session=session,
            role='user',
            content='Hello'
        )
        
        ChatMessage.objects.create(
            session=session,
            role='assistant',
            content='Hi there!'
        )
        
        retrieved_session = self.chat_service.get_session_history(
            self.user, 
            str(session.id)
        )
        
        self.assertEqual(retrieved_session.id, session.id)
        self.assertEqual(retrieved_session.messages.count(), 2)
    
    def test_get_session_history_not_found(self):
        """Test retrieving non-existent session."""
        result = self.chat_service.get_session_history(
            self.user, 
            str(uuid.uuid4())
        )
        
        self.assertIsNone(result)
    
    def test_list_user_sessions(self):
        """Test listing user sessions."""
        # Create multiple sessions
        session1 = ChatSession.objects.create(user=self.user, title="Session 1")
        session2 = ChatSession.objects.create(user=self.user, title="Session 2")
        
        # Create session for different user
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )
        ChatSession.objects.create(user=other_user, title="Other Session")
        
        sessions = self.chat_service.list_user_sessions(self.user)
        
        self.assertEqual(len(sessions), 2)
        session_ids = [s.id for s in sessions]
        self.assertIn(session1.id, session_ids)
        self.assertIn(session2.id, session_ids)
    
    def test_delete_session(self):
        """Test deleting a session."""
        session = ChatSession.objects.create(user=self.user)
        session_id = str(session.id)
        
        result = self.chat_service.delete_session(self.user, session_id)
        
        self.assertTrue(result)
        
        # Verify session is deactivated, not deleted
        session.refresh_from_db()
        self.assertFalse(session.is_active)
    
    def test_delete_session_not_found(self):
        """Test deleting non-existent session."""
        result = self.chat_service.delete_session(
            self.user, 
            str(uuid.uuid4())
        )
        
        self.assertFalse(result)
    
    @patch('ai_chat.services.ChatService._detect_active_features')
    def test_context_management(self, mock_detect_features):
        """Test conversation context management."""
        mock_detect_features.return_value = ['cv_upload', 'job_search']
        
        session = ChatSession.objects.create(user=self.user)
        
        # Create initial context
        context = ChatContext.objects.create(
            session=session,
            user_profile_data={'name': 'Test User'},
            active_features=['portfolio_generation']
        )
        
        # Update context
        self.chat_service._update_session_context(
            session=session,
            user_message="I want to upload my CV and find jobs",
            ai_response="I can help you with both!",
            additional_context={'feature_request': 'cv_upload'}
        )
        
        context.refresh_from_db()
        
        # Verify features were merged
        self.assertIn('cv_upload', context.active_features)
        self.assertIn('job_search', context.active_features)
        self.assertIn('portfolio_generation', context.active_features)
        
        # Verify additional context was stored
        self.assertEqual(context.context_data['feature_request'], 'cv_upload')


class PlatformIntegrationServiceTests(TestCase):
    """Test platform integration service."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.integration_service = PlatformIntegrationService()
    
    def test_cv_analysis_no_cv(self):
        """Test CV analysis request when no CV uploaded."""
        # Create profile without CV
        from profiles.models import Profile
        Profile.objects.create(user=self.user)
        
        result = self.integration_service.handle_cv_analysis_request(
            self.user, 
            'session-id'
        )
        
        self.assertFalse(result['success'])
        self.assertIn("haven't uploaded a CV", result['message'])
    
    @patch('ai_chat.services.analyze_cv_file')
    def test_cv_analysis_success(self, mock_analyze_cv):
        """Test successful CV analysis."""
        from profiles.models import Profile
        
        # Mock CV analysis result
        mock_result = Mock()
        mock_result.skills = ['Python', 'Django', 'React', 'JavaScript', 'SQL']
        mock_result.work_experience = [{'title': 'Developer', 'years': 2}]
        mock_result.education = [{'degree': 'BS Computer Science'}]
        mock_analyze_cv.return_value = mock_result
        
        # Create profile with CV
        profile = Profile.objects.create(user=self.user)
        profile.cv_file = 'test_cv.pdf'
        profile.save()
        
        result = self.integration_service.handle_cv_analysis_request(
            self.user, 
            'session-id'
        )
        
        self.assertTrue(result['success'])
        self.assertIn("analyzed your CV", result['message'])
        self.assertEqual(result['data']['skills_count'], 5)
        self.assertEqual(result['data']['experience_years'], 1)
        self.assertEqual(result['data']['education_count'], 1)
    
    def test_portfolio_generation_no_cv(self):
        """Test portfolio generation request when no CV uploaded."""
        from profiles.models import Profile
        Profile.objects.create(user=self.user)
        
        result = self.integration_service.handle_portfolio_generation_request(
            self.user, 
            'session-id'
        )
        
        self.assertFalse(result['success'])
        self.assertIn("need your CV first", result['message'])
    
    def test_portfolio_generation_existing_portfolio(self):
        """Test portfolio generation when portfolio already exists."""
        from profiles.models import Profile
        
        profile = Profile.objects.create(user=self.user)
        profile.cv_file = 'test_cv.pdf'
        profile.portfolio_url = 'https://example.com/portfolio'
        profile.save()
        
        result = self.integration_service.handle_portfolio_generation_request(
            self.user, 
            'session-id'
        )
        
        self.assertTrue(result['success'])
        self.assertIn("already have a portfolio", result['message'])
        self.assertIn("https://example.com/portfolio", result['message'])
    
    def test_portfolio_generation_ready(self):
        """Test portfolio generation when ready to generate."""
        from profiles.models import Profile
        
        profile = Profile.objects.create(user=self.user)
        profile.cv_file = 'test_cv.pdf'
        profile.save()
        
        result = self.integration_service.handle_portfolio_generation_request(
            self.user, 
            'session-id'
        )
        
        self.assertTrue(result['success'])
        self.assertIn("generate a professional portfolio", result['message'])
        self.assertEqual(result['action_required'], 'portfolio_template_selection')
    
    @patch('ai_chat.services.get_personalized_job_recommendations')
    def test_job_recommendations_success(self, mock_get_recommendations):
        """Test successful job recommendations."""
        from jobs.models import Job, Company
        
        # Create mock job recommendations
        company = Company.objects.create(
            name='Tech Corp',
            description='A tech company',
            industry='Technology',
            size='100-500',
            location='San Francisco, CA',
            website='https://techcorp.com'
        )
        
        job = Job.objects.create(
            title='Software Engineer',
            company=company,
            description='Great opportunity',
            location='San Francisco, CA',
            salary_range='$80k-$120k',
            job_type='full-time'
        )
        job.match_score = 92
        
        mock_get_recommendations.return_value = [job]
        
        result = self.integration_service.handle_job_recommendations_request(
            self.user, 
            'session-id'
        )
        
        self.assertTrue(result['success'])
        self.assertIn("1 great job opportunities", result['message'])
        self.assertEqual(len(result['data']['recommendations']), 1)
        self.assertEqual(result['data']['recommendations'][0]['title'], 'Software Engineer')
        self.assertEqual(result['data']['recommendations'][0]['match_score'], 92)
    
    @patch('ai_chat.services.get_personalized_job_recommendations')
    def test_job_recommendations_empty(self, mock_get_recommendations):
        """Test job recommendations when no jobs found."""
        mock_get_recommendations.return_value = []
        
        result = self.integration_service.handle_job_recommendations_request(
            self.user, 
            'session-id'
        )
        
        self.assertTrue(result['success'])
        self.assertIn("don't have any specific job recommendations", result['message'])


class ChatAPITests(APITestCase):
    """Test AI chat API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create JWT token for authentication
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_list_sessions_empty(self):
        """Test listing sessions when none exist."""
        url = reverse('ai_chat:session-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(len(response.data['sessions']), 0)
    
    def test_list_sessions_with_data(self):
        """Test listing sessions with existing data."""
        # Create test sessions
        session1 = ChatSession.objects.create(user=self.user, title="Session 1")
        session2 = ChatSession.objects.create(user=self.user, title="Session 2")
        
        # Add messages to sessions
        ChatMessage.objects.create(
            session=session1,
            role='user',
            content='Hello'
        )
        
        url = reverse('ai_chat:session-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['sessions']), 2)
    
    def test_create_session(self):
        """Test creating a new session."""
        url = reverse('ai_chat:session-list')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['is_active'], True)
        
        # Verify session was created in database
        session_id = response.data['id']
        session = ChatSession.objects.get(id=session_id)
        self.assertEqual(session.user, self.user)
    
    def test_get_session_detail(self):
        """Test retrieving session details."""
        session = ChatSession.objects.create(user=self.user, title="Test Session")
        
        # Add messages
        ChatMessage.objects.create(
            session=session,
            role='user',
            content='Hello'
        )
        ChatMessage.objects.create(
            session=session,
            role='assistant',
            content='Hi there!'
        )
        
        url = reverse('ai_chat:session-detail', kwargs={'session_id': session.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(session.id))
        self.assertEqual(response.data['title'], "Test Session")
        self.assertEqual(len(response.data['messages']), 2)
    
    def test_get_session_detail_not_found(self):
        """Test retrieving non-existent session."""
        url = reverse('ai_chat:session-detail', kwargs={'session_id': uuid.uuid4()})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_session_title(self):
        """Test updating session title."""
        session = ChatSession.objects.create(user=self.user, title="Old Title")
        
        url = reverse('ai_chat:session-detail', kwargs={'session_id': session.id})
        data = {'title': 'New Title'}
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'New Title')
        
        # Verify in database
        session.refresh_from_db()
        self.assertEqual(session.title, 'New Title')
    
    def test_delete_session(self):
        """Test deleting a session."""
        session = ChatSession.objects.create(user=self.user)
        
        url = reverse('ai_chat:session-detail', kwargs={'session_id': session.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify session is deactivated
        session.refresh_from_db()
        self.assertFalse(session.is_active)
    
    @patch('ai_chat.services.ChatService.send_message')
    def test_send_message(self, mock_send_message):
        """Test sending a message."""
        # Mock service response
        user_message = Mock()
        user_message.session.id = uuid.uuid4()
        ai_message = Mock()
        
        mock_send_message.return_value = (user_message, ai_message)
        
        url = reverse('ai_chat:send-message')
        data = {
            'message': 'Hello AI',
            'session_id': str(uuid.uuid4())
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('session_id', response.data)
        self.assertIn('user_message', response.data)
        self.assertIn('ai_response', response.data)
        
        # Verify service was called correctly
        mock_send_message.assert_called_once_with(
            user=self.user,
            message='Hello AI',
            session_id=data['session_id'],
            additional_context={}
        )
    
    def test_send_message_invalid_data(self):
        """Test sending message with invalid data."""
        url = reverse('ai_chat:send-message')
        data = {}  # Missing required 'message' field
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('ai_chat.services.ChatService.send_message')
    def test_quick_chat(self, mock_send_message):
        """Test quick chat endpoint."""
        # Mock service response
        user_message = Mock()
        user_message.session.id = uuid.uuid4()
        ai_message = Mock()
        ai_message.content = "Quick response"
        
        mock_send_message.return_value = (user_message, ai_message)
        
        url = reverse('ai_chat:quick-chat')
        data = {'message': 'Quick question'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Quick question')
        self.assertEqual(response.data['response'], 'Quick response')
        self.assertIn('session_id', response.data)
    
    @patch('ai_chat.services.PlatformIntegrationService.handle_cv_analysis_request')
    @patch('ai_chat.services.ChatService.send_message')
    def test_analyze_cv_chat(self, mock_send_message, mock_cv_analysis):
        """Test CV analysis chat endpoint."""
        # Mock integration service response
        mock_cv_analysis.return_value = {
            'success': True,
            'message': 'CV analyzed successfully',
            'data': {'skills_count': 10}
        }
        
        # Mock chat service response
        user_message = Mock()
        user_message.session.id = uuid.uuid4()
        ai_message = Mock()
        
        mock_send_message.return_value = (user_message, ai_message)
        
        url = reverse('ai_chat:analyze-cv')
        data = {'session_id': str(uuid.uuid4())}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('analysis_result', response.data)
        self.assertIn('ai_response', response.data)
        self.assertTrue(response.data['analysis_result']['success'])
    
    def test_unauthorized_access(self):
        """Test API access without authentication."""
        self.client.credentials()  # Remove authentication
        
        url = reverse('ai_chat:session-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ChatSerializerTests(TestCase):
    """Test AI chat serializers."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_chat_session_serializer(self):
        """Test ChatSessionSerializer."""
        session = ChatSession.objects.create(user=self.user, title="Test Session")
        
        # Add messages
        ChatMessage.objects.create(
            session=session,
            role='user',
            content='Hello'
        )
        ChatMessage.objects.create(
            session=session,
            role='assistant',
            content='Hi there!'
        )
        
        serializer = ChatSessionSerializer(session)
        data = serializer.data
        
        self.assertEqual(data['title'], "Test Session")
        self.assertEqual(data['is_active'], True)
        self.assertEqual(len(data['messages']), 2)
        self.assertEqual(data['message_count'], 2)
    
    def test_chat_message_serializer(self):
        """Test ChatMessageSerializer."""
        session = ChatSession.objects.create(user=self.user)
        message = ChatMessage.objects.create(
            session=session,
            role='user',
            content='Test message',
            metadata={'test': 'data'}
        )
        
        serializer = ChatMessageSerializer(message)
        data = serializer.data
        
        self.assertEqual(data['role'], 'user')
        self.assertEqual(data['content'], 'Test message')
        self.assertEqual(data['status'], 'completed')
        self.assertEqual(data['metadata']['test'], 'data')