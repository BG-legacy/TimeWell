import pytest
from pydantic import ValidationError
from app.schemas.habit import HabitCreate

def test_valid_habit_creation():
    """Test creation of valid habits for different frequencies."""
    # Daily habit
    daily_habit = HabitCreate(
        title="Morning Meditation",
        description="10 minutes of mindfulness meditation",
        frequency="daily",
        color="#4287f5",
        icon="meditation"
    )
    assert daily_habit.frequency == "daily"
    assert daily_habit.title == "Morning Meditation"
    
    # Weekly habit
    weekly_habit = HabitCreate(
        title="Weekend Jogging",
        description="30 minutes jogging",
        frequency="weekly",
        target_days=[5, 6],  # Saturday and Sunday
        color="#ff5733",
        icon="running"
    )
    assert weekly_habit.frequency == "weekly"
    assert weekly_habit.target_days == [5, 6]
    
    # Monthly habit
    monthly_habit = HabitCreate(
        title="Budget Review",
        description="Review monthly budget",
        frequency="monthly",
        target_days=[1],  # First day of month
        color="#33ff57",
        icon="money"
    )
    assert monthly_habit.frequency == "monthly"
    assert monthly_habit.target_days == [1]

def test_frequency_validation():
    """Test that frequency must be one of the allowed values."""
    with pytest.raises(ValidationError) as excinfo:
        HabitCreate(
            title="Invalid Frequency",
            frequency="annually"  # Not allowed
        )
    
    assert "frequency" in str(excinfo.value)
    assert "annually" in str(excinfo.value)

def test_target_days_validation_for_daily():
    """Test that daily habits should not have target days."""
    with pytest.raises(ValidationError) as excinfo:
        HabitCreate(
            title="Invalid Daily Habit",
            frequency="daily",
            target_days=[1, 2, 3]  # Not allowed for daily habits
        )
    
    assert "target_days" in str(excinfo.value)
    assert "Daily habits" in str(excinfo.value)

def test_target_days_validation_for_weekly():
    """Test that weekly habits have valid day numbers (0-6)."""
    with pytest.raises(ValidationError) as excinfo:
        HabitCreate(
            title="Invalid Weekly Habit",
            frequency="weekly",
            target_days=[0, 7]  # 7 is not valid (should be 0-6)
        )
    
    assert "target_days" in str(excinfo.value)
    assert "0 (Monday) and 6 (Sunday)" in str(excinfo.value)

def test_target_days_validation_for_monthly():
    """Test that monthly habits have valid day numbers (1-31)."""
    with pytest.raises(ValidationError) as excinfo:
        HabitCreate(
            title="Invalid Monthly Habit",
            frequency="monthly",
            target_days=[0, 15]  # 0 is not valid (should be 1-31)
        )
    
    assert "target_days" in str(excinfo.value)
    assert "between 1 and 31" in str(excinfo.value)

def test_color_validation():
    """Test color validation for habits."""
    # Valid colors
    habit1 = HabitCreate(
        title="Habit with # color",
        frequency="daily",
        color="#4287f5"
    )
    assert habit1.color == "#4287f5"
    
    habit2 = HabitCreate(
        title="Habit without # color",
        frequency="daily",
        color="4287f5"
    )
    assert habit2.color == "#4287f5"  # Should add # prefix
    
    habit3 = HabitCreate(
        title="Habit with short color",
        frequency="daily",
        color="#f00"  # Short form
    )
    assert habit3.color == "#f00"
    
    # Invalid color
    with pytest.raises(ValidationError) as excinfo:
        HabitCreate(
            title="Habit with invalid color",
            frequency="daily",
            color="#XYZ"  # Not a valid hex color
        )
    
    assert "Color must be a valid hex color code" in str(excinfo.value) 