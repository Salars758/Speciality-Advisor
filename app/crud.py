# crud.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models, schemas
from typing import Optional
from datetime import datetime

# --- User ---
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.user_id == user_id, models.User.is_active == True).first()

def get_user_by_login(db: Session, login: str):
    return db.query(models.User).filter(models.User.login == login).first()

def get_users(db: Session, current_user: dict):
    role = current_user["role"]
    user_id = current_user["user_id"]
    query = db.query(models.User).filter(models.User.is_active == True)
    if role == "applicant":
        query = query.filter(models.User.user_id == user_id)
    elif role == "psychologist":
        query = query.filter(models.User.role == "applicant")
    return query.all()

def create_user(db: Session, user: schemas.UserCreate):
    if get_user_by_login(db, user.login):
        raise ValueError("Login already exists")
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise ValueError("Email already exists")
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate, current_user: dict):
    target_user = get_user(db, user_id)
    if not target_user:
        raise ValueError("User not found")
    if current_user["role"] == "applicant" and current_user["user_id"] != user_id:
        raise PermissionError("Applicants can only update their own profile")
    data = user_update.model_dump(exclude_unset=True)
    for key, value in data.items():
        if value is not None:
            setattr(target_user, key, value)
    db.commit()
    db.refresh(target_user)
    return target_user

def delete_user(db: Session, user_id: int, current_user: dict):
    if current_user["role"] != "admin":
        raise PermissionError("Only admin can delete users")
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if user:
        user.is_active = False
        db.commit()
        return True
    return False

# --- Trait ---
def get_trait(db: Session, trait_id: int):
    return db.query(models.Trait).filter(models.Trait.trait_id == trait_id, models.Trait.is_active == True).first()

def get_traits(db: Session, current_user: dict):
    query = db.query(models.Trait)
    if current_user["role"] == "applicant":
        query = query.filter(models.Trait.is_active == True)
    return query.all()

def create_trait(db: Session, trait: schemas.TraitCreate, current_user: dict):
    if current_user["role"] not in ["admin", "psychologist"]:
        raise PermissionError("Only admin or psychologist can create traits")
    db_trait = models.Trait(**trait.model_dump())
    db.add(db_trait)
    db.commit()
    db.refresh(db_trait)
    return db_trait

def update_trait(db: Session, trait_id: int, trait_update: schemas.TraitUpdate, current_user: dict):
    if current_user["role"] not in ["admin", "psychologist"]:
        raise PermissionError("Only admin or psychologist can update traits")
    trait = get_trait(db, trait_id)
    if not trait:
        raise ValueError("Trait not found")
    if trait_update.trait_type != trait.trait_type:
        used = db.query(models.SpecializationTrait).filter(models.SpecializationTrait.trait_id == trait_id).first()
        if used:
            raise ValueError("Cannot change trait_type: trait is already in use")
    for key, value in trait_update.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(trait, key, value)
    db.commit()
    db.refresh(trait)
    return trait

def delete_trait(db: Session, trait_id: int, current_user: dict):
    if current_user["role"] != "admin":
        raise PermissionError("Only admin can delete traits")
    
    trait = db.query(models.Trait).filter(models.Trait.trait_id == trait_id).first()
    if not trait:
        raise ValueError("Trait not found")
    used = db.query(models.SpecializationTrait).filter(
        models.SpecializationTrait.trait_id == trait_id
    ).first()
    if used:
        raise ValueError("Cannot delete trait: it is already in use by one or more specializations")
    trait.is_active = False
    db.commit()
    return True

# --- Specialization ---
def get_specialization(db: Session, spec_id: int):
    return db.query(models.Specialization).filter(models.Specialization.specialization_id == spec_id, models.Specialization.is_active == True).first()

def get_specializations(db: Session, current_user: dict):
    query = db.query(models.Specialization)
    if current_user["role"] == "applicant":
        query = query.filter(models.Specialization.is_active == True)
    return query.all()

