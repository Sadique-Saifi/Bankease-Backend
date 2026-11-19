import random
import string
from django.db import transaction
from apps.accounts.models import CustomerProfile

def generate_customer_number():
    """Generate a unique 10-digit customer number prefixed with CUST."""
    while True:
        num = f"CUST{''.join(random.choices(string.digits, k=6))}"
        if not CustomerProfile.objects.filter(customer_number=num).exists():
            return num
