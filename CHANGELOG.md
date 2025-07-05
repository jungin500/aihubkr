# Changelog

All notable changes to AIHubKR will be documented in this file.

## [0.2.0] - 2025/07/06

### Added
- **API Key Authentication**: Replaced username/password authentication with API key system
- **Environment Variable Support**: Support for `AIHUB_APIKEY` environment variable
- **Modern CLI Interface**: New subcommand-based interface with `list`, `files`, `download`, `help`
- **Automatic Credential Saving**: API keys are automatically saved after first use
- **Updated API Endpoints**: Support for new AIHub API endpoints
- **Migration Guide**: Comprehensive guide for users upgrading from v1.x
- **Enhanced Error Handling**: Better error messages and validation

### Changed
- **Authentication Flow**: No more login/logout required - just provide API key
- **CLI Commands**: 
  - `login` → API key validation
  - `logout` → Removed (no longer needed)
  - `download` → `download` (modern subcommand)
  - `list` → `list` (modern subcommand)
  - Added `files` and `help` subcommands
- **Download Behavior**: Downloads now go to current directory by default
- **API Endpoints**: Updated to match new AIHub API structure
- **GUI Interface**: Updated to use API key input instead of username/password

### Removed
- **Username/Password Authentication**: Completely removed old auth system
- **Login/Logout Commands**: No longer needed with API key system
- **Session Management**: Replaced with stateless API key validation
- **Output Directory Parameter**: Downloads now use current directory
- **Complex Authentication Flow**: Simplified to single API key validation
- **Legacy CLI Modes**: Removed old `d`, `l`, `-help` modes

### Fixed
- **API Compatibility**: Fixed compatibility with new AIHub API
- **Error Handling**: Improved error messages for authentication failures
- **File Download**: Updated to use new download endpoint structure
- **File Merging**: Improved part file merging process
- **Progress Tracking**: Better download progress indication

### Technical Changes
- **Core Authentication Module**: Complete rewrite of `auth.py`
- **Downloader Module**: Updated endpoints and authentication headers
- **CLI Main Module**: Refactored to use modern subcommand interface
- **GUI Main Module**: Updated authentication UI and validation
- **Configuration**: Updated to store API keys instead of credentials

### Breaking Changes
- **Authentication**: Must use API key instead of username/password
- **CLI Interface**: Command structure completely changed to modern subcommands
- **Configuration**: Old credentials will not work with new version
- **API Endpoints**: All API calls now use different endpoints

### Migration Notes
- Users must obtain API key from AIHub website
- Old credentials will be ignored
- CLI commands have changed significantly to modern subcommand format
- GUI authentication flow is different
- See `MIGRATION_GUIDE.md` for detailed migration instructions

## [0.1.x] - Previous Versions

### Features (Deprecated)
- Username/password authentication
- Login/logout functionality
- Session-based authentication
- Complex CLI interface with multiple modes
- Output directory specification

### Note
Version 0.1.x is deprecated and no longer supported. All users should upgrade to version 0.2.0 or later. 