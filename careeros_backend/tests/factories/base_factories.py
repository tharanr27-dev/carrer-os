"""Factories for generating fake test data using factory_boy and Faker."""

import uuid
from datetime import datetime, timezone

import factory
from factory import Faker, LazyFunction


class UserFactory(factory.Factory):
    class Meta:
        model = dict

    id = LazyFunction(uuid.uuid4)
    email = Faker("email")
    full_name = Faker("name")
    is_active = True
    is_verified = True
    role = "candidate"
    created_at = LazyFunction(lambda: datetime.now(timezone.utc))


class RecruiterFactory(factory.Factory):
    class Meta:
        model = dict

    id = LazyFunction(uuid.uuid4)
    email = Faker("company_email")
    full_name = Faker("name")
    role = "recruiter"
    company_id = LazyFunction(uuid.uuid4)


class CollegeFactory(factory.Factory):
    class Meta:
        model = dict

    id = LazyFunction(uuid.uuid4)
    name = Faker("company")
    domain = Faker("domain_name")
    city = Faker("city")


class CompanyFactory(factory.Factory):
    class Meta:
        model = dict

    id = LazyFunction(uuid.uuid4)
    name = Faker("company")
    website = Faker("url")
    industry = "Technology"


class ResumeFactory(factory.Factory):
    class Meta:
        model = dict

    id = LazyFunction(uuid.uuid4)
    user_id = LazyFunction(uuid.uuid4)
    title = Faker("job")
    content = Faker("text", max_nb_chars=500)
    version = 1
    is_primary = True


class MentorSessionFactory(factory.Factory):
    class Meta:
        model = dict

    id = LazyFunction(uuid.uuid4)
    user_id = LazyFunction(uuid.uuid4)
    is_active = True


class JobFactory(factory.Factory):
    class Meta:
        model = dict

    id = LazyFunction(uuid.uuid4)
    title = Faker("job")
    company = Faker("company")
    location = Faker("city")
    description = Faker("text", max_nb_chars=300)
    is_active = True


class InterviewSessionFactory(factory.Factory):
    class Meta:
        model = dict

    id = LazyFunction(uuid.uuid4)
    user_id = LazyFunction(uuid.uuid4)
    interview_type = "technical"
    status = "in_progress"


class CommunicationSessionFactory(factory.Factory):
    class Meta:
        model = dict

    id = LazyFunction(uuid.uuid4)
    user_id = LazyFunction(uuid.uuid4)
    session_type = "presentation"
    status = "in_progress"


class RecommendationFactory(factory.Factory):
    class Meta:
        model = dict

    id = LazyFunction(uuid.uuid4)
    user_id = LazyFunction(uuid.uuid4)
    title = Faker("sentence", nb_words=5)
    recommendation_type = "career_path"
    score = 0.91


class AIResponseFactory(factory.Factory):
    class Meta:
        model = dict

    status = "success"
    response_text = "Mocked provider response"
    tokens_used = 42
    latency_ms = 12
    provider = "mock"