def create_specialization(db: Session, spec: schemas.SpecializationCreate, current_user: dict):
    if current_user["role"] != "admin":
        raise PermissionError("Only admin can create specializations")
    if db.query(models.Specialization).filter(models.Specialization.code == spec.code).first():
        raise ValueError("Specialization code must be unique")
    db_spec = models.Specialization(**spec.model_dump())
    db.add(db_spec)
    db.commit()
    db.refresh(db_spec)
    return db_spec

def update_specialization(db: Session, spec_id: int, spec_update: schemas.SpecializationUpdate, current_user: dict):
    if current_user["role"] != "admin":
        raise PermissionError("Only admin can update specializations")
    spec = get_specialization(db, spec_id)
    if not spec:
        raise ValueError("Specialization not found")
    for key, value in spec_update.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(spec, key, value)
    db.commit()
    db.refresh(spec)
    return spec

def delete_specialization(db: Session, spec_id: int, current_user: dict):
    if current_user["role"] != "admin":
        raise PermissionError("Only admin can delete specializations")
    spec = db.query(models.Specialization).filter(models.Specialization.specialization_id == spec_id).first()
    if spec:
        spec.is_active = False
        db.commit()
        return True
    return False

# --- Test ---
def get_test_id_by_name(db: Session, name: str):
    return db.query(models.Test).filter(
        models.Test.name == name,
        models.Test.is_active == True
    ).order_by(models.Test.test_id.desc()).first()

def get_test(db: Session, test_id: int):
    return db.query(models.Test).filter(models.Test.test_id == test_id, models.Test.is_active == True).first()

def get_tests(db: Session, current_user: dict):
    query = db.query(models.Test)
    if current_user["role"] == "applicant":
        query = query.filter(models.Test.is_active == True)
    return query.all()

def create_test(db: Session, test: schemas.TestCreate, current_user: dict):
    if current_user["role"] not in ["admin", "psychologist"]:
        raise PermissionError("Only admin or psychologist can create tests")
    db_test = models.Test(**test.model_dump())
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    return db_test

def update_test(db: Session, test_id: int, test_update: schemas.TestUpdate, current_user: dict):
    if current_user["role"] not in ["admin", "psychologist"]:
        raise PermissionError("Only admin or psychologist can update tests")
    test = get_test(db, test_id)
    if not test:
        raise ValueError("Test not found")
    # Нельзя обновлять, если есть сессии
    session_exists = db.query(models.TestSession).filter(models.TestSession.test_id == test_id).first()
    if session_exists:
        raise ValueError("Cannot update test that has been used in sessions")
    for key, value in test_update.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(test, key, value)
    db.commit()
    db.refresh(test)
    return test

def delete_test(db: Session, test_id: int, current_user: dict):
    if current_user["role"] != "admin":
        raise PermissionError("Only admin can delete tests")
    test = db.query(models.Test).filter(models.Test.test_id == test_id).first()
    if not test:
        raise ValueError("Test not found")
    session_exists = db.query(models.TestSession).filter(
        models.TestSession.test_id == test_id).first()
    if session_exists:
        raise ValueError("Cannot delete test that has been used in sessions")
    test.is_active = False
    db.commit()
    return True

# --- Question ---
def get_question(db: Session, question_id: int):
    return db.query(models.Question).filter(models.Question.question_id == question_id).first()

def get_questions(db: Session, current_user: dict):
    query = db.query(models.Question)
    if current_user["role"] == "applicant":
        raise PermissionError("Only admin or psychologist can get questions")
    return query.all()

