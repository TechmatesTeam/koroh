# Portfolio URL Structure Changes

## Overview
Updated the portfolio generator to use the current host (localhost for development) and implement the proper URL structure with `https://hostname/@username/portfolio-name`.

## Changes Made

### 1. Mock API Updates (`web/lib/mock-api.ts`)
- **Enhanced `generatePortfolio()` method** to accept `portfolioName` and `template` parameters
- **Dynamic host detection** - uses `window.location.host` for current domain
- **Protocol selection** - uses `http` for localhost, `https` for production domains
- **Username generation** - extracts username from email (before @ symbol) or uses first+last name
- **URL structure** - implements `protocol://host/@username/portfolio-name` format
- **Auto-generated portfolio names** - creates default name if none provided

### 2. API Interface Updates (`web/lib/api.ts`)
- Updated `generatePortfolio()` to accept optional parameters for template and portfolio name
- Maintains backward compatibility with existing calls

### 3. Portfolio Generator Component (`web/components/portfolio/portfolio-generator.tsx`)
- **Added portfolio name field** in template selection step
- **URL sanitization** - automatically converts portfolio names to URL-safe format (lowercase, hyphens only)
- **Real-time URL preview** - shows the actual URL structure as user types
- **Enhanced preview section** - displays username and portfolio name separately
- **Improved error handling** and user feedback

### 4. New Portfolio URL Preview Component (`web/components/portfolio/portfolio-url-preview.tsx`)
- **Interactive URL builder** with real-time preview
- **Visual URL breakdown** - color-coded components (host, username, portfolio name)
- **Copy and preview functionality**
- **Educational tooltips** explaining URL structure
- **Automatic sanitization** of portfolio names

### 5. Portfolio Viewer Page (`web/app/@[username]/[portfolioName]/page.tsx`)
- **Dynamic route handler** for the new URL structure
- **Portfolio loading** from localStorage (mock implementation)
- **Responsive design** with proper styling based on portfolio customizations
- **Sharing and export functionality**
- **Error handling** for non-existent portfolios

### 6. Comprehensive Testing (`web/__tests__/components/portfolio/portfolio-url-generation.test.tsx`)
- **URL generation validation** for different scenarios
- **Host detection testing** (localhost vs production)
- **Username extraction testing** from various email formats
- **Portfolio name sanitization testing**
- **Data persistence testing**

## URL Structure Examples

### Development (localhost)
```
http://localhost:3000/@john.doe/my-awesome-portfolio
http://localhost:3004/@jane.smith/professional-portfolio
```

### Production
```
https://koroh.com/@john.doe/my-awesome-portfolio
https://app.koroh.com/@jane.smith/professional-portfolio
```

## URL Components

1. **Protocol**: `http` for localhost, `https` for production
2. **Host**: Current domain (e.g., `localhost:3000`, `koroh.com`)
3. **Username**: Extracted from user's email or generated from name (prefixed with `@`)
4. **Portfolio Name**: User-defined or auto-generated, URL-safe format

## Features

### Automatic URL Sanitization
- Converts to lowercase
- Replaces special characters with hyphens
- Removes consecutive hyphens
- Trims leading/trailing hyphens

### Real-time Preview
- Shows URL as user types
- Color-coded components for clarity
- Copy to clipboard functionality
- Direct preview link

### Responsive Design
- Works on all screen sizes
- Mobile-friendly input and preview
- Accessible keyboard navigation

### Error Handling
- Graceful fallbacks for missing data
- User-friendly error messages
- Validation feedback

## Testing Coverage

✅ URL generation with localhost  
✅ URL generation with production domains  
✅ Username extraction from email  
✅ Auto-generated portfolio names  
✅ Special character handling  
✅ Data persistence  
✅ Portfolio retrieval  

## Next Steps

1. **Backend Integration**: Replace mock API with real backend endpoints
2. **User Authentication**: Integrate with actual user authentication system
3. **Portfolio Templates**: Add more sophisticated template rendering
4. **Custom Domains**: Support for custom domain mapping
5. **Analytics**: Track portfolio views and engagement
6. **SEO Optimization**: Add meta tags and structured data for better search visibility

## Migration Notes

- Existing portfolios will need URL migration to new structure
- Old URLs should redirect to new format for backward compatibility
- Consider implementing URL aliases for branded portfolio names