# test_crud.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from decimal import Decimal
from app import models, schemas, crud

TEST_DATABASE_URL = "mysql+pymysql://adm:qwerty%40@192.168.56.101:3306/specialityadvisor"
engine = create_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    #models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()



#pytest application/tests/test_crud.py -v
#pytest test_crud.py::test_create_user -v -s


# Пользователь
# =======================

def test_create_user(db): # Создание пользователя (с учетом запрета дублирования некоторых полей)
    user_data = schemas.UserCreate(
        full_name="Виктор", login="aavityaa", email="daafarslan@test.com", password="123", role="applicant"
    )
    user = crud.create_user(db, user_data)
    print(f"\nЗарегестирован пользователь с данными:")
    print(f"\nid: {user.user_id}")
    print(f"full name: {user.full_name}")
    print(f"login: {user.login}")
    print(f"email: {user.email}")
    print(f"role: {user.role}")
    print(f"created at: {user.created_at}")

def test_get_user(db): #Вывод данных пользователя по конкретному id
    retrieved = crud.get_user(db, 2)
    print(f"\nid: {retrieved.user_id}")
    print(f"full name: {retrieved.full_name}")
    print(f"login: {retrieved.login}")
    print(f"email: {retrieved.email}")
    print(f"role: {retrieved.role}")
    print(f"created at: {retrieved.created_at}")

# def test_get_users_applicant(db): #Тест функционала - запрос списка пользователей от лица абитуриента
#     current_user = {"role": "applicant", "user_id": 1}
#     users = crud.get_users(db, current_user)
#     print(f"\nКоличество пользователей: {len(users)}")
#     for u in users:
#         print(f"id: {u.user_id}, login: {u.login}, role: {u.role}, name: {u.full_name}")

# def test_get_users_psychologist(db): #Тест функционала - запрос списка пользователей от лица психолога
#     current_user = {"role": "psychologist", "user_id": 6}
#     users = crud.get_users(db, current_user)
#     print(f"\nКоличество пользователей: {len(users)}")
#     for u in users:
#         print(f"id: {u.user_id}, login: {u.login}, role: {u.role}, name: {u.full_name}")

# def test_get_users_admin(db): #Тест функционала - запрос списка пользователей от лица админа
#     current_user = {"role": "admin", "user_id": 8}
#     users = crud.get_users(db, current_user)
#     print(f"\nКоличество пользователей: {len(users)}")
#     for u in users:
#         print(f"id: {u.user_id}, login: {u.login}, role: {u.role}, name: {u.full_name}")


def test_update_user(db): #Обновление данных пользователя, для пользователя - СВОИ, для остальных - ВСЕ
    current_user = {"role": "admin", "user_id": 1}
    retrieved = crud.get_user(db, 11)
    print(f"\nИзменены данные пользователя с:")
    print(f"\nid: {retrieved.user_id}")
    print(f"full name: {retrieved.full_name}")
    print(f"login: {retrieved.login}")
    print(f"email: {retrieved.email}")
    print(f"role: {retrieved.role}")
    print(f"created at: {retrieved.created_at}")
    print(f"\nна:")
    updated = crud.update_user(db, 11, schemas.UserUpdate(full_name="New Name", email="asdasdasd@yandex.ru"), current_user)
    print(f"\nid: {updated.user_id}")
    print(f"full name: {updated.full_name}")
    print(f"login: {updated.login}")
    print(f"email: {updated.email}")
    print(f"role: {updated.role}")
    print(f"created at: {updated.created_at}")

def test_delete_user(db): #Удаление (архивирование) учетной записи пользователя, только для админа
    current_user = {"role": "admin", "user_id": 8}
    retrieved = crud.get_user(db, 12)
    result = crud.delete_user(db, 12, current_user)
    print(f"\nУдаление пользователя: {result}")
    print(f"\nУдален пользователь с данными:")
    print(f"\nid: {retrieved.user_id}")
    print(f"full name: {retrieved.full_name}")
    print(f"login: {retrieved.login}")
    print(f"email: {retrieved.email}")
    print(f"role: {retrieved.role}")
    print(f"created at: {retrieved.created_at}")

# Специальности
# =======================

def test_create_specialization(db): #Создание специальности, только для админа
    current_user = {"role": "applicant", "user_id": 1}
    spec = crud.create_specialization(db, schemas.SpecializationCreate(code=708, name="Рыболовля", description="Рыб"), current_user)
    print(f"\nСоздана специальность {spec.name} с данными:")
    print(f"\ncode: {spec.code}")
    print(f"name: {spec.name}")
    print(f"description: {spec.description}")

