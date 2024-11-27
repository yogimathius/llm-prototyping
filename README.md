# LLM Prototyping API

A Django-based API for prototyping LLM interactions with different AI roles and personalities.

## Prerequisites

- Python 3.12+
- Access to GitHub Models (for GITHUB_TOKEN)
- PostgreSQL (optional - SQLite is default)

## Related Projects

- [Frontend Repository](https://github.com/yogimathius/frontend) - React/Remix frontend for this API

## Setup Instructions

1. Clone the repository:

```bash
git clone
cd llm-prototyping
```

2. Create and activate virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create `.env` file in project root:

```env
OPENAI_API_KEY=your_openai_api_key
GITHUB_TOKEN=your_github_token
```

5. Run database migrations:

```bash
python manage.py migrate
```

6. Initialize LLM roles and users:

Run the initialization script:

```bash
python manage.py initialize_roles
```

Create a mock user:

```bash
python manage.py initialize_mock_user
```

7. Start the development server:

```bash
python manage.py runserver
```

## API Endpoints

### Ask Role

- **URL**: `/ai/ask-role/`
- **Method**: `POST`
- **Body**:

```json
{
  "prompt": "What does it mean when I dream of flying?",
  "role": "Dream Interpreter"
}
```

- **Success Response**:

```json
{
  "response": "Dreams of flying often symbolize...",
  "role": "Dream Interpreter"
}
```

- **Error Response**:

```json
{
  "error": "Missing prompt or role"
}
```

### List Roles

- **URL**: `/ai/roles/`
- **Method**: `GET`
- **Success Response**:

```json
[
  {
    "name": "Dream Interpreter",
    "description": "I interpret dreams using various psychological and cultural perspectives."
  },
  {
    "name": "Consciousness Explorer",
    "description": "I explore consciousness and its various states and phenomena."
  }
]
```

## Frontend Integration

1. Clone the frontend repository:

```bash
git clone git@github.com:yogimathius/frontend.git
cd frontend
npm install
npm run dev
```

2. Ensure the API is running on `http://localhost:8000` (default Django development server)

## Development

- The API uses Django's built-in development server
- SQLite database is used by default
- CORS is enabled for localhost frontend development
- Debug mode is enabled by default

## Security Notes

- Never commit `.env` file or sensitive credentials
- The GITHUB_TOKEN should have minimal required permissions
- In production, update CORS settings and security configurations

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

# AI Dialogue Project

A Django/React application that facilitates dynamic conversations between different AI personas using OpenAI and Ollama.

## Next Steps

### 1. Randomize Full Dialogue Order

- [ ] Add randomization to role selection in DialogueGenerator
- [ ] Create method to shuffle roles while maintaining context
- [ ] Add option to specify "first speaker" roles
- [ ] Consider weighted randomization based on role relevance

### 2. Enhance Ollama Integration

- [ ] Add Ollama controls to frontend
  - [ ] Toggle for Ollama/OpenAI
  - [ ] Model selection dropdown
  - [ ] Streaming controls
- [ ] Implement streaming response handler
  - [ ] Add loading states for stream chunks
  - [ ] Show real-time token generation
  - [ ] Add stop/cancel functionality
- [ ] Model management
  - [ ] List available Ollama models
  - [ ] Show model status/availability
  - [ ] Model performance metrics

### 3. Context Enhancement with History

- [ ] Create conversation memory system
  - [ ] Define memory structure
  - [ ] Set memory limits
  - [ ] Implement cleanup strategies
- [ ] Add history retrieval features
  - [ ] Filter by role/topic
  - [ ] Search functionality
  - [ ] Relevance scoring
- [ ] Implement context injection
  - [ ] Add relevant history to prompts
  - [ ] Allow manual history selection
  - [ ] Create context window management

### Future Considerations

1. **Performance Optimization**

   - [ ] Caching frequently used contexts
   - [ ] Batch processing for history analysis
   - [ ] Efficient memory management

2. **User Experience**

   - [ ] Visual feedback during streaming
   - [ ] Progress indicators
   - [ ] Response quality metrics

3. **Advanced Features**
   - [ ] Role relationship mapping
   - [ ] Dynamic context weighting
   - [ ] Conversation branching

### Testing Strategy

- [ ] Unit tests for randomization
- [ ] Integration tests for streaming
- [ ] Performance tests for history retrieval
- [ ] End-to-end tests for full dialogue flow

### Documentation Needs

- [ ] API documentation updates
- [ ] Streaming implementation guide
- [ ] History integration examples
- [ ] Configuration options
