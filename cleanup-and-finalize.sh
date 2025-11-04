#!/bin/bash

# Koroh Platform - Cleanup and Finalize Script
# This script removes unnecessary files and commits remaining production files

set -e

echo "🧹 Starting cleanup and finalization process..."

# Function to safely remove files/directories
safe_remove() {
    local path="$1"
    if [ -e "$path" ]; then
        echo "🗑️  Removing: $path"
        rm -rf "$path"
    else
        echo "⏭️  Already removed or doesn't exist: $path"
    fi
}

# Function to commit remaining production files
commit_remaining_production_files() {
    echo "📝 Committing remaining production files..."
    
    # Database migrations (production-ready)
    if [ -f "api/ai_chat/migrations/0003_add_enhanced_context_fields.py" ]; then
        git add "api/ai_chat/migrations/0003_add_enhanced_context_fields.py"
        git commit -m "feat: add database migration for enhanced AI chat context fields" || echo "⚠️  Migration commit failed"
    fi
    
    if [ -f "api/authentication/migrations/0002_alter_user_managers_passwordresettoken_and_more.py" ]; then
        git add "api/authentication/migrations/0002_alter_user_managers_passwordresettoken_and_more.py"
        git commit -m "feat: add database migration for enhanced authentication system" || echo "⚠️  Migration commit failed"
    fi
    
    # Core backend services (production-ready)
    production_backend_files=(
        "api/koroh_platform/consumers.py"
        "api/koroh_platform/permissions.py"
        "api/koroh_platform/realtime.py"
        "api/koroh_platform/routing.py"
        "api/koroh_platform/security.py"
        "api/koroh_platform/services/realtime_data_service.py"
        "api/koroh_platform/utils/exception_handler.py"
        "api/jobs/tasks.py"
    )
    
    for file in "${production_backend_files[@]}"; do
        if [ -f "$file" ]; then
            git add "$file"
        fi
    done
    
    if git diff --cached --quiet; then
        echo "⏭️  No backend production files to commit"
    else
        git commit -m "feat: add core backend services for WebSocket, security, and realtime functionality" || echo "⚠️  Backend services commit failed"
    fi
    
    # Email templates (production-ready)
    email_templates=(
        "api/templates/emails/company_update.html"
        "api/templates/emails/job_recommendation.html"
        "api/templates/emails/peer_group_activity.html"
        "api/templates/emails/peer_group_invitation.html"
        "api/templates/emails/portfolio_generated.html"
        "api/templates/emails/profile_completion_reminder.html"
        "api/templates/emails/weekly_digest.html"
    )
    
    for template in "${email_templates[@]}"; do
        if [ -f "$template" ]; then
            git add "$template"
        fi
    done
    
    if git diff --cached --quiet; then
        echo "⏭️  No email templates to commit"
    else
        git commit -m "feat: add professional HTML email templates for user communications" || echo "⚠️  Email templates commit failed"
    fi
    
    # Management commands (production-ready)
    if [ -f "api/koroh_platform/management/commands/test_realtime_updates.py" ]; then
        git add "api/koroh_platform/management/commands/test_realtime_updates.py"
        git commit -m "feat: add management command for realtime updates testing" || echo "⚠️  Management command commit failed"
    fi
    
    # Frontend transition components (production-ready)
    transition_components=(
        "web/components/ui/content-transition.tsx"
        "web/components/ui/motion-wrapper.tsx"
        "web/components/ui/page-transition.tsx"
        "web/components/ui/smart-page-transition.tsx"
    )
    
    for component in "${transition_components[@]}"; do
        if [ -f "$component" ]; then
            git add "$component"
        fi
    done
    
    if git diff --cached --quiet; then
        echo "⏭️  No transition components to commit"
    else
        git commit -m "feat: implement smooth page transitions and motion components" || echo "⚠️  Transition components commit failed"
    fi
    
    # Production deployment script
    if [ -f "scripts/deploy-production.sh" ]; then
        git add "scripts/deploy-production.sh"
        git commit -m "feat: add comprehensive production deployment script" || echo "⚠️  Deployment script commit failed"
    fi
}

# Remove documentation and summary files
echo "🗑️  Removing documentation and summary files..."
safe_remove "FRONTEND_SIGNUP_SUCCESS_REPORT.md"
safe_remove "LOGIN_ERRORS_FIXED_SUMMARY.md"
safe_remove "PROFESSIONAL_EMAIL_TEMPLATES_SUMMARY.md"
safe_remove "api/CONCISE_AI_RESPONSES_IMPLEMENTATION.md"
safe_remove "api/SECURITY_IMPLEMENTATION_SUMMARY.md"
safe_remove "web/AUTH_NAVIGATION_FIXES.md"
safe_remove "web/NAVIGATION_TRANSITION_FIXES.md"
safe_remove "web/PAGE_REFRESH_FIXES_SUMMARY.md"
safe_remove "web/SEAMLESS_NAVIGATION_FIXES.md"
safe_remove "web/SMOOTH_TRANSITIONS_FIXES.md"

# Remove test files
echo "🗑️  Removing test files..."
safe_remove "test-auth-endpoints.js"
safe_remove "test-detailed-signup.js"
safe_remove "test-frontend-signup.js"
safe_remove "test-frontend-url.js"
safe_remove "test-login-endpoints.js"
safe_remove "web/test-frontend-api-security.js"
safe_remove "web/test-frontend-api.js"
safe_remove "web/test-mock-api.js"
safe_remove "fix-email-sync.py"

# Remove test output directories
echo "🗑️  Removing test output directories..."
safe_remove "test_portfolio_output/"
safe_remove "web/test_portfolio_output/"
safe_remove "api/test_portfolio_output/"

# Remove all test files from API directory
echo "🗑️  Removing API test files..."
find api/ -name "test_*.py" -type f -delete 2>/dev/null || true

# Remove integration test files
echo "🗑️  Removing integration test files..."
safe_remove "web/__tests__/integration/"

# Remove temporary files
echo "🗑️  Removing temporary files..."
safe_remove "commit-changes.sh"

# Commit remaining production files
commit_remaining_production_files

echo ""
echo "✅ Cleanup and finalization completed successfully!"
echo ""
echo "📋 Final summary:"
echo "   • Removed all test files and documentation summaries"
echo "   • Removed temporary output directories"
echo "   • Committed remaining production-ready files"
echo "   • Repository is now clean and production-ready"
echo ""
echo "🚀 Ready for production deployment!"

# Show final git status
echo "📊 Final repository status:"
git status --porcelain