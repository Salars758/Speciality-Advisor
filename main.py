# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta
import crud
import models
import schemas
import auth
import database
from database import engine
from apscheduler.schedulers.asyncio import AsyncIOScheduler

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SpecialityAdvisor API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # или укажите точные адреса: ["http://localhost:8080", "http://127.0.0.1:5500"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler = AsyncIOScheduler()

@app.on_event("startup")
def start_scheduler():
    db = database.SessionLocal()
    try:
        crud.cleanup_abandoned_sessions(db, max_age_minutes=30)  # сразу при старте
    finally:
        db.close()
    scheduler.add_job(
        lambda: crud.cleanup_abandoned_sessions(database.SessionLocal(), 30),
        'interval',
        minutes=15,  # каждые 15 минут
        id='cleanup_sessions'
    )
    scheduler.start()

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()
#pip install fastapi uvicorn[standard] sqlalchemy python-jose[cryptography] passlib[bcrypt] pydantic email-validator pymysql python-multipart
#uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Auth endpoints
@app.post("/auth/token", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db)
):
    user = crud.get_user_by_login(db, form_data.username)
    if not user or not auth.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": str(user.user_id), "role": user.role, "full_name": user.full_name},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- User ---
@app.post("/users/", response_model=schemas.UserRead)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    try:
        return crud.create_user(db, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/", response_model=List[schemas.UserRead])
def read_users(
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    return crud.get_users(db, current_user)

@app.get("/users/{user_id}", response_model=schemas.UserRead)
def read_user(user_id: int, db: Session = Depends(database.get_db), current_user: dict = Depends(auth.get_current_user)):
    user = crud.get_user(db, user_id)
    if not user or (current_user["role"] == "applicant" and current_user["user_id"] != user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}", response_model=schemas.UserRead)
def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        return crud.update_user(db, user_id, user_update, current_user)
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        result = crud.delete_user(db, user_id, current_user)
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        return {"detail": "User deactivated"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

# --- Trait ---
@app.post("/traits/", response_model=schemas.TraitRead)
def create_trait(
    trait: schemas.TraitCreate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        return crud.create_trait(db, trait, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@app.get("/traits/", response_model=List[schemas.TraitRead])
def read_traits(
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    return crud.get_traits(db, current_user)

@app.put("/traits/{trait_id}", response_model=schemas.TraitRead)
def update_trait(
    trait_id: int,
    trait_update: schemas.TraitUpdate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        return crud.update_trait(db, trait_id, trait_update, current_user)
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/traits/{trait_id}")
def delete_trait(
    trait_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        result = crud.delete_trait(db, trait_id, current_user)
        if not result:
            raise HTTPException(status_code=404, detail="Trait not found or in use")
        return {"detail": "Trait deactivated"}
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Specialization ---
@app.post("/specializations/", response_model=schemas.SpecializationRead)
def create_specialization(
    spec: schemas.SpecializationCreate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        return crud.create_specialization(db, spec, current_user)
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/specializations/", response_model=List[schemas.SpecializationRead])
def read_specializations(
    db: Session = Depends(database.get_db)
):
    return crud.get_specializations(db)

@app.put("/specializations/{spec_id}", response_model=schemas.SpecializationRead)
def update_specialization(
    spec_id: int,
    spec_update: schemas.SpecializationUpdate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        return crud.update_specialization(db, spec_id, spec_update, current_user)
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/specializations/{spec_id}")
def delete_specialization(
    spec_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        result = crud.delete_specialization(db, spec_id, current_user)
        if not result:
            raise HTTPException(status_code=404, detail="Specialization not found")
        return {"detail": "Specialization deactivated"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

# --- Test ---
@app.post("/tests/", response_model=schemas.TestRead)
def create_test(
    test: schemas.TestCreate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        return crud.create_test(db, test, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@app.get("/tests/", response_model=List[schemas.TestRead])
def read_tests(
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    return crud.get_tests(db, current_user)

@app.put("/tests/{test_id}", response_model=schemas.TestRead)
def update_test(
    test_id: int,
    test_update: schemas.TestUpdate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        return crud.update_test(db, test_id, test_update, current_user)
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/tests/{test_id}")
def delete_test(
    test_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        result = crud.delete_test(db, test_id, current_user)
        if not result:
            raise HTTPException(status_code=404, detail="Test not found or in use")
        return {"detail": "Test deactivated"}
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Question ---
@app.post("/questions/", response_model=schemas.QuestionRead)
def create_question(
    question: schemas.QuestionCreate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        return crud.create_question(db, question, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@app.get("/questions/", response_model=List[schemas.QuestionRead])
def read_questions(
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    return db.query(models.Question).all()

# --- Question ---
@app.get("/tests/{test_id}/questions/", response_model=List[schemas.QuestionRead])
def read_questions_for_test(
    test_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Возвращает все вопросы, принадлежащие определенному тесту."""
    # Проверка существования теста
    test = crud.get_test(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Получаем вопросы по test_id
    questions = db.query(models.Question).filter(models.Question.test_id == test_id).all()
    return questions

@app.put("/questions/{question_id}", response_model=schemas.QuestionRead)
def update_question(
    question_id: int,
    question_update: schemas.QuestionUpdate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        return crud.update_question(db, question_id, question_update, current_user)
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/questions/{question_id}")
def delete_question(
    question_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        result = crud.delete_question(db, question_id, current_user)
        if not result:
            raise HTTPException(status_code=404, detail="Question not found")
        return {"detail": "Question deleted"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

# --- AnswerOption ---
@app.get("/answers/", response_model=List[schemas.AnswerOptionRead])
def read_answer_options(
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    return db.query(models.AnswerOption).all()

@app.post("/answers/", response_model=schemas.AnswerOptionRead)
def create_answer_option(
    answer: schemas.AnswerOptionCreate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        return crud.create_answer_option(db, answer, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@app.put("/answers/{answer_id}", response_model=schemas.AnswerOptionRead)
def update_answer_option(
    answer_id: int,
    answer_update: schemas.AnswerOptionUpdate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        return crud.update_answer_option(db, answer_id, answer_update, current_user)
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/answers/{answer_id}")
def delete_answer_option(
    answer_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        result = crud.delete_answer_option(db, answer_id, current_user)
        if not result:
            raise HTTPException(status_code=404, detail="Answer not found")
        return {"detail": "Answer deleted"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

# --- SpecializationTrait ---
@app.post("/requirements/", response_model=schemas.SpecializationTraitRead)
def create_requirement(
    req: schemas.SpecializationTraitCreate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        return crud.create_specialization_trait(db, req, current_user)
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/requirements/{spec_id}/{trait_id}", response_model=schemas.SpecializationTraitRead)
def update_requirement(
    spec_id: int,
    trait_id: int,
    req_update: schemas.SpecializationTraitUpdate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        return crud.update_specialization_trait(db, spec_id, trait_id, req_update, current_user)
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/requirements/", response_model=List[schemas.SpecializationTraitRead])
def read_requirements(
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        return crud.read_specialization_traits(db, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@app.delete("/requirements/{spec_id}/{trait_id}")
def delete_requirement(
    spec_id: int,
    trait_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        result = crud.delete_specialization_trait(db, spec_id, trait_id, current_user)
        if not result:
            raise HTTPException(status_code=404, detail="Requirement not found")
        return {"detail": "Requirement deleted"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

# --- TestSession ---
@app.post("/sessions/", response_model=schemas.TestSessionRead)
def create_session(
    session: schemas.TestSessionCreate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        return crud.create_test_session(db, session, current_user)
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/sessions/{session_id}", response_model=schemas.TestSessionRead)
def read_session(
    session_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    session = crud.get_test_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if current_user["role"] == "applicant" and session.user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not your session")
    return session

@app.get("/users/{user_id}/sessions/", response_model=List[schemas.TestSessionRead])
def read_user_sessions(
    user_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    if current_user["role"] == "applicant" and current_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not your sessions")
    return crud.get_user_sessions(db, user_id)

@app.put("/sessions/{session_id}", response_model=schemas.TestSessionRead)
def update_session(
    session_id: int,
    session_update: schemas.TestSessionUpdate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        return crud.update_test_session(db, session_id, session_update, current_user)
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        result = crud.delete_test_session(db, session_id, current_user)
        if not result:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"detail": "Session deleted"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

# --- UserAnswer ---
@app.post("/answers/user/", response_model=schemas.UserAnswerRead)
def submit_answer(
    answer: schemas.UserAnswerCreate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        return crud.create_user_answer(db, answer, current_user)
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/sessions/{session_id}/answers/", response_model=List[schemas.UserAnswerRead])
def read_session_answers(
    session_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    session = crud.get_test_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if current_user["role"] == "applicant" and session.user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not your session")
    return crud.get_session_answers(db, session_id)

@app.delete("/answers/user/{record_id}")
def delete_user_answer_endpoint(
    record_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        result = crud.delete_user_answer(db, record_id, current_user)
        if not result:
            raise HTTPException(status_code=404, detail="Answer not found")
        return {"detail": "Answer deleted"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

# --- TestResult ---
@app.post("/results/", response_model=schemas.TestResultRead)
def create_result(
    result: schemas.TestResultCreate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        return crud.create_test_result(db, result, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@app.get("/users/{user_id}/results/", response_model=List[schemas.TestResultRead])
def read_user_results(
    user_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    if current_user["role"] == "applicant" and current_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not your results")
    return crud.get_user_results(db, user_id)

@app.put("/results/{user_id}/{trait_id}", response_model=schemas.TestResultRead)
def update_result(
    user_id: int,
    trait_id: int,
    result_update: schemas.TestResultUpdate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        return crud.update_test_result(db, user_id, trait_id, result_update, current_user)
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/results/{user_id}/{trait_id}")
def delete_result(
    user_id: int,
    trait_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        result = crud.delete_test_result(db, user_id, trait_id, current_user)
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")
        return {"detail": "Result deleted"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@app.get("/users/{user_id}/recommendations")
def get_recommendations(
    user_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    if current_user["role"] == "applicant" and current_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not your recommendations")
    try:
        recs = crud.get_recommendations_for_user(db, user_id)
        return recs
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/sessions/{session_id}/calculate-results/")
def trigger_calculate_results(
    session_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    session = crud.get_test_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not your session")
    if not session.is_completed:
        raise HTTPException(status_code=400, detail="Session not completed")
    try:
        crud.calculate_test_results(db, session_id, current_user)
        return {"detail": "Results calculated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats/specialization-recommendation-frequency", response_model=List[dict])
def get_specialization_recommendation_frequency_endpoint(
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """
    Возвращает частоту, с которой каждая активная специальность рекомендовалась пользователям.
    Доступно только админам и психологам.
    """
    if current_user["role"] not in ["admin", "psychologist"]:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return crud.get_specialization_recommendation_frequency(db)

# В main.py
@app.get("/stats/trait-average-scores", response_model=List[dict])
def get_trait_average_scores_endpoint(
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    if current_user["role"] not in ["admin", "psychologist"]:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return crud.get_trait_average_scores(db)