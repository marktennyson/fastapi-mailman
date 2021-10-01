"""
Dummy email backend that does nothing.
"""

from fastapi_mailman.backends.base import BaseEmailBackend


class EmailBackend(BaseEmailBackend):
    async def send_messages(self, email_messages):
        return len(list(email_messages))
