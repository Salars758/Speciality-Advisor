# crud.py
from sqlalchemy.orm import Session
from sqlalchemy import func
import models
import schemas
import auth
from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict

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
        raise ValueError("Этот логин уже занят")
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise ValueError("Эта электронная почта уже занята")
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        full_name=user.full_name,
        login=user.login,
        email=user.email,
        password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate, current_user: dict):
    if current_user["role"] == "applicant" and current_user["user_id"] != user_id:
        raise PermissionError("Недостаточно прав")
    
    db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not db_user:
        raise ValueError("Пользователь не найден")

    # Проверка уникальности логина
    if user_update.login is not None and user_update.login != db_user.login:
        if db.query(models.User).filter(models.User.login == user_update.login).first():
            raise ValueError("Этот логин уже занят")

    # Проверка уникальности email
    if user_update.email is not None and user_update.email != db_user.email:
        if db.query(models.User).filter(models.User.email == user_update.email).first():
            raise ValueError("Эта электронная почта уже занята")

    # Обновление полей
    if user_update.full_name is not None:
        db_user.full_name = user_update.full_name
    if user_update.login is not None:
        db_user.login = user_update.login
    if user_update.email is not None:
        db_user.email = user_update.email

    # Обработка смены пароля (без изменений)
    if user_update.new_password is not None:
        if not user_update.old_password:
            raise ValueError("Требуется старый пароль для смены пароля")
        if not auth.verify_password(user_update.old_password, db_user.password):
            raise ValueError("Неверный старый пароль")
        db_user.password = auth.get_password_hash(user_update.new_password)

    db.commit()
    db.refresh(db_user)
    return db_user

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

def get_specializations(db: Session):
    return db.query(models.Specialization).filter(models.Specialization.is_active == True).all()

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
    # ВСЕГДА показываем только активные тесты — даже админам/психологам
    return db.query(models.Test).filter(models.Test.is_active == True).all()

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
        trait_id=question.trait_id, 
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

