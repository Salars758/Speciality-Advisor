# schemas.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from decimal import Decimal
from datetime import datetime

# --- Auth ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None

# --- User ---
class UserBase(BaseModel):
    full_name: str = Field(..., max_length=255)
    login: str = Field(..., max_length=255)
    email: str = Field(..., max_length=255)

class UserCreate(UserBase):
    password: str = Field(..., max_length=255)
    role: str = "applicant"

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v:
            raise ValueError('Invalid email')
        return v

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    login: Optional[str] = Field(None, max_length=255)
    old_password: Optional[str] = Field(None, max_length=255)
    new_password: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)

class UserRead(UserBase):
    user_id: int
    role: str
    is_active: bool

    model_config = {"from_attributes": True}

# --- Trait ---
class TraitBase(BaseModel):
    trait_name: str = Field(..., max_length=255)
    trait_type: str = Field(..., max_length=255)
    description: Optional[str] = None

class TraitCreate(TraitBase):
    pass

class TraitUpdate(BaseModel):
    trait_name: Optional[str] = Field(None, max_length=255)
    trait_type: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None

class TraitRead(TraitBase):
    trait_id: int
    is_active: bool

    model_config = {"from_attributes": True}

# --- Specialization ---
class SpecializationBase(BaseModel):
    code: int
    name: str = Field(..., max_length=255)
    description: Optional[str] = None

class SpecializationCreate(SpecializationBase):
    pass

class SpecializationUpdate(BaseModel):
    code: Optional[int] = None
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None

class SpecializationRead(SpecializationBase):
    specialization_id: int
    is_active: bool

    model_config = {"from_attributes": True}

# --- Test ---
class TestBase(BaseModel):
    name: str = Field(..., max_length=255)
    instruction: Optional[str] = None

class TestCreate(TestBase):
    pass

class TestUpdate(TestBase):
    name: Optional[str] = Field(None, max_length=255)
    instruction: Optional[str] = Field(None, max_length=255)

class TestRead(TestBase):
    test_id: int
    is_active: bool

    model_config = {"from_attributes": True}

# --- Question ---
class QuestionBase(BaseModel):
    test_id: int
    trait_id: int
    question_number: int
    question_text: str

class QuestionCreate(BaseModel):
    test_id: int
    trait_id: int
    question_text: str

class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    question_number: Optional[int] = None

class QuestionRead(QuestionBase):
    question_id: int

    model_config = {"from_attributes": True}

# --- AnswerOption ---
class AnswerOptionBase(BaseModel):
    question_id: int
    answer_text: str
    score: Decimal = Field(ge=0, le=100)

class AnswerOptionCreate(AnswerOptionBase):
    pass

class AnswerOptionUpdate(BaseModel):
    question_id: Optional[int] = None
    answer_text: Optional[str] = None
    score: Optional[Decimal] = Field(default=None, ge=0, le=100)

class AnswerOptionRead(AnswerOptionBase):
    answer_id: int

    model_config = {"from_attributes": True}

# --- SpecializationTrait ---
class SpecializationTraitBase(BaseModel):
    specialization_id: int
    trait_id: int
    min_level: Decimal = Field(ge=0, le=100)
    weight: Decimal = Field(gt=0, le=1)

class SpecializationTraitCreate(SpecializationTraitBase):
    pass

class SpecializationTraitUpdate(BaseModel):
    min_level: Decimal = Field(ge=0, le=100)
    weight: Decimal = Field(gt=0, le=1)

class SpecializationTraitRead(SpecializationTraitBase):
    model_config = {"from_attributes": True}

# --- TestResult ---
class TestResultBase(BaseModel):
    user_id: int
    trait_id: int
    level: Decimal = Field(ge=0, le=100)

class TestResultCreate(TestResultBase):
    pass

class TestResultUpdate(BaseModel):
    level: Decimal = Field(ge=0, le=100)

class TestResultRead(TestResultBase):
    model_config = {"from_attributes": True}

# --- TestSession ---
class TestSessionBase(BaseModel):
    test_id: int

class TestSessionCreate(TestSessionBase):
    pass

class TestSessionUpdate(BaseModel):
    total_score: Optional[Decimal] = Field(None, ge=0, le=100)
    is_completed: Optional[bool] = None
    completed_at: Optional[datetime] = None

class TestSessionRead(BaseModel):
    session_id: int
    user_id: int
    test_id: int
    total_score: Decimal
    is_completed: bool
    started_at: datetime

    model_config = {"from_attributes": True}

# --- UserAnswer ---
class UserAnswerBase(BaseModel):
    session_id: int
    question_id: int
    answer_id: int

class UserAnswerCreate(UserAnswerBase):
    pass

class UserAnswerRead(UserAnswerBase):
    record_id: int

    model_config = {"from_attributes": True}