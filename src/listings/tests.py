from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class TasteLocalUnitTests(TestCase):

    # -------------------------------------------------
    # UT01 - Test user creation
    # -------------------------------------------------
    def test_user_creation(self):
        user = User.objects.create(username="tourist1")
        self.assertEqual(user.username, "tourist1")


    # -------------------------------------------------
    # UT02 - Test user password validation
    # -------------------------------------------------
    def test_user_password(self):
        user = User.objects.create_user(username="tourist2", password="testpass123")
        self.assertTrue(user.check_password("testpass123"))


    # -------------------------------------------------
    # UT03 - Test listing queryset retrieval
    # -------------------------------------------------
    def test_listing_queryset(self):
        users = User.objects.all()
        self.assertIsNotNone(users)


    # -------------------------------------------------
    # UT04 - Test database record count
    # -------------------------------------------------
    def test_user_count(self):
        User.objects.create(username="userA")
        User.objects.create(username="userB")

        count = User.objects.count()
        self.assertEqual(count, 2)