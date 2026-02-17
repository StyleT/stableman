# Stableman Blanketing Rules & Guidelines 🐴

> **⚠️ CRITICAL**: Keep this document synchronized with the actual implementation in `main_tab.py`. Any changes to blanketing logic, thresholds, or recommendations MUST be reflected here immediately.

## Core Principles

### Temperature Reference
- **Uses "FEELS LIKE" temperature** - accounts for wind chill and humidity
- **Forecast-aware decisions** - considers weather until next care phase
- **Anti-overheating priority** - horses tolerate brief cold better than overblanketing

### Care Phase System
- **🌅 Morning** (until 11:00 AM): Initial assessment and blanketing
- **☀️ Day** (11:00 AM - 3:50 PM): Midday monitoring and adjustments
- **🌙 Night** (3:50 PM - 11:00 AM next day): Overnight care period

## Blanketing Thresholds

### Horses OUT (Outdoor/Pasture)
| Feels Like Temperature | Category | Recommendation |
|----------------------|----------|----------------|
| **50°F and above** | None | No blanket needed |
| **40-49°F** | Light | Turnout sheet without neck piece |
| **30-39°F** | Medium | Fleece sheet + turnout sheet with neck piece |
| **Below 30°F** | Heavy | Weighted blanket with neck piece + turnout sheet without neck piece |

### Horses IN (Barn/Stall)
| Feels Like Temperature | Category | Recommendation |
|----------------------|----------|----------------|
| **45°F and above** | None | No blanket needed |
| **35-44°F** | Light | Turnout sheet without neck piece |
| **25-34°F** | Medium | Fleece sheet + turnout sheet with neck piece |
| **Below 25°F** | Heavy | Weighted blanket with neck piece + turnout sheet without neck piece |

### Donkey-Specific Rules
- **Light/Medium Blanket Categories**: No blanketing required
- **Heavy Blanket Category**: Weighted blanket only
- **All other conditions**: No blanketing required

## Decision Logic

### Forecast Integration
1. **Current Phase Timing**: Forecast analyzed until next care phase
   - Morning → Day phase (11:00 AM)
   - Day → Night phase (3:50 PM)  
   - Night → Morning phase (11:00 AM next day)

2. **Effective Temperature**: Uses minimum of current feels-like and forecast low

3. **Morning Options** (Special Case):
   - **Conservative**: Blanket until Night phase (accounts for full day)
   - **Normal**: Standard blanketing until Day phase only

### Anti-Overheating Logic
- **Temperature Drop ≥10°F**: Triggers smart blanketing alert
- **Current warm + Forecast cold**: Steps down one blanket category
- **Reasoning**: "Horses tolerate brief cold better than overblanketing"

### Category Step-Down Rules
- Heavy → Medium (when overheating risk detected)
- Medium → Light (when overheating risk detected)
- Light → unchanged (minimum safe level)

## Implementation Details

### Code Location
- **Primary Logic**: `main_tab.py` → `render_main_tab()` function
- **Thresholds**: Lines ~158-163 in `main_tab.py`
- **Recommendations**: `display_blanketing_recommendation()` function
- **Forecast Logic**: `get_next_phase_forecast()` function

### Key Variables
```python
# Horses OUT thresholds
thresholds = {'light': 50, 'medium': 40, 'heavy': 30}

# Horses IN thresholds  
thresholds = {'light': 45, 'medium': 35, 'heavy': 25}
```

### Temperature Calculation
```python
effective_temp = min(current_feels_like, min_forecast_feels_like)
```

## Care Instructions by Category

### ☀️ No Blanket Needed
- **Horses**: No blanketing required
- **Donkeys**: No blanketing required
- **OUT**: Ensure adequate shade and water
- **IN**: Ensure adequate ventilation in barn

### 🧸 Light Blanketing
- **Horses**: Turnout sheet without neck piece
- **Donkeys**: No blanketing required  
- **Care**: Monitor for comfort and proper fit

### 🧥 Medium Blanketing
- **Horses**: Fleece sheet + turnout sheet with neck piece over it
- **Donkeys**: No blanketing required
- **Care**: Check layering is secure and comfortable

### 🥶 Heavy Blanketing
- **Horses**: Weighted blanket with neck piece + turnout sheet without neck piece over it
- **Donkeys**: Weighted blanket
- **Care**: Check animals hourly for signs of cold stress
- **OUT**: Ensure adequate shelter and windbreak
- **IN**: Monitor closely even in barn environment

## Maintenance Requirements

### When to Update This Document
1. **Temperature threshold changes** in code
2. **New blanketing categories** added
3. **Care instruction modifications**
4. **Forecast logic changes**
5. **Phase timing adjustments**
6. **Animal-specific rule updates**

### Validation Checklist
- [ ] Thresholds match `main_tab.py` implementation
- [ ] Recommendations match `display_blanketing_recommendation()` function
- [ ] Phase timing matches `get_current_phase()` logic
- [ ] Forecast integration matches `get_next_phase_forecast()` behavior
- [ ] Anti-overheating logic documented correctly

---

**Last Updated**: February 16, 2026  
**Synchronized with**: `main_tab.py` implementation  
**Version**: 2.0 (Forecast-aware with Night phase)