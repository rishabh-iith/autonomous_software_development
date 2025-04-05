# Flight Tracking System - Task Automation

A Python-based automation tool that streamlines the software development workflow by automatically generating subtasks, creating Jira tickets, and producing test cases using Google's Gemini AI.

## Overview

This system automates the process of breaking down high-level software development tasks into manageable subtasks and test cases. It uses the Gemini AI API to intelligently analyze requirements and generate appropriate subtasks, then automatically creates and links these in Jira. The system also generates comprehensive test cases for each subtask.

## Features

- **Task Decomposition**: Analyzes a high-level requirement and breaks it down into 3-5 distinct, non-overlapping subtasks
- **Jira Integration**: Automatically creates linked Jira tickets for the main task and subtasks
- **Test Case Generation**: Creates 3-5 detailed test cases for each subtask
- **API Resilience**: Implements key rotation and retry mechanisms to handle rate limiting
- **Rich Metadata**: Categorizes tasks and suggests component names for better organization

## How It Works

1. **Input Collection**: The user enters a high-level task requirement
2. **Parent Ticket Creation**: Creates a parent Jira ticket for the main requirement
3. **Subtask Generation**: Uses Gemini API to analyze the requirement and generate 3-5 distinct subtasks
4. **Jira Ticket Creation**: Creates Jira tickets for each subtask and links them to the parent ticket
5. **Test Case Generation**: Generates test cases for each subtask and creates them as linked subtasks in Jira
6. **Verification**: Displays all created tickets to confirm successful creation

## Code Structure

- **Configuration Section**: Contains Jira API credentials and Gemini API keys
- **Gemini API Functions**: Handles communication with Gemini, including key rotation and fallback logic
- **Jira API Functions**: Manages ticket creation and retrieval operations
- **Task Generation Functions**: Uses AI to generate structured development tasks
- **Jira Linking Functions**: Creates relationships between tasks and subtasks
- **Test Case Generation**: Creates detailed test cases for each task

## Requirements

- Python 3.6+
- Jira account with API access
- Google Gemini API key(s)
- Required Python packages:
  - requests
  - google.generativeai
  - json
  - time

## Setup

1. Clone this repository
2. Install required dependencies:
   ```
   pip install requests google-generativeai
   ```
3. Configure your credentials in the configuration section:
   - Set your Jira email, API token, and base URL
   - Add your Gemini API key(s)
   - Set your Jira project key

## Usage

Run the script and follow the prompts:

```
python flight_tracking_system.py
```

When prompted, enter your main task requirement. The system will handle the rest, generating tasks, creating Jira tickets, and generating test cases.

## Security Notes

- The code contains API keys and credentials - consider using environment variables or a secure credential manager instead of hardcoding sensitive information
- Rotating between multiple API keys helps prevent rate limiting issues with the Gemini API

## Future Enhancements

- Add support for custom fields in Jira tickets
- Implement webhook integration for real-time updates
- Add a GUI interface for easier interaction
- Include estimation capabilities for generated tasks
- Add support for additional AI providers beyond Gemini

## License

[Insert your license information here]

## Contributors

[Your name and contact information]