def test_get_specializations(db): #Получение специальностей, для админа - ВСЕ, для остальных - ТОЛЬКО АКТИВНЫЕ
    current_user = {"role": "admin", "user_id": 2}
    specs = crud.get_specializations(db, current_user)
    print(f"\nКоличество специальностей: {len(specs)}")
    for s in specs:
        print(f"id: {s.specialization_id}, code: {s.code}, name: {s.name}, description: {s.description}")

def test_update_specialization(db): #Обновление специальности, только для админа
    admin_user = {"role": "admin", "user_id": 8}
    spec = crud.get_specialization(db, 4)
    print(f"\nДанные спецальности {spec.name} изменены с:")
    print(f"\ncode: {spec.code}")
    print(f"name: {spec.name}")
    print(f"description: {spec.description}")
    print(f"\n на:")
    updated = crud.update_specialization(db, 4, schemas.SpecializationUpdate(name="Ежеловля"), admin_user)
    print(f"\ncode: {updated.code}")
    print(f"name: {updated.name}")
    print(f"description: {updated.description}")

def test_delete_specialization(db): #Удаление (архивирование) специалности, только для админа
    admin_user = {"role": "admin", "user_id": 8}
    spec = crud.get_specialization(db, 4)
    result = crud.delete_specialization(db, 4, admin_user)
    print(f"\nУдаление специальности: {result}")
    print(f"\nУдалена специальность с данными:")
    print(f"\ncode: {spec.code}")
    print(f"name: {spec.name}")
    print(f"description: {spec.description}")

# Качества
# =======================

def test_create_trait(db): #Создание нового качества
    current_user = {"role": "admin", "user_id": 1}
    trait = crud.create_trait(db, schemas.TraitCreate(trait_name="T2", trait_type="TT2", description="D2"), current_user)
    print(f"\nСоздано качество с данными:")
    print(f"\ntrait_name: {trait.trait_name}")
    print(f"trait_type: {trait.trait_type}")
    print(f"description: {trait.description}")

def test_get_traits(db): #Получение качеств
    current_user = {"role": "applicant", "user_id": 2}
    traits = crud.get_traits(db, current_user)
    print(f"\nКоличество качеств: {len(traits)}")
    for t in traits:
        print(f"id: {t.trait_id}, trait_name: {t.trait_name}, trait_type: {t.trait_type}, description: {t.description}")

def test_update_trait(db): #Обновление данных качества
    psy_user = {"role": "psychologist", "user_id": 1}
    trait = crud.get_trait(db, 2)
    print(f"\nДанные качества {trait.trait_name} изменены с:")
    print(f"\ntrait_name: {trait.trait_name}")
    print(f"trait_type: {trait.trait_type}")
    print(f"description: {trait.description}")
    print(f"\n на:")
    updated = crud.update_trait(db, trait.trait_id, schemas.TraitUpdate(trait_name="T8"), psy_user)
    print(f"\ntrait_name: {updated.trait_name}")
    print(f"trait_type: {updated.trait_type}")
    print(f"description: {updated.description}")

def test_delete_trait(db): #Удаление (архивирование) качества
    admin_user = {"role": "admin", "user_id": 2}
    trait = crud.get_trait(db, 1)
    result = crud.delete_trait(db, 1, admin_user)
    print(f"\nУдаление качества: {result}")
    print(f"\nУдалено качество с данными:")
    print(f"\ntrait_name: {trait.trait_name}")
    print(f"trait_type: {trait.trait_type}")
    print(f"description: {trait.description}")

# Тесты
# =======================

def test_create_test(db): #Создание теста (название направление теста (область, которую тестирует данный тест). инструкция описывает требования к тесту)
    current_user = {"role": "admin", "user_id": 1}
    test = crud.create_test(db, schemas.TestCreate(name="Test1", instruction="Инстр."), current_user)
    print(f"\nСоздан тест с данными:")
    print(f"\nname: {test.name}")
    print(f"instruction: {test.instruction}")

def test_get_tests(db): #Получение тестов
    current_user = {"role": "applicant", "user_id": 2}
    tests = crud.get_tests(db, current_user)
    print(f"\nКоличество тестов: {len(tests)}")
    for t in tests:
        print(f"id: {t.test_id}, name: {t.name}, instruction: {t.instruction}")

def test_update_test(db): #Обновление данные теста
    psy_user = {"role": "psychologist", "user_id": 1}
    test = crud.get_test(db, 2)
    print(f"\nДанные теста {test.name} изменены с:")
    print(f"\nname: {test.name}")
    print(f"instruction: {test.instruction}")
    print(f"\n на:")
    updated = crud.update_test(db, 2, schemas.TestUpdate(name="New"), psy_user)
    print(f"\nname: {updated.name}")
    print(f"instruction: {updated.instruction}")

