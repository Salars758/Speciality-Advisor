# populate.py
from sqlalchemy.orm import Session
from app import models, database, schemas

def populate():
    engine = database.engine
    models.Base.metadata.create_all(bind=engine)
    db = Session(engine)

    try:
        # Пользователи
        user1 = models.User(full_name="Арслан", login="arslan", password="123", email="arslan@example.com", role="applicant")
        user2 = models.User(full_name="Психолог Иван", login="psy_iv", password="123", email="psy@example.com", role="psychologist")
        admin = models.User(full_name="Админ", login="admin", password="123", email="admin@example.com", role="admin")
        db.add_all([user1, user2, admin])

        # Качества
        trait1 = models.Trait(trait_name="Аналитическое мышление", trait_type="Когнитивное", description="Способность анализировать информацию")
        trait2 = models.Trait(trait_name="Коммуникабельность", trait_type="Личностное", description="Умение взаимодействовать с людьми")
        db.add_all([trait1, trait2])

        # Специальности
        spec1 = models.Specialization(code=501, name="Информатика и вычислительная техника", description="Разработка ПО, архитектура систем")
        spec2 = models.Specialization(code=555, name="Психология", description="Диагностика и коррекция")
        db.add_all([spec1, spec2])

        db.commit()
        db.refresh(spec1); db.refresh(spec2); db.refresh(trait1); db.refresh(trait2)

        # Требования
        req1 = models.SpecializationTrait(specialization_id=spec1.specialization_id, trait_id=trait1.trait_id, min_level=4.0, weight=0.8)
        req2 = models.SpecializationTrait(specialization_id=spec2.specialization_id, trait_id=trait2.trait_id, min_level=3.0, weight=0.7)
        db.add_all([req1, req2])

        # Тест
        test = models.Test(name="Профориентационный тест", instruction="Ответьте на все вопросы")
        db.add(test)
        db.commit()
        db.refresh(test)

        # Вопросы
        q1 = models.Question(test_id=test.test_id, question_number=1, question_text="Вам нравится решать логические задачи?")
        q2 = models.Question(test_id=test.test_id, question_number=2, question_text="Любите ли вы общаться с новыми людьми?")
        db.add_all([q1, q2])
        db.commit()
        db.refresh(q1); db.refresh(q2)

        # Ответы
        a1 = models.AnswerOption(question_id=q1.question_id, answer_text="Очень нравится", score=5.0)
        a2 = models.AnswerOption(question_id=q1.question_id, answer_text="Иногда", score=3.0)
        a3 = models.AnswerOption(question_id=q1.question_id, answer_text="Не нравится", score=0.0)
        a4 = models.AnswerOption(question_id=q2.question_id, answer_text="Очень люблю", score=5.0)
        a5 = models.AnswerOption(question_id=q2.question_id, answer_text="Нейтрально", score=3.0)
        a6 = models.AnswerOption(question_id=q2.question_id, answer_text="Не люблю", score=0.0)
        db.add_all([a1, a2, a3, a4, a5, a6])

        db.commit()
        print("Тестовые данные успешно добавлены!")

    except Exception as e:
        db.rollback()
        print(f"Ошибка при заполнении: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    populate()