def create_question(db: Session, question: schemas.QuestionCreate, current_user: dict):
    if current_user["role"] not in ["admin", "psychologist"]:
        raise PermissionError("Only admin or psychologist can create questions")
    max_num = db.query(func.max(models.Question.question_number))\
    .filter(models.Question.test_id == question.test_id)\
    .scalar()
    next_num = (max_num or 0) + 1
    db_question = models.Question(
        test_id=question.test_id,
        question_number=next_num,
        question_text=question.question_text
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

def update_question(db: Session, question_id: int, question_update: schemas.QuestionUpdate, current_user: dict):
    if current_user["role"] not in ["admin", "psychologist"]:
        raise PermissionError("Only admin or psychologist can update questions")
    question = get_question(db, question_id)
    if not question:
        raise ValueError("Question not found")
    for key, value in question_update.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(question, key, value)
    db.commit()
    db.refresh(question)
    return question

def delete_question(db: Session, question_id: int, current_user: dict):
    if current_user["role"] not in ["admin", "psychologist"]:
        raise PermissionError("Only admin or psychologist can delete questions")
    question = db.query(models.Question).filter(models.Question.question_id == question_id).first()
    if question:
        db.delete(question)
        db.commit()
        return True
    return False

# --- AnswerOption ---
def get_answer_option(db: Session, answer_id: int):
    return db.query(models.AnswerOption).filter(models.AnswerOption.answer_id == answer_id).first()

def create_answer_option(db: Session, answer: schemas.AnswerOptionCreate, current_user: dict):
    if current_user["role"] not in ["admin", "psychologist"]:
        raise PermissionError("Only admin or psychologist can create answers")
    db_answer = models.AnswerOption(**answer.model_dump())
    db.add(db_answer)
    db.commit()
    db.refresh(db_answer)
    return db_answer

def update_answer_option(db: Session, answer_id: int, answer_update: schemas.AnswerOptionUpdate, current_user: dict):
    if current_user["role"] not in ["admin", "psychologist"]:
        raise PermissionError("Only admin or psychologist can update answers")
    answer = get_answer_option(db, answer_id)
    if not answer:
        raise ValueError("Answer not found")
    for key, value in answer_update.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(answer, key, value)
    db.commit()
    db.refresh(answer)
    return answer

def delete_answer_option(db: Session, answer_id: int, current_user: dict):
    if current_user["role"] not in ["admin", "psychologist"]:
        raise PermissionError("Only admin or psychologist can delete answers")
    answer = db.query(models.AnswerOption).filter(models.AnswerOption.answer_id == answer_id).first()
    if answer:
        db.delete(answer)
        db.commit()
        return True
    return False

# --- SpecializationTrait ---
def get_specialization_trait(db: Session, spec_id: int, trait_id: int):
    return db.query(models.SpecializationTrait).filter(
        models.SpecializationTrait.specialization_id == spec_id,
        models.SpecializationTrait.trait_id == trait_id
    ).first()

def create_specialization_trait(db: Session, req: schemas.SpecializationTraitCreate, current_user: dict):
    if current_user["role"] not in ["admin", "psychologist"]:
        raise PermissionError("Only admin or psychologist can create requirements")
    if not get_specialization(db, req.specialization_id):
        raise ValueError("Specialization not found")
    if not get_trait(db, req.trait_id):
        raise ValueError("Trait not found")
    db_req = models.SpecializationTrait(**req.model_dump())
    db.add(db_req)
    db.commit()
    db.refresh(db_req)
    return db_req

def update_specialization_trait(db: Session, spec_id: int, trait_id: int, req_update: schemas.SpecializationTraitUpdate, current_user: dict):
    if current_user["role"] not in ["admin", "psychologist"]:
        raise PermissionError("Only admin or psychologist can update requirements")
    req = get_specialization_trait(db, spec_id, trait_id)
    if not req:
        raise ValueError("Requirement not found")
    for key, value in req_update.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(req, key, value)
    db.commit()
    db.refresh(req)
    return req

def delete_specialization_trait(db: Session, spec_id: int, trait_id: int, current_user: dict):
    if current_user["role"] not in ["admin", "psychologist"]:
        raise PermissionError("Only admin or psychologist can delete requirements")
    req = db.query(models.SpecializationTrait).filter(
        models.SpecializationTrait.specialization_id == spec_id,
        models.SpecializationTrait.trait_id == trait_id
    ).first()
    if req:
        db.delete(req)
        db.commit()
        return True
    return False

# --- TestSession ---
def get_test_session(db: Session, session_id: int):
    return db.query(models.TestSession).filter(models.TestSession.session_id == session_id).first()

def get_user_sessions(db: Session, user_id: int):
    return db.query(models.TestSession).filter(models.TestSession.user_id == user_id).all()

def create_test_session(db: Session, session: schemas.TestSessionCreate, current_user: dict):
    if current_user["role"] != "applicant":
        raise PermissionError("Only applicants can start sessions")
    if current_user["user_id"] != session.user_id:
        raise PermissionError("Applicants can only start sessions for themselves")
    if not get_test(db, session.test_id):
        raise ValueError("Test not found")
    db_session = models.TestSession(**session.model_dump())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def update_test_session(db: Session, session_id: int, session_update: schemas.TestSessionUpdate, current_user: dict):
    if current_user["role"] != "admin":
        raise PermissionError("Only admin can finalize sessions")
    session = get_test_session(db, session_id)
    if not session:
        raise ValueError("Session not found")
    for key, value in session_update.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(session, key, value)
    if session_update.is_completed and not session.completed_at:
        session.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    return session

def delete_test_session(db: Session, session_id: int, current_user: dict):
    if current_user["role"] != "admin":
        raise PermissionError("Only admin can delete sessions")
    session = db.query(models.TestSession).filter(models.TestSession.session_id == session_id).first()
    if session:
        db.delete(session)
        db.commit()
        return True
    return False

# --- UserAnswer ---
def get_user_answer(db: Session, record_id: int):
    return db.query(models.UserAnswer).filter(models.UserAnswer.record_id == record_id).first()

def get_session_answers(db: Session, session_id: int):
    return db.query(models.UserAnswer).filter(models.UserAnswer.session_id == session_id).all()

def create_user_answer(db: Session, answer: schemas.UserAnswerCreate, current_user: dict):
    session = get_test_session(db, answer.session_id)
    if not session:
        raise ValueError("Session not found")
    if current_user["role"] == "applicant":
        if session.user_id != current_user["user_id"]:
            raise PermissionError("Applicants can only answer in their own sessions")
        if session.is_completed:
            raise ValueError("Cannot answer in completed session")
    existing = db.query(models.UserAnswer).filter(
        models.UserAnswer.session_id == answer.session_id,
        models.UserAnswer.question_id == answer.question_id
    ).first()
    if existing:
        raise ValueError("User has already answered this question in the session")

    db_answer = models.UserAnswer(**answer.model_dump())
    db.add(db_answer)
    db.commit()
    db.refresh(db_answer)
    return db_answer

def delete_user_answer(db: Session, record_id: int, current_user: dict):
    if current_user["role"] != "admin":
        raise PermissionError("Only admin can delete answers")
    answer = db.query(models.UserAnswer).filter(models.UserAnswer.record_id == record_id).first()
    if answer:
        db.delete(answer)
        db.commit()
        return True
    return False

# --- TestResult ---
def get_test_result(db: Session, user_id: int, trait_id: int):
    return db.query(models.TestResult).filter(
        models.TestResult.user_id == user_id,
        models.TestResult.trait_id == trait_id
    ).first()

def get_user_results(db: Session, user_id: int):
    return db.query(models.TestResult).filter(models.TestResult.user_id == user_id).all()

def create_test_result(db: Session, result: schemas.TestResultCreate, current_user: dict):
    if current_user["role"] != "admin":
        raise PermissionError("Only admin can calculate results")
    db_result = models.TestResult(**result.model_dump())
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result

def update_test_result(db: Session, user_id: int, trait_id: int, result_update: schemas.TestResultUpdate, current_user: dict):
    if current_user["role"] not in ["admin", "psychologist"]:
        raise PermissionError("Only admin or psychologist can correct results")
    result = get_test_result(db, user_id, trait_id)
    if not result:
        raise ValueError("Result not found")
    result.level = result_update.level
    db.commit()
    db.refresh(result)
    return result

def delete_test_result(db: Session, user_id: int, trait_id: int, current_user: dict):
    if current_user["role"] != "admin":
        raise PermissionError("Only admin can delete results")
    result = db.query(models.TestResult).filter(
        models.TestResult.user_id == user_id,
        models.TestResult.trait_id == trait_id
    ).first()
    if result:
        db.delete(result)
        db.commit()
        return True
    return False