def test_delete_test(db): #Удаление (ахрхивирование) теста
    admin_user = {"role": "admin", "user_id": 2}
    test = crud.get_test(db, 2)
    result = crud.delete_test(db, 2, admin_user)
    print(f"\nУдаление теста: {result}")
    print(f"\nУдален тест с данными:")
    print(f"\ntrait_name: {test.name}")
    print(f"trait_type: {test.instruction}")

# Вопросы
# =======================

def test_create_question(db): #Создание нового вопроса в каком-то тесте, доступ только для админов и психологов
    psy_user = {"role": "admin", "user_id": 1}
    test_name = "Новый тест"
    test_id_t = crud.get_test_id_by_name(db, test_name)
    print({test_id_t.test_id})
    q = crud.create_question(db, schemas.QuestionCreate(test_id=test_id_t.test_id, question_text="Q3"), psy_user)
    print(f"\nСоздан новый вопрос для теста: {test_name}")
    print(f"\nquestion_text: {q.question_text}")

def test_get_questions(db): #Получение вопросов
    current_user = {"role": "admin", "user_id": 2}
    questions = crud.get_questions(db, current_user)
    print(f"\nКоличество тестов: {len(questions)}")
    for q in questions:
        print(f"id: {q.question_id}, test_id: {q.test_id}, question_number: {q.question_number}, question_text: {q.question_text}")

def test_update_question(db): #Обновление данных вопроса
    psy_user = {"role": "psychologist", "user_id": 1}
    question = crud.get_question(db, 2)
    print(f"\nДанные вопроса {question.question_text} изменены с:")
    print(f"\nquestion_id: {question.question_id}")
    print(f"test_id: {question.test_id}")
    print(f"question_num: {question.question_number}")
    print(f"question_text: {question.question_text}")
    print(f"\n на:")
    updated = crud.update_question(db, 2, schemas.QuestionUpdate(question_text="New"), psy_user)
    print(f"\nquestion_id: {updated.question_id}")
    print(f"test_id: {updated.test_id}")
    print(f"question_num: {updated.question_number}")
    print(f"question_text: {updated.question_text}")

def test_delete_question(db):
    psy_user = {"role": "psychologist", "user_id": 1}
    question = crud.get_question(db, 3)
    result = crud.delete_question(db, 3, psy_user)
    print(f"\nУдаление вопроса: {result}")
    print(f"\nУдален вопрос с данными:")
    print(f"\nquestion_id: {question.question_id}")
    print(f"test_id: {question.test_id}")
    print(f"question_number: {question.question_number}")
    print(f"question_text: {question.question_text}")


# Варианты ответов
# =============================

def test_create_answer_option(db): #Создание ответа для какого-то вопроса, доступ только для админов и психологов
    psy_user = {"role": "psychologist", "user_id": 1}
    answer = crud.create_answer_option(db, schemas.AnswerOptionCreate(
        question_id=1, answer_text="Ответ", score=Decimal('95.50')
    ), psy_user)
    print(f"\nСоздан ответ для вопроса с id: {answer.question_id}")
    print(f"answer_text: {answer.answer_text}")
    print(f"score: {answer.score}")


def test_update_answer_option(db): #Обновление данных варианта ответа
    psy_user = {"role": "psychologist", "user_id": 1}
    updated = crud.update_answer_option(db, 1, schemas.AnswerOptionUpdate(
        answer_text="Обновлённый ответ", score=Decimal('80.00')
    ), psy_user)
    print(f"\nДанные варианта ответа обновлены:")
    print(f"answer_id: {updated.answer_id}")
    print(f"question_id: {updated.question_id}")
    print(f"answer_text: {updated.answer_text}")
    print(f"score: {updated.score}")


def test_delete_answer_option(db): #Удаление варианта ответа
    psy_user = {"role": "psychologist", "user_id": 1}
    answer = crud.get_answer_option(db, 3)
    result = crud.delete_answer_option(db, 3, psy_user)
    print(f"\nУдаление варианта ответа: {result}")
    if answer:
        print(f"Удалён ответ с данными:")
        print(f"answer_id: {answer.answer_id}")
        print(f"question_id: {answer.question_id}")
        print(f"answer_text: {answer.answer_text}")
        print(f"score: {answer.score}")
    else:
        print("Ответ не найден до удаления")

# Требования специальности
# =============================

