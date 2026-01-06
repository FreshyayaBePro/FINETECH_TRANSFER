import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_views_status_code_200(client):
    user = User.objects.create_user(
        email="test@test.com",
        phone="90000000",
        password="pass1234",
        is_verified=True
    )

    client.login(email="test@test.com", password="pass1234")

    urls = [
        reverse("admin_dashboard"),
        reverse("transaction_history"),
        reverse("activate_account"),
    ]

    for url in urls:
        response = client.get(url)
        assert response.status_code == 200
