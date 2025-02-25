import pytest
from tests.factories import InstagramUserFactory

@pytest.mark.django_db
def test_instagram_user(instagram_user):
    assert instagram_user.__str__ == "test_user"