def test_create_specialization_trait(db): #Создание требований специальности
    psy_user = {"role": "psychologist", "user_id": 2}
    req = crud.create_specialization_trait(db, schemas.SpecializationTraitCreate(
        specialization_id=2,
        trait_id=3,
        min_level=5,
        weight=Decimal('0.75')
    ), psy_user)
    print(f"\nСозданы требования для специальности с id: {req.specialization_id}")
    print(f"trait_id: {req.trait_id}")
    print(f"min_level: {req.min_level}")
    print(f"weight: {req.weight}")

def test_update_specialization_trait(db):
    psy_user = {"role": "psychologist", "user_id": 2}
    updated = crud.update_specialization_trait(
        db, 2, 1,
        schemas.SpecializationTraitUpdate(min_level=8, weight=Decimal('0.9')), psy_user
    )
    print(f"\nДанные требований специальности обновлены:")
    print(f"\nspecialization_id: {updated.specialization_id}")
    print(f"trait_id: {updated.trait_id}")
    print(f"min_level: {updated.min_level}")
    print(f"weight: {updated.weight}")


def test_delete_specialization_trait(db):
    psy_user = {"role": "psychologist", "user_id": 2}
    spec_trait = crud.get_specialization_trait(db, 2, 3)
    result = crud.delete_specialization_trait(db, 2, 3, psy_user)
    print(f"Удалёно требование специальности с данными:")
    print(f"specialization_id: {spec_trait.specialization_id}")
    print(f"trait_id: {spec_trait.trait_id}")
    print(f"min_level: {spec_trait.min_level}")
    print(f"weight: {spec_trait.weight}")

# Результаты тестов
# ===============================

def test_create_test_result(db): #Создание нового результата теста
    current_user = {"role": "admin", "user_id": 1}
    result = crud.create_test_result(db, schemas.TestResultCreate(
        user_id=3, trait_id=3, level=Decimal('85.25')
    ), current_user)
    print(f"\nСозданы результаты теста для пользователя с id: {result.user_id}")
    print(f"trait_id: {result.trait_id}")
    print(f"level: {result.level}")

def test_update_test_result(db):
    psy_user = {"role": "psychologist", "user_id": 2}
    updated = crud.update_test_result(db, 3, 1, schemas.TestResultUpdate(level=Decimal('3.0')), psy_user)
    print(f"\nДанные результата теста обновлены:")
    print(f"\nuser_id: {updated.user_id}")
    print(f"trait_id: {updated.trait_id}")
    print(f"level: {updated.level}")

def test_delete_test_result(db):
    admin_user = {"role": "admin", "user_id": 1}
    test_res = crud.get_test_result(db, 3, 3)
    result = crud.delete_test_result(db, 3, 3, admin_user)
    print(f"Удалён результат теста с данными:")
    print(f"\nuser_id: {test_res.user_id}")
    print(f"trait_id: {test_res.trait_id}")
    print(f"level: {test_res.level}")

# Сессии тестов
# =============================

def test_create_test_session(db): #Создание новой сессии теста
    current_user = {"role": "applicant", "user_id": 4}
    session = crud.create_test_session(db, schemas.TestSessionCreate(
        user_id=4, test_id=1
    ), current_user)
    print(f"\nСоздана сессия теста для пользователя с id: {session.user_id}")
    print(f"test_id: {session.test_id}")

def test_update_test_session(db):
    admin_user = {"role": "admin", "user_id": 1}
    updated = crud.update_test_session(db, 2, schemas.TestSessionUpdate(is_completed=True, total_score=Decimal('88.50')), admin_user)
    print(f"\nДанные сессии теста обновлены:")
    print(f"\nsession_id: {updated.session_id}")
    print(f"user_id: {updated.user_id}")
    print(f"test_id: {updated.test_id}")
    print(f"total_score: {updated.total_score}")
    print(f"completed_at: {updated.completed_at}")


def test_delete_test_session(db):
    admin_user = {"role": "admin", "user_id": 1}
    tes_sess = crud.get_test_session(db, 1)
    result = crud.delete_test_session(db, 1, admin_user)
    print(f"Удалёна сессия теста с данными:")
    print(f"\nuser_id: {tes_sess.user_id}")
    print(f"trait_id: {tes_sess.test_id}")
    print(f"total_score: {tes_sess.total_score}")


# Ответы абитуриентов
# ================================

def test_create_user_answer(db): #Создание ответа абитуриента
    current_user = {"role": "applicant", "user_id": 3}
    user_answer = crud.create_user_answer(db, schemas.UserAnswerCreate(
        session_id=1,
        question_id=1,
        answer_id=1
    ), current_user)
    print(f"\nСоздан ответ пользователя с id сессии: {user_answer.session_id}")
    print(f"question_id: {user_answer.question_id}")
    print(f"answer_id: {user_answer.answer_id}")