def read_specialization_traits(db: Session, current_user: dict):
    return db.query(models.SpecializationTrait).all()

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
    if not get_test(db, session.test_id):
        raise ValueError("Test not found")
    # Игнорируем session.user_id — подставляем из токена
    db_session = models.TestSession(
        user_id=current_user["user_id"],
        test_id=session.test_id
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def update_test_session(db: Session, session_id: int, session_update: schemas.TestSessionUpdate, current_user: dict):
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
    query = db.query(models.TestSession).filter(models.TestSession.session_id == session_id)
    
    # Ограничение по пользователю — только если НЕ админ
    if current_user["role"] != "admin":
        query = query.filter(models.TestSession.user_id == current_user["user_id"])
    
    session = query.first()
    
    if not session:
        return False

    # Запрет удаления завершённых сессий для не-админов
    if current_user["role"] != "admin" and session.is_completed:
        return False

    db.delete(session)
    db.commit()
    return True
    

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
    
    # Удаляем старый ответ на этот вопрос в этой сессии (если есть)
    existing = db.query(models.UserAnswer).filter(
        models.UserAnswer.session_id == answer.session_id,
        models.UserAnswer.question_id == answer.question_id
    ).first()
    if existing:
        db.delete(existing)
        db.commit()

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

def calculate_test_results(db: Session, session_id: int, current_user: dict):
    session = get_test_session(db, session_id)
    if not session or not session.is_completed:
        raise ValueError("Session not found or not completed")

    # Получить все ответы
    answers = db.query(models.UserAnswer)\
        .filter(models.UserAnswer.session_id == session_id)\
        .join(models.AnswerOption)\
        .join(models.Question)\
        .all()

    if not answers:
        raise ValueError("No answers in session")

    # Агрегация по trait_id
    trait_scores = defaultdict(list)
    for ans in answers:
        trait_id = ans.question.trait_id
        score = float(ans.answer.score)
        trait_scores[trait_id].append(score)

    # Удалить старые результаты (если есть)
    db.query(models.TestResult).filter(
        models.TestResult.user_id == session.user_id
    ).delete()

    # Создать новые результаты
    results = []
    for trait_id, scores in trait_scores.items():
        avg = round(sum(scores) / len(scores), 2)
        result = models.TestResult(
            user_id=session.user_id,
            trait_id=trait_id,
            level=min(max(avg, 0), 100)
        )
        db.add(result)
        results.append(result)

    db.commit()
    return results

def get_recommendations_for_user(db: Session, user_id: int):
    # Получить результаты пользователя
    user_results = {
        r.trait_id: float(r.level)
        for r in db.query(models.TestResult).filter(models.TestResult.user_id == user_id).all()
    }
    if not user_results:
        raise ValueError("No test results found")

    # Получить все названия качеств один раз
    trait_names = {
        t.trait_id: t.trait_name
        for t in db.query(models.Trait).all()
    }

    specs = db.query(models.Specialization).filter(models.Specialization.is_active == True).all()
    
    strict_recommendations = []  # Специальности, где все требования выполнены
    all_scores = []             # Все специальности с рассчитанной совместимостью

    for spec in specs:
        reqs = db.query(models.SpecializationTrait).filter(
            models.SpecializationTrait.specialization_id == spec.specialization_id
        ).all()
        if not reqs:
            continue

        meets_all = True
        total_weight = 0.0
        compatibility = 0.0
        required_trait_names = []

        # Проходим по всем требованиям, даже если одно уже не выполнено
        for req in reqs:
            user_level = user_results.get(req.trait_id, 0.0)
            trait_name = trait_names.get(req.trait_id, f"Качество {req.trait_id}")
            
            # Проверяем, выполняется ли минимальный порог
            if user_level < float(req.min_level):
                meets_all = False  # Но НЕ прерываем цикл — нужно посчитать совместимость полностью
            
            # Всегда учитываем в совместимости (даже при несоответствии)
            compatibility += (user_level / 100.0) * float(req.weight)
            total_weight += float(req.weight)
            required_trait_names.append(trait_name)

        # Пропускаем, если нет веса (деление на ноль)
        if total_weight <= 0:
            continue

        score = round(compatibility / total_weight, 4)

        # Формируем общий объект рекомендации
        rec = {
            "specialization_id": spec.specialization_id,
            "code": spec.code,
            "name": spec.name,
            "description": spec.description,
            "compatibility": score,
            "required_traits": required_trait_names
        }

        # Сохраняем для fallback
        all_scores.append(rec)

        # Если все требования выполнены — добавляем в строгие рекомендации
        if meets_all:
            strict_recommendations.append(rec)

    # Основной приоритет: если есть хотя бы одна строгая рекомендация — возвращаем только их
    if strict_recommendations:
        strict_recommendations.sort(key=lambda x: x["compatibility"], reverse=True)
        return strict_recommendations

    # Fallback: если ни одна специальность не подходит — возвращаем топ-3 по совместимости
    all_scores.sort(key=lambda x: x["compatibility"], reverse=True)
    fallback_recommendations = all_scores[:3]  # Можно изменить число при желании

    return fallback_recommendations


def cleanup_abandoned_sessions(db: Session, max_age_minutes: int = 30):
    """
    Удаляет незавершённые сессии, которые не обновлялись дольше max_age_minutes минут.
    Вызывать можно при запуске приложения или по расписанию.
    """
    cutoff = datetime.utcnow() - timedelta(minutes=max_age_minutes)
    abandoned = db.query(models.TestSession).filter(
        models.TestSession.is_completed == False,
        models.TestSession.updated_at < cutoff
    ).all()

    for session in abandoned:
        # Удаляем ответы (опционально, cascade сделает это автоматически)
        db.query(models.UserAnswer).filter(
            models.UserAnswer.session_id == session.session_id
        ).delete()
        db.delete(session)

    if abandoned:
        db.commit()
        print(f"Очищено {len(abandoned)} зависших сессий")

# В crud.py, после get_recommendations_for_user

# В crud.py, после get_recommendations_for_user
def get_specialization_recommendation_frequency(db: Session):
    """
    Возвращает частоту рекомендаций по ВСЕМ активным специальностям:
    учитывается ТОЛЬКО ПЕРВАЯ рекомендация для каждого пользователя.
    Специальности без рекомендаций включаются с count=0.
    """
    from collections import Counter
    
    # Получаем всех пользователей, у которых есть результаты
    user_ids = db.query(models.TestResult.user_id).distinct().all()
    user_ids = [uid[0] for uid in user_ids]
    counter = Counter()

    # Предзагружаем все активные специальности
    all_specs = {
        s.specialization_id: {"code": s.code, "name": s.name}
        for s in db.query(models.Specialization)
        .filter(models.Specialization.is_active == True)
        .all()
    }

    # Подсчитываем ТОЛЬКО ПЕРВУЮ рекомендацию для каждого пользователя
    for user_id in user_ids:
        try:
            recs = get_recommendations_for_user(db, user_id)
            if recs:  # Если список рекомендаций не пуст
                first_rec = recs[0]  # Берём ТОЛЬКО первую рекомендацию
                spec_id = first_rec["specialization_id"]
                counter[spec_id] += 1
        except ValueError:
            # Нет результатов — пропускаем
            continue

    # Формируем результат, включая все активные специальности
    result = []
    for spec_id, info in all_specs.items():
        count = counter.get(spec_id, 0)
        result.append({
            "specialization_id": spec_id,
            "code": info["code"],
            "name": info["name"],
            "count": count
        })

    # Сортируем по коду
    result.sort(key=lambda x: x["code"])
    return result

# В crud.py
def get_trait_average_scores(db: Session):
    """Возвращает средний балл по каждому качеству на основе test_result.
    Качества без результатов отображаются со средним = 0."""
    from sqlalchemy import func
    results = db.query(
        models.Trait.trait_id,
        models.Trait.trait_name,
        models.Trait.trait_type,
        func.coalesce(func.avg(models.TestResult.level), 0).label('average_score')
    ).outerjoin(models.TestResult, models.TestResult.trait_id == models.Trait.trait_id)\
     .filter(models.Trait.is_active == True)\
     .group_by(models.Trait.trait_id, models.Trait.trait_name, models.Trait.trait_type)\
     .all()
    return [
        {
            "trait_id": r.trait_id,
            "name": r.trait_name,
            "type": r.trait_type,
            "average_score": float(r.average_score or 0)
        }
        for r in results
    ]