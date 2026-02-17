# Stableman - Copilot Instructions 🐴

## Project Overview
Stableman is a Streamlit web application that provides horse blanketing instructions to stable hands based on weather conditions and established care guidelines. The app integrates with Weather APIs to deliver real-time, condition-specific blanketing recommendations. The project follows a minimal single-file architecture with straightforward deployment to Streamlit Cloud.

## Architecture & Structure
- **Single-file app**: All functionality is contained in `streamlit_app.py`
- **Weather Integration**: Connects to Weather APIs for real-time conditions
- **Decision Logic**: Implements horse blanketing guidelines based on weather data
- **Minimal dependencies**: Core requirements in `requirements.txt` (Streamlit + weather API client)
- **Virtual environment workflow**: Uses `.venv` for local development
- **Cloud-ready**: Configured for easy Streamlit Cloud deployment

## Development Workflow

### Local Development
```bash
# Setup (first time)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Daily development
source .venv/bin/activate
streamlit run streamlit_app.py
```

### Testing Changes
- Run locally at `http://localhost:8501` for immediate feedback
- Streamlit auto-reloads on file changes (hot reload)
- Use `st.rerun()` for programmatic page refreshes

## Streamlit Patterns Used

### Page Configuration
```python
st.set_page_config(page_title="Stableman", page_icon="🐴")
```
- Set at the very beginning of the app
- Defines browser tab title and favicon

### Component Examples in Codebase
- **Text Input**: `st.text_input()` with conditional display
- **Slider**: `st.slider()` with min/max/default values
- **Selectbox**: `st.selectbox()` with predefined options
- **Button with Animation**: `st.button()` triggers `st.balloons()`

### Layout Structure
1. Page config → Title → About section
2. Interactive components with immediate feedback
3. Divider → Footer info with external links

## Project-Specific Conventions
- **Emoji Usage**: Heavy use of emojis in titles and messages (🐴, 👋, 🎉, 💡)
- **Immediate Feedback**: All inputs show results immediately (no submit buttons)
- **Success Animations**: Use `st.balloons()` and `st.success()` for positive feedback
- **Information Display**: Use `st.info()` for helpful tips and external links

## Common Tasks

### Adding New Components
Add between existing components in `streamlit_app.py`, maintaining the pattern:
```python
# Component
result = st.component_name("label", parameters)
if result:
    st.write(f"Display: {result}")
```

### Deployment
- Push to GitHub → Deploy via [share.streamlit.io](https://share.streamlit.io)
- Main file path: `streamlit_app.py`
- Automatic dependency detection from `requirements.txt`

### Styling & UX
- Use `st.divider()` to separate sections
- Combine `st.header()` and `st.write()` for content sections
- Wrap helpful information in `st.info()` with markdown links

## Key Files
- [`streamlit_app.py`](streamlit_app.py) - Main application (single source of truth)
- [`requirements.txt`](requirements.txt) - Dependencies (keep minimal)
- [`README.md`](README.md) - Setup and deployment instructions

## External Dependencies
- **Streamlit**: Core framework, version pinned to >=1.30.0
- **Weather API**: External service integration for real-time weather data
- **Python**: Requires 3.8+ (specified in README)
- **Streamlit Cloud**: Deployment target (no additional config needed)