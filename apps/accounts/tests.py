from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse("auth-register")
        self.login_url = reverse("auth-login")

    def test_customer_registration_and_login(self):
        # 1. Register
        reg_payload = {
            "username": "unittest_cust",
            "email": "unittest_cust@example.com",
            "password": "StrongPassword@123",
            "password_confirm": "StrongPassword@123",
            "full_name": "Unit Test Customer",
            "phone_number": "+91 9998887776",
            "address": "123 Test St",
        }
        res = self.client.post(self.register_url, reg_payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["status"], "success")

        # 2. Login
        login_payload = {
            "username": "unittest_cust",
            "password": "StrongPassword@123",
        }
        res = self.client.post(self.login_url, login_payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data["data"])
        self.assertEqual(res.data["data"]["user"]["role"], User.Role.CUSTOMER)

    def test_invalid_login(self):
        res = self.client.post(self.login_url, {"username": "ghost", "password": "wrong